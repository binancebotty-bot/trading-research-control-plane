# Python ↔ TradingView Parity

## Overview

Parity testing compares Python/py2pine backtest results against TradingView Strategy Tester results to validate equivalence.

## Parity Philosophy

- **Python is the fast research engine** — rapid iteration, parameter sweeps, candidate elimination
- **TradingView is the validation engine** — final independent validation/source of truth
- **Parity is NOT assumed** — it must be proven with controlled inputs
- **Discrepancies are classified** — never claim parity when unexplained material differences remain

## Deterministic Strategy Fixtures

For parity testing, we use deterministic strategies with controlled inputs:

### Fixture 1: SMA Crossover
```pine
//@version=5
strategy("SMA Crossover Parity Test", overlay=true)
fast = input.int(10, "Fast SMA")
slow = input.int(30, "Slow SMA")
if ta.crossover(ta.sma(close, fast), ta.sma(close, slow))
    strategy.entry("Long", strategy.long)
if ta.crossunder(ta.sma(close, fast), ta.sma(close, slow))
    strategy.close("Long")
```

### Fixture 2: RSI Mean Reversion
```pine
//@version=5
strategy("RSI Mean Reversion Parity Test", overlay=true)
rsiLength = input.int(14, "RSI Length")
overbought = input.int(70, "Overbought")
oversold = input.int(30, "Oversold")
rsi = ta.rsi(close, rsiLength)
if rsi < oversold
    strategy.entry("Long", strategy.long)
if rsi > overbought
    strategy.close("Long")
```

### Fixture 3: ATR Breakout
```pine
//@version=5
strategy("ATR Breakout Parity Test", overlay=true)
atrLength = input.int(14, "ATR Length")
atrMult = input.float(2.0, "ATR Multiplier")
atr = ta.atr(atrLength)
if close > close[1] + atr * atrMult
    strategy.entry("Long", strategy.long)
if close < close[1] - atr * atrMult
    strategy.close("Long")
```

## Comparison Metrics

| Metric | Tolerance | Classification if Exceeded |
|--------|-----------|---------------------------|
| Return % | 0.5% | EXECUTION_SEMANTICS |
| Max Drawdown % | 0.5% | EXECUTION_SEMANTICS |
| Win Rate % | 1.0% | EXECUTION_SEMANTICS |
| Profit Factor | 0.1 | EXECUTION_SEMANTICS |
| Trade Count | 15% relative | EXECUTION_SEMANTICS |
| Avg Win % | 3.0% | ROUNDING |
| Avg Loss % | 3.0% | ROUNDING |
| Net Profit | 1% relative | FEE_MODEL |
| Equity Curve | Visual | DATA_DIFFERENCE |

## Discrepancy Classifications

| Classification | Description | Common Causes |
|----------------|-------------|---------------|
| `DATA_DIFFERENCE` | Different data used | Different date ranges, data sources, or bar counts |
| `EXECUTION_SEMANTICS` | Different execution model | Fill price assumptions, order types, slippage |
| `ROUNDING` | Minor numerical differences | Floating point precision, tick size rounding |
| `FEE_MODEL` | Different fee structures | Commission rates, spread, funding |
| `SLIPPAGE_MODEL` | Different slippage assumptions | Fixed vs variable slippage, market impact |
| `POSITION_SIZING` | Different position sizing | Percent equity vs fixed size, pyramiding |
| `BAR_TIMING` | Different bar timing | Signal bar vs execution bar, intrabar vs close |
| `PINE_SEMANTICS` | Pine-specific behavior | `ta.*` function differences, `request.security` |
| `UNKNOWN` | Unclassified discrepancy | Requires investigation |

## Parity Test Procedure

1. **Select deterministic fixture** — controlled inputs, no randomness
2. **Run Python backtest** — record all metrics
3. **Deploy to TradingView** — compile, add to chart, run Strategy Tester
4. **Extract TV results** — read summary, trades, equity
5. **Compare metrics** — apply tolerances, classify discrepancies
6. **Generate parity report** — document results, classifications, evidence

## Parity Report Format

```markdown
# Parity Report: {strategy_name}

## Configuration
- Symbol: {symbol}
- Timeframe: {timeframe}
- Date Range: {start} to {end}
- Parameters: {parameters}

## Results

| Metric | Python | TradingView | Difference | Tolerance | Status |
|--------|--------|-------------|------------|-----------|--------|
| Return % | {py} | {tv} | {diff} | {tol} | {status} |
| ... | ... | ... | ... | ... | ... |

## Discrepancies
1. {metric}: {classification} — {details}

## Verdict
- **Parity**: PASS/FAIL
- **Material Discrepancies**: {count}
- **Summary**: {summary}
```

## Tolerance Configuration

```python
PARITY_TOLERANCES = {
    'return_pct': 0.5,        # 0.5% absolute difference
    'max_dd_pct': 0.5,        # 0.5% absolute difference
    'win_rate': 1.0,          # 1% absolute difference
    'profit_factor': 0.1,     # 0.1 absolute difference
    'n_trades': 0.15,         # 15% relative difference
    'avg_win_pct': 3.0,       # 3% absolute difference
    'avg_loss_pct': 3.0,      # 3% absolute difference
}
```

## Known Sources of Discrepancy

1. **Data differences** — Python uses local CSV, TV uses live data feed
2. **Execution model** — Python simulates O→H→L→C, TV uses actual broker fills
3. **Fee model** — Python uses configurable CostModel, TV uses broker-specific fees
4. **Slippage** — Python supports none/fixed/percent, TV uses market slippage
5. **Position sizing** — Python supports multiple modes, TV uses strategy settings
6. **Bar timing** — Python executes on bar close, TV may use intrabar execution
7. **Pine semantics** — `ta.*` functions may have subtle differences from Python equivalents

## Acceptance Criteria

Parity is considered **PASSED** when:
- All metrics within tolerance
- No material discrepancies (beyond 2x tolerance)
- Discrepancies are classified and explained
- Evidence is documented and reproducible

Parity is considered **FAILED** when:
- Any metric exceeds 2x tolerance
- Unexplained material discrepancies remain
- Evidence is missing or incomplete