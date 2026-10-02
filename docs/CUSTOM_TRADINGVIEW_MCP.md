# Custom TradingView MCP

## Overview

The custom TradingView MCP server (`tradingview-mcp-jackson`) provides 97 tools for Pine Script editing, chart control, and Strategy Tester interaction via Chrome DevTools Protocol (CDP).

## Location

- **Repository**: `C:\Users\wigmore\trading_stack\tradingview-mcp-jackson`
- **Server**: `src/server.js` (stdio), `src/mcp-http-server.js` (HTTP :9223)
- **CDP**: Chrome DevTools Protocol on port 9222
- **Transport**: stdio (default) or HTTP

## Tool Categories

### Pine Editor Tools (14 tools)

| Tool | Description | Read/Write |
|------|-------------|------------|
| `pine_get_source` | Get current Pine Script source from editor | READ |
| `pine_set_source` | Set Pine Script source in editor | WRITE |
| `pine_compile_facade` | Compile via TradingView pine-facade (server-side, no popup) | READ |
| `pine_analyze` | Static analysis without compiling | READ |
| `pine_check` | Compile via TradingView server API | READ |
| `pine_get_errors` | Get compilation errors from Monaco markers | READ |
| `pine_get_console` | Read Pine Script console/log output | READ |
| `pine_save` | Save current Pine Script (Ctrl+S) | WRITE |
| `pine_list_scripts` | List saved Pine Scripts | READ |
| `pine_new` | Create new blank Pine Script | WRITE |
| `pine_open` | Open saved Pine Script by name | WRITE |
| `pine_replace_script` | Inject Pine source into live Monaco editor | WRITE |
| `pine_add_to_chart` | Add current editor script to chart | WRITE |
| `pine_save_script` | Save current script (Ctrl+S) | WRITE |

### Lab Tools (5 tools) — Popup-Safe

| Tool | Description | Read/Write |
|------|-------------|------------|
| `pine_full_cycle_indicator` | Full indicator cycle: compile → inject → optionally add to chart | WRITE |
| `pine_full_cycle_strategy` | Full strategy cycle: compile → inject → add to chart → read Strategy Tester | WRITE |
| `tv_state_snapshot` | Snapshot chart symbol/timeframe, Pine editor state, Strategy Tester visibility, open modals | READ |
| `pine_detect_blocking_modal` | Detect & classify any blocking TradingView modal | READ |
| `pine_resolve_known_modal` | Safely resolve ONLY a known+expected modal | WRITE |

### Chart Control Tools (8 tools)

| Tool | Description | Read/Write |
|------|-------------|------------|
| `chart_get_state` | Get current chart state (symbol, timeframe, chart type, indicators) | READ |
| `chart_set_symbol` | Change the chart symbol | WRITE |
| `chart_set_timeframe` | Change the chart timeframe/resolution | WRITE |
| `chart_set_type` | Change chart type | WRITE |
| `chart_manage_indicator` | Add or remove an indicator/study on the chart | WRITE |
| `chart_get_visible_range` | Get the visible date range and bars range | READ |
| `chart_set_visible_range` | Zoom the chart to a specific date range | WRITE |
| `chart_scroll_to_date` | Jump the chart view to center on a specific date | WRITE |

### Strategy Tester Tools (1 tool)

| Tool | Description | Read/Write |
|------|-------------|------------|
| `strategy_tester_read_summary` | Read the Strategy Tester backtest summary | READ |

### Symbol Tools (2 tools)

| Tool | Description | Read/Write |
|------|-------------|------------|
| `symbol_info` | Get detailed metadata about the current symbol | READ |
| `symbol_search` | Search for symbols by name or keyword | READ |

### Health & Diagnostics (1 tool)

| Tool | Description | Read/Write |
|------|-------------|------------|
| `health_check` | Check MCP server and browser connection health | READ |

## High-Level Workflows

### Strategy Deployment Cycle

```
1. pine_compile_facade(source)     → Verify compilation (no popup)
2. pine_replace_script(source)     → Inject into Monaco editor
3. pine_add_to_chart()             → Add to chart
4. strategy_tester_read_summary()  → Read backtest results
```

### Indicator Deployment Cycle

```
1. pine_compile_facade(source)     → Verify compilation
2. pine_replace_script(source)     → Inject into editor
3. pine_add_to_chart()             → Add to chart (optional)
```

### Safe Modal Handling

```
1. tv_state_snapshot()             → Detect open modals
2. pine_detect_blocking_modal()   → Classify modal type
3. pine_resolve_known_modal()     → Resolve if expected
```

## Configuration

```json
{
  "mcp_dir": "C:\\Users\\wigmore\\trading_stack\\tradingview-mcp-jackson",
  "transport": "stdio",
  "http_port": 9223,
  "cdp_port": 9222
}
```

## Prerequisites

- Node.js 18+
- Chrome/Chromium with remote debugging enabled
- TradingView account (logged in via CDP)
- Pine Editor open in browser

## Safety

- **Read-only tools** for state inspection
- **Popup-safe lab tools** for compilation without modal interference
- **Modal detection** before any write operation
- **Health check** before operations
- **No live trading** — this MCP does not place orders