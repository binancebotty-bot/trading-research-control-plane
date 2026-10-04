# Static timestamp-domain reconciliation — directive 5982741645

## Scope and immutable evidence

No live rerun, Pine write, compile, chart update, save, or trading action was performed.
The original live result and restoration remain immutable; the original comparison FAIL is not rewritten.

Original packet: `proofs/live_e2e_parity_20261004_5982350057/public-proof.json`.
SHA256: `4d119e5ef0b8f716350e9712aa66ab1e82879f2c7f4db652beb25bf7f8625cb8`.
Runtime head in that packet: `45568bbbf5793360dbaa25ba6ecfdf6c5e4a43f1`.

## Separate timestamp domains

1. Python signal-bar open: six pinned UTC epochs in `fixtures/tv_ethusdt_15m_3long/manifest.json`.
2. Python legacy `entry_fill_time` / `exit_fill_time`: explicitly derived by `control_plane/parity_fixture.py` lines 43–44 as `signal_time + 900`. Those are calculated close-boundaries, not native TV observations.
3. TV native closed-trade time: the existing captured `raw_native_trade.e.tm` / `.x.tm` in milliseconds, preserved verbatim in projected entry/exit fields. The attested MCP extraction source in `C:/Users/wigmore/.hermes/pine-control/static-5973974972/mcp-isolated-recovery/src/core/data.js` lines 213–217 maps the native fields directly; it does not add 900 seconds.
4. Raw-order `tm`: observed `[0,1,2,3,4,5]` on the separate order stream. These are non-epoch sequential values; their broader internal meaning is not proven and they are unsupported for epoch-time parity.

The native trades also carry execution-bar references `e.b/x.b = 20794/20796, 20798/20800, 20802/20804`. All six native report timestamps exactly equal the six pinned signal-bar epochs. The fixture uses `time == <pinned bar-open epoch>` and `process_orders_on_close=true`; prices match those same bars' closes. This supports the interpretation that native report time identifies the execution bar by its opening epoch. It does not prove or manufacture a native wall-clock bar-close instant.

The old comparison of a native execution-bar timestamp with a Python-derived close-boundary fails by exactly one 15-minute interval. That inequality remains true. The equivalent-domain comparison is separately PASS on the existing immutable capture: three long quantity-one closed trades, six complete raw orders, all entry/exit prices and native PnL match, total profit difference `5.64E-13` within `0.000001`.

`control_plane/parity_timestamp_domains.py` is a strict, fixture-scoped static comparator. It does not replace transport/native-attestation gates, change strategy economics, claim live authority, or emit derived values as native timestamps. Controller adjudication is still required.

## Recovered prior evidence — do not confuse TV validation with paired parity

- **REAL_TV_MEANINGFUL, but not a recovered paired Python↔TV vector**: `C:/Users/wigmore/OneDrive/Documents/WinAgentGPT/toolchain_proofs/tv_validation_pack_batch_20260515_175855/breakout_volatility_01_BO_DONCHIAN_VOLUME_20260515_135311_strategy.txt`. Physically recovered JSON reports `source=internal_api_plus_panel_text`, exact strategy name, `performance.all.totalTrades=160`, `filledOrders.length=320`, and net profit `1059.0775749999984`. Matching CSV: `C:/Users/wigmore/trading_stack/TradingView_Strategy_TopPerformers/TV_AUTOMATED_VALIDATION_PACK_RESULTS.csv`. This is meaningful historical TV execution evidence, not proof of this fixture's timestamp semantics or paired parity.
- **INCOMPATIBLE_WITH_CURRENT_SEMANTICS as a direct substitute**: `C:/Users/wigmore/trading_stack/Tradingview Backtesting/tv_parity_backtester_v2.py`. Its documented execution model is `process_orders_on_close=false`, next-bar-open fills, nonzero default fees; the current controlled fixture is same-bar close with zero fees. A source file promising TV parity is not itself an executed paired proof.
- **PLACEHOLDER_OR_ZERO_TRADE category (pending TV capture, not an assertion of zero trades)**: `C:/Users/wigmore/trading_stack/TradingView_Strategy_TopPerformers/validation_results_manual.csv` has blank TV metrics and `PENDING_MANUAL_TRADINGVIEW_CAPTURE`. Local Python trade counts do not establish genuine TV results.
- **NOT_FOUND_IN_BOUNDED_SEARCH for a recent compatible paired vector**: one finite pass across three targeted estate roots (depth two, 29 directories, 15 candidate paths), followed by a read-only bounded OpenCode SQLite search for py2pine/tv_parity (six most recent relevant parts, excluding unrelated Hyperliquid sessions in the refined query). Recovered recent parts were edits/diagnostics rather than a paired native-trade proof. This is a bounded-search result, not a claim that prior parity never existed or that all sessions/artifacts were exhausted. No fixture was rebuilt.

## Verification and advisory workers

Fourteen new parameterised test cases plus the existing fixture tests: focused combined suite **26 passed**, independently under inherited and scrubbed environments. Full suite **112 passed, 26 subtests passed** in both environments with third-party pytest plugin autoload disabled. Tests prove the old domain comparison fails, equivalent domains pass, one-bar/price/quantity/PnL/direction/summary/capture-integrity mismatches fail, raw-order ordinals cannot substitute for native epochs, and no fabricated native fill-time output is emitted.

Three local workers completed in parallel across the two installed local provider-model routes. A third distinct verified free route was unavailable; no paid fallback. Exact ledger is `delegate-ledger.json`. Their output is advisory only. The adversarial worker's missing-count/missing-exit-time/missing-ordinal assertions contradict explicit source checks and were rejected. The timestamp worker conflated separate raw-order ordinals with native closed-trade epochs; that conflation was not accepted as evidence.

Graphify was rebuilt without an LLM: 1210 nodes / 1905 edges. The new comparator is called by the regression suite; no existing production pipeline was silently redirected. Mutable runtime state and graph outputs are not part of the patch.

## Authority boundary

Architect ruling 5982833575 identifies the loop as ADVANCING and preserves PRODUCT_EXECUTION_HOLD pending MD disposition. Only this static/read-only packet was executed. No MD release, production certification, live-retry permission, or stand-down is inferred.
