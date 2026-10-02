"""
Execute Real MCP Proof Ladder
=============================
Actually invokes MCP tools against the live TradingView session.
Captures real evidence for each proof step.
"""

import sys
import json
import time
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

sys.path.insert(0, str(Path(__file__).parent.parent))

from control_plane.backends.mcp_client import MCPClient, MCPToolResult


class ProofLadder:
    """Execute the custom MCP proof ladder with real tool invocations."""
    
    def __init__(self, output_dir: Path = None):
        self.client = MCPClient()
        self.output_dir = output_dir or Path("proofs/runs") / datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results: List[Dict[str, Any]] = []
        self.run_id = hashlib.sha256(str(time.time()).encode()).hexdigest()[:16]
    
    def run(self) -> Dict[str, Any]:
        """Execute the complete proof ladder."""
        print("=" * 70)
        print("CUSTOM MCP PROOF LADDER - REAL EXECUTION")
        print("=" * 70)
        print(f"Run ID: {self.run_id}")
        print(f"Started: {datetime.now().isoformat()}")
        print()
        
        # Start MCP server
        print("[Step 0] Starting MCP server...")
        if not self.client.start():
            return self._create_failure_result("Failed to start MCP server")
        print("  MCP server started")
        print()
        
        try:
            # Step 1: Initialize
            print("[Step 1] MCP initialize...")
            init_result = self._execute_step("initialize", self._step_initialize)
            
            # Step 2: Tool discovery
            print("[Step 2] MCP tool discovery...")
            tools_result = self._execute_step("tool_discovery", self._step_tool_discovery)
            
            # Step 3: Health check
            print("[Step 3] Health check...")
            health_result = self._execute_step("health_check", self._step_health_check)
            
            # Step 4: Chart state read
            print("[Step 4] Chart state read...")
            chart_state_result = self._execute_step("chart_state_read", self._step_chart_state)
            
            # Step 5: Symbol read
            print("[Step 5] Symbol info...")
            symbol_result = self._execute_step("symbol_read", self._step_symbol_info)
            
            # Step 6: Timeframe read (from chart state)
            print("[Step 6] Timeframe read...")
            timeframe_result = self._execute_step("timeframe_read", self._step_timeframe_read)
            
            # Step 7: Pine source read
            print("[Step 7] Pine source read...")
            pine_read_result = self._execute_step("pine_source_read", self._step_pine_get_source)
            
            # Step 8: Pine static analysis
            print("[Step 8] Pine static analysis...")
            pine_analyze_result = self._execute_step("pine_static_analysis", self._step_pine_analyze)
            
            # Step 9: Pine compile
            print("[Step 9] Pine compile...")
            pine_compile_result = self._execute_step("pine_compile", self._step_pine_compile)
            
            # Step 10: Compiler diagnostics
            print("[Step 10] Compiler diagnostics...")
            compiler_diag_result = self._execute_step("compiler_diagnostics", self._step_compiler_diagnostics)
            
            # Step 11: Controlled Pine source write
            print("[Step 11] Controlled Pine source write...")
            pine_write_result = self._execute_step("pine_source_write", self._step_pine_write)
            
            # Step 12: Compile modified fixture
            print("[Step 12] Compile modified fixture...")
            compile_fixture_result = self._execute_step("compile_modified_fixture", self._step_compile_fixture)
            
            # Step 13: Add fixture strategy to chart
            print("[Step 13] Add fixture strategy to chart...")
            add_chart_result = self._execute_step("add_to_chart", self._step_add_to_chart)
            
            # Step 14: Strategy Tester availability
            print("[Step 14] Strategy Tester availability...")
            tester_avail_result = self._execute_step("strategy_tester_availability", self._step_tester_availability)
            
            # Step 15: Strategy Tester summary
            print("[Step 15] Strategy Tester summary...")
            tester_summary_result = self._execute_step("strategy_tester_summary", self._step_tester_summary)
            
            # Step 16: Trade extraction
            print("[Step 16] Trade extraction...")
            trades_result = self._execute_step("trade_extraction", self._step_trade_extraction)
            
            # Step 17: Equity/drawdown extraction
            print("[Step 17] Equity/drawdown extraction...")
            equity_result = self._execute_step("equity_extraction", self._step_equity_extraction)
            
            # Step 18: Chart/symbol change
            print("[Step 18] Chart/symbol change...")
            symbol_change_result = self._execute_step("symbol_change", self._step_symbol_change)
            
            # Step 19: Timeframe change
            print("[Step 19] Timeframe change...")
            timeframe_change_result = self._execute_step("timeframe_change", self._step_timeframe_change)
            
            # Step 20: State restoration
            print("[Step 20] State restoration...")
            restore_result = self._execute_step("state_restoration", self._step_state_restoration)
            
            # Step 21: Complete Pine strategy cycle
            print("[Step 21] Complete Pine strategy cycle...")
            full_cycle_result = self._execute_step("full_strategy_cycle", self._step_full_cycle)
            
            # Generate final report
            return self._generate_report()
            
        except Exception as e:
            print(f"Proof ladder failed: {e}")
            return self._create_failure_result(str(e))
        finally:
            self.client.stop()
    
    def _execute_step(self, step_name: str, step_fn) -> Dict[str, Any]:
        """Execute a single proof step and record the result."""
        start = time.time()
        try:
            result = step_fn()
            elapsed = time.time() - start
            record = {
                "step": step_name,
                "status": "PASS" if result.get("success") else "FAIL",
                "elapsed_seconds": elapsed,
                "timestamp": datetime.now().isoformat(),
                "result": result,
            }
            self.results.append(record)
            status = "PASS" if record["status"] == "PASS" else "FAIL"
            print(f"  {step_name}: {status} ({elapsed:.2f}s)")
            if not result.get("success"):
                print(f"    Error: {result.get('error', 'Unknown')}")
            return result
        except Exception as e:
            elapsed = time.time() - start
            record = {
                "step": step_name,
                "status": "FAIL",
                "elapsed_seconds": elapsed,
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
            }
            self.results.append(record)
            print(f"  {step_name}: FAIL ({elapsed:.2f}s) - {e}")
            return {"success": False, "error": str(e)}
    
    def _step_initialize(self) -> Dict[str, Any]:
        """Step 1: Initialize MCP connection."""
        result = self.client.initialize()
        return {
            "success": True,
            "server_info": result,
        }
    
    def _step_tool_discovery(self) -> Dict[str, Any]:
        """Step 2: Discover all tools."""
        tools = self.client.list_tools()
        categories = {}
        for tool in tools:
            cat = tool.category
            categories[cat] = categories.get(cat, 0) + 1
        
        return {
            "success": True,
            "total_tools": len(tools),
            "categories": categories,
            "tools": [{"name": t.name, "description": t.description, "category": t.category} for t in tools],
        }
    
    def _step_health_check(self) -> Dict[str, Any]:
        """Step 3: Health check."""
        result = self.client.call_tool("tv_health_check", {})
        return {
            "success": result.success,
            "result": result.result,
            "error": result.error,
            "latency_ms": result.execution_time_ms,
        }
    
    def _step_chart_state(self) -> Dict[str, Any]:
        """Step 4: Chart state read."""
        result = self.client.call_tool("chart_get_state", {})
        return {
            "success": result.success,
            "result": result.result,
            "error": result.error,
            "latency_ms": result.execution_time_ms,
        }
    
    def _step_symbol_info(self) -> Dict[str, Any]:
        """Step 5: Symbol info."""
        result = self.client.call_tool("symbol_info", {})
        return {
            "success": result.success,
            "result": result.result,
            "error": result.error,
            "latency_ms": result.execution_time_ms,
        }
    
    def _step_timeframe_read(self) -> Dict[str, Any]:
        """Step 6: Timeframe read (from chart state)."""
        # Get chart state which includes timeframe
        result = self.client.call_tool("chart_get_state", {})
        if result.success and isinstance(result.result, dict):
            timeframe = result.result.get("timeframe", "unknown")
            return {
                "success": True,
                "timeframe": timeframe,
                "latency_ms": result.execution_time_ms,
            }
        return {"success": False, "error": "Could not read timeframe from chart state"}
    
    def _step_pine_get_source(self) -> Dict[str, Any]:
        """Step 7: Pine source read."""
        result = self.client.call_tool("pine_get_source", {})
        return {
            "success": result.success,
            "result": result.result,
            "error": result.error,
            "latency_ms": result.execution_time_ms,
        }
    
    def _step_pine_analyze(self) -> Dict[str, Any]:
        """Step 8: Pine static analysis."""
        # First get the current source
        source_result = self.client.call_tool("pine_get_source", {})
        if not source_result.success:
            return {"success": False, "error": "Could not get Pine source for analysis"}
        
        # Analyze the source
        source = source_result.result
        if isinstance(source, dict):
            source = source.get("source", source.get("text", ""))
        
        result = self.client.call_tool("pine_analyze", {"source": source})
        return {
            "success": result.success,
            "result": result.result,
            "error": result.error,
            "latency_ms": result.execution_time_ms,
        }
    
    def _step_pine_compile(self) -> Dict[str, Any]:
        """Step 9: Pine compile."""
        # Get current source
        source_result = self.client.call_tool("pine_get_source", {})
        if not source_result.success:
            return {"success": False, "error": "Could not get Pine source for compilation"}
        
        source = source_result.result
        if isinstance(source, dict):
            source = source.get("source", source.get("text", ""))
        
        result = self.client.call_tool("pine_compile", {"source": source})
        return {
            "success": result.success,
            "result": result.result,
            "error": result.error,
            "latency_ms": result.execution_time_ms,
        }
    
    def _step_compiler_diagnostics(self) -> Dict[str, Any]:
        """Step 10: Compiler diagnostics."""
        result = self.client.call_tool("pine_get_errors", {})
        return {
            "success": result.success,
            "result": result.result,
            "error": result.error,
            "latency_ms": result.execution_time_ms,
        }
    
    def _step_pine_write(self) -> Dict[str, Any]:
        """Step 11: Controlled Pine source write."""
        # Use a simple test strategy
        test_source = """//@version=5
strategy("TRCP_Test_Strategy", overlay=true)
if ta.crossover(ta.sma(close, 10), ta.sma(close, 30))
    strategy.entry("Long", strategy.long)
if ta.crossunder(ta.sma(close, 10), ta.sma(close, 30))
    strategy.close("Long")
"""
        result = self.client.call_tool("pine_set_source", {"source": test_source})
        return {
            "success": result.success,
            "result": result.result,
            "error": result.error,
            "latency_ms": result.execution_time_ms,
        }
    
    def _step_compile_fixture(self) -> Dict[str, Any]:
        """Step 12: Compile modified fixture."""
        test_source = """//@version=5
strategy("TRCP_Test_Strategy_v2", overlay=true)
if ta.crossover(ta.sma(close, 10), ta.sma(close, 30))
    strategy.entry("Long", strategy.long)
if ta.crossunder(ta.sma(close, 10), ta.sma(close, 30))
    strategy.close("Long")
"""
        result = self.client.call_tool("pine_compile", {"source": test_source})
        return {
            "success": result.success,
            "result": result.result,
            "error": result.error,
            "latency_ms": result.execution_time_ms,
        }
    
    def _step_add_to_chart(self) -> Dict[str, Any]:
        """Step 13: Add fixture strategy to chart."""
        result = self.client.call_tool("pine_add_to_chart", {})
        return {
            "success": result.success,
            "result": result.result,
            "error": result.error,
            "latency_ms": result.execution_time_ms,
        }
    
    def _step_tester_availability(self) -> Dict[str, Any]:
        """Step 14: Strategy Tester availability."""
        result = self.client.call_tool("tv_ui_state", {})
        return {
            "success": result.success,
            "result": result.result,
            "error": result.error,
            "latency_ms": result.execution_time_ms,
        }
    
    def _step_tester_summary(self) -> Dict[str, Any]:
        """Step 15: Strategy Tester summary."""
        result = self.client.call_tool("strategy_tester_read_summary", {})
        return {
            "success": result.success,
            "result": result.result,
            "error": result.error,
            "latency_ms": result.execution_time_ms,
        }
    
    def _step_trade_extraction(self) -> Dict[str, Any]:
        """Step 16: Trade extraction."""
        result = self.client.call_tool("data_get_trades", {})
        return {
            "success": result.success,
            "result": result.result,
            "error": result.error,
            "latency_ms": result.execution_time_ms,
        }
    
    def _step_equity_extraction(self) -> Dict[str, Any]:
        """Step 17: Equity/drawdown extraction."""
        result = self.client.call_tool("data_get_equity", {})
        return {
            "success": result.success,
            "result": result.result,
            "error": result.error,
            "latency_ms": result.execution_time_ms,
        }
    
    def _step_symbol_change(self) -> Dict[str, Any]:
        """Step 18: Chart/symbol change."""
        # First get current state
        current = self.client.call_tool("chart_get_state", {})
        current_symbol = "BTCUSDT"
        if current.success and isinstance(current.result, dict):
            current_symbol = current.result.get("symbol", "BTCUSDT")
        
        # Change to ETHUSDT
        result = self.client.call_tool("chart_set_symbol", {"symbol": "ETHUSDT"})
        return {
            "success": result.success,
            "result": result.result,
            "error": result.error,
            "latency_ms": result.execution_time_ms,
            "previous_symbol": current_symbol,
        }
    
    def _step_timeframe_change(self) -> Dict[str, Any]:
        """Step 19: Timeframe change."""
        result = self.client.call_tool("chart_set_timeframe", {"timeframe": "4h"})
        return {
            "success": result.success,
            "result": result.result,
            "error": result.error,
            "latency_ms": result.execution_time_ms,
        }
    
    def _step_state_restoration(self) -> Dict[str, Any]:
        """Step 20: State restoration."""
        # Restore symbol
        symbol_result = self.client.call_tool("chart_set_symbol", {"symbol": "BTCUSDT"})
        # Restore timeframe
        timeframe_result = self.client.call_tool("chart_set_timeframe", {"timeframe": "1h"})
        
        success = symbol_result.success and timeframe_result.success
        return {
            "success": success,
            "symbol_restore": {"success": symbol_result.success, "error": symbol_result.error},
            "timeframe_restore": {"success": timeframe_result.success, "error": timeframe_result.error},
        }
    
    def _step_full_cycle(self) -> Dict[str, Any]:
        """Step 21: Complete Pine strategy cycle."""
        test_source = """//@version=5
strategy("TRCP_Full_Cycle_Test", overlay=true)
if ta.crossover(ta.sma(close, 10), ta.sma(close, 30))
    strategy.entry("Long", strategy.long)
if ta.crossunder(ta.sma(close, 10), ta.sma(close, 30))
    strategy.close("Long")
"""
        result = self.client.call_tool("pine_full_cycle_strategy", {
            "source": test_source,
            "add_to_chart": True,
            "allow_update_existing": False,
        })
        return {
            "success": result.success,
            "result": result.result,
            "error": result.error,
            "latency_ms": result.execution_time_ms,
        }
    
    def _generate_report(self) -> Dict[str, Any]:
        """Generate the final proof report."""
        total = len(self.results)
        passed = sum(1 for r in self.results if r["status"] == "PASS")
        failed = sum(1 for r in self.results if r["status"] == "FAIL")
        
        report = {
            "run_id": self.run_id,
            "timestamp": datetime.now().isoformat(),
            "total_steps": total,
            "passed": passed,
            "failed": failed,
            "results": self.results,
        }
        
        # Save report
        report_path = self.output_dir / "proof_ladder_report.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        # Save raw evidence
        evidence_path = self.output_dir / "raw_evidence.json"
        with open(evidence_path, 'w') as f:
            json.dump({
                "run_id": self.run_id,
                "timestamp": datetime.now().isoformat(),
                "steps": self.results,
            }, f, indent=2, default=str)
        
        print()
        print("=" * 70)
        print("PROOF LADDER COMPLETE")
        print("=" * 70)
        print(f"Total: {total}")
        print(f"PASS: {passed}")
        print(f"FAIL: {failed}")
        print(f"Report saved to: {report_path}")
        
        return report
    
    def _create_failure_result(self, error: str) -> Dict[str, Any]:
        """Create a failure result."""
        return {
            "run_id": self.run_id,
            "timestamp": datetime.now().isoformat(),
            "status": "FAIL",
            "error": error,
            "results": self.results,
        }


def main():
    ladder = ProofLadder()
    report = ladder.run()
    return report


if __name__ == "__main__":
    main()