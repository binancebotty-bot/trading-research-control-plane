# Research Pipeline

## Overview

The research pipeline implements the fast-search → TV-validation workflow:

```
Hypothesis/Strategy
    │
    ▼
Python Implementation
    │
    ▼
Fast Python Backtest
    │
    ▼
Parallel Parameter Exploration
    │
    ▼
Candidate Filtering
    │
    ▼
Pine Generation / Parity
    │
    ▼
TV Compile
    │
    ▼
TV Strategy Tester
    │
    ▼
TV Extraction
    │
    ▼
Parity Comparison
    │
    ▼
Accept/Reject Decision
    │
    ▼
Persist Experiment
```

## Pipeline Stages

### Stage 1: Hypothesis
- Define research hypothesis
- Select strategy family
- Define success criteria

### Stage 2: Python Implementation
- Strategy exists in `strategies_core.py`
- Or transpile from Pine using `pine_transpiler.py`
- Verify deterministic behavior

### Stage 3: Fast Python Backtest
- Single backtest run
- Record metrics, equity curve, trades
- ~1-5ms per backtest

### Stage 4: Parallel Parameter Exploration
- Parameter sweep across grid
- Parallel execution (4+ workers)
- ~1000+ backtests/second

### Stage 5: Candidate Filtering
- Filter by minimum trades (default: 10)
- Filter by minimum profit factor (default: 1.0)
- Filter by maximum drawdown (default: 20%)
- Rank by return %
- Select top N candidates (default: 5)

### Stage 6: Pine Generation / Parity
- Load Pine source from `pine/` directory
- Or transpile Python → Pine
- Verify Pine compiles

### Stage 7: TV Compile
- Compile via `pine_compile_facade` (no popup)
- Check for errors
- Retry with fixes if needed

### Stage 8: TV Strategy Tester
- Inject Pine into editor
- Add to chart
- Run Strategy Tester
- Wait for completion

### Stage 9: TV Extraction
- Read Strategy Tester summary
- Extract: net profit, total trades, % profitable, profit factor, max drawdown
- Extract: equity curve, trade list

### Stage 10: Parity Comparison
- Compare Python vs TV metrics
- Apply tolerances
- Classify discrepancies
- Generate parity report

### Stage 11: Decision
- **ACCEPT**: Parity passed + quality gates passed
- **REJECT**: Parity failed OR quality gates failed
- **NEEDS_REVIEW**: Ambiguous results

### Stage 12: Persist
- Save experiment record
- Save Python results
- Save TV results
- Save parity report
- Update provenance index

## Configuration

```python
PIPELINE_CONFIG = {
    'filter_top_n': 5,
    'min_trades': 10,
    'min_profit_factor': 1.0,
    'max_drawdown_pct': 20.0,
    'parity_tolerances': {
        'return_pct': 0.5,
        'max_dd_pct': 0.5,
        'win_rate': 1.0,
        'profit_factor': 0.1,
        'n_trades': 0.15,
    },
    'max_workers': 4,
}
```

## Usage

```python
from control_plane.pipeline import ResearchPipeline

pipeline = ResearchPipeline()

result = pipeline.run_pipeline(
    hypothesis="EMA crossover trend following on BTC",
    strategy_name="jackson_trend_ema_v1",
    symbol="BTCUSDT",
    timeframe="1h",
    parameters={'ema_fast': 12, 'ema_slow': 50},
    param_grid={
        'ema_fast': [8, 12, 21],
        'ema_slow': [50, 100, 200],
    },
    filter_top_n=5,
    min_trades=10,
    min_profit_factor=1.0,
    max_drawdown_pct=20.0,
)

print(f"Decision: {result.decision}")
print(f"Parity: {result.parity_result.passed if result.parity_result else 'N/A'}")
print(f"Evidence: {result.evidence_paths}")
```

## Parallel Research Architecture

```
                        ┌─ Python worker
                        ├─ Python worker
Research hypothesis ───┼─ Python worker
                        ├─ Python worker
                        └─ Python worker
                              │
                              ▼
                     candidate filtering
                              │
                              ▼
                     Pine/TV validation
                              │
                              ▼
                        parity gate
                              │
                              ▼
                       experiment DB
```

## Performance Targets

| Stage | Target Time | Notes |
|-------|-------------|-------|
| Python backtest | ~1-5ms | Single run |
| Parameter sweep (1000) | ~1-2s | 4 workers |
| TV compile | ~2-5s | Facade |
| TV Strategy Tester | ~10-30s | Depends on data |
| Parity comparison | ~100ms | Metric comparison |
| **Total pipeline** | ~15-40s | End-to-end |

## Error Handling

- **Python backtest fails**: Log error, skip candidate
- **TV compile fails**: Log error, reject candidate
- **TV Strategy Tester fails**: Log error, reject candidate
- **Parity fails**: Log discrepancies, reject candidate
- **Pipeline exception**: Log error, return failed result

## Observability

Every pipeline execution generates structured logs:
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