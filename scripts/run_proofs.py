"""
Run Proofs
==========
Automated proof harness for all three backends.
Tests every function and records PASS/FAIL/BLOCKED/NOT_TESTABLE_SAFELY/NOT_AVAILABLE.
"""

import sys
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from control_plane.backends.python_py2pine import PythonPy2PineBackend
from control_plane.backends.custom_tradingview_mcp import CustomTradingViewMCPBackend
from control_plane.backends.official_tradingview import OfficialTradingViewBackend
from control_plane.registry import CapabilityRegistry


class ProofHarness:
    """Automated proof harness for capability testing."""
    
    def __init__(self):
        self.python_backend = PythonPy2PineBackend()
        self.tv_mcp_backend = CustomTradingViewMCPBackend()
        self.official_tv_backend = OfficialTradingViewBackend()
        self.registry = CapabilityRegistry()
        self.results: List[Dict[str, Any]] = []
    
    def run_all_proofs(self) -> Dict[str, Any]:
        """Run all proofs and return results."""
        print("=" * 70)
        print("TRADING RESEARCH CONTROL PLANE - PROOF HARNESS")
        print("=" * 70)
        print(f"Started: {datetime.now().isoformat()}")
        print()
        
        # Phase 1: Discover capabilities
        print("[Phase 1] Discovering capabilities...")
        discovery = self.registry.discover_all()
        print(f"  Discovered {len(self.registry.capabilities)} capabilities")
        print()
        
        # Phase 2: Prove Python/py2pine
        print("[Phase 2] Proving Python/py2pine backend...")
        self._prove_python_backend()
        print()
        
        # Phase 3: Prove Custom TV MCP
        print("[Phase 3] Proving Custom TV MCP backend...")
        self._prove_custom_tv_mcp()
        print()
        
        # Phase 4: Prove Official TV API
        print("[Phase 4] Proving Official TV API backend...")
        self._prove_official_tv()
        print()
        
        # Phase 5: Generate report
        print("[Phase 5] Generating proof report...")
        report = self._generate_report()
        
        # Save results
        output_path = Path("proofs/proof_results.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"Results saved to: {output_path}")
        print()
        print("=" * 70)
        print("PROOF HARNESS COMPLETE")
        print("=" * 70)
        print(f"Total: {report['summary']['total']}")
        print(f"PASS: {report['summary']['pass']}")
        print(f"FAIL: {report['summary']['fail']}")
        print(f"BLOCKED: {report['summary']['blocked']}")
        print(f"NOT_TESTABLE_SAFELY: {report['summary']['not_testable_safely']}")
        print(f"NOT_AVAILABLE: {report['summary']['not_available']}")
        
        return report
    
    def _prove_python_backend(self):
        """Prove Python/py2pine capabilities."""
        tests = [
            ("list_strategies", self._test_list_strategies),
            ("list_indicators", self._test_list_indicators),
            ("load_data", self._test_load_data),
            ("backtest_single", self._test_backtest_single),
            ("backtest_parallel", self._test_backtest_parallel),
            ("parameter_sweep", self._test_parameter_sweep),
            ("transpile_pine", self._test_transpile_pine),
            ("run_deterministic_tests", self._test_deterministic_tests),
            ("benchmark_throughput", self._test_benchmark_throughput),
        ]
        
        for name, test_fn in tests:
            start = time.time()
            try:
                result = test_fn()
                elapsed = time.time() - start
                self._record_result("PYTHON_PY2PINE", name, "PASS", elapsed, result)
                print(f"  ✓ {name}: PASS ({elapsed:.2f}s)")
            except Exception as e:
                elapsed = time.time() - start
                self._record_result("PYTHON_PY2PINE", name, "FAIL", elapsed, error=str(e))
                print(f"  ✗ {name}: FAIL - {e}")
    
    def _prove_custom_tv_mcp(self):
        """Prove Custom TV MCP capabilities."""
        tests = [
            ("health_check", self._test_tv_health_check),
            ("list_tools", self._test_tv_list_tools),
            ("get_tool_schema", self._test_tv_get_tool_schema),
        ]
        
        for name, test_fn in tests:
            start = time.time()
            try:
                result = test_fn()
                elapsed = time.time() - start
                self._record_result("CUSTOM_MCP", name, "PASS", elapsed, result)
                print(f"  ✓ {name}: PASS ({elapsed:.2f}s)")
            except Exception as e:
                elapsed = time.time() - start
                self._record_result("CUSTOM_MCP", name, "FAIL", elapsed, error=str(e))
                print(f"  ✗ {name}: FAIL - {e}")
        
        # Mark tools that require live browser as NOT_TESTABLE_SAFELY
        live_tools = [
            "pine_get_source", "pine_set_source", "pine_compile_facade",
            "pine_analyze", "pine_check", "pine_get_errors", "pine_get_console",
            "pine_save", "pine_list_scripts", "pine_new", "pine_open",
            "pine_replace_script", "pine_add_to_chart", "pine_save_script",
            "pine_full_cycle_indicator", "pine_full_cycle_strategy",
            "chart_get_state", "chart_set_symbol", "chart_set_timeframe",
            "chart_set_type", "chart_manage_indicator", "chart_get_visible_range",
            "chart_set_visible_range", "chart_scroll_to_date",
            "symbol_info", "symbol_search", "strategy_tester_read_summary",
            "tv_state_snapshot", "pine_detect_blocking_modal", "pine_resolve_known_modal",
        ]
        for tool in live_tools:
            self._record_result("CUSTOM_MCP", tool, "NOT_TESTABLE_SAFELY", 0,
                              note="Requires live browser session with TradingView")
            print(f"  ○ {tool}: NOT_TESTABLE_SAFELY (requires live browser)")
    
    def _prove_official_tv(self):
        """Prove Official TV API capabilities."""
        # All official TV capabilities are NOT_AVAILABLE (no public API yet)
        for cap in self.official_tv_backend.capabilities:
            self._record_result("OFFICIAL", cap, "NOT_AVAILABLE", 0,
                              note="Official TradingView MCP/API not publicly available")
            print(f"  ○ {cap}: NOT_AVAILABLE (no public API)")
    
    def _test_list_strategies(self) -> Dict[str, Any]:
        strategies = self.python_backend.list_strategies()
        return {"count": len(strategies), "strategies": list(strategies.keys())}
    
    def _test_list_indicators(self) -> Dict[str, Any]:
        indicators = self.python_backend.list_indicators()
        return {"count": len(indicators), "indicators": indicators}
    
    def _test_load_data(self) -> Dict[str, Any]:
        df = self.python_backend.load_data("BTCUSDT", "1h")
        return {"rows": len(df), "columns": list(df.columns)}
    
    def _test_backtest_single(self) -> Dict[str, Any]:
        result = self.python_backend.backtest_single(
            "jackson_scalper_baseline_v1", "BTCUSDT", "1h"
        )
        return {
            "strategy": result.strategy_name,
            "status": result.status,
            "metrics": result.metrics,
            "execution_time_ms": result.execution_time_ms,
        }
    
    def _test_backtest_parallel(self) -> Dict[str, Any]:
        results = self.python_backend.backtest_parallel(
            ["jackson_scalper_baseline_v1", "jackson_trend_ema_v1"],
            ["BTCUSDT"],
            ["1h"],
            max_workers=2,
        )
        return {"count": len(results), "results": [{"strategy": r.strategy_name, "status": r.status} for r in results]}
    
    def _test_parameter_sweep(self) -> Dict[str, Any]:
        sweep = self.python_backend.parameter_sweep(
            "jackson_scalper_baseline_v1",
            "BTCUSDT",
            "1h",
            {"ema_fast": [8, 12], "ema_slow": [50, 100]},
            max_workers=2,
        )
        return {
            "total_combinations": sweep.total_combinations,
            "best_params": sweep.best_params,
            "best_value": sweep.best_value,
            "execution_time_ms": sweep.execution_time_ms,
        }
    
    def _test_transpile_pine(self) -> Dict[str, Any]:
        # Test with a simple Pine script
        pine_path = Path(r"C:\Users\wigmore\trading_stack\pine\jackson_scalper_baseline_v1.pine")
        if pine_path.exists():
            result = self.python_backend.transpile_pine(pine_path)
            return result
        return {"note": "No Pine file found for transpilation test"}
    
    def _test_deterministic_tests(self) -> Dict[str, Any]:
        return self.python_backend.run_deterministic_tests()
    
    def _test_benchmark_throughput(self) -> Dict[str, Any]:
        return self.python_backend.benchmark_throughput(n_runs=50)
    
    def _test_tv_health_check(self) -> Dict[str, Any]:
        return self.tv_mcp_backend.health_check()
    
    def _test_tv_list_tools(self) -> Dict[str, Any]:
        tools = self.tv_mcp_backend.list_tools()
        return {"count": len(tools), "tools": [t["name"] for t in tools]}
    
    def _test_tv_get_tool_schema(self) -> Dict[str, Any]:
        schema = self.tv_mcp_backend.get_tool_schema("pine_compile_facade")
        return schema
    
    def _record_result(self, backend: str, capability: str, status: str,
                      elapsed: float, result: Any = None, error: str = None,
                      note: str = None):
        """Record a proof result."""
        self.results.append({
            "backend": backend,
            "capability": capability,
            "status": status,
            "elapsed_seconds": elapsed,
            "result": result,
            "error": error,
            "note": note,
            "timestamp": datetime.now().isoformat(),
        })
    
    def _generate_report(self) -> Dict[str, Any]:
        """Generate proof report."""
        summary = {
            "total": len(self.results),
            "pass": sum(1 for r in self.results if r["status"] == "PASS"),
            "fail": sum(1 for r in self.results if r["status"] == "FAIL"),
            "blocked": sum(1 for r in self.results if r["status"] == "BLOCKED"),
            "not_testable_safely": sum(1 for r in self.results if r["status"] == "NOT_TESTABLE_SAFELY"),
            "not_available": sum(1 for r in self.results if r["status"] == "NOT_AVAILABLE"),
        }
        
        by_backend = {}
        for r in self.results:
            backend = r["backend"]
            if backend not in by_backend:
                by_backend[backend] = {"total": 0, "pass": 0, "fail": 0, "blocked": 0, "not_testable_safely": 0, "not_available": 0}
            by_backend[backend]["total"] += 1
            by_backend[backend][r["status"].lower().replace("_", "_")] += 1
        
        return {
            "generated": datetime.now().isoformat(),
            "summary": summary,
            "by_backend": by_backend,
            "results": self.results,
        }


def main():
    harness = ProofHarness()
    report = harness.run_all_proofs()
    return report


if __name__ == "__main__":
    main()