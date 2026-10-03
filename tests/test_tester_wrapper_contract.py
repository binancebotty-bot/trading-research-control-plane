from unittest.mock import Mock
from control_plane.backends.custom_tradingview_mcp import CustomTradingViewMCPBackend, TVCallResult


def backend(payload):
    b = CustomTradingViewMCPBackend(autostart=False)
    b.call_tool = Mock(return_value=TVCallResult(tool='strategy_tester_read_summary', ok=True, payload=payload))
    return b


def test_nested_real_summary_is_normalized_exactly():
    values = {'net_profit': -72.7019811240018, 'total_trades': 162, 'percent_profitable': 0.41358024691358025, 'profit_factor': 0.9590458150074851, 'max_drawdown': 520.4788089090016, 'avg_trade': 0, 'largest_loss': 112.98776680600005}
    b = backend({'success': True, 'summary': values})
    r = b.read_strategy_tester()
    for k, v in values.items():
        assert getattr(r, k) == v
    assert r.raw_data == {'success': True, 'summary': values}


def test_top_level_camelcase_still_supported_and_zero_is_preserved():
    b = backend({'netProfit': 0, 'totalTrades': 2, 'percentProfitable': 0, 'profitFactor': 0, 'maxDrawdown': 3})
    r = b.read_strategy_tester()
    assert (r.net_profit, r.total_trades, r.percent_profitable, r.profit_factor, r.max_drawdown) == (0, 2, 0, 0, 3)
    assert r.avg_trade is None


def test_nested_missing_fields_fall_back_to_supported_top_level_without_fabrication():
    r = backend({'summary': {'total_trades': 162}, 'netProfit': 0}).read_strategy_tester()
    assert r.total_trades == 162
    assert r.net_profit == 0
    assert r.profit_factor is None


def test_open_panel_uses_runtime_enum():
    b = backend({})
    b.open_strategy_tester()
    b.call_tool.assert_called_once_with('ui_open_panel', {'panel': 'strategy-tester', 'action': 'open'})


def test_nested_strategy_identity_is_preserved_without_invention():
    r = backend({'summary': {'strategy_name': 'Observed strategy', 'total_trades': 0}}).read_strategy_tester()
    assert r.strategy_name == 'Observed strategy'
    assert r.to_dict()['strategy_name'] == 'Observed strategy'
    assert r.total_trades == 0
    assert backend({}).read_strategy_tester().strategy_name is None
    assert backend({'summary': {'strategy_name': None}, 'strategyName': 'Fallback forbidden'}).read_strategy_tester().strategy_name is None

