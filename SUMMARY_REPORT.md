# Trading Research Control Plane - Comprehensive Report

## 1. File Structure
```
trading-research-control-plane/
├── control_plane/
│   ├── backends/
│   │   ├── custom_tradingview_mcp.py   # Wrapper for existing 97-tool MCP server
│   │   ├── official_tradingview.py     # Interface for official TradingView API (not publicly available)
│   │   ├── python_py2pine.py           # High-speed backtesting backend (wraps proven components)
│   │   └── __init__.py
│   ├── observability.py
│   ├── pipeline.py
│   ├── provenance.py
│   ├── registry.py                     # Capability registry
│   ├── safety.py
│   └── __init__.py
├── docs/
├── experiments/
├── fixtures/
├── proofs/
│   ├── FINAL_CAPABILITY_REPORT.md      # Overall capability summary
│   └── PYTHON_TV_PARITY_REPORT.md      # Python↔TV parity framework
├── registry/
├── scripts/
│   ├── run_parity.py                   # Parity test execution
│   ├── run_pipeline.py                 # Research pipeline execution
│   └── run_proofs.py                   # Automated proof harness
├── tests/
│   ├── test_capabilities.py
│   ├── test_parity.py
│   ├── test_pipeline.py
│   └── test_safety.py
├── .env.example
├── .gitignore
├── README.md
└── requirements.txt
```

## 2. Backend Details

### 2.1 control_plane/backends/custom_tradingview_mcp.py
- **Purpose**: Wrapper for the existing 97-tool TradingView MCP server (tradingview-mcp-jackson)
- **Status**: Real implementation, but simplified
- **Key Features**:
  - Provides access to Pine editor tools (get/set source, compile, analyze, etc.)
  - Chart control tools (symbol, timeframe, type, indicators)
  - Strategy Tester integration (read summary)
  - Full cycle methods (indicator/strategy: compile → inject → [add to chart] → [read tester])
  - Modal handling and health check
- **Limitations**:
  - `_call_tool` method is a simplified implementation (notes: "in production would use proper MCP protocol")
  - Requires live TradingView browser session for actual tool execution
  - Returns tool metadata for registry purposes; actual execution depends on MCP client connection
- **Dependencies**: 
  - Requires Node.js MCP server running (`tradingview-mcp-jackson`)
  - Requires active TradingView session in browser

### 2.2 control_plane/backends/official_tradingview.py
- **Purpose**: Interface for official TradingView MCP/API (when publicly available)
- **Status**: Real implementation, but currently unavailable
- **Key Features**:
  - Defines capabilities for market data, fundamentals, news, watchlists, alerts, etc.
  - Includes fallback implementations using unofficial sources (e.g., tvDatafeed for market data)
  - Marks most capabilities as `NOT_AVAILABLE` pending official API release
- **Current State**:
  - All 20 official capabilities are `NOT_AVAILABLE` (no public API access)
  - Limited unofficial fallbacks functional (market data via tvDatafeed, symbol search via public API)
  - Designed to be enabled when official TradingView MCP/API becomes publicly available

### 2.3 control_plane/backends/python_py2pine.py
- **Purpose**: High-speed backtesting and research backend
- **Status**: Real, functional implementation
- **Key Features**:
  - Wraps proven components from `trading_stack`:
    - 19 core Jackson strategies (`strategies_core.py`)
    - 30+ Pine indicators with TV-parity (`pine_indicators.py`)
    - TV-parity backtester (`tv_parity_backtester_v2.py`)
    - Pine transpiler (`pine_transpiler.py`)
  - Supports:
    - Single backtest (`backtest_single`)
    - Parallel backtesting (`backtest_parallel`)
    - Parameter sweeps (`parameter_sweep`)
    - Walk-forward analysis (defined but not proven)
    - Pine→Python transpilation (`transpile_pine`)
    - Deterministic test suite (`run_deterministic_tests`)
    - Throughput benchmarking (`benchmark_throughput`)
  - Provenance tracking for all experiments
- **Dependencies**:
  - Requires historical CSV data in `trading_stack/data/`
  - Uses pandas, numpy for computations

## 3. Capability Registry (`control_plane/registry.py`)
- **Purpose**: Machine-readable registry covering all three backends
- **Functionality**:
  - Discovers capabilities from each backend's `get_capability_registry()` method
  - Classifies capabilities across backends (OFFICIAL_ONLY, CUSTOM_ONLY, PYTHON_ONLY, etc.)
  - Tracks test status, reliability, dependencies, limitations
  - Generates JSON reports and summary statistics
- **Current State** (from proofs):
  - 60 total functions discovered
  - 20 Official, 30 Custom MCP, 10 Python/py2pine
  - 12 PASS (Python backend fully tested)
  - 28 NOT_TESTABLE_SAFELY (require live TV session)
  - 20 NOT_AVAILABLE (official API not public)

## 4. Proof Reports

### 4.1 proofs/FINAL_CAPABILITY_REPORT.md
- **Summary**:
  - 60 total capabilities discovered
  - 12 PASS (Python backend)
  - 0 FAIL
  - 28 NOT_TESTABLE_SAFELY (Custom MCP tools requiring live TV)
  - 20 NOT_AVAILABLE (Official TV API)
- **Major Gaps**:
  1. Official TradingView API not publicly available
  2. Live TV testing required for 28 Custom MCP functions
  3. Parity validation requires live TV session
  4. Walk-forward defined but not implemented/proven
  5. Autonomous research foundation built but not implemented (by design)

### 4.2 proofs/PYTHON_TV_PARITY_REPORT.md
- **Purpose**: Documents Python↔TradingView parity testing framework
- **Components**:
  - 5 deterministic strategy fixtures (SMA crossover, RSI mean reversion, etc.)
  - 8 comparison metrics with explicit tolerances
  - 9 discrepancy classifications (DATA_DIFFERENCE, EXECUTION_SEMANTICS, etc.)
  - Automated comparison logic
- **Current Status**: NOT_TESTABLE_SAFELY (requires live TV session for both Python backtest and TV Strategy Tester execution)

## 5. Test Files
- `tests/test_capabilities.py`: Tests capability registry and backend discovery
- `tests/test_parity.py`: Tests parity classification and result structures
- `tests/test_pipeline.py`: Tests research pipeline stages and structure
- `tests/test_safety.py`: Tests safety checks (look-ahead bias, overfitting, etc.)
- **Status**: All tests pass in CI/python-only environment (do not require live TV)

## 6. Scripts
- `scripts/run_parity.py`: Executes Python↔TV parity tests (requires live TV for full comparison)
- `scripts/run_pipeline.py`: Executes complete research pipeline (hypothesis → fast backtest → TV validation → decision)
- `scripts/run_proofs.py`: Automated proof harness that tests every function and records PASS/FAIL/BLOCKED/NOT_TESTABLE_SAFELY/NOT_AVAILABLE

## 7. Real vs Placeholder Assessment
- **custom_tradingview_mcp.py**: **REAL** but simplified implementation. Not a placeholder in the sense of being empty, but the MCP tool calling layer is a simplified wrapper that would need replacement with a proper MCP client protocol for production use. The high-level workflows and tool schemas are real.
- **official_tradingview.py**: **REAL** interface layer. Currently functions as a placeholder for future official API, but the fallback implementations (where available) are real. Most capabilities are correctly marked as NOT_AVAILABLE pending public API release.
- **python_py2pine.py**: **REAL** and fully functional backend. All proven capabilities (backtesting, transpilation, indicators, etc.) are operational and tested.

## 8. What Needs to be Fixed / Addressed

### 8.1 Immediate Action Items (for custom_tradingview_mcp.py placeholder)
The `custom_tradingview_mcp.py` file contains a simplified `_call_tool` method that notes: "This is a simplified implementation - in production would use proper MCP protocol." To address this:
- Replace the simplified stdio-based tool calling with a proper MCP client implementation
- Implement robust connection handling, request/response parsing, and error handling per MCP specification
- Maintain backward compatibility with existing high-level workflow methods

### 8.2 Environmental Dependencies
- **Official TradingView API**: Not publicly available (external dependency). Monitor TradingView developer releases for public MCP/API availability.
- **Live TV Session Requirements**: 28 Custom MCP functions require an active TradingView browser session. For automated testing:
  - Consider implementing a mock MCP server for CI/testing
  - Or document manual verification procedures requiring live session
- **Data Requirements**: Python backend requires historical CSV data in `trading_stack/data/`

### 8.3 Feature Gaps to Implement
- **Walk-forward analysis**: Defined in Python backend capabilities but not yet implemented/proven
- **Autonomous research layer**: Foundation exists (pipeline, provenance, safety) but autonomous decision-making loop not implemented (by design per safety boundaries)
- **Enhanced parity testing**: Implement automated parity regression suite that can run when live TV session is available

### 8.4 Safety and Boundaries (by design, not fixes)
- **RESEARCH ONLY**: No live order execution (intentional)
- **No credentials in Git**: Enforced via .gitignore and .env.example
- **Paper/simulation only**: All backtests are simulated
- **Environment separation**: RESEARCH → PAPER/SIMULATION → TRADING_EXECUTION (boundaries respected)

## 9. Current Operational State
- **Python/py2pine backend**: Fully operational for automated research (backtesting, parameter sweeps, transpilation, etc.)
- **Custom TradingView MCP backend**: Operational when live TradingView session and MCP server are available
- **Official TradingView backend**: Awaiting public API release; currently provides interface and unofficial fallbacks where possible
- **Capability registry, proofs, tests, scripts**: All functional and validated in python-only CI environment

## 10. Recommendations
1. For immediate Python-only research: Use `python_py2pine.py` backend with `run_pipeline.py` or direct API calls
2. For TradingView-dependent work: Ensure `tradingview-mcp-jackson` MCP server is running and TradingView browser session is active
3. Monitor for official TradingView MCP/API release to enable `official_tradingview.py` capabilities
4. Consider implementing mock MCP server for automated testing of Custom MCP functions
5. Implement walk-forward analysis to complete Python backend capability set