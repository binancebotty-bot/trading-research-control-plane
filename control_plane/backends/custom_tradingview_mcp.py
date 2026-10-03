"""
Custom TradingView MCP Backend
===============================

Canonical execution path for every TradingView operation in the control plane.

This backend owns the *real* MCP transport (``MCPClient`` -> node
``src/server.js`` -> stdio JSON-RPC 2.0 -> Chrome DevTools Protocol -> the live
TradingView page). There is exactly one reality: this module never fabricates a
response. If the MCP server or the browser is unavailable, calls fail loudly.

The 2026-10-02 handoff was invalidated because this class previously contained a
``_call_tool`` stub that returned::

    {"tool": ..., "args": ..., "note": "Tool metadata - actual execution requires MCP client"}

and reported ``success=True`` regardless of reality. That stub is gone. Every
call now carries an ``ExecutionAttestation`` binding the payload to a concrete
CDP target, and the invariant gates in ``control_plane.invariants`` reject any
payload that is empty, a request echo, or carries placeholder markers.
"""

from __future__ import annotations

import os
import sys
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from control_plane.backends.mcp_client import MCPClient, MCPToolInfo
from control_plane.invariants import (
    ExecutionAttestation,
    Verdict,
    pine_write_requires_hash_readback,
    scan_for_placeholder,
    sha256_of,
    tv_mutation_requires_readback,
)

MCP_DIR = Path(r"C:\Users\wigmore\trading_stack\tradingview-mcp-jackson")

# The MCP server's own CDP settings (tradingview-mcp-jackson/src/connection.js).
# These must agree, or the MCP will drive a different browser than we certify.
CDP_HOST = os.environ.get("CDP_HOST", "127.0.0.1")
CDP_PORT = int(os.environ.get("CDP_PORT", "9222"))


class MCPTransport(Enum):
    STDIO = "stdio"
    HTTP = "http"


@dataclass
class TVCallResult:
    """A real MCP tool result plus the attestation that it really happened."""

    tool: str
    ok: bool
    payload: Any = None
    error: Optional[str] = None
    attestation: Optional[ExecutionAttestation] = None
    raw_response: str = ""
    execution_time_ms: float = 0.0

    @property
    def genuine(self) -> bool:
        return self.ok and self.attestation is not None and self.attestation.is_genuine

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool": self.tool,
            "ok": self.ok,
            "genuine": self.genuine,
            "payload": self.payload,
            "error": self.error,
            "attestation": self.attestation.to_dict() if self.attestation else None,
            "raw_response": self.raw_response,
            "execution_time_ms": self.execution_time_ms,
        }


@dataclass
class PineCompileResult:
    success: bool
    errors: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[Dict[str, Any]] = field(default_factory=list)
    raw_data: Dict[str, Any] = field(default_factory=dict)
    attestation: Optional[ExecutionAttestation] = None


@dataclass
class StrategyTesterResult:
    """Strategy Tester metrics, extracted from a real run."""

    strategy_name: Optional[str] = None
    net_profit: Optional[float] = None
    total_trades: Optional[int] = None
    percent_profitable: Optional[float] = None
    profit_factor: Optional[float] = None
    max_drawdown: Optional[float] = None
    avg_trade: Optional[float] = None
    avg_win: Optional[float] = None
    avg_loss: Optional[float] = None
    largest_win: Optional[float] = None
    largest_loss: Optional[float] = None
    raw_data: Dict[str, Any] = field(default_factory=dict)
    attestation: Optional[ExecutionAttestation] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "strategy_name": self.strategy_name,
            "net_profit": self.net_profit,
            "total_trades": self.total_trades,
            "percent_profitable": self.percent_profitable,
            "profit_factor": self.profit_factor,
            "max_drawdown": self.max_drawdown,
            "avg_trade": self.avg_trade,
            "avg_win": self.avg_win,
            "avg_loss": self.avg_loss,
            "largest_win": self.largest_win,
            "largest_loss": self.largest_loss,
            "raw_data": self.raw_data,
            "attestation": self.attestation.to_dict() if self.attestation else None,
        }


class CustomTradingViewMCPBackend:
    """
    Canonical TradingView backend backed by genuine MCP execution.

    Every public method performs real I/O against the live TradingView page.
    Mutations are verified by reading state back, and the verification verdict is
    returned alongside the result so callers can enforce it.
    """

    def __init__(
        self,
        mcp_dir: Optional[Path] = None,
        transport: MCPTransport = MCPTransport.STDIO,
        cdp_host: str = CDP_HOST,
        cdp_port: int = CDP_PORT,
        autostart: bool = True,
    ):
        self.mcp_dir = Path(mcp_dir) if mcp_dir else MCP_DIR
        self.transport = transport
        self._client = MCPClient(
            server_dir=str(self.mcp_dir),
            server_script="src/server.js",
            cdp_host=cdp_host,
            cdp_port=cdp_port,
        )
        self._started = False
        self._initialized = False
        if autostart:
            self.start()

    # ------------------------------------------------------------------ #
    # Lifecycle
    # ------------------------------------------------------------------ #

    def start(self) -> bool:
        """Start and initialise the MCP server process."""
        if self._started:
            return True
        if not self._client.start():
            raise RuntimeError(
                "TradingView MCP server failed to start; refusing to fabricate results"
            )
        self._client.initialize()
        self._started = True
        self._initialized = True
        return True

    def stop(self) -> None:
        self._client.stop()
        self._started = False

    @property
    def client(self) -> MCPClient:
        return self._client

    @property
    def backend_id(self) -> str:
        return "TRADINGVIEW_CUSTOM_MCP"

    # ------------------------------------------------------------------ #
    # Session identity
    # ------------------------------------------------------------------ #

    def describe_session(self) -> Dict[str, Any]:
        """
        Establish which browser/tab this backend actually controls.

        Answers the corrective-pass questions: which Edge instance, which CDP
        port, which TradingView tab, and was it visible.
        """
        cdp = self._client.verify_cdp_endpoint()
        match = self._client.assert_target_matches_cdp()
        tv_targets = cdp.get("tradingview_targets", [])
        state = self.call_tool("chart_get_state", {})
        snapshot = self.call_tool("tv_state_snapshot", {})
        return {
            "cdp_endpoint": f"{self.cdp_host}:{self.cdp_port}",
            "cdp_reachable": cdp.get("reachable"),
            "cdp_browser": cdp.get("browser"),
            "cdp_protocol": cdp.get("protocol_version"),
            "cdp_target_count": len(cdp.get("targets", [])),
            "tradingview_chart_tabs": tv_targets,
            "mcp_target_id": match.get("mcp_target_id"),
            "mcp_target_url": match.get("mcp_target_url"),
            "mcp_target_title": match.get("mcp_target_title"),
            "mcp_cdp_endpoint_match": match.get("verdict"),
            "chart_state": state.payload,
            "state_snapshot": snapshot.payload,
            "visible_session": bool(match.get("target_found_on_cdp")),
        }

    @property
    def cdp_host(self) -> str:
        return self._client.cdp_host

    @property
    def cdp_port(self) -> int:
        return self._client.cdp_port

    # ------------------------------------------------------------------ #
    # The single canonical tool-call path
    # ------------------------------------------------------------------ #

    def call_tool(self, tool: str, args: Optional[Dict[str, Any]] = None) -> TVCallResult:
        """
        Invoke an MCP tool over the real transport and mint an attestation.

        This is the ONLY path to TradingView in the control plane. There is no
        metadata fallback: a failure here propagates as a failure.
        """
        if not self._started:
            self.start()

        result = self._client.call_tool(tool, args or {})
        payload = result.result

        identity: Dict[str, Any] = {}
        try:
            identity = self._client.get_target_identity()
        except Exception:
            identity = {}

        attestation = ExecutionAttestation(
            tool=tool,
            transport="stdio-jsonrpc" if result.success else "stdio-jsonrpc(failed)",
            target_id=identity.get("target_id"),
            target_url=identity.get("target_url"),
            target_title=identity.get("target_title"),
            cdp_host=self.cdp_host,
            cdp_port=self.cdp_port,
            request_id=result.request_id,
            payload_sha256=sha256_of(payload),
            payload_nonempty=payload not in (None, {}, [], ""),
            placeholder_markers=scan_for_placeholder(payload),
        )

        return TVCallResult(
            tool=tool,
            ok=result.success,
            payload=payload,
            error=result.error,
            attestation=attestation,
            raw_response=result.raw_response,
            execution_time_ms=result.execution_time_ms,
        )

    # ------------------------------------------------------------------ #
    # Read state (non-mutating)
    # ------------------------------------------------------------------ #

    def get_chart_state(self) -> TVCallResult:
        return self.call_tool("chart_get_state", {})

    def get_pine_source(self) -> TVCallResult:
        return self.call_tool("pine_get_source", {})

    def get_visible_range(self) -> TVCallResult:
        return self.call_tool("chart_get_visible_range", {})

    def list_scripts(self) -> TVCallResult:
        return self.call_tool("pine_list_scripts", {})

    def detect_modal(self) -> TVCallResult:
        return self.call_tool("pine_detect_blocking_modal", {})

    # ------------------------------------------------------------------ #
    # Mutations with mandatory readback
    # ------------------------------------------------------------------ #

    def _read_symbol(self) -> Optional[str]:
        res = self.get_chart_state()
        payload = res.payload if isinstance(res.payload, dict) else {}
        return payload.get("symbol")

    def _read_timeframe(self) -> Optional[str]:
        res = self.get_chart_state()
        payload = res.payload if isinstance(res.payload, dict) else {}
        return payload.get("resolution")

    def set_symbol(self, symbol: str, settle_seconds: float = 1.5) -> Dict[str, Any]:
        """
        Change chart symbol and PROVE it landed via state readback.

        A successful MCP response is not sufficient; the chart must report the
        requested symbol afterwards (TV_MUTATION_REQUIRES_READBACK).
        """
        before = self._read_symbol()
        call = self.call_tool("chart_set_symbol", {"symbol": symbol})
        time.sleep(settle_seconds)
        after = self._read_symbol()
        verdict = tv_mutation_requires_readback("symbol", before, symbol, after)
        return {
            "operation": "chart_set_symbol",
            "requested": symbol,
            "before": before,
            "after": after,
            "mcp_ok": call.ok,
            "mcp_payload": call.payload,
            "mcp_attestation": call.attestation.to_dict() if call.attestation else None,
            "verdict": verdict.to_dict(),
            "passed": verdict.passed,
        }

    def set_timeframe(self, timeframe: str, settle_seconds: float = 1.5) -> Dict[str, Any]:
        """Change chart timeframe and prove it via state readback."""
        before = self._read_timeframe()
        call = self.call_tool("chart_set_timeframe", {"timeframe": timeframe})
        time.sleep(settle_seconds)
        after = self._read_timeframe()
        verdict = tv_mutation_requires_readback("timeframe", before, timeframe, after)
        return {
            "operation": "chart_set_timeframe",
            "requested": timeframe,
            "before": before,
            "after": after,
            "mcp_ok": call.ok,
            "mcp_payload": call.payload,
            "mcp_attestation": call.attestation.to_dict() if call.attestation else None,
            "verdict": verdict.to_dict(),
            "passed": verdict.passed,
        }

    def _read_pine_source(self) -> Optional[str]:
        res = self.get_pine_source()
        payload = res.payload
        if isinstance(payload, dict):
            for key in ("source", "code", "text", "pine_source", "content"):
                if isinstance(payload.get(key), str):
                    return payload[key]
            return None
        if isinstance(payload, str):
            return payload
        return None

    def set_pine_source(self, source: str, settle_seconds: float = 1.0) -> Dict[str, Any]:
        """
        Write Pine source to the editor and PROVE it via hash readback.

        Fail closed on ``pine_set_source`` failure: never invoke an alternate
        write mechanism. Always return the observed source/hash evidence.
        """
        before = self._read_pine_source()
        call = self.call_tool("pine_set_source", {"source": source})
        time.sleep(settle_seconds)
        after = self._read_pine_source()
        verdict = pine_write_requires_hash_readback(before, source, after)
        return {
            "operation": "pine_set_source",
            "tool_used": call.tool,
            "before_sha256": sha256_of(before) if before is not None else None,
            "requested_sha256": sha256_of(source),
            "after_sha256": sha256_of(after) if after is not None else None,
            "mcp_ok": call.ok,
            "mcp_payload": call.payload,
            "mcp_attestation": call.attestation.to_dict() if call.attestation else None,
            "verdict": verdict.to_dict(),
            "passed": call.ok and verdict.passed,
        }

    # ------------------------------------------------------------------ #
    # Compile / deploy
    # ------------------------------------------------------------------ #

    def compile_pine(self, source: Optional[str] = None) -> PineCompileResult:
        """
        Compile Pine against TradingView.

        Prefers ``pine_compile`` (uses the open editor). ``pine_compile_facade``
        does not exist in this server and is never called.
        """
        args: Dict[str, Any] = {"source": source} if source else {}
        call = self.call_tool("pine_compile", args)
        payload = call.payload if isinstance(call.payload, dict) else {}
        errors = payload.get("errors") or []
        warnings = payload.get("warnings") or []
        success = bool(payload.get("success", call.ok)) and not errors
        return PineCompileResult(
            success=success,
            errors=errors if isinstance(errors, list) else [errors],
            warnings=warnings if isinstance(warnings, list) else [warnings],
            raw_data=payload,
            attestation=call.attestation,
        )

    def add_to_chart(self, allow_update_existing: bool = True, expected_study_id: Optional[str] = None) -> TVCallResult:
        args = {"allow_update_existing": allow_update_existing}
        if expected_study_id is not None:
            if not isinstance(expected_study_id, str) or not expected_study_id or expected_study_id.strip() != expected_study_id:
                raise ValueError("expected_study_id must be an exact non-empty string without surrounding whitespace")
            args["expected_study_id"] = expected_study_id
        return self.call_tool("pine_add_to_chart", args)

    def create_new_script(self, script_type: str = "strategy") -> TVCallResult:
        return self.call_tool("pine_new", {"type": script_type})

    def open_strategy_tester(self) -> TVCallResult:
        """Foreground the Strategy Tester panel (bottom widget bar)."""
        return self.call_tool("ui_open_panel", {"panel": "strategy-tester", "action": "open"})

    def ui_evaluate(self, expression: str) -> TVCallResult:
        """
        Independent read layer: evaluate JS in the page and return the value.

        Per tradingview-mcp-jackson/AGENTS.md, a mutation should be confirmed
        through at least two independent layers. This is the second layer that
        does not depend on the MCP's own readback.
        """
        return self.call_tool("ui_evaluate", {"expression": expression})

    def document_title(self) -> TVCallResult:
        return self.ui_evaluate("document.title")

    def screenshot(self, path: Optional[str] = None) -> TVCallResult:
        args: Dict[str, Any] = {}
        if path:
            args["filename"] = path
        return self.call_tool("capture_screenshot", args)

    # ------------------------------------------------------------------ #
    # Strategy Tester extraction (real data only)
    # ------------------------------------------------------------------ #

    def read_strategy_tester(self) -> StrategyTesterResult:
        """Read Strategy Tester summary from a real run."""
        call = self.call_tool("strategy_tester_read_summary", {})
        data = call.payload if isinstance(call.payload, dict) else {}
        summary = data.get("summary") if isinstance(data.get("summary"), dict) else {}

        def metric(camel: str, snake: str):
            for shape in (summary, data):
                for key in (camel, snake):
                    if key in shape:
                        return shape[key]
            return None

        return StrategyTesterResult(
            strategy_name=metric("strategyName", "strategy_name"),
            net_profit=metric("netProfit", "net_profit"),
            total_trades=metric("totalTrades", "total_trades"),
            percent_profitable=metric("percentProfitable", "percent_profitable"),
            profit_factor=metric("profitFactor", "profit_factor"),
            max_drawdown=metric("maxDrawdown", "max_drawdown"),
            avg_trade=metric("avgTrade", "avg_trade"),
            avg_win=metric("avgWin", "avg_win"),
            avg_loss=metric("avgLoss", "avg_loss"),
            largest_win=metric("largestWin", "largest_win"),
            largest_loss=metric("largestLoss", "largest_loss"),
            raw_data=data,
            attestation=call.attestation,
        )

    def get_strategy_results(self) -> TVCallResult:
        return self.call_tool("data_get_strategy_results", {})

    def get_trades(self, max_trades: Optional[int] = None) -> TVCallResult:
        """Read genuine raw order records; never label them native closed trades."""
        if max_trades is not None and (isinstance(max_trades, bool) or not isinstance(max_trades, int) or not 1 <= max_trades <= 1000):
            raise ValueError("max_trades must be an integer in 1..1000")
        args = {} if max_trades is None else {"max_trades": max_trades}
        result = self.call_tool("data_get_trades", args)
        if result.ok and isinstance(result.payload, dict):
            payload = dict(result.payload)
            records = payload.pop("trades", payload.get("raw_order_records", []))
            payload.pop("trade_count", None)
            payload.update(record_semantics="raw_order_records", raw_order_records=records,
                           raw_order_record_count=len(records), closed_trades=payload.get("closed_trades"),
                           order_stream_complete=payload.get("order_stream_complete"))
            result.payload = payload
        return result

    def get_equity(self) -> TVCallResult:
        """Extract the real equity curve from the Strategy Tester."""
        return self.call_tool("data_get_equity", {})

    def get_ohlcv(self, **kwargs) -> TVCallResult:
        return self.call_tool("data_get_ohlcv", kwargs)

    # ------------------------------------------------------------------ #
    # Tool discovery / registry
    # ------------------------------------------------------------------ #

    def list_tools(self) -> List[MCPToolInfo]:
        """Discover tools from the real server (not a hardcoded list)."""
        if not self._started:
            self.start()
        return self._client.list_tools()

    @property
    def capabilities(self) -> List[str]:
        return sorted(t.name for t in self.list_tools())

    def get_capability_registry(self) -> Dict[str, Any]:
        return {
            "backend": self.backend_id,
            "transport": "stdio-jsonrpc-2.0",
            "server_dir": str(self.mcp_dir),
            "cdp_endpoint": f"{self.cdp_host}:{self.cdp_port}",
            "tool_count": len(self.capabilities),
            "tools": self.capabilities,
            "placeholder_execution": False,
            "attestation": "ExecutionAttestation required for every TV result",
        }


def create_custom_tv_mcp_backend(**kwargs) -> CustomTradingViewMCPBackend:
    return CustomTradingViewMCPBackend(**kwargs)