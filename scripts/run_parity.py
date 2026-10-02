"""
Run Parity Tests
================
Compare Python/py2pine backtest results against TradingView Strategy Tester.
"""

import sys
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

sys.path.insert(0, str(Path(__file__).parent.parent))

from control_plane.backends.python_py2pine import PythonPy2PineBackend
from control_plane.backends.custom_tradingview_mcp import CustomTradingViewMCPBackend
from control_plane.pipeline import ParityResult, ParityClassification


# Parity tolerances
PARITY_TOLERANCES = {
    'return_pct': 0.5,
    'max_dd_pct': 0.5,
    'win_rate': 1.0,
    'profit_factor': 0.1,
    'n_trades': 0.15,
    'avg_win_pct': 3.0,
    'avg_loss_pct': 3.0,
}


class ParityTestRunner:
    """Run parity tests between Python and TradingView."""
    
    def __init__(self):
        self.python_backend = PythonPy2PineBackend()
        self.tv_mcp_backend = CustomTradingViewMCPBackend()
        self.results: List[Dict[str, Any]] = []
    
    def run_parity_tests(self) -> Dict[str, Any]:
        """Run all parity tests."""
        print("=" * 70)
        print("PYTHON ↔ TRADINGVIEW PARITY TESTS")
        print("=" * 70)
        print(f"Started: {datetime.now().isoformat()}")
        print()
        
        # Test 1: Python backtest (baseline)
        print("[Test 1] Python backtest baseline...")
        py_result = self.python_backend.backtest_single(
            "jackson_scalper_baseline_v1", "BTCUSDT", "1h"
        )
        print(f"  Strategy: {py_result.strategy_name}")
        print(f"  Status: {py_result.status}")
        print(f"  Return: {py_result.metrics.get('return_pct', 'N/A')}%")
        print(f"  Trades: {py_result.metrics.get('n_trades', 'N/A')}")
        print(f"  Profit Factor: {py_result.metrics.get('profit_factor', 'N/A')}")
        print()
        
        # Test 2: TV Strategy Tester (if available)
        print("[Test 2] TradingView Strategy Tester...")
        try:
            tv_result = self.tv_mcp_backend.read_strategy_tester()
            if tv_result.raw_data and 'error' not in tv_result.raw_data:
                print(f"  Net Profit: {tv_result.net_profit}")
                print(f"  Total Trades: {tv_result.total_trades}")
                print(f"  % Profitable: {tv_result.percent_profitable}")
                print(f"  Profit Factor: {tv_result.profit_factor}")
                print(f"  Max Drawdown: {tv_result.max_drawdown}")
                tv_data = tv_result.raw_data
            else:
                print("  TV Strategy Tester not available (no active strategy)")
                tv_data = None
        except Exception as e:
            print(f"  TV Strategy Tester error: {e}")
            tv_data = None
        print()
        
        # Test 3: Parity comparison
        print("[Test 3] Parity comparison...")
        if py_result.status == "ok" and tv_data:
            parity = self._compare_parity(py_result, tv_data)
            print(f"  Parity: {'PASS' if parity['passed'] else 'FAIL'}")
            print(f"  Discrepancies: {len(parity['discrepancies'])}")
            for d in parity['discrepancies']:
                print(f"    - {d['metric']}: Python={d['python']}, TV={d['tradingview']}, diff={d['difference']:.4f}")
        else:
            parity = {
                'passed': False,
                'discrepancies': [{'error': 'Missing Python or TV result'}],
                'classifications': ['UNKNOWN'],
            }
            print("  Cannot compare - missing results")
        print()
        
        # Generate report
        report = {
            'generated': datetime.now().isoformat(),
            'python_result': {
                'strategy': py_result.strategy_name,
                'symbol': py_result.symbol,
                'timeframe': py_result.timeframe,
                'status': py_result.status,
                'metrics': py_result.metrics,
            },
            'tv_result': tv_data,
            'parity': parity,
            'tolerances': PARITY_TOLERANCES,
        }
        
        # Save report
        output_path = Path("proofs/parity_results.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"Results saved to: {output_path}")
        print()
        print("=" * 70)
        print("PARITY TESTS COMPLETE")
        print("=" * 70)
        
        return report
    
    def _compare_parity(self, py_result, tv_data) -> Dict[str, Any]:
        """Compare Python and TV results."""
        discrepancies = []
        classifications = []
        
        py_metrics = py_result.metrics
        
        # Map TV metrics to Python metric names
        tv_metrics = {
            'return_pct': tv_data.get('netProfit', 0) / 10000 * 100 if tv_data.get('netProfit') else None,
            'max_dd_pct': tv_data.get('maxDrawdown', 0),
            'win_rate': tv_data.get('percentProfitable', 0),
            'profit_factor': tv_data.get('profitFactor', 0),
            'n_trades': tv_data.get('totalTrades', 0),
            'avg_win_pct': tv_data.get('avgWin', 0),
            'avg_loss_pct': tv_data.get('avgLoss', 0),
        }
        
        for metric, tolerance in PARITY_TOLERANCES.items():
            py_val = py_metrics.get(metric)
            tv_val = tv_metrics.get(metric)
            
            if py_val is not None and tv_val is not None:
                if metric == 'n_trades':
                    # Relative tolerance for trade count
                    if py_val > 0:
                        diff = abs(py_val - tv_val) / py_val
                        if diff > tolerance:
                            discrepancies.append({
                                'metric': metric,
                                'python': py_val,
                                'tradingview': tv_val,
                                'difference': diff,
                                'tolerance': tolerance,
                            })
                            classifications.append('EXECUTION_SEMANTICS')
                else:
                    # Absolute tolerance
                    diff = abs(py_val - tv_val)
                    if diff > tolerance:
                        discrepancies.append({
                            'metric': metric,
                            'python': py_val,
                            'tradingview': tv_val,
                            'difference': diff,
                            'tolerance': tolerance,
                        })
                        classifications.append('EXECUTION_SEMANTICS')
        
        return {
            'passed': len(discrepancies) == 0,
            'discrepancies': discrepancies,
            'classifications': list(set(classifications)),
        }


def main():
    runner = ParityTestRunner()
    report = runner.run_parity_tests()
    return report


if __name__ == "__main__":
    main()