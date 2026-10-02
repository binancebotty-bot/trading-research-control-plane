# Trading Research Control Plane

A unified control plane integrating three research backends for systematic trading strategy research:

1. **Python / py2pine** — High-speed backtesting, parallel experimentation, parameter sweeps
2. **Custom TradingView MCP** — Pine Editor, compilation, chart control, Strategy Tester
3. **Official TradingView MCP/API** — Market data, fundamentals, news, watchlists, alerts

## Architecture

```
Hypothesis/Strategy
    │
    ▼
Python Implementation
    │
    ▼
Fast Python Backtest (parallel parameter exploration)
    │
    ▼
Candidate Filtering & Ranking
    │
    ▼
Pine Generation / Parity
    │
    ▼
Custom TradingView MCP → Compile → Chart → Strategy Tester
    │
    ▼
TV Trades/Metrics/Equity Extraction
    │
    ▼
Parity Comparison (Python vs TradingView)
    │
    ▼
Accept/Reject Candidate
    │
    ▼
Experiment DB (provenance, evidence, rejection reasons)
```

## Repository Structure

```
trading-research-control-plane/
├── README.md
├── docs/
│   ├── ARCHITECTURE.md
│   ├── CAPABILITY_MATRIX.md
│   ├── OFFICIAL_TRADINGVIEW.md
│   ├── CUSTOM_TRADINGVIEW_MCP.md
│   ├── PYTHON_PY2PINE.md
│   ├── PARITY.md
│   ├── RESEARCH_PIPELINE.md
│   ├── AUTONOMOUS_RESEARCH_GAPS.md
│   └── SECURITY.md
├── registry/
│   └── capabilities.json
├── control_plane/
│   ├── __init__.py
│   ├── backends/
│   │   ├── __init__.py
│   │   ├── python_py2pine.py
│   │   ├── custom_tradingview_mcp.py
│   │   └── official_tradingview.py
│   ├── registry.py
│   ├── pipeline.py
│   ├── provenance.py
│   ├── safety.py
│   └── observability.py
├── fixtures/
│   ├── deterministic_strategies/
│   └── test_data/
├── tests/
│   ├── test_capabilities.py
│   ├── test_parity.py
│   ├── test_pipeline.py
│   └── test_safety.py
├── proofs/
│   ├── FINAL_CAPABILITY_REPORT.md
│   └── PYTHON_TV_PARITY_REPORT.md
├── experiments/
└── scripts/
    ├── run_proofs.py
    ├── run_parity.py
    └── run_pipeline.py
```

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run capability discovery
python -m control_plane.registry discover

# Run proof harness
python scripts/run_proofs.py

# Run parity tests
python scripts/run_parity.py

# Run full research pipeline
python scripts/run_pipeline.py --strategy fixtures/deterministic_strategies/sma_crossover.py
```

## Backend Capabilities

### Python / py2pine (PRIMARY: Fast Research)
- 19 core Jackson strategies ported to Python
- 30+ Pine indicators faithfully reimplemented (RMA/Wilder smoothing)
- TV-parity backtester with exact execution model (O→H→L→C path)
- Parallel execution across strategies × assets × timeframes
- Parameter sweeps, grid search, walk-forward validation
- ~1000+ backtests/second on modern hardware

### Custom TradingView MCP (PRIMARY: Pine/TV Validation)
- 97 MCP tools via stdio/HTTP
- Pine Editor: read/write/compile/analyze
- Chart control: symbol, timeframe, indicators, visible range
- Strategy Tester: read summary, trades, equity curve
- Lab tools: popup-safe compile, inject, add-to-chart, full cycles
- CDP browser automation (port 9222)

### Official TradingView MCP/API (PRIMARY: Data/Research)
- Market data (OHLCV, quotes, symbol search)
- Fundamentals, analyst data, filings
- News, economic calendar
- Watchlists, alerts, alert history
- Stable native TradingView access

## Safety Boundaries

This is a **RESEARCH** system only:
- No live order execution
- No API keys, OAuth tokens, or credentials in Git
- Explicit separation: RESEARCH → PAPER/SIMULATION → TRADING_EXECUTION
- `.gitignore` and `.env.example` enforce secret hygiene

## Provenance & Observability

Every experiment receives a unique ID with:
- Hypothesis, strategy source/hash, parameters
- Symbol, timeframe, dataset identity, date range
- Python result, TradingView result, parity result
- Rejection reason, timestamps, evidence locations
- Structured logs: WHAT, WHY, WHICH, WHAT RESULT

## Status

See `proofs/FINAL_CAPABILITY_REPORT.md` for current capability matrix and test results.