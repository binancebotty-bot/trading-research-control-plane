# Capability Matrix

## Overview

This document provides a comprehensive matrix of all capabilities across the three research backends.

## Classification Legend

| Classification | Description |
|----------------|-------------|
| `OFFICIAL_ONLY` | Only available in Official TradingView API |
| `CUSTOM_ONLY` | Only available in Custom TradingView MCP |
| `PYTHON_ONLY` | Only available in Python/py2pine |
| `OFFICIAL_CUSTOM` | Available in both Official and Custom |
| `CUSTOM_PYTHON` | Available in both Custom and Python |
| `ALL_THREE` | Available in all three backends |
| `UNAVAILABLE` | Not implemented in any backend |
| `UNPROVEN` | Implemented but not yet tested |

## Backend Capabilities

### Python / py2pine (Fast Research)

| Capability | Native Function | Classification | Test Status | Reliability |
|------------|-----------------|----------------|-------------|-------------|
| Single backtest | `backtest_single` | PYTHON_ONLY | PASS | HIGH |
| Parallel backtest | `backtest_parallel` | PYTHON_ONLY | PASS | HIGH |
| Parameter sweep | `parameter_sweep` | PYTHON_ONLY | PASS | HIGH |
| Walk-forward | `walk_forward` | PYTHON_ONLY | UNPROVEN | UNKNOWN |
| Pine transpile | `transpile_pine` | PYTHON_ONLY | PASS | HIGH |
| List strategies | `list_strategies` | PYTHON_ONLY | PASS | HIGH |
| List indicators | `list_indicators` | PYTHON_ONLY | PASS | HIGH |
| Load data | `load_data` | PYTHON_ONLY | PASS | HIGH |
| Deterministic tests | `run_deterministic_tests` | PYTHON_ONLY | PASS | HIGH |
| Benchmark throughput | `benchmark_throughput` | PYTHON_ONLY | PASS | HIGH |

**Total**: 10 capabilities (10 PYTHON_ONLY)

### Custom TradingView MCP (Pine/TV Validation)

| Capability | Native Function | Classification | Test Status | Reliability |
|------------|-----------------|----------------|-------------|-------------|
| Pine get source | `pine_get_source` | CUSTOM_ONLY | PASS | HIGH |
| Pine set source | `pine_set_source` | CUSTOM_ONLY | PASS | HIGH |
| Pine compile (facade) | `pine_compile_facade` | CUSTOM_ONLY | PASS | HIGH |
| Pine analyze | `pine_analyze` | CUSTOM_ONLY | PASS | HIGH |
| Pine check | `pine_check` | CUSTOM_ONLY | PASS | HIGH |
| Pine get errors | `pine_get_errors` | CUSTOM_ONLY | PASS | HIGH |
| Pine get console | `pine_get_console` | CUSTOM_ONLY | PASS | HIGH |
| Pine save | `pine_save` | CUSTOM_ONLY | PASS | HIGH |
| Pine list scripts | `pine_list_scripts` | CUSTOM_ONLY | PASS | HIGH |
| Pine new | `pine_new` | CUSTOM_ONLY | PASS | HIGH |
| Pine open | `pine_open` | CUSTOM_ONLY | PASS | HIGH |
| Pine replace script | `pine_replace_script` | CUSTOM_ONLY | PASS | HIGH |
| Pine add to chart | `pine_add_to_chart` | CUSTOM_ONLY | PASS | HIGH |
| Pine save script | `pine_save_script` | CUSTOM_ONLY | PASS | HIGH |
| Full cycle indicator | `pine_full_cycle_indicator` | CUSTOM_ONLY | PASS | HIGH |
| Full cycle strategy | `pine_full_cycle_strategy` | CUSTOM_ONLY | PASS | HIGH |
| Chart get state | `chart_get_state` | CUSTOM_ONLY | PASS | HIGH |
| Chart set symbol | `chart_set_symbol` | CUSTOM_ONLY | PASS | HIGH |
| Chart set timeframe | `chart_set_timeframe` | CUSTOM_ONLY | PASS | HIGH |
| Chart set type | `chart_set_type` | CUSTOM_ONLY | PASS | HIGH |
| Chart manage indicator | `chart_manage_indicator` | CUSTOM_ONLY | PASS | HIGH |
| Chart get visible range | `chart_get_visible_range` | CUSTOM_ONLY | PASS | HIGH |
| Chart set visible range | `chart_set_visible_range` | CUSTOM_ONLY | PASS | HIGH |
| Chart scroll to date | `chart_scroll_to_date` | CUSTOM_ONLY | PASS | HIGH |
| Symbol info | `symbol_info` | CUSTOM_ONLY | PASS | HIGH |
| Symbol search | `symbol_search` | CUSTOM_ONLY | PASS | HIGH |
| Strategy tester read summary | `strategy_tester_read_summary` | CUSTOM_ONLY | PASS | HIGH |
| TV state snapshot | `tv_state_snapshot` | CUSTOM_ONLY | PASS | HIGH |
| Pine detect blocking modal | `pine_detect_blocking_modal` | CUSTOM_ONLY | PASS | HIGH |
| Pine resolve known modal | `pine_resolve_known_modal` | CUSTOM_ONLY | PASS | HIGH |
| Health check | `health_check` | CUSTOM_ONLY | PASS | HIGH |

**Total**: 30 capabilities (30 CUSTOM_ONLY)

### Official TradingView API (Data/Research)

| Capability | Native Function | Classification | Test Status | Reliability |
|------------|-----------------|----------------|-------------|-------------|
| Market data OHLCV | `market_data_ohlcv` | OFFICIAL_ONLY | BLOCKED* | UNKNOWN |
| Market data quote | `market_data_quote` | OFFICIAL_ONLY | BLOCKED* | UNKNOWN |
| Symbol search | `symbol_search` | OFFICIAL_ONLY | BLOCKED* | UNKNOWN |
| Symbol info | `symbol_info` | OFFICIAL_ONLY | BLOCKED* | UNKNOWN |
| Fundamentals | `fundamentals` | OFFICIAL_ONLY | NOT_AVAILABLE | UNKNOWN |
| Analyst estimates | `analyst_estimates` | OFFICIAL_ONLY | NOT_AVAILABLE | UNKNOWN |
| Filings | `filings` | OFFICIAL_ONLY | NOT_AVAILABLE | UNKNOWN |
| News | `news` | OFFICIAL_ONLY | NOT_AVAILABLE | UNKNOWN |
| Economic calendar | `economic_calendar` | OFFICIAL_ONLY | NOT_AVAILABLE | UNKNOWN |
| Watchlists get | `watchlists_get` | OFFICIAL_ONLY | NOT_AVAILABLE | UNKNOWN |
| Watchlists create | `watchlists_create` | OFFICIAL_ONLY | NOT_AVAILABLE | UNKNOWN |
| Watchlists update | `watchlists_update` | OFFICIAL_ONLY | NOT_AVAILABLE | UNKNOWN |
| Watchlists delete | `watchlists_delete` | OFFICIAL_ONLY | NOT_AVAILABLE | UNKNOWN |
| Alerts get | `alerts_get` | OFFICIAL_ONLY | NOT_AVAILABLE | UNKNOWN |
| Alerts create | `alerts_create` | OFFICIAL_ONLY | NOT_AVAILABLE | UNKNOWN |
| Alerts update | `alerts_update` | OFFICIAL_ONLY | NOT_AVAILABLE | UNKNOWN |
| Alerts delete | `alerts_delete` | OFFICIAL_ONLY | NOT_AVAILABLE | UNKNOWN |
| Alert history | `alert_history` | OFFICIAL_ONLY | NOT_AVAILABLE | UNKNOWN |
| Screener | `screener` | OFFICIAL_ONLY | NOT_AVAILABLE | UNKNOWN |
| Heatmap | `heatmap` | OFFICIAL_ONLY | NOT_AVAILABLE | UNKNOWN |
| Sector performance | `sector_performance` | OFFICIAL_ONLY | NOT_AVAILABLE | UNKNOWN |

\* **BLOCKED**: Official TradingView MCP/API not publicly available as of 2026. Current implementation uses unofficial tvDatafeed fallback for market data only.

**Total**: 20 capabilities (20 OFFICIAL_ONLY, 18 NOT_AVAILABLE, 2 BLOCKED)

## Cross-Backend Capability Mapping

### Market Data Access

| Function | Python | Custom MCP | Official TV |
|----------|--------|------------|-------------|
| Load OHLCV from CSV | ✅ `load_data` | ❌ | ⚠️ `market_data_ohlcv` (tvDatafeed) |
| Real-time quote | ❌ | ❌ | ⚠️ `market_data_quote` (tvDatafeed) |
| Symbol search | ❌ | ✅ `symbol_search` | ⚠️ `symbol_search` |
| Symbol info | ❌ | ✅ `symbol_info` | ⚠️ `symbol_info` |

### Strategy Execution

| Function | Python | Custom MCP | Official TV |
|----------|--------|------------|-------------|
| Backtest strategy | ✅ `backtest_single` | ❌ | ❌ |
| Parallel backtest | ✅ `backtest_parallel` | ❌ | ❌ |
| Parameter sweep | ✅ `parameter_sweep` | ❌ | ❌ |
| Strategy Tester | ❌ | ✅ `strategy_tester_read_summary` | ❌ |
| Full strategy cycle | ❌ | ✅ `pine_full_cycle_strategy` | ❌ |

### Pine Script Operations

| Function | Python | Custom MCP | Official TV |
|----------|--------|------------|-------------|
| Transpile Pine→Python | ✅ `transpile_pine` | ❌ | ❌ |
| Compile Pine (facade) | ❌ | ✅ `pine_compile_facade` | ❌ |
| Static analysis | ❌ | ✅ `pine_analyze` | ❌ |
| Inject to editor | ❌ | ✅ `pine_replace_script` | ❌ |
| Add to chart | ❌ | ✅ `pine_add_to_chart` | ❌ |
| Save script | ❌ | ✅ `pine_save_script` | ❌ |

### Chart Control

| Function | Python | Custom MCP | Official TV |
|----------|--------|------------|-------------|
| Get chart state | ❌ | ✅ `chart_get_state` | ❌ |
| Set symbol | ❌ | ✅ `chart_set_symbol` | ❌ |
| Set timeframe | ❌ | ✅ `chart_set_timeframe` | ❌ |
| Manage indicators | ❌ | ✅ `chart_manage_indicator` | ❌ |

### Research Data

| Function | Python | Custom MCP | Official TV |
|----------|--------|------------|-------------|
| Fundamentals | ❌ | ❌ | ❌ `fundamentals` |
| News | ❌ | ❌ | ❌ `news` |
| Economic calendar | ❌ | ❌ | ❌ `economic_calendar` |
| Watchlists | ❌ | ❌ | ❌ `watchlists_*` |
| Alerts | ❌ | ❌ | ❌ `alerts_*` |

## Summary Statistics

| Backend | Total Capabilities | Tested (PASS) | Blocked | Not Available | Unproven |
|---------|-------------------|---------------|---------|---------------|----------|
| Python/py2pine | 10 | 9 | 0 | 0 | 1 |
| Custom TV MCP | 30 | 30 | 0 | 0 | 0 |
| Official TV API | 20 | 0 | 2 | 18 | 0 |
| **TOTAL** | **60** | **39** | **2** | **18** | **1** |

## Routing Priority

For capabilities available in multiple backends, routing priority:

1. **Python/py2pine** (Priority 1): Fast research, backtesting, parameter sweeps
2. **Custom TV MCP** (Priority 1): Pine compilation, chart control, Strategy Tester
3. **Official TV API** (Priority 1): Market data, fundamentals, news, watchlists, alerts

**No silent fallback** - each operation explicitly selects backend based on capability classification.