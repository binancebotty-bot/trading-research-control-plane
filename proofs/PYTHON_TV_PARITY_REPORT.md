# Python ↔ TradingView Parity Report

**Generated**: 2026-10-02  
**Repository**: trading-research-control-plane  
**Version**: 0.1.0

---

## Overview

This report documents the Python ↔ TradingView parity testing framework and results.

## Parity Philosophy

- **Python is the fast research engine** — rapid iteration, parameter sweeps, candidate elimination
- **TradingView is the validation engine** — final independent validation/source of truth
- **Parity is NOT assumed** — it must be proven with controlled inputs
- **Discrepancies are classified** — never claim parity when unexplained material differences remain

---

## Deterministic Strategy Fixtures

### Fixture 1: SMA Crossover
- **Pine**: `ta.crossover(ta.sma(close, 10), ta.sma(close, 30))`
- **Python**: `sma_crossover(df, fast=10, slow=30)`
- **Parameters**: `{'fast': 10, 'slow': 30}`

### Fixture 2: RSI Mean Reversion
- **Pine**: `ta.rsi(close, 14)` with 30/70 thresholds
- **Python**: `rsi_mean_reversion(df, rsi_length=14, overbought=70, oversold=30)`
- **Parameters**: `{'rsi_length': 14, 'overbought': 70, 'oversold': 30}`

### Fixture 3: ATR Breakout
- **Pine**: `ta.atr(14)` with 2.0 multiplier
- **Python**: `atr_breakout(df, atr_length=14, atr_mult=2.0)`
- **Parameters**: `{'atr_length': 14, 'atr_mult': 2.0}`

### Fixture 4: Bollinger Band Mean Reversion
- **Pine**: `ta.sma(close, 20)` ± 2.0 * `ta.stdev(close, 20)`
- **Python**: `bollinger_mean_reversion(df, length=20, mult=2.0)`
- **Parameters**: `{'length': 20, 'mult': 2.0}`

### Fixture 5: MACD Crossover
- **Pine**: `ta.macd(close, 12, 26, 9)`
- **Python**: `macd_crossover(df, fast=12, slow=26, signal=9)`
- **Parameters**: `{'fast': 12, 'slow': 26, 'signal': 9}`

---

## Comparison Metrics & Tolerances

| Metric | Tolerance | Type | Classification if Exceeded |
|--------|-----------|------|---------------------------|
| Return % | 0.5% | Absolute | EXECUTION_SEMANTICS |
| Max Drawdown % | 0.5% | Absolute | EXECUTION_SEMANTICS |
| Win Rate % | 1.0% | Absolute | EXECUTION_SEMANTICS |
| Profit Factor | 0.1 | Absolute | EXECUTION_SEMANTICS |
| Trade Count | 15% | Relative | EXECUTION_SEMANTICS |
| Avg Win % | 3.0% | Absolute | ROUNDING |
| Avg Loss % | 3.0% | Absolute | ROUNDING |
| Net Profit | 1% | Relative | FEE_MODEL |

---

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

---

## Test Results

### Python Backtest Results

| Strategy | Symbol | Timeframe | Return % | Trades | Profit Factor | Max DD % |
|----------|--------|-----------|----------|--------|---------------|----------|
| jackson_scalper_baseline_v1 | BTCUSDT | 1h | (see proof_results.json) | - | - | - |

### TradingView Strategy Tester Results

| Strategy | Symbol | Timeframe | Net Profit | Total Trades | % Profitable | Profit Factor | Max DD |
|----------|--------|-----------|------------|--------------|--------------|---------------|--------|
| N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |

**Note**: TV Strategy Tester results require live browser session with active strategy on chart.

### Parity Comparison

| Metric | Python | TradingView | Difference | Tolerance | Status |
|--------|--------|-------------|------------|-----------|--------|
| N/A | N/A | N/A | N/A | N/A | NOT_TESTABLE |

**Note**: Parity comparison requires live TV session for both Python backtest and TV Strategy Tester execution.

---

## Known Sources of Discrepancy

1. **Data differences** — Python uses local CSV, TV uses live data feed
2. **Execution model** — Python simulates O→H→L→C, TV uses actual broker fills
3. **Fee model** — Python uses configurable CostModel, TV uses broker-specific fees
4. **Slippage** — Python supports none/fixed/percent, TV uses market slippage
5. **Position sizing** — Python supports multiple modes, TV uses strategy settings
6. **Bar timing** — Python executes on bar close, TV may use intrabar execution
7. **Pine semantics** — `ta.*` functions may have subtle differences from Python equivalents

---

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

---

## Conclusion

The parity testing framework is fully implemented with:
- 5 deterministic strategy fixtures (Pine + Python equivalents)
- 8 comparison metrics with explicit tolerances
- 9 discrepancy classifications
- Automated comparison logic
- Evidence generation and persistence

**Current Status**: NOT_TESTABLE_SAFELY (requires live TV session)

**Next Steps**:
1. Run parity tests with live TV session
2. Document actual discrepancies
3. Refine tolerances based on empirical results
4. Build parity regression test suite