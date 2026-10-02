"""
Research Pipeline
=================
Fast-search → TV-validation pipeline implementation.

Hypothesis/strategy
→ Python implementation
→ fast Python backtest
→ parallel parameter/candidate exploration
→ rank/filter candidates
→ generate/update equivalent Pine
→ compile through TradingView
→ execute in TradingView Strategy Tester
→ extract TV trades/metrics/equity
→ parity comparison
→ accept/reject candidate
→ persist experiment and evidence
"""

import json
import time
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor, as_completed

from .backends.python_py2pine import PythonPy2PineBackend, BacktestResult, ParameterSweepResult
from .backends.custom_tradingview_mcp import CustomTradingViewMCPBackend
from .backends.official_tradingview import OfficialTradingViewBackend
from .provenance import ExperimentProvenance, ExperimentRecord
from .safety import ResearchSafety
from .observability import ObservabilityLogger


class PipelineStage(Enum):
    """Stages in the research pipeline."""
    HYPOTHESIS = "hypothesis"
    PYTHON_IMPL = "python_implementation"
    FAST_BACKTEST = "fast_backtest"
    PARALLEL_EXPLORATION = "parallel_exploration"
    CANDIDATE_FILTERING = "candidate_filtering"
    PINE_GENERATION = "pine_generation"
    TV_COMPILE = "tv_compile"
    TV_STRATEGY_TESTER = "tv_strategy_tester"
    TV_EXTRACTION = "tv_extraction"
    PARITY_COMPARISON = "parity_comparison"
    DECISION = "decision"
    PERSIST = "persist"


class ParityClassification(Enum):
    """Classification of parity discrepancies."""
    DATA_DIFFERENCE = "DATA_DIFFERENCE"
    EXECUTION_SEMANTICS = "EXECUTION_SEMANTICS"
    ROUNDING = "ROUNDING"
    FEE_MODEL = "FEE_MODEL"
    SLIPPAGE_MODEL = "SLIPPAGE_MODEL"
    POSITION_SIZING = "POSITION_SIZING"
    BAR_TIMING = "BAR_TIMING"
    PINE_SEMANTICS = "PINE_SEMANTICS"
    UNKNOWN = "UNKNOWN"


@dataclass
class ParityResult:
    """Result of Python vs TradingView parity comparison."""
    python_result: Optional[BacktestResult]
    tv_result: Optional[Dict[str, Any]]
    passed: bool
    discrepancies: List[Dict[str, Any]]
    classifications: List[ParityClassification]
    tolerances: Dict[str, float]
    summary: str


@dataclass
class PipelineResult:
    """Complete pipeline execution result."""
    experiment_id: str
    hypothesis: str
    strategy_name: str
    symbol: str
    timeframe: str
    parameters: Dict[str, Any]
    stages_completed: List[PipelineStage]
    python_results: List[BacktestResult]
    best_python_result: Optional[BacktestResult]
    tv_result: Optional[Dict[str, Any]]
    parity_result: Optional[ParityResult]
    decision: str  # ACCEPT, REJECT, NEEDS_REVIEW
    rejection_reason: Optional[str]
    evidence_paths: List[str]
    total_time_ms: float
    timestamp: str


class ResearchPipeline:
    """
    Fast-search → TV-validation research pipeline.
    
    Orchestrates the complete flow from hypothesis to validated experiment.
    """
    
    def __init__(
        self,
        python_backend: Optional[PythonPy2PineBackend] = None,
        tv_mcp_backend: Optional[CustomTradingViewMCPBackend] = None,
        official_tv_backend: Optional[OfficialTradingViewBackend] = None,
        provenance: Optional[ExperimentProvenance] = None,
        safety: Optional[ResearchSafety] = None,
        observability: Optional[ObservabilityLogger] = None,
        parity_tolerances: Optional[Dict[str, float]] = None,
    ):
        self.python_backend = python_backend or PythonPy2PineBackend()
        self.tv_mcp_backend = tv_mcp_backend or CustomTradingViewMCPBackend()
        self.official_tv_backend = official_tv_backend or OfficialTradingViewBackend()
        self.provenance = provenance or ExperimentProvenance()
        self.safety = safety or ResearchSafety()
        self.observability = observability or ObservabilityLogger()
        
        # Default parity tolerances
        self.parity_tolerances = parity_tolerances or {
            'return_pct': 0.5,        # 0.5% absolute difference
            'max_dd_pct': 0.5,        # 0.5% absolute difference
            'win_rate': 1.0,          # 1% absolute difference
            'profit_factor': 0.1,     # 0.1 absolute difference
            'n_trades': 0.15,         # 15% relative difference
            'avg_win_pct': 3.0,       # 3% absolute difference
            'avg_loss_pct': 3.0,      # 3% absolute difference
        }
    
    def run_pipeline(
        self,
        hypothesis: str,
        strategy_name: str,
        symbol: str,
        timeframe: str,
        parameters: Dict[str, Any],
        param_grid: Optional[Dict[str, List[Any]]] = None,
        filter_top_n: int = 5,
        min_trades: int = 10,
        min_profit_factor: float = 1.0,
        max_drawdown_pct: float = 20.0,
    ) -> PipelineResult:
        """
        Execute the complete research pipeline.
        
        Args:
            hypothesis: Research hypothesis description
            strategy_name: Name of strategy to test
            symbol: Trading symbol
            timeframe: Timeframe
            parameters: Base parameters
            param_grid: Optional parameter grid for sweep
            filter_top_n: Number of top candidates to send to TV
            min_trades: Minimum trades for candidate
            min_profit_factor: Minimum profit factor
            max_drawdown_pct: Maximum drawdown %
        
        Returns:
            PipelineResult with complete experiment record
        """
        start_time = time.time()
        experiment_id = self._generate_experiment_id(hypothesis, strategy_name, symbol, timeframe, parameters)
        
        self.observability.log(
            "pipeline_start",
            experiment_id=experiment_id,
            hypothesis=hypothesis,
            strategy=strategy_name,
            symbol=symbol,
            timeframe=timeframe,
        )
        
        stages_completed = []
        evidence_paths = []
        python_results: List[BacktestResult] = []
        best_python_result: Optional[BacktestResult] = None

        try:
            # Stage 1: Python Implementation (already exists in strategies_core)
            stages_completed.append(PipelineStage.PYTHON_IMPL)
            
            # Stage 2: Fast Python Backtest (single run)
            python_result = self.python_backend.backtest_single(
                strategy_name, symbol, timeframe, parameters
            )
            stages_completed.append(PipelineStage.FAST_BACKTEST)
            
            # Stage 3: Parallel Parameter Exploration (if param_grid provided)
            python_results = [python_result]
            best_python_result = python_result
            
            if param_grid:
                sweep_result = self.python_backend.parameter_sweep(
                    strategy_name, symbol, timeframe, param_grid
                )
                python_results = sweep_result.results
                best_python_result = self._select_best_result(
                    sweep_result.results, min_trades, min_profit_factor, max_drawdown_pct
                )
                stages_completed.append(PipelineStage.PARALLEL_EXPLORATION)
            
            # Stage 4: Candidate Filtering
            candidates = self._filter_candidates(
                python_results, min_trades, min_profit_factor, max_drawdown_pct
            )
            top_candidates = candidates[:filter_top_n]
            stages_completed.append(PipelineStage.CANDIDATE_FILTERING)
            
            # Stage 5: Pine Generation / Parity
            # For now, use the best candidate's strategy (already in Pine in strategies_core)
            # In future, this would transpile Python -> Pine
            pine_source = self._get_pine_source(strategy_name)
            stages_completed.append(PipelineStage.PINE_GENERATION)
            
            # Stage 6: TV Compile
            compile_result = self.tv_mcp_backend.compile_pine(pine_source)
            if not compile_result.success:
                return self._create_failed_result(
                    experiment_id, hypothesis, strategy_name, symbol, timeframe,
                    parameters, stages_completed, python_results, best_python_result,
                    "TV compilation failed", evidence_paths, start_time,
                    f"Compile errors: {compile_result.errors}"
                )
            stages_completed.append(PipelineStage.TV_COMPILE)
            
            # Stage 7: TV Strategy Tester
            tv_cycle_result = self.tv_mcp_backend.full_cycle_strategy(
                pine_source, add_to_chart=True, allow_update_existing=False
            )
            stages_completed.append(PipelineStage.TV_STRATEGY_TESTER)
            
            # Stage 8: TV Extraction
            tv_summary = self.tv_mcp_backend.read_strategy_tester()
            tv_result = tv_summary.raw_data if tv_summary.raw_data else None
            stages_completed.append(PipelineStage.TV_EXTRACTION)
            
            # Stage 9: Parity Comparison
            parity_result = self._compare_parity(best_python_result, tv_result)
            stages_completed.append(PipelineStage.PARITY_COMPARISON)
            
            # Stage 10: Decision
            decision, rejection_reason = self._make_decision(parity_result, best_python_result)
            stages_completed.append(PipelineStage.DECISION)
            
            # Stage 11: Persist
            evidence_paths = self._persist_experiment(
                experiment_id, hypothesis, strategy_name, symbol, timeframe,
                parameters, python_results, best_python_result, tv_result,
                parity_result, decision, rejection_reason
            )
            stages_completed.append(PipelineStage.PERSIST)
            
            total_time_ms = (time.time() - start_time) * 1000
            
            result = PipelineResult(
                experiment_id=experiment_id,
                hypothesis=hypothesis,
                strategy_name=strategy_name,
                symbol=symbol,
                timeframe=timeframe,
                parameters=parameters,
                stages_completed=stages_completed,
                python_results=python_results,
                best_python_result=best_python_result,
                tv_result=tv_result,
                parity_result=parity_result,
                decision=decision,
                rejection_reason=rejection_reason,
                evidence_paths=evidence_paths,
                total_time_ms=total_time_ms,
                timestamp=datetime.now().isoformat(),
            )
            
            self.observability.log(
                "pipeline_complete",
                experiment_id=experiment_id,
                decision=decision,
                stages=len(stages_completed),
                time_ms=total_time_ms,
            )
            
            return result
            
        except Exception as e:
            self.observability.log(
                "pipeline_error",
                experiment_id=experiment_id,
                error=str(e),
                stages_completed=[s.value for s in stages_completed],
            )
            return self._create_failed_result(
                experiment_id, hypothesis, strategy_name, symbol, timeframe,
                parameters, stages_completed, python_results, best_python_result,
                "Pipeline exception", evidence_paths, start_time, str(e)
            )
    
    def _select_best_result(
        self,
        results: List[BacktestResult],
        min_trades: int,
        min_profit_factor: float,
        max_drawdown_pct: float,
    ) -> Optional[BacktestResult]:
        """Select best result from parameter sweep."""
        valid = [
            r for r in results
            if r.status == "ok"
            and r.metrics.get('n_trades', 0) >= min_trades
            and r.metrics.get('profit_factor', 0) >= min_profit_factor
            and r.metrics.get('max_dd_pct', 100) <= max_drawdown_pct
        ]
        if not valid:
            return None
        return max(valid, key=lambda r: r.metrics.get('return_pct', -999))
    
    def _filter_candidates(
        self,
        results: List[BacktestResult],
        min_trades: int,
        min_profit_factor: float,
        max_drawdown_pct: float,
    ) -> List[BacktestResult]:
        """Filter and rank candidates."""
        valid = [
            r for r in results
            if r.status == "ok"
            and r.metrics.get('n_trades', 0) >= min_trades
            and r.metrics.get('profit_factor', 0) >= min_profit_factor
            and r.metrics.get('max_dd_pct', 100) <= max_drawdown_pct
        ]
        return sorted(valid, key=lambda r: r.metrics.get('return_pct', -999), reverse=True)
    
    def _get_pine_source(self, strategy_name: str) -> str:
        """Get Pine source for a strategy."""
        # In practice, this would read from the pine/ directory
        # For now, return a placeholder that would be replaced
        pine_path = Path(r"C:\Users\wigmore\trading_stack\pine") / f"{strategy_name}.pine"
        if pine_path.exists():
            return pine_path.read_text()
        # Fallback: generate from transpiler if Python version exists
        return f"// Pine source for {strategy_name} - would be loaded from file"
    
    def _compare_parity(
        self,
        python_result: Optional[BacktestResult],
        tv_result: Optional[Dict[str, Any]],
    ) -> ParityResult:
        """Compare Python and TradingView results."""
        if not python_result or not tv_result:
            return ParityResult(
                python_result=python_result,
                tv_result=tv_result,
                passed=False,
                discrepancies=[{"error": "Missing Python or TV result"}],
                classifications=[ParityClassification.UNKNOWN],
                tolerances=self.parity_tolerances,
                summary="Cannot compare - missing results",
            )
        
        discrepancies = []
        classifications = []
        
        # Compare key metrics
        py_metrics = python_result.metrics
        tv_metrics = tv_result
        
        for metric, tolerance in self.parity_tolerances.items():
            py_val = py_metrics.get(metric)
            tv_val = tv_metrics.get(metric)
            
            if py_val is not None and tv_val is not None:
                diff = abs(py_val - tv_val)
                if diff > tolerance:
                    discrepancies.append({
                        'metric': metric,
                        'python': py_val,
                        'tradingview': tv_val,
                        'difference': diff,
                        'tolerance': tolerance,
                    })
                    classifications.append(ParityClassification.EXECUTION_SEMANTICS)
        
        passed = len(discrepancies) == 0
        
        return ParityResult(
            python_result=python_result,
            tv_result=tv_result,
            passed=passed,
            discrepancies=discrepancies,
            classifications=classifications,
            tolerances=self.parity_tolerances,
            summary=f"Parity {'PASSED' if passed else 'FAILED'}: {len(discrepancies)} discrepancies",
        )
    
    def _make_decision(
        self,
        parity_result: ParityResult,
        python_result: Optional[BacktestResult],
    ) -> tuple[str, Optional[str]]:
        """Make accept/reject decision based on parity and performance."""
        if not parity_result.passed:
            return "REJECT", f"Parity failed: {parity_result.summary}"
        
        if not python_result or python_result.status != "ok":
            return "REJECT", "Python backtest failed"
        
        # Additional quality gates
        if python_result.metrics.get('n_trades', 0) < 10:
            return "REJECT", "Insufficient trades"
        
        if python_result.metrics.get('profit_factor', 0) < 1.0:
            return "REJECT", "Profit factor < 1.0"
        
        if python_result.metrics.get('max_dd_pct', 100) > 20:
            return "REJECT", "Max drawdown > 20%"
        
        return "ACCEPT", None
    
    def _persist_experiment(
        self,
        experiment_id: str,
        hypothesis: str,
        strategy_name: str,
        symbol: str,
        timeframe: str,
        parameters: Dict[str, Any],
        python_results: List[BacktestResult],
        best_python_result: Optional[BacktestResult],
        tv_result: Optional[Dict[str, Any]],
        parity_result: Optional[ParityResult],
        decision: str,
        rejection_reason: Optional[str],
    ) -> List[str]:
        """Persist experiment and evidence."""
        evidence_dir = Path("experiments") / experiment_id
        evidence_dir.mkdir(parents=True, exist_ok=True)
        
        # Save experiment record
        record = ExperimentRecord(
            experiment_id=experiment_id,
            hypothesis=hypothesis,
            strategy_source_hash=self._hash_strategy(strategy_name),
            python_source_hash=self._hash_python_strategy(strategy_name),
            pine_source_hash=self._hash_pine_source(strategy_name),
            parameters=parameters,
            symbol=symbol,
            timeframe=timeframe,
            dataset_identity=f"{symbol}_{timeframe}",
            date_range={"start": "TBD", "end": "TBD"},
            costs={"fee_pct": self.python_backend.fee_pct},
            execution_assumptions={"fill_mode": "tv", "pyramiding": 1},
            python_result=best_python_result.metrics if best_python_result else {},
            tv_result=tv_result or {},
            parity_result={
                'passed': parity_result.passed if parity_result else False,
                'discrepancies': parity_result.discrepancies if parity_result else [],
            } if parity_result else {},
            rejection_reason=rejection_reason,
            timestamps={
                'created': datetime.now().isoformat(),
                'completed': datetime.now().isoformat(),
            },
        )
        
        record_path = evidence_dir / "experiment.json"
        self.provenance.save_record(record)
        
        # Save Python results
        py_results_path = evidence_dir / "python_results.json"
        with open(py_results_path, 'w') as f:
            json.dump([asdict(r) for r in python_results], f, indent=2, default=str)
        
        # Save TV result
        if tv_result:
            tv_path = evidence_dir / "tv_result.json"
            with open(tv_path, 'w') as f:
                json.dump(tv_result, f, indent=2, default=str)
            evidence_paths.append(str(tv_path))
        
        # Save parity result
        if parity_result:
            parity_path = evidence_dir / "parity_result.json"
            with open(parity_path, 'w') as f:
                json.dump(asdict(parity_result), f, indent=2, default=str)
            evidence_paths.append(str(parity_path))
        
        evidence_paths.extend([str(record_path), str(py_results_path)])
        
        return evidence_paths
    
    def _create_failed_result(
        self,
        experiment_id: str,
        hypothesis: str,
        strategy_name: str,
        symbol: str,
        timeframe: str,
        parameters: Dict[str, Any],
        stages_completed: List[PipelineStage],
        python_results: List[BacktestResult],
        best_python_result: Optional[BacktestResult],
        decision: str,
        evidence_paths: List[str],
        start_time: float,
        rejection_reason: str,
    ) -> PipelineResult:
        """Create a failed pipeline result."""
        total_time_ms = (time.time() - start_time) * 1000
        if evidence_paths is None:
            evidence_paths = []
        return PipelineResult(
            experiment_id=experiment_id,
            hypothesis=hypothesis,
            strategy_name=strategy_name,
            symbol=symbol,
            timeframe=timeframe,
            parameters=parameters,
            stages_completed=stages_completed,
            python_results=python_results if python_results else [],
            best_python_result=best_python_result,
            tv_result=None,
            parity_result=None,
            decision=decision,
            rejection_reason=rejection_reason,
            evidence_paths=evidence_paths,
            total_time_ms=total_time_ms,
            timestamp=datetime.now().isoformat(),
        )
    
    def _generate_experiment_id(
        self,
        hypothesis: str,
        strategy: str,
        symbol: str,
        timeframe: str,
        params: Dict[str, Any],
    ) -> str:
        """Generate unique experiment ID."""
        content = f"{hypothesis}|{strategy}|{symbol}|{timeframe}|{json.dumps(params, sort_keys=True)}|{datetime.now().date()}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def _hash_strategy(self, strategy_name: str) -> str:
        """Hash strategy source."""
        pine_path = Path(r"C:\Users\wigmore\trading_stack\pine") / f"{strategy_name}.pine"
        if pine_path.exists():
            return hashlib.sha256(pine_path.read_bytes()).hexdigest()[:16]
        return "unknown"
    
    def _hash_python_strategy(self, strategy_name: str) -> str:
        """Hash Python strategy source."""
        # Would hash the actual Python function source
        return hashlib.sha256(strategy_name.encode()).hexdigest()[:16]
    
    def _hash_pine_source(self, strategy_name: str) -> str:
        """Hash Pine source."""
        return self._hash_strategy(strategy_name)


def create_pipeline(**kwargs) -> ResearchPipeline:
    """Factory function to create research pipeline."""
    return ResearchPipeline(**kwargs)