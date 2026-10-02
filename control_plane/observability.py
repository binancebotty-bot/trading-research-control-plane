"""
Observability
=============
Structured logs establishing:
WHAT was tested
WHY it was tested
WHICH implementation ran
WHICH data was used
WHICH code revision ran
WHICH parameters ran
WHAT result occurred
WHETHER TradingView validated it
WHETHER parity passed
WHERE evidence lives
"""

import json
import time
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
import threading


class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class EventType(Enum):
    PIPELINE_START = "pipeline_start"
    PIPELINE_COMPLETE = "pipeline_complete"
    PIPELINE_ERROR = "pipeline_error"
    BACKTEST_START = "backtest_start"
    BACKTEST_COMPLETE = "backtest_complete"
    BACKTEST_ERROR = "backtest_error"
    PARAMETER_SWEEP_START = "parameter_sweep_start"
    PARAMETER_SWEEP_COMPLETE = "parameter_sweep_complete"
    TV_COMPILE = "tv_compile"
    TV_STRATEGY_TESTER = "tv_strategy_tester"
    TV_EXTRACTION = "tv_extraction"
    PARITY_COMPARISON = "parity_comparison"
    DECISION = "decision"
    EXPERIMENT_PERSISTED = "experiment_persisted"
    SAFETY_CHECK = "safety_check"
    CAPABILITY_DISCOVERED = "capability_discovered"
    CAPABILITY_TESTED = "capability_tested"


@dataclass
class StructuredLogEntry:
    """Structured log entry with all required fields."""
    timestamp: str
    level: LogLevel
    event_type: EventType
    experiment_id: Optional[str]
    # WHAT
    what_tested: str
    # WHY
    why_tested: str
    # WHICH implementation
    implementation: str  # PYTHON_PY2PINE, TRADINGVIEW_CUSTOM_MCP, TRADINGVIEW_OFFICIAL
    # WHICH data
    data_used: Dict[str, Any]
    # WHICH code revision
    code_revision: str
    # WHICH parameters
    parameters: Dict[str, Any]
    # WHAT result
    result: Dict[str, Any]
    # WHETHER TradingView validated
    tv_validated: bool
    # WHETHER parity passed
    parity_passed: Optional[bool]
    # WHERE evidence lives
    evidence_location: Optional[str]
    # Additional context
    context: Dict[str, Any] = field(default_factory=dict)


class ObservabilityLogger:
    """
    Structured observability logger.
    
    Every log entry captures:
    - WHAT was tested
    - WHY it was tested
    - WHICH implementation ran
    - WHICH data was used
    - WHICH code revision ran
    - WHICH parameters ran
    - WHAT result occurred
    - WHETHER TradingView validated it
    - WHETHER parity passed
    - WHERE evidence lives
    """
    
    def __init__(self, log_dir: Path = Path("logs")):
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._log_file = self.log_dir / f"observability_{datetime.now().strftime('%Y%m%d')}.jsonl"
        self._lock = threading.Lock()
        self._code_revision = self._get_code_revision()
    
    def _get_code_revision(self) -> str:
        """Get current git commit hash."""
        try:
            import subprocess
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True, text=True, cwd=Path.cwd()
            )
            if result.returncode == 0:
                return result.stdout.strip()[:12]
        except Exception:
            pass
        return "unknown"
    
    def log(
        self,
        event_type: EventType,
        level: LogLevel = LogLevel.INFO,
        experiment_id: Optional[str] = None,
        what_tested: str = "",
        why_tested: str = "",
        implementation: str = "PYTHON_PY2PINE",
        data_used: Optional[Dict[str, Any]] = None,
        parameters: Optional[Dict[str, Any]] = None,
        result: Optional[Dict[str, Any]] = None,
        tv_validated: bool = False,
        parity_passed: Optional[bool] = None,
        evidence_location: Optional[str] = None,
        **context,
    ):
        """Log a structured entry."""
        entry = StructuredLogEntry(
            timestamp=datetime.now().isoformat(),
            level=level,
            event_type=event_type,
            experiment_id=experiment_id,
            what_tested=what_tested,
            why_tested=why_tested,
            implementation=implementation,
            data_used=data_used or {},
            code_revision=self._code_revision,
            parameters=parameters or {},
            result=result or {},
            tv_validated=tv_validated,
            parity_passed=parity_passed,
            evidence_location=evidence_location,
            context=context,
        )
        
        with self._lock:
            with open(self._log_file, 'a') as f:
                f.write(json.dumps(asdict(entry), default=str) + '\n')
    
    def log_backtest(
        self,
        experiment_id: str,
        strategy: str,
        symbol: str,
        timeframe: str,
        parameters: Dict[str, Any],
        result: Dict[str, Any],
        implementation: str = "PYTHON_PY2PINE",
    ):
        """Log a backtest execution."""
        self.log(
            event_type=EventType.BACKTEST_COMPLETE,
            experiment_id=experiment_id,
            what_tested=f"Backtest: {strategy} on {symbol} {timeframe}",
            why_tested="Strategy performance evaluation",
            implementation=implementation,
            data_used={"symbol": symbol, "timeframe": timeframe},
            parameters=parameters,
            result=result,
            tv_validated=False,
            parity_passed=None,
        )
    
    def log_parity(
        self,
        experiment_id: str,
        strategy: str,
        symbol: str,
        timeframe: str,
        python_result: Dict[str, Any],
        tv_result: Dict[str, Any],
        parity_passed: bool,
        discrepancies: List[Dict[str, Any]],
    ):
        """Log a parity comparison."""
        self.log(
            event_type=EventType.PARITY_COMPARISON,
            experiment_id=experiment_id,
            what_tested=f"Parity: {strategy} on {symbol} {timeframe}",
            why_tested="Validate Python vs TradingView equivalence",
            implementation="PARITY_CHECK",
            data_used={"symbol": symbol, "timeframe": timeframe},
            parameters={},
            result={
                "python": python_result,
                "tradingview": tv_result,
                "discrepancies": discrepancies,
            },
            tv_validated=True,
            parity_passed=parity_passed,
        )
    
    def log_decision(
        self,
        experiment_id: str,
        decision: str,
        rejection_reason: Optional[str],
        python_result: Dict[str, Any],
    ):
        """Log an accept/reject decision."""
        self.log(
            event_type=EventType.DECISION,
            level=LogLevel.INFO if decision == "ACCEPT" else LogLevel.WARNING,
            experiment_id=experiment_id,
            what_tested=f"Decision: {decision}",
            why_tested="Determine if candidate passes quality gates",
            implementation="DECISION_ENGINE",
            data_used={},
            parameters={},
            result={
                "decision": decision,
                "rejection_reason": rejection_reason,
                "python_metrics": python_result,
            },
            tv_validated=False,
            parity_passed=None,
        )
    
    def log_experiment_persisted(
        self,
        experiment_id: str,
        evidence_paths: List[str],
    ):
        """Log experiment persistence."""
        self.log(
            event_type=EventType.EXPERIMENT_PERSISTED,
            experiment_id=experiment_id,
            what_tested="Experiment persistence",
            why_tested="Record experiment for provenance",
            implementation="PROVENANCE",
            data_used={},
            parameters={},
            result={"evidence_paths": evidence_paths},
            tv_validated=False,
            parity_passed=None,
            evidence_location=evidence_paths[0] if evidence_paths else None,
        )
    
    def query_logs(
        self,
        experiment_id: Optional[str] = None,
        event_type: Optional[EventType] = None,
        level: Optional[LogLevel] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        limit: int = 100,
    ) -> List[StructuredLogEntry]:
        """Query logs with filters."""
        entries = []
        
        # Read all log files
        for log_file in sorted(self.log_dir.glob("observability_*.jsonl")):
            with open(log_file, 'r') as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        entry = StructuredLogEntry(**data)
                        
                        # Apply filters
                        if experiment_id and entry.experiment_id != experiment_id:
                            continue
                        if event_type and entry.event_type != event_type:
                            continue
                        if level and entry.level != level:
                            continue
                        if start_time and entry.timestamp < start_time:
                            continue
                        if end_time and entry.timestamp > end_time:
                            continue
                        
                        entries.append(entry)
                    except Exception:
                        continue
        
        # Sort by timestamp descending
        entries.sort(key=lambda e: e.timestamp, reverse=True)
        return entries[:limit]
    
    def generate_summary_report(self, experiment_id: str) -> Dict[str, Any]:
        """Generate observability summary for an experiment."""
        entries = self.query_logs(experiment_id=experiment_id, limit=1000)
        
        return {
            'experiment_id': experiment_id,
            'total_events': len(entries),
            'events_by_type': {
                e.value: sum(1 for entry in entries if entry.event_type == e)
                for e in EventType
            },
            'events_by_level': {
                l.value: sum(1 for entry in entries if entry.level == l)
                for l in LogLevel
            },
            'implementations_used': list(set(e.implementation for e in entries)),
            'tv_validated_count': sum(1 for e in entries if e.tv_validated),
            'parity_checks': sum(1 for e in entries if e.parity_passed is not None),
            'parity_passed': sum(1 for e in entries if e.parity_passed is True),
            'timeline': [
                {
                    'timestamp': e.timestamp,
                    'event': e.event_type.value,
                    'what': e.what_tested,
                    'result_summary': str(e.result)[:200] if e.result else '',
                }
                for e in entries
            ],
        }


def create_observability(**kwargs) -> ObservabilityLogger:
    """Factory function to create observability logger."""
    return ObservabilityLogger(**kwargs)