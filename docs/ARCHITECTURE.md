# Architecture

## Overview

The Trading Research Control Plane integrates three distinct research backends into a unified system for systematic trading strategy research.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    TRADING RESEARCH CONTROL PLANE                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐     │
│  │  PYTHON / PY2PINE │    │ CUSTOM TV MCP    │    │ OFFICIAL TV API  │     │
│  │  (Fast Research)  │    │ (Pine/TV Valid)  │    │ (Data/Research)  │     │
│  └────────┬─────────┘    └────────┬─────────┘    └────────┬─────────┘     │
│           │                       │                       │                │
│           └───────────────────────┼───────────────────────┘                │
│                                   ▼                                        │
│                    ┌────────────────────────┐                             │
│                    │   CAPABILITY REGISTRY  │                             │
│                    │   (Machine-readable)   │                             │
│                    └───────────┬────────────┘                             │
│                                │                                          │
│                    ┌───────────▼────────────┐                             │
│                    │   RESEARCH PIPELINE    │                             │
│                    │  (Fast-search → TV)    │                             │
│                    └───────────┬────────────┘                             │
│                                │                                          │
│           ┌───────────────────┼───────────────────┐                      │
│           ▼                   ▼                   ▼                      │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐              │
│  │  PROVENANCE  │    │   SAFETY     │    │ OBSERVABILITY│              │
│  │  (Experiments)│    │  (Guards)    │    │   (Logs)     │              │
│  └──────────────┘    └──────────────┘    └──────────────┘              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Three Backends

### 1. Python / py2pine (Primary: Fast Research)

**Location**: `control_plane/backends/python_py2pine.py`

**Proven Components**:
- 19 core Jackson strategies (`strategies_core.py`)
- 30+ Pine indicators with TV-parity (`pine_indicators.py`)
- TV-parity backtester (`tv_parity_backtester_v2.py`)
- Pine transpiler (`pine_transpiler.py`)
- Parallel runner (`run_core_backtests.py`)

**Capabilities**:
- Single backtest: ~1-5ms
- Parallel execution: 4+ workers
- Parameter sweeps: 1000+ combinations
- Walk-forward validation
- Deterministic test suite (16 tests)

**Data Flow**:
```
Strategy Function → run_strategy_engine → CostModel → Trade Log → Metrics
```

### 2. Custom TradingView MCP (Primary: Pine/TV Validation)

**Location**: `control_plane/backends/custom_tradingview_mcp.py`

**Proven Components**:
- 97 MCP tools via stdio/HTTP (port 9223)
- Pine Editor: read/write/compile/analyze/check
- Chart control: symbol, timeframe, indicators, range
- Lab tools: facade compile, inject, add-to-chart, full cycles
- Strategy Tester: read_summary (net profit, trades, %win, PF, max DD)
- CDP browser automation (port 9222)

**Capabilities**:
- Pine compilation (facade - no popup)
- Static analysis (array bounds, unguarded access)
- Chart manipulation
- Strategy deployment
- TV metrics/trades/equity extraction

**Data Flow**:
```
Pine Source → pine_compile (facade) → pine_replace_script → pine_add_to_chart → strategy_tester_read_summary
```

### 3. Official TradingView MCP/API (Primary: Data/Research)

**Location**: `control_plane/backends/official_tradingview.py`

**Status**: Official MCP/API not yet publicly available (2026)

**Current Implementation**:
- tvDatafeed (unofficial) for market data
- Public REST endpoints for symbol search/info
- Interface defined for future official access

**Planned Capabilities**:
- Market data (OHLCV, quotes)
- Fundamentals, analyst estimates, filings
- News, economic calendar
- Watchlists, alerts, alert history
- Screener, heatmap, sector performance

## Control Plane Components

### Capability Registry (`control_plane/registry.py`)

Machine-readable catalog of ALL functions across three backends.

**Classification**:
- `OFFICIAL_ONLY` - Only in official TV
- `CUSTOM_ONLY` - Only in custom MCP
- `PYTHON_ONLY` - Only in Python
- `OFFICIAL_CUSTOM` - In both official and custom
- `CUSTOM_PYTHON` - In both custom and Python
- `ALL_THREE` - In all three
- `UNAVAILABLE` - Not implemented
- `UNPROVEN` - Not yet tested

### Research Pipeline (`control_plane/pipeline.py`)

Fast-search → TV-validation pipeline:

```
Hypothesis/Strategy
    │
    ▼
Python Implementation (strategies_core.py)
    │
    ▼
Fast Python Backtest (run_strategy_engine)
    │
    ▼
Parallel Parameter Exploration (parameter_sweep)
    │
    ▼
Candidate Filtering (min_trades, min_PF, max_DD)
    │
    ▼
Pine Generation (from pine/ directory or transpiler)
    │
    ▼
TV Compile (pine_compile facade)
    │
    ▼
TV Strategy Tester (pine_full_cycle_strategy)
    │
    ▼
TV Extraction (strategy_tester_read_summary)
    │
    ▼
Parity Comparison (tolerances per metric)
    │
    ▼
Accept/Reject Decision
    │
    ▼
Persist Experiment (provenance)
```

### Experiment Provenance (`control_plane/provenance.py`)

Every experiment gets unique ID with immutable record:

- Hypothesis, strategy source/hash, Python source/hash, Pine source/hash
- Parameters, symbol, timeframe, dataset identity, date range
- Costs, execution assumptions
- Python result, TV result, parity result
- Rejection reason, timestamps
- **Lock mechanism prevents overwrites**

### Research Safety (`control_plane/safety.py`)

Protections against:
- Look-ahead bias (code pattern detection)
- Overfitting (train/val/OOS degradation thresholds)
- Survivorship bias (symbol coverage checks)
- Parameter leakage (optimisation history tracking)
- Data leakage (temporal overlap, hash comparison)
- Cherry-picking (result reporting ratio)
- Repeated optimisation (max 3 per holdout)
- False parity (2x tolerance rule)
- Duplicate experiments (hash deduplication)
- Unrecorded failures (provenance verification)

**Dataset Splits**: TRAIN, VALIDATION, OUT_OF_SAMPLE, FORWARD

### Observability (`control_plane/observability.py`)

Structured logs with all required fields:

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

## Safety Boundaries

```
┌─────────────────────────────────────────────────────────────────┐
│                        RESEARCH (THIS REPO)                     │
│  - No live orders                                               │
│  - No credentials in Git                                        │
│  - .gitignore, .env.example enforced                            │
│  - Paper/simulation only                                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      PAPER / SIMULATION                         │
│  - Simulated execution with realistic costs                     │
│  - No real capital at risk                                      │
│  - Separate environment                                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    TRADING EXECUTION (SEPARATE)                 │
│  - Live order execution                                         │
│  - Real capital                                                 │
│  - Requires explicit approval                                   │
│  - NOT in this repository                                       │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow Summary

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  HYPOTHESIS │────▶│  PYTHON     │────▶│  PARALLEL   │────▶│  CANDIDATE  │
│             │     │  BACKTEST   │     │  EXPLORE    │     │  FILTER     │
└─────────────┘     └─────────────┘     └─────────────┘     └──────┬──────┘
                                                                    │
                                                                    ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  PERSIST    │◀────│  DECISION   │◀────│  PARITY     │◀────│  TV VALID   │
│  EXPERIMENT │     │  ACCEPT/    │     │  COMPARE    │     │  (Strategy  │
│             │     │  REJECT     │     │             │     │  Tester)    │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
```

## Repository Structure

```
trading-research-control-plane/
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
├── scripts/
│   ├── run_proofs.py
│   ├── run_parity.py
│   └── run_pipeline.py
├── requirements.txt
├── .gitignore
├── .env.example
└── README.md
```