# Python / py2pine Backtesting

## Overview

The Python/py2pine backtesting system provides high-speed strategy research, parallel experimentation, and parameter sweeps. It wraps the existing proven backtesting infrastructure from `trading_stack/Tradingview Backtesting`.

## Location

- **Repository**: `C:\Users\wigmore\Tradingview Backtesting`
- **Key Files**:
  - `strategies_core.py` — 19 Jackson strategies
  - `pine_indicators.py` — 30+ Pine indicators with TV-parity
  - `tv_parity_backtester_v2.py` — TV-parity backtester engine
  - `pine_transpiler.py` — Pine→Python transpiler
  - `run_core_backtests.py` — Parallel runner

## Architecture

```
Strategy Function (strategies_core.py)
    │
    ▼
run_strategy_engine (tv_parity_backtester_v2.py)
    │
    ├── CostModel (fees, slippage)
    ├── FillMode (TV execution model: O→H→L→C path)
    ├── Position Sizing (percent_equity, fixed, etc.)
    │
    ▼
Trade Log → Equity Curve → Metrics
```

## Strategies (19 Total)

| # | Strategy | Category | Description |
|---|----------|----------|-------------|
| 1 | jackson_scalper_baseline_v1 | Scalper | Baseline scalper with EMA trend filter |
| 2 | jackson_scalper_atr_v2 | Scalper | ATR-based scalper with dynamic stops |
| 3 | jackson_scalper_rsi_v3 | Scalper | RSI mean-reversion scalper |
| 4 | jackson_trend_ema_v1 | Trend | EMA crossover trend follower |
| 5 | jackson_trend_macd_v2 | Trend | MACD histogram trend follower |
| 6 | jackson_trend_adx_v3 | Trend | ADX-filtered trend follower |
| 7 | jackson_breakout_donchian_v1 | Breakout | Donchian channel breakout |
| 8 | jackson_breakout_bollinger_v2 | Breakout | Bollinger Band breakout |
| 9 | jackson_breakout_keltner_v3 | Breakout | Keltner channel breakout |
| 10 | jackson_reversal_rsi_v1 | Reversal | RSI oversold/overbought reversal |
| 11 | jackson_reversal_stoch_v2 | Reversal | Stochastic reversal |
| 12 | jackson_reversal_divergence_v3 | Reversal | Price/indicator divergence reversal |
| 13 | jackson_range_meanrev_v1 | Range | Mean reversion in ranging markets |
| 14 | jackson_range_grid_v2 | Range | Grid trading in ranges |
| 15 | jackson_momentum_roc_v1 | Momentum | Rate of change momentum |
| 16 | jackson_momentum_cci_v2 | Momentum | CCI momentum |
| 17 | jackson_volatility_atr_v1 | Volatility | ATR-based volatility strategy |
| 18 | jackson_volatility_vix_v2 | Volatility | VIX-based volatility strategy |
| 19 | jackson_hybrid_multi_v1 | Hybrid | Multi-indicator hybrid strategy |

## Indicators (30+)

All indicators faithfully reimplement Pine Script semantics including RMA/Wilder smoothing:

- **Trend**: EMA, SMA, HMA, VWMA, Supertrend, Parabolic SAR
- **Momentum**: RSI, Stochastic, Stoch RSI, CCI, ROC, Williams %R
- **Volatility**: ATR, Bollinger Bands, Keltner Channels, Donchian Channels
- **Volume**: OBV, CMF, VWAP, Volume Profile
- **Oscillators**: MACD, ADX, QQE, Hull MA
- **Utility**: Crossover, Crossunder, Highest, Lowest, True Range, Linreg

## Execution Model (TV-Parity)

The backtester replicates TradingView's execution model:

1. **Signal Generation**: Strategy logic runs on bar close
2. **Order Placement**: Orders placed at next bar open
3. **Fill Simulation**: O→H→L→C path determines fill price
   - Stop orders: filled if high/low crosses stop level
   - Limit orders: filled if high/low crosses limit level
   - Market orders: filled at open
4. **Position Sizing**: Percent of equity, fixed size, or Kelly criterion
5. **Cost Model**: Configurable fees, slippage, spread

## Cost Model

```python
CostModel(
    fee_pct=0.0008,        # 0.08% per trade
    fixed_fee=0.0,          # Fixed fee per trade
    slippage_type='none',   # none, fixed, percent
    slippage_val=0.0,       # Slippage value
    tick_size=0.01,         # Minimum price increment
)
```

## Parallel Execution

```python
# Run multiple strategies in parallel
results = backend.backtest_parallel(
    strategy_names=['jackson_scalper_baseline_v1', 'jackson_trend_ema_v1'],
    symbols=['BTCUSDT', 'ETHUSDT'],
    timeframes=['1h', '4h'],
    max_workers=4,
)
```

## Parameter Sweeps

```python
# Sweep parameters
sweep = backend.parameter_sweep(
    strategy_name='jackson_scalper_baseline_v1',
    symbol='BTCUSDT',
    timeframe='1h',
    param_grid={
        'ema_fast': [8, 12, 21],
        'ema_slow': [50, 100, 200],
        'atr_period': [14, 21, 28],
    },
    metric='return_pct',
    max_workers=4,
)
```

## Deterministic Test Suite

16 deterministic tests verify:
- Data ingestion
- Strategy execution
- Entry/exit logic
- Position sizing
- Fee calculation
- Equity curve
- Drawdown calculation
- Trade ledger
- Metrics calculation
- Parameter changes
- Repeatability
- Parallel execution
- Batch testing
- Result persistence
- TV-parity execution model

## Performance

- **Single backtest**: ~1-5ms
- **Parallel (4 workers)**: ~1000+ backtests/second
- **Parameter sweep (1000 combos)**: ~1-2 seconds

## Data Format

CSV files with columns: `open_time, open, high, low, close, volume`

```
data/
├── BTCUSDT/
│   ├── BTCUSDT_1h.csv
│   ├── BTCUSDT_4h.csv
│   └── BTCUSDT_1d.csv
├── ETHUSDT/
│   ├── ETHUSDT_1h.csv
│   ├── ETHUSDT_4h.csv
│   └── ETHUSDT_1d.csv
└── ...
```

## Pine Transpiler

The transpiler converts Pine Script to Python:

```python
from pine_transpiler import transpile_file

ok, msg = transpile_file(Path("strategy.pine"))
# Returns (success, output_path_or_error)
```

## Integration

```python
from control_plane.backends.python_py2pine import PythonPy2PineBackend

backend = PythonPy2PineBackend()

# Single backtest
result = backend.backtest_single(
    strategy_name='jackson_scalper_baseline_v1',
    symbol='BTCUSDT',
    timeframe='1h',
    parameters={'ema_fast': 12, 'ema_slow': 50},
)

# Parallel backtest
results = backend.backtest_parallel(
    strategy_names=['jackson_scalper_baseline_v1'],
    symbols=['BTCUSDT', 'ETHUSDT'],
    timeframes=['1h', '4h'],
)

# Parameter sweep
sweep = backend.parameter_sweep(
    strategy_name='jackson_scalper_baseline_v1',
    symbol='BTCUSDT',
    timeframe='1h',
    param_grid={'ema_fast': [8, 12, 21], 'ema_slow': [50, 100, 200]},
)

# Deterministic tests
tests = backend.run_deterministic_tests()

# Benchmark
benchmark = backend.benchmark_throughput(n_runs=100)
```