"""
Research Safety
===============
Protections against:
- look-ahead bias
- overfitting
- survivorship bias
- parameter leakage
- data leakage
- cherry-picking
- repeated optimisation against holdout data
- inconsistent datasets
- false Python/Pine parity
- duplicate experiments
- unrecorded failed experiments

Separate datasets/concepts for:
TRAIN, VALIDATION, OUT_OF_SAMPLE, FORWARD
"""

import hashlib
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class DatasetSplit(Enum):
    """Dataset split types for research safety."""
    TRAIN = "TRAIN"
    VALIDATION = "VALIDATION"
    OUT_OF_SAMPLE = "OUT_OF_SAMPLE"
    FORWARD = "FORWARD"


class SafetyViolation(Enum):
    """Types of safety violations."""
    LOOK_AHEAD_BIAS = "LOOK_AHEAD_BIAS"
    OVERFITTING = "OVERFITTING"
    SURVIVORSHIP_BIAS = "SURVIVORSHIP_BIAS"
    PARAMETER_LEAKAGE = "PARAMETER_LEAKAGE"
    DATA_LEAKAGE = "DATA_LEAKAGE"
    CHERRY_PICKING = "CHERRY_PICKING"
    REPEATED_OPTIMISATION = "REPEATED_OPTIMISATION"
    INCONSISTENT_DATASETS = "INCONSISTENT_DATASETS"
    FALSE_PARITY = "FALSE_PARITY"
    DUPLICATE_EXPERIMENT = "DUPLICATE_EXPERIMENT"
    UNRECORDED_FAILURE = "UNRECORDED_FAILURE"


@dataclass
class SafetyCheck:
    """Result of a safety check."""
    passed: bool
    violation: Optional[SafetyViolation] = None
    details: str = ""
    severity: str = "ERROR"  # ERROR, WARNING, INFO


@dataclass
class DatasetInfo:
    """Information about a dataset split."""
    split: DatasetSplit
    symbol: str
    timeframe: str
    start_date: str
    end_date: str
    bars: int
    hash: str  # Hash of the data for integrity


class ResearchSafety:
    """
    Research safety protections.
    
    Explicitly designs protections against common research pitfalls.
    Separates datasets: TRAIN, VALIDATION, OUT_OF_SAMPLE, FORWARD.
    """
    
    def __init__(self, data_dir: Path = Path(r"C:\Users\wigmore\trading_stack\data")):
        self.data_dir = data_dir
        self._dataset_registry: Dict[str, DatasetInfo] = {}
        self._experiment_hashes: Set[str] = set()
        self._optimisation_history: List[Dict[str, Any]] = []
        self._max_optimisations_per_holdout = 3
    
    def register_dataset(
        self,
        split: DatasetSplit,
        symbol: str,
        timeframe: str,
        start_date: str,
        end_date: str,
    ) -> DatasetInfo:
        """Register a dataset split with integrity hash."""
        # Load data to compute hash
        import pandas as pd
        csv_path = self.data_dir / symbol / f"{symbol}_{timeframe}.csv"
        if not csv_path.exists():
            raise FileNotFoundError(f"Data not found: {csv_path}")
        
        df = pd.read_csv(csv_path)
        # Filter to date range
        if 'open_time' in df.columns:
            if pd.to_numeric(df['open_time'], errors='coerce').iloc[0] > 1e15:
                df['open_time'] = df['open_time'].astype('int64') // 1000
            df['datetime'] = pd.to_datetime(df['open_time'], unit='ms')
        elif 'timestamp' in df.columns:
            df['datetime'] = pd.to_datetime(df['timestamp'])
        
        df = df.set_index('datetime').sort_index()
        df = df[(df.index >= start_date) & (df.index <= end_date)]
        
        # Compute hash of the data
        data_hash = hashlib.sha256(
            df[['open', 'high', 'low', 'close', 'volume']].to_numpy().tobytes()
        ).hexdigest()[:16]
        
        info = DatasetInfo(
            split=split,
            symbol=symbol,
            timeframe=timeframe,
            start_date=start_date,
            end_date=end_date,
            bars=len(df),
            hash=data_hash,
        )
        
        key = f"{split.value}_{symbol}_{timeframe}_{start_date}_{end_date}"
        self._dataset_registry[key] = info
        
        return info
    
    def get_dataset(self, split: DatasetSplit, symbol: str, timeframe: str,
                    start_date: str, end_date: str) -> Optional[DatasetInfo]:
        """Get registered dataset info."""
        key = f"{split.value}_{symbol}_{timeframe}_{start_date}_{end_date}"
        return self._dataset_registry.get(key)
    
    def check_look_ahead_bias(
        self,
        strategy_code: str,
        indicators_used: List[str],
    ) -> SafetyCheck:
        """Check for look-ahead bias in strategy code."""
        # Genuinely suspicious look-ahead patterns in Pine/Python.
        #
        # NOTE: bare series brackets (close[1], high[2], ...) are NOT look-ahead.
        # A positive integer offset in Pine indexes PAST bars (close[1] = previous bar),
        # so flagging the bracket itself is a false positive. Only genuinely future /
        # repainting / realtime-only constructs are flagged.
        import re
        look_ahead_patterns = [
            'security(',        # can access other-symbol/timeframe data carelessly
            'request.security', # Pine v5
            'barstate.islast',  # only true on last bar (repaint risk)
            'barstate.isrealtime',  # real-time only
            'lookahead',
            'lookahead_on',
        ]
        
        violations = []
        for pattern in look_ahead_patterns:
            if pattern in strategy_code:
                violations.append(pattern)
        # Indexed series references: ONLY a non-negative LITERAL integer index
        # (close[1], close[0]) is a known-safe past-bar reference. Dynamic/unknown
        # indices (close[i], high[offset]) and negative indices (close[-1]) are
        # conservatively FLAGGED -- never silently exempted.
        for match in re.finditer(r'\b(?:close|high|low|open|volume)\s*\[([^\]]*)\]', strategy_code):
            inner = match.group(1).strip()
            if re.fullmatch(r'\d+', inner):
                continue  # non-negative literal -> known-safe past-bar access
            if match.group(0) not in violations:
                violations.append(match.group(0))
        
        if violations:
            return SafetyCheck(
                passed=False,
                violation=SafetyViolation.LOOK_AHEAD_BIAS,
                details=f"Potential look-ahead patterns found: {violations}",
                severity="WARNING",
            )
        
        return SafetyCheck(passed=True, details="No obvious look-ahead patterns detected")
    
    def check_overfitting(
        self,
        train_result: Dict[str, Any],
        validation_result: Dict[str, Any],
        oos_result: Optional[Dict[str, Any]] = None,
        degradation_threshold: float = 0.3,
    ) -> SafetyCheck:
        """Check for overfitting by comparing train/validation/OOS performance."""
        train_pf = train_result.get('profit_factor', 0)
        val_pf = validation_result.get('profit_factor', 0)
        
        if train_pf > 0 and val_pf > 0:
            degradation = (train_pf - val_pf) / train_pf
            if degradation > degradation_threshold:
                return SafetyCheck(
                    passed=False,
                    violation=SafetyViolation.OVERFITTING,
                    details=f"Profit factor degraded {degradation:.1%} from train ({train_pf:.2f}) to validation ({val_pf:.2f})",
                    severity="ERROR",
                )
        
        if oos_result:
            oos_pf = oos_result.get('profit_factor', 0)
            if val_pf > 0 and oos_pf > 0:
                degradation = (val_pf - oos_pf) / val_pf
                if degradation > degradation_threshold:
                    return SafetyCheck(
                        passed=False,
                        violation=SafetyViolation.OVERFITTING,
                        details=f"Profit factor degraded {degradation:.1%} from validation ({val_pf:.2f}) to OOS ({oos_pf:.2f})",
                        severity="ERROR",
                    )
        
        return SafetyCheck(passed=True, details="No significant overfitting detected")
    
    def check_survivorship_bias(
        self,
        symbols_tested: List[str],
        universe_symbols: List[str],
    ) -> SafetyCheck:
        """Check for survivorship bias in symbol selection."""
        if len(symbols_tested) < len(universe_symbols) * 0.5:
            return SafetyCheck(
                passed=False,
                violation=SafetyViolation.SURVIVORSHIP_BIAS,
                details=f"Only {len(symbols_tested)}/{len(universe_symbols)} symbols tested - potential survivorship bias",
                severity="WARNING",
            )
        return SafetyCheck(passed=True, details="Adequate symbol coverage")
    
    def check_parameter_leakage(
        self,
        param_grid: Dict[str, List[Any]],
        optimisation_metric: str,
        n_optimisations: int,
    ) -> SafetyCheck:
        """Check for parameter leakage from repeated optimisation."""
        total_combinations = 1
        for values in param_grid.values():
            total_combinations *= len(values)
        
        # Rule of thumb: need at least 10x more combinations than optimisations
        if n_optimisations > total_combinations / 10:
            return SafetyCheck(
                passed=False,
                violation=SafetyViolation.PARAMETER_LEAKAGE,
                details=f"Too many optimisations ({n_optimisations}) for parameter space ({total_combinations} combinations)",
                severity="ERROR",
            )
        
        # Track optimisation history
        opt_key = hashlib.sha256(
            f"{json.dumps(param_grid, sort_keys=True)}|{optimisation_metric}".encode()
        ).hexdigest()[:16]
        
        count = sum(1 for h in self._optimisation_history if h.get('key') == opt_key)
        if count >= self._max_optimisations_per_holdout:
            return SafetyCheck(
                passed=False,
                violation=SafetyViolation.REPEATED_OPTIMISATION,
                details=f"Parameter space optimised {count} times against same holdout - exceeds limit of {self._max_optimisations_per_holdout}",
                severity="ERROR",
            )
        
        self._optimisation_history.append({
            'key': opt_key,
            'metric': optimisation_metric,
            'timestamp': datetime.now().isoformat(),
        })
        
        return SafetyCheck(passed=True, details="Parameter leakage check passed")
    
    def check_data_leakage(
        self,
        train_dataset: DatasetInfo,
        test_dataset: DatasetInfo,
    ) -> SafetyCheck:
        """Check for data leakage between train and test sets."""
        # Check for temporal overlap
        train_end = train_dataset.end_date
        test_start = test_dataset.start_date
        
        if train_end >= test_start:
            return SafetyCheck(
                passed=False,
                violation=SafetyViolation.DATA_LEAKAGE,
                details=f"Temporal overlap: train ends {train_end}, test starts {test_start}",
                severity="ERROR",
            )
        
        # Check for same data hash (exact duplicate)
        if train_dataset.hash == test_dataset.hash:
            return SafetyCheck(
                passed=False,
                violation=SafetyViolation.DATA_LEAKAGE,
                details="Train and test datasets have identical data hash",
                severity="ERROR",
            )
        
        return SafetyCheck(passed=True, details="No data leakage detected")
    
    def check_cherry_picking(
        self,
        all_results: List[Dict[str, Any]],
        reported_results: List[Dict[str, Any]],
    ) -> SafetyCheck:
        """Check for cherry-picking of results."""
        if len(reported_results) < len(all_results) * 0.1:
            return SafetyCheck(
                passed=False,
                violation=SafetyViolation.CHERRY_PICKING,
                details=f"Only {len(reported_results)}/{len(all_results)} results reported - potential cherry-picking",
                severity="WARNING",
            )
        return SafetyCheck(passed=True, details="Adequate result reporting")
    
    def check_false_parity(
        self,
        parity_result: Dict[str, Any],
        tolerance_check: bool = True,
    ) -> SafetyCheck:
        """Check for false Python/Pine parity claims."""
        if not parity_result.get('passed', False):
            return SafetyCheck(
                passed=False,
                violation=SafetyViolation.FALSE_PARITY,
                details=f"Parity check failed: {parity_result.get('summary', 'Unknown')}",
                severity="ERROR",
            )
        
        if tolerance_check:
            discrepancies = parity_result.get('discrepancies', [])
            material_discrepancies = [
                d for d in discrepancies
                if d.get('difference', 0) > d.get('tolerance', 0) * 2
            ]
            if material_discrepancies:
                return SafetyCheck(
                    passed=False,
                    violation=SafetyViolation.FALSE_PARITY,
                    details=f"Material discrepancies beyond 2x tolerance: {len(material_discrepancies)}",
                    severity="ERROR",
                )
        
        return SafetyCheck(passed=True, details="Parity check passed")
    
    def check_duplicate_experiment(
        self,
        experiment_hash: str,
    ) -> SafetyCheck:
        """Check for duplicate experiment."""
        if experiment_hash in self._experiment_hashes:
            return SafetyCheck(
                passed=False,
                violation=SafetyViolation.DUPLICATE_EXPERIMENT,
                details=f"Experiment with hash {experiment_hash} already exists",
                severity="ERROR",
            )
        
        self._experiment_hashes.add(experiment_hash)
        return SafetyCheck(passed=True, details="New experiment")
    
    def check_unrecorded_failure(
        self,
        experiment_id: str,
        provenance_dir: Path,
    ) -> SafetyCheck:
        """Check if failed experiments are recorded."""
        exp_dir = provenance_dir / experiment_id
        if not exp_dir.exists():
            return SafetyCheck(
                passed=False,
                violation=SafetyViolation.UNRECORDED_FAILURE,
                details=f"Experiment {experiment_id} has no provenance record",
                severity="WARNING",
            )
        return SafetyCheck(passed=True, details="Experiment recorded")
    
    def run_all_checks(
        self,
        experiment_id: str,
        strategy_code: str,
        indicators_used: List[str],
        train_result: Dict[str, Any],
        validation_result: Dict[str, Any],
        oos_result: Optional[Dict[str, Any]],
        param_grid: Dict[str, List[Any]],
        optimisation_metric: str,
        n_optimisations: int,
        train_dataset: DatasetInfo,
        test_dataset: DatasetInfo,
        symbols_tested: List[str],
        universe_symbols: List[str],
        all_results: List[Dict[str, Any]],
        reported_results: List[Dict[str, Any]],
        parity_result: Dict[str, Any],
        provenance_dir: Path,
    ) -> List[SafetyCheck]:
        """Run all safety checks for an experiment."""
        checks = []
        
        # Generate experiment hash
        exp_hash = hashlib.sha256(experiment_id.encode()).hexdigest()[:16]
        
        checks.append(self.check_duplicate_experiment(exp_hash))
        checks.append(self.check_look_ahead_bias(strategy_code, indicators_used))
        checks.append(self.check_overfitting(train_result, validation_result, oos_result))
        checks.append(self.check_survivorship_bias(symbols_tested, universe_symbols))
        checks.append(self.check_parameter_leakage(param_grid, optimisation_metric, n_optimisations))
        checks.append(self.check_data_leakage(train_dataset, test_dataset))
        checks.append(self.check_cherry_picking(all_results, reported_results))
        checks.append(self.check_false_parity(parity_result))
        checks.append(self.check_unrecorded_failure(experiment_id, provenance_dir))
        
        return checks
    
    def get_safety_report(self, checks: List[SafetyCheck]) -> Dict[str, Any]:
        """Generate safety report from checks."""
        passed = sum(1 for c in checks if c.passed)
        failed = sum(1 for c in checks if not c.passed)
        errors = sum(1 for c in checks if not c.passed and c.severity == "ERROR")
        warnings = sum(1 for c in checks if not c.passed and c.severity == "WARNING")
        
        violations = [c.violation.value for c in checks if not c.passed and c.violation]
        
        return {
            'total_checks': len(checks),
            'passed': passed,
            'failed': failed,
            'errors': errors,
            'warnings': warnings,
            'violations': violations,
            'overall_passed': failed == 0,
            'details': [
                {
                    'violation': c.violation.value if c.violation else None,
                    'passed': c.passed,
                    'details': c.details,
                    'severity': c.severity,
                }
                for c in checks
            ],
        }


def create_safety(**kwargs) -> ResearchSafety:
    """Factory function to create research safety."""
    return ResearchSafety(**kwargs)