"""
False-PASS Invariants
=====================

Every invariant here exists because a real false-PASS slipped through a previous
handoff. Each invariant is a hard gate: if it is not satisfied, the caller MUST
fail. There is no "warn" path and no tolerance knob that can manufacture a PASS.

The invariants are deliberately evidence-shaped rather than boolean-shaped: they
return the observed values alongside the verdict so an independent reviewer can
re-derive *why* a gate passed or failed from the persisted evidence alone.

Required invariants (per corrective-pass mandate):

    PARITY_REQUIRES_REAL_TV_RESULT
    PARITY_REQUIRES_PYTHON_TRADES_GT_0
    PARITY_REQUIRES_TV_TRADES_GT_0
    TV_MUTATION_REQUIRES_READBACK
    PINE_WRITE_REQUIRES_HASH_READBACK
    STRATEGY_TESTER_PASS_REQUIRES_ACTUAL_METRICS
    TRADE_EXTRACTION_PASS_REQUIRES_ACTUAL_TRADE_PAYLOAD
    FULL_PIPELINE_REQUIRES_REAL_TV_EXECUTION
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple


# --------------------------------------------------------------------------- #
# Placeholder detection
# --------------------------------------------------------------------------- #

# Substrings that identify a non-execution response. The 2026-10-02 handoff was
# invalidated by exactly this marker appearing in committed evidence.
PLACEHOLDER_MARKERS = (
    "actual execution requires mcp client",
    "tool metadata",
    "placeholder",
    "not implemented",
    "todo",
    "stub",
    "mock",
    "simulated",
    "dummy",
    "fake",
)

# Keys that, when they are the *only* keys present, mean the response is an echo
# of our own request rather than data observed from TradingView.
REQUEST_ECHO_KEYS = frozenset({"tool", "args", "arguments", "name"})


def normalize(value: Any) -> str:
    """Lowercase string form for substring scanning."""
    if value is None:
        return ""
    if not isinstance(value, str):
        try:
            value = json.dumps(value, default=str)
        except (TypeError, ValueError):
            value = str(value)
    return value.lower()


def scan_for_placeholder(value: Any) -> List[str]:
    """Return every placeholder marker found anywhere in ``value``."""
    blob = normalize(value)
    return [m for m in PLACEHOLDER_MARKERS if m in blob]


def is_request_echo(payload: Any) -> bool:
    """
    True when ``payload`` carries no data beyond our own request parameters.

    A real TradingView response always brings chart-observed fields (symbol,
    resolution, studies, metrics, trades, ...). A dict whose non-null keys are
    entirely a restatement of the request is an echo, not evidence.
    """
    if not isinstance(payload, dict):
        return False
    meaningful = {
        k
        for k, v in payload.items()
        if v is not None and k not in REQUEST_ECHO_KEYS and v != {} and v != []
    }
    return not meaningful


# --------------------------------------------------------------------------- #
# Execution attestation
# --------------------------------------------------------------------------- #


@dataclass
class ExecutionAttestation:
    """
    Proof that a payload came from a live TradingView session over the real MCP
    transport, bound to one specific browser target.

    The control-plane backend mints this for every tool call. Invariants refuse
    any payload that cannot present one.
    """

    tool: str
    transport: str                     # must be "stdio-jsonrpc"
    target_id: Optional[str] = None    # CDP page target id
    target_url: Optional[str] = None
    target_title: Optional[str] = None
    cdp_host: Optional[str] = None
    cdp_port: Optional[int] = None
    request_id: Optional[str] = None
    payload_sha256: Optional[str] = None
    payload_nonempty: bool = False
    placeholder_markers: List[str] = field(default_factory=list)
    is_request_echo: bool = False
    executed_at: str = field(default_factory=lambda: datetime.now().isoformat())

    @property
    def is_genuine(self) -> bool:
        """Attestation alone is sufficient to rule out a placeholder."""
        return (
            self.transport == "stdio-jsonrpc"
            and bool(self.target_id)
            and bool(self.target_url)
            and self.payload_nonempty
            and not self.placeholder_markers
            and not self.is_request_echo
        )

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["is_genuine"] = self.is_genuine
        return d


def sha256_of(value: Any) -> str:
    """Stable hash of any JSON-serialisable payload."""
    if isinstance(value, str):
        raw = value
    else:
        try:
            raw = json.dumps(value, sort_keys=True, default=str)
        except (TypeError, ValueError):
            raw = str(value)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------- #
# Verdicts
# --------------------------------------------------------------------------- #


@dataclass
class Verdict:
    """Outcome of one invariant check, carrying the observed evidence."""

    name: str
    passed: bool
    observed: Dict[str, Any] = field(default_factory=dict)
    reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class InvariantViolation(Exception):
    """Raised when a hard gate refuses to pass. Callers must not swallow this."""

    def __init__(self, name: str, reason: str, observed: Optional[Dict[str, Any]] = None):
        self.name = name
        self.reason = reason
        self.observed = observed or {}
        super().__init__(f"{name}: {reason}")


def _require(verdict: Verdict) -> Verdict:
    """Raise if the verdict failed. Used to make PASS impossible to fake."""
    if not verdict.passed:
        raise InvariantViolation(verdict.name, verdict.reason, verdict.observed)
    return verdict


# --------------------------------------------------------------------------- #
# The invariants
# --------------------------------------------------------------------------- #


def parity_requires_real_tv_result(attestation: Optional[ExecutionAttestation],
                                   tv_payload: Any) -> Verdict:
    """
    PARITY_REQUIRES_REAL_TV_RESULT

    Rejects placeholder, empty, echo, unattested, or metadata-only TV payloads.
    """
    name = "PARITY_REQUIRES_REAL_TV_RESULT"
    observed: Dict[str, Any] = {"tv_payload_type": type(tv_payload).__name__}

    if attestation is None:
        return Verdict(name, False, observed, "no execution attestation supplied for TV result")
    observed["attestation"] = attestation.to_dict()

    if attestation.transport != "stdio-jsonrpc":
        return Verdict(name, False, observed,
                       f"transport is {attestation.transport!r}, not the real stdio JSON-RPC MCP transport")
    if not attestation.target_id:
        return Verdict(name, False, observed, "TV result is not bound to a CDP target id")
    if not attestation.payload_nonempty:
        return Verdict(name, False, observed, "TV payload is empty")
    markers = scan_for_placeholder(tv_payload) or attestation.placeholder_markers
    if markers:
        observed["placeholder_markers"] = markers
        return Verdict(name, False, observed, f"TV payload carries placeholder markers: {markers}")
    if attestation.is_request_echo or is_request_echo(tv_payload):
        return Verdict(name, False, observed, "TV payload is a request echo, not observed TradingView data")
    if not attestation.is_genuine:
        return Verdict(name, False, observed, "attestation failed genuineness self-check")
    return Verdict(name, True, observed, "TV result is attested real MCP execution against a live CDP target")


def parity_requires_python_trades_gt_0(python_result: Any) -> Verdict:
    """
    PARITY_REQUIRES_PYTHON_TRADES_GT_0

    A zero-trade Python run carries no information to compare against.
    """
    name = "PARITY_REQUIRES_PYTHON_TRADES_GT_0"
    n = extract_trade_count(python_result)
    observed = {"python_trade_count": n}
    if n is None:
        return Verdict(name, False, observed, "python trade count could not be determined")
    if n <= 0:
        return Verdict(name, False, observed, "python produced 0 trades; parity comparison is vacuous")
    return Verdict(name, True, observed, f"python produced {n} trades")


def parity_requires_tv_trades_gt_0(attestation: Optional[ExecutionAttestation],
                                   tv_trades: Any) -> Verdict:
    """
    PARITY_REQUIRES_TV_TRADES_GT_0

    Requires a genuine attestation AND a non-empty, non-placeholder trade payload.
    """
    name = "PARITY_REQUIRES_TV_TRADES_GT_0"
    real = parity_requires_real_tv_result(attestation, tv_trades)
    observed = dict(real.observed)
    n = extract_trade_count(tv_trades)
    observed["tv_trade_count"] = n
    if not real.passed:
        return Verdict(name, False, observed, f"prerequisite failed: {real.reason}")
    if n is None:
        return Verdict(name, False, observed, "tv trade count could not be determined")
    if n <= 0:
        return Verdict(name, False, observed, "TradingView returned 0 trades")
    return Verdict(name, True, observed, f"TradingView returned {n} trades")


def tv_mutation_requires_readback(kind: str, before: Any, requested: Any,
                                  after: Any) -> Verdict:
    """
    TV_MUTATION_REQUIRES_READBACK

    A mutation is only proven by observing the requested state afterwards.
    ``kind`` is e.g. "symbol" or "timeframe".
    """
    name = "TV_MUTATION_REQUIRES_READBACK"
    observed = {"kind": kind, "before": before, "requested": requested, "after": after}
    if after is None:
        return Verdict(name, False, observed, f"no {kind} state was read back after mutation")
    if requested is None:
        return Verdict(name, False, observed, f"no requested {kind} value recorded")
    if _norm(kind, after) != _norm(kind, requested):
        return Verdict(name, False, observed,
                       f"{kind} read-back {after!r} != requested {requested!r}")
    return Verdict(name, True, observed, f"{kind} read-back matches requested value")


def pine_write_requires_hash_readback(before_source: Optional[str], requested_source: str,
                                      after_source: Optional[str]) -> Verdict:
    """
    PINE_WRITE_REQUIRES_HASH_READBACK

    Proves the Pine Editor buffer actually holds the source we intended to write.
    """
    name = "PINE_WRITE_REQUIRES_HASH_READBACK"
    before_hash = sha256_of(before_source) if before_source is not None else None
    requested_hash = sha256_of(requested_source)
    after_hash = sha256_of(after_source) if after_source is not None else None
    observed = {
        "before_hash": before_hash,
        "requested_hash": requested_hash,
        "after_hash": after_hash,
        "changed": (before_hash != requested_hash) if before_hash else None,
    }
    if after_source is None:
        return Verdict(name, False, observed, "pine source could not be read back from the editor")
    if after_hash != requested_hash:
        return Verdict(name, False, observed,
                       "pine read-back hash does not match requested source hash")
    if before_hash == after_hash:
        return Verdict(name, False, observed,
                       "pine read-back hash equals the previous buffer; write did not land")
    return Verdict(name, True, observed, "pine editor read-back hash matches the requested source")


def strategy_tester_pass_requires_actual_metrics(attestation: Optional[ExecutionAttestation],
                                                 metrics: Any) -> Verdict:
    """
    STRATEGY_TESTER_PASS_REQUIRES_ACTUAL_METRICS

    Requires numeric, non-null Strategy Tester metrics from a real execution.
    """
    name = "STRATEGY_TESTER_PASS_REQUIRES_ACTUAL_METRICS"
    real = parity_requires_real_tv_result(attestation, metrics)
    observed = dict(real.observed)
    if not real.passed:
        return Verdict(name, False, observed, f"prerequisite failed: {real.reason}")
    numeric = _collect_numeric(metrics)
    observed["numeric_metric_fields"] = sorted(numeric)
    observed["numeric_metric_count"] = len(numeric)
    if not numeric:
        return Verdict(name, False, observed,
                       "no numeric Strategy Tester metrics were returned")
    if numeric.get("total_trades", 0) <= 0:
        return Verdict(name, False, observed,
                       "Strategy Tester reported 0 trades; metrics are not meaningful")
    return Verdict(name, True, observed,
                   f"{len(numeric)} numeric Strategy Tester metrics returned")


def trade_extraction_pass_requires_actual_trade_payload(attestation: Optional[ExecutionAttestation],
                                                       trades: Any) -> Verdict:
    """
    TRADE_EXTRACTION_PASS_REQUIRES_ACTUAL_TRADE_PAYLOAD

    A real trade list must contain per-trade records with entry/exit detail.
    """
    name = "TRADE_EXTRACTION_PASS_REQUIRES_ACTUAL_TRADE_PAYLOAD"
    real = parity_requires_real_tv_result(attestation, trades)
    observed = dict(real.observed)
    if not real.passed:
        return Verdict(name, False, observed, f"prerequisite failed: {real.reason}")
    rows = extract_trade_rows(trades)
    observed["trade_rows"] = len(rows)
    if not rows:
        return Verdict(name, False, observed, "trade payload contained no per-trade rows")
    has_detail = any(
        any(k in row for k in ("entry_time", "entryTime", "entry_price", "entryPrice"))
        for row in rows
    )
    observed["rows_with_entry_detail"] = has_detail
    if not has_detail:
        return Verdict(name, False, observed,
                       "trade rows lack entry/exit detail; cannot support trade-by-trade parity")
    return Verdict(name, True, observed, f"{len(rows)} real trade rows with entry/exit detail")


def full_pipeline_requires_real_tv_execution(stage_attestations: Dict[str, Any],
                                              tv_metrics: Any,
                                              tv_trades: Any) -> Verdict:
    """
    FULL_PIPELINE_REQUIRES_REAL_TV_EXECUTION

    Every TradingView stage of the pipeline must present a genuine attestation.
    """
    name = "FULL_PIPELINE_REQUIRES_REAL_TV_EXECUTION"
    required_stages = (
        "compile",
        "inject",
        "add_to_chart",
        "strategy_tester",
    )
    observed: Dict[str, Any] = {"stages_present": sorted(stage_attestations)}

    missing = [s for s in required_stages if s not in stage_attestations]
    if missing:
        observed["missing_stages"] = missing
        return Verdict(name, False, observed, f"pipeline did not execute TV stages: {missing}")

    unproven = []
    for stage, att in stage_attestations.items():
        if att is None:
            unproven.append(stage)
            continue
        if not getattr(att, "is_genuine", False):
            unproven.append(stage)
    observed["unproven_stages"] = unproven
    if unproven:
        return Verdict(name, False, observed,
                       f"pipeline TV stages lack genuine execution attestation: {unproven}")

    metrics_gate = strategy_tester_pass_requires_actual_metrics(
        stage_attestations.get("strategy_tester"), tv_metrics)
    trades_gate = trade_extraction_pass_requires_actual_trade_payload(
        stage_attestations.get("strategy_tester"), tv_trades)
    observed["metrics_gate"] = metrics_gate.to_dict()
    observed["trades_gate"] = trades_gate.to_dict()
    if not metrics_gate.passed:
        return Verdict(name, False, observed, f"metrics gate failed: {metrics_gate.reason}")
    if not trades_gate.passed:
        return Verdict(name, False, observed, f"trades gate failed: {trades_gate.reason}")
    return Verdict(name, True, observed, "all TradingView pipeline stages are genuinely attested")


# --------------------------------------------------------------------------- #
# Shared extraction helpers
# --------------------------------------------------------------------------- #


def _norm(kind: str, value: Any) -> str:
    """Compare symbols/timeframes tolerantly (case, exchange suffix, tv resolution)."""
    text = str(value).strip().upper()
    if kind == "timeframe":
        alias = {"1M": "1", "1MIN": "1", "3M": "3", "5M": "5", "15M": "15", "30M": "30",
                 "1H": "60", "60M": "60", "4H": "240", "240M": "240",
                 "1D": "D", "D1": "D", "1W": "W", "W1": "W"}
        text = alias.get(text, text)
        if text.isdigit():
            return str(int(text))
        return text
    if ":" in text:                      # BINANCE:BTCUSDT -> BTCUSDT
        text = text.split(":", 1)[1]
    return text


def extract_trade_count(payload: Any) -> Optional[int]:
    """Best-effort trade count from a heterogeneous payload."""
    if payload is None:
        return None
    if isinstance(payload, (int, float)) and not isinstance(payload, bool):
        return int(payload)
    if isinstance(payload, list):
        return len(payload)
    if isinstance(payload, dict):
        for key in ("totalTrades", "total_trades", "n_trades", "numTrades",
                    "trades_count", "trade_count", "closed_trades"):
            if key in payload:
                val = payload[key]
                if isinstance(val, (int, float)) and not isinstance(val, bool):
                    return int(val)
                if isinstance(val, list):
                    return len(val)
        for key in ("trades", "trade_log", "orders", "results", "data"):
            if isinstance(payload.get(key), list):
                return len(payload[key])
        numeric = [v for k, v in payload.items() if "trade" in k.lower()
                   and isinstance(v, (int, float)) and not isinstance(v, bool)]
        if numeric:
            return int(numeric[0])
    return None


def extract_trade_rows(payload: Any) -> List[Dict[str, Any]]:
    """Normalise a trade list into a list of dict rows."""
    if payload is None:
        return []
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if isinstance(payload, dict):
        for key in ("trades", "trade_log", "orders", "results", "data", "list"):
            val = payload.get(key)
            if isinstance(val, list):
                return [row for row in val if isinstance(row, dict)]
    return []


def _collect_numeric(payload: Any, _depth: int = 0) -> Dict[str, float]:
    """Flatten numeric leaves out of a nested metrics payload."""
    found: Dict[str, float] = {}
    if _depth > 6:
        return found
    if isinstance(payload, dict):
        for key, val in payload.items():
            if isinstance(val, bool) or val is None:
                continue
            if isinstance(val, (int, float)):
                found[key] = float(val)
            elif isinstance(val, (dict, list)):
                for sub_key, sub_val in _collect_numeric(val, _depth + 1).items():
                    found[f"{key}.{sub_key}"] = sub_val
    elif isinstance(payload, list) and payload:
        merged = _collect_numeric(payload[0], _depth + 1)
        for key, val in merged.items():
            found[key] = val
    return found


# --------------------------------------------------------------------------- #
# Aggregated gate
# --------------------------------------------------------------------------- #

ALL_INVARIANTS = (
    "PARITY_REQUIRES_REAL_TV_RESULT",
    "PARITY_REQUIRES_PYTHON_TRADES_GT_0",
    "PARITY_REQUIRES_TV_TRADES_GT_0",
    "TV_MUTATION_REQUIRES_READBACK",
    "PINE_WRITE_REQUIRES_HASH_READBACK",
    "STRATEGY_TESTER_PASS_REQUIRES_ACTUAL_METRICS",
    "TRADE_EXTRACTION_PASS_REQUIRES_ACTUAL_TRADE_PAYLOAD",
    "FULL_PIPELINE_REQUIRES_REAL_TV_EXECUTION",
)


def evaluate_all(verdicts: List[Verdict]) -> Dict[str, Any]:
    """Aggregate verdicts into a machine-readable gate summary."""
    passed = [v for v in verdicts if v.passed]
    failed = [v for v in verdicts if not v.passed]
    return {
        "invariants_declared": list(ALL_INVARIANTS),
        "invariants_exercised": [v.name for v in verdicts],
        "invariants_exercised_all_declared": {v.name for v in verdicts} == set(ALL_INVARIANTS),
        "passed": [v.to_dict() for v in passed],
        "failed": [v.to_dict() for v in failed],
        "gate": "PASS" if not failed else "FAIL",
    }