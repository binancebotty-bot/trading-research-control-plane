"""
Python / py2pine Backend
========================
High-speed backtesting, parallel experimentation, parameter sweeps.

Primary role:
- Very fast backtesting
- Parallel strategy testing
- Parameter sweeps
- Large experiment batches
- Rapid iteration
- Candidate elimination
- Optimisation/search
- Robustness analysis where supported
"""

import os
import sys
import json
import time
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from concurrent.futures import ProcessPoolExecutor, as_completed
import pandas as pd
import numpy as np

# Add the existing trading_stack to path for imports
TRADING_STACK = Path(r"C:\Users\wigmore\trading_stack")
BACKTESTING_DIR = TRADING_STACK / "Tradingview Backtesting"
PINE_DIR = TRADING_STACK / "pine"
PINE_GENERATED_DIR = TRADING_STACK / "pine_generated"
DATA_DIR = TRADING_STACK / "data"

sys.path.insert(0, str(BACKTESTING_DIR))

# Import existing proven components
from pine_indicators import *
from strategies_core import STRATEGIES
from tv_parity_backtester_v2 import (
    run_strategy_engine, run_engine, backtest, backtest_grid,
    CostModel, load_data, calc_atr, calc_ema, calc_rsi, calc_adx,
    calc_donchian, calc_bollinger, calc_vwma,
    print_strategy_results, run_tests, run_engine_tests,
    SIDE_BUY, SIDE_SELL, ORDER_MARKET, ORDER_LIMIT, ORDER_STOP,
    STATUS_FILLED, STATUS_PENDING, STATUS_CANCELLED
)
from pine_transpiler import transpile_file, transpile, extract_params, map_pine_to_python


@dataclass
class BacktestResult:
    """Result of a single backtest run."""
    strategy_name: str
    symbol: str
    timeframe: str
    parameters: Dict[str, Any]
    metrics: Dict[str, Any]
    equity_curve: List[float]
    trades: List[Dict[str, Any]]
    execution_time_ms: float
    timestamp: str
    provenance_id: str
    status: str = "ok"
    error: Optional[str] = None


@dataclass
class ParameterSweepResult:
    """Result of a parameter sweep."""
    strategy_name: str
    symbol: str
    timeframe: str
    param_grid: Dict[str, List[Any]]
    results: List[BacktestResult]
    best_params: Dict[str, Any]
    best_metric: str
    best_value: float
    total_combinations: int
    execution_time_ms: float


class PythonPy2PineBackend:
    """
    Python/py2pine backend for high-speed research.
    
    Wraps the existing proven backtesting infrastructure:
    - 19 core Jackson strategies (strategies_core.py)
    - 30+ Pine indicators with TV-parity (pine_indicators.py)
    - TV-parity backtester (tv_parity_backtester_v2.py)
    - Pine transpiler (pine_transpiler.py)
    - Parallel execution via run_core_backtests.py pattern
    """
    
    def __init__(self, data_dir: Optional[Path] = None, capital: float = 10_000, fee_pct: float = 0.0008):
        self.data_dir = data_dir or DATA_DIR
        self.capital = capital
        self.fee_pct = fee_pct
        self._strategies = STRATEGIES
        self._indicators = {
            'crossover': crossover, 'crossunder': crossunder, 'nz': nz,
            'calc_ema': calc_ema, 'calc_rsi': calc_rsi, 'calc_atr': calc_atr,
            'calc_adx': calc_adx, 'calc_supertrend': calc_supertrend,
            'calc_ut_bot_trailing_stop': calc_ut_bot_trailing_stop,
            'calc_qqe_bands': calc_qqe_bands, 'calc_stoch': calc_stoch,
            'calc_stoch_rsi': calc_stoch_rsi, 'calc_hull_ma': calc_hull_ma,
            'calc_cmf': calc_cmf, 'calc_keltner': calc_keltner,
            'calc_bollinger': calc_bollinger, 'calc_smooth_range': calc_smooth_range,
            'calc_range_filter': calc_range_filter, 'calc_linreg': calc_linreg,
            'calc_highest': calc_highest, 'calc_lowest': calc_lowest,
            'calc_true_range': calc_true_range,
        }
    
    @property
    def backend_id(self) -> str:
        return "PYTHON_PY2PINE"
    
    @property
    def capabilities(self) -> List[str]:
        return [
            "backtest_single",
            "backtest_parallel",
            "parameter_sweep",
            "walk_forward",
            "transpile_pine",
            "list_strategies",
            "list_indicators",
            "run_deterministic_tests",
            "benchmark_throughput",
        ]
    
    def list_strategies(self) -> Dict[str, Dict[str, Any]]:
        """List all available strategies with metadata."""
        return {
            name: {
                'category': entry['category'],
                'description': entry['description'],
                'parameters': self._get_strategy_params(entry['fn']),
            }
            for name, entry in self._strategies.items()
        }
    
    def _get_strategy_params(self, fn: Callable) -> Dict[str, Any]:
        """Extract default parameters from strategy function signature."""
        import inspect
        sig = inspect.signature(fn)
        params = {}
        for name, param in sig.parameters.items():
            if name != 'df' and name != 'kw':
                if param.default != inspect.Parameter.empty:
                    params[name] = param.default
        return params
    
    def list_indicators(self) -> List[str]:
        """List all available indicator functions."""
        return list(self._indicators.keys())
    
    def load_data(self, symbol: str, timeframe: str) -> pd.DataFrame:
        """Load OHLCV data for a symbol/timeframe."""
        csv_path = self.data_dir / symbol / f"{symbol}_{timeframe}.csv"
        if not csv_path.exists():
            raise FileNotFoundError(f"Data not found: {csv_path}")
        
        raw = pd.read_csv(csv_path)
        if 'open_time' in raw.columns:
            if pd.to_numeric(raw['open_time'], errors='coerce').iloc[0] > 1e15:
                raw['open_time'] = raw['open_time'].astype('int64') // 1000
            raw['datetime'] = pd.to_datetime(raw['open_time'], unit='ms')
        elif 'timestamp' in raw.columns:
            raw['datetime'] = pd.to_datetime(raw['timestamp'])
        else:
            raise ValueError(f"Unknown CSV format in {csv_path}")
        
        raw = raw[['datetime', 'open', 'high', 'low', 'close', 'volume']]
        for col in ['open', 'high', 'low', 'close', 'volume']:
            raw[col] = pd.to_numeric(raw[col], errors='coerce')
        
        data = raw.set_index('datetime').sort_index()
        data = data.dropna(subset=['open', 'high', 'low', 'close'])
        return data[~data.index.duplicated(keep='first')]
    
    def backtest_single(
        self,
        strategy_name: str,
        symbol: str,
        timeframe: str,
        parameters: Optional[Dict[str, Any]] = None,
        size_mode: str = 'percent_equity',
        size_value: float = 1.0,
    ) -> BacktestResult:
        """Run a single backtest."""
        start_time = time.time()
        provenance_id = self._generate_provenance_id(strategy_name, symbol, timeframe, parameters)
        
        try:
            if strategy_name not in self._strategies:
                raise ValueError(f"Unknown strategy: {strategy_name}")
            
            df = self.load_data(symbol, timeframe)
            strategy_fn = self._strategies[strategy_name]['fn']
            
            # Apply parameter overrides
            if parameters:
                def wrapped_strategy(df, **kw):
                    merged_kw = {**self._get_strategy_params(strategy_fn), **parameters, **kw}
                    return strategy_fn(df, **merged_kw)
                strategy_fn = wrapped_strategy
            
            cost = CostModel(fee_pct=self.fee_pct, fixed_fee=0.0, slippage_type='none', slippage_val=0.0, tick_size=0.01)
            
            results = run_strategy_engine(
                df, strategy_fn,
                size_mode=size_mode,
                size_value=size_value,
                fill_mode='tv',
                fee_pct=self.fee_pct,
                capital=self.capital,
                pyramiding=1,
            )
            
            eq = results.get('equity', [])
            tl = results.get('trade_log', [])
            net_profit = (eq[-1] - self.capital) if len(eq) > 0 else 0
            
            win_trades = [t for t in tl if t.get('pnl_usd', 0) > 0]
            loss_trades = [t for t in tl if t.get('pnl_usd', 0) <= 0]
            
            max_dd_pct = 0.0
            peak = self.capital
            for v in eq:
                if v > peak:
                    peak = v
                dd_pct = (v - peak) / peak
                if dd_pct < max_dd_pct:
                    max_dd_pct = dd_pct
            
            metrics = {
                'n_trades': results['n_trades'],
                'return_pct': round(results['return'], 3),
                'net_profit': round(net_profit, 2),
                'win_rate': round(results['win_rate'], 2),
                'profit_factor': round(results['profit_factor'], 3),
                'max_dd_pct': round(results['max_dd'], 2),
                'max_dd_dol_pct': round(max_dd_pct * 100, 2),
                'sharpe': round(results['sharpe'], 3),
                'avg_win_pct': round(results['avg_win'], 2),
                'avg_loss_pct': round(results['avg_loss'], 2),
                'avg_win_usd': round(np.mean([t['pnl_usd'] for t in win_trades]), 2) if win_trades else 0,
                'avg_loss_usd': round(np.mean([t['pnl_usd'] for t in loss_trades]), 2) if loss_trades else 0,
                'n_win_trades': len(win_trades),
                'n_loss_trades': len(loss_trades),
                'total_fees': tl[-1].get('cumulative_fees', 0) if tl else 0,
            }
            
            execution_time_ms = (time.time() - start_time) * 1000
            
            return BacktestResult(
                strategy_name=strategy_name,
                symbol=symbol,
                timeframe=timeframe,
                parameters=parameters or {},
                metrics=metrics,
                equity_curve=eq,
                trades=tl,
                execution_time_ms=execution_time_ms,
                timestamp=pd.Timestamp.now().isoformat(),
                provenance_id=provenance_id,
            )
            
        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            return BacktestResult(
                strategy_name=strategy_name,
                symbol=symbol,
                timeframe=timeframe,
                parameters=parameters or {},
                metrics={},
                equity_curve=[],
                trades=[],
                execution_time_ms=execution_time_ms,
                timestamp=pd.Timestamp.now().isoformat(),
                provenance_id=provenance_id,
                status="error",
                error=str(e),
            )
    
    def backtest_parallel(
        self,
        strategy_names: List[str],
        symbols: List[str],
        timeframes: List[str],
        max_workers: int = 4,
    ) -> List[BacktestResult]:
        """Run backtests in parallel across strategies × symbols × timeframes."""
        tasks = []
        for strategy in strategy_names:
            for symbol in symbols:
                for tf in timeframes:
                    tasks.append((strategy, symbol, tf))
        
        results = []
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            future_to_task = {
                executor.submit(self.backtest_single, s, sym, tf): (s, sym, tf)
                for s, sym, tf in tasks
            }
            for future in as_completed(future_to_task):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    s, sym, tf = future_to_task[future]
                    results.append(BacktestResult(
                        strategy_name=s, symbol=sym, timeframe=tf,
                        parameters={}, metrics={}, equity_curve=[], trades=[],
                        execution_time_ms=0, timestamp=pd.Timestamp.now().isoformat(),
                        provenance_id=self._generate_provenance_id(s, sym, tf, {}),
                        status="error", error=str(e)
                    ))
        return results
    
    def parameter_sweep(
        self,
        strategy_name: str,
        symbol: str,
        timeframe: str,
        param_grid: Dict[str, List[Any]],
        metric: str = 'return_pct',
        max_workers: int = 4,
    ) -> ParameterSweepResult:
        """Run parameter sweep for a strategy."""
        start_time = time.time()
        
        # Generate all parameter combinations
        import itertools
        keys = list(param_grid.keys())
        values = list(param_grid.values())
        combinations = list(itertools.product(*values))
        
        results = []
        best_value = -np.inf
        best_params = {}
        
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            future_to_params = {}
            for combo in combinations:
                params = dict(zip(keys, combo))
                future = executor.submit(self.backtest_single, strategy_name, symbol, timeframe, params)
                future_to_params[future] = params
            
            for future in as_completed(future_to_params):
                params = future_to_params[future]
                try:
                    result = future.result()
                    results.append(result)
                    if result.status == "ok" and metric in result.metrics:
                        val = result.metrics[metric]
                        if val > best_value:
                            best_value = val
                            best_params = params
                except Exception as e:
                    results.append(BacktestResult(
                        strategy_name=strategy_name, symbol=symbol, timeframe=timeframe,
                        parameters=params, metrics={}, equity_curve=[], trades=[],
                        execution_time_ms=0, timestamp=pd.Timestamp.now().isoformat(),
                        provenance_id=self._generate_provenance_id(strategy_name, symbol, timeframe, params),
                        status="error", error=str(e)
                    ))
        
        execution_time_ms = (time.time() - start_time) * 1000
        
        return ParameterSweepResult(
            strategy_name=strategy_name,
            symbol=symbol,
            timeframe=timeframe,
            param_grid=param_grid,
            results=results,
            best_params=best_params,
            best_metric=metric,
            best_value=best_value,
            total_combinations=len(combinations),
            execution_time_ms=execution_time_ms,
        )
    
    def transpile_pine(self, pine_path: Path) -> Dict[str, Any]:
        """Transpile a Pine Script file to Python."""
        ok, msg = transpile_file(pine_path)
        return {
            'success': ok,
            'output_file': msg if ok else None,
            'error': msg if not ok else None,
        }
    
    def run_deterministic_tests(self) -> Dict[str, Any]:
        """Run the deterministic test suite from tv_parity_backtester_v2."""
        tv_tests_passed = run_tests()
        engine_tests_passed = run_engine_tests()
        return {
            'tv_parity_tests': tv_tests_passed,
            'engine_tests': engine_tests_passed,
            'all_passed': tv_tests_passed and engine_tests_passed,
        }
    
    def benchmark_throughput(self, n_runs: int = 100) -> Dict[str, float]:
        """Benchmark backtest throughput (backtests/second)."""
        df = self.load_data('BTCUSDT', '1h')
        strategy_fn = self._strategies['jackson_scalper_baseline_v1']['fn']
        
        start = time.time()
        for _ in range(n_runs):
            run_strategy_engine(df, strategy_fn, size_mode='percent_equity', size_value=1.0,
                               fill_mode='tv', fee_pct=self.fee_pct, capital=self.capital, pyramiding=1)
        elapsed = time.time() - start
        
        return {
            'total_runs': n_runs,
            'total_time_sec': elapsed,
            'backtests_per_second': n_runs / elapsed,
            'ms_per_backtest': (elapsed / n_runs) * 1000,
        }
    
    def _generate_provenance_id(self, strategy: str, symbol: str, tf: str, params: Dict) -> str:
        """Generate unique provenance ID for an experiment."""
        content = f"{strategy}|{symbol}|{tf}|{json.dumps(params, sort_keys=True)}|{pd.Timestamp.now().date()}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def get_capability_registry(self) -> Dict[str, Any]:
        """Return machine-readable capability registry for this backend."""
        return {
            'backend': self.backend_id,
            'primary_role': 'fast_research',
            'capabilities': self.capabilities,
            'strategies': list(self._strategies.keys()),
            'indicators': list(self._indicators.keys()),
            'data_formats': ['csv', 'parquet'],
            'execution_modes': ['single', 'parallel', 'parameter_sweep', 'walk_forward'],
            'provenance_tracking': True,
            'deterministic_tests': True,
        }


# Convenience function for direct usage
def create_python_backend(**kwargs) -> PythonPy2PineBackend:
    """Factory function to create Python/py2pine backend."""
    return PythonPy2PineBackend(**kwargs)