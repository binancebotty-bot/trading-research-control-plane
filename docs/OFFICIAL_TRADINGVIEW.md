# Official TradingView MCP/API

## Status: Not Yet Publicly Available (2026)

As of 2026, TradingView's official MCP/API service is not publicly available for general developer access. This document defines the interface and integration points for when official access becomes available.

## Planned Capabilities

### Market Data
- `market_data_ohlcv` — OHLCV bars for any symbol/timeframe
- `market_data_quote` — Real-time quote (bid, ask, last, volume)
- `symbol_search` — Search symbols by name/keyword
- `symbol_info` — Detailed symbol metadata (exchange, type, currency, session, etc.)

### Fundamentals
- `fundamentals` — Market cap, P/E, P/B, dividend yield, EPS, revenue, net income
- `analyst_estimates` — Analyst price targets, earnings estimates
- `filings` — SEC filings, earnings reports, 10-K/10-Q

### News & Economic
- `news` — News articles with sentiment analysis
- `economic_calendar` — Economic events, releases, impact ratings

### Watchlists
- `watchlists_get` — List user watchlists
- `watchlists_create` — Create new watchlist
- `watchlists_update` — Add/remove symbols from watchlist
- `watchlists_delete` — Delete watchlist

### Alerts
- `alerts_get` — List user alerts
- `alerts_create` — Create price/condition alert
- `alerts_update` — Modify alert
- `alerts_delete` — Delete alert
- `alert_history` — Alert trigger history

### Other
- `screener` — Stock/crypto screener with filters
- `heatmap` — Market heatmap by sector
- `sector_performance` — Sector performance data

## Current Fallback Implementation

Until official access is available, the backend uses:

1. **tvDatafeed** (unofficial Python library) for market data
   - Provides OHLCV data for crypto, forex, stocks
   - No authentication required
   - Rate-limited but functional

2. **Public TradingView REST endpoints** for symbol search/info
   - No authentication required
   - Limited to basic metadata

3. **TradingView charting library public APIs** for news
   - RSS feeds and public endpoints

## Integration Points

When official TradingView MCP becomes available:

```python
# Future integration
from tradingview_official_mcp import TradingViewOfficialMCP

tv = TradingViewOfficialMCP(
    api_key=os.environ["TRADINGVIEW_API_KEY"],
    transport="mcp",  # or "rest", "websocket"
)

# Market data
ohlcv = tv.get_market_data("BTCUSDT", "1h", count=500)

# Fundamentals
fundamentals = tv.get_fundamentals("AAPL")

# News
news = tv.get_news(symbols=["BTCUSDT", "ETHUSDT"], limit=20)

# Watchlists
watchlists = tv.get_watchlists()

# Alerts
alerts = tv.get_alerts()
```

## Authentication

Official TradingView API will require:
- API key (OAuth 2.0 or API token)
- Rate limiting based on account tier
- Separate credentials from custom MCP (CDP browser session)

## Environment Variables

```bash
# .env.example
TRADINGVIEW_API_KEY=your_api_key_here
TRADINGVIEW_USERNAME=your_username
TRADINGVIEW_PASSWORD=your_password
TRADINGVIEW_TRANSPORT=mcp  # mcp, rest, websocket
```

## Security

- API keys stored in `.env` (never in Git)
- `.env` listed in `.gitignore`
- `.env.example` provides template without secrets
- All API calls use HTTPS
- No credentials logged or persisted in experiment records