import json
from pathlib import Path
from unittest.mock import Mock
import pytest
from control_plane.parity_fixture import run_fixture, reconstruct_controlled_orders
from control_plane.backends.custom_tradingview_mcp import CustomTradingViewMCPBackend, TVCallResult

FIXTURE = Path(__file__).parents[1] / 'fixtures/tv_ethusdt_15m_3long/manifest.json'

def test_static_fixture_three_decimal_trades_and_hashes():
    result = run_fixture(FIXTURE)
    assert result['closed_trade_count'] == 3
    assert len(result['trades']) == 3
    manifest = json.loads(FIXTURE.read_text())
    assert result == manifest['expected_python_result']

def test_raw_orders_are_not_native_closed_trades():
    b = CustomTradingViewMCPBackend(autostart=False)
    b.call_tool = Mock(return_value=TVCallResult('data_get_trades', True, {'trades':[{'id':1}], 'trade_count':1}))
    result = b.get_trades(max_trades=50)
    b.call_tool.assert_called_once_with('data_get_trades', {'max_trades':50})
    assert result.payload['record_semantics'] == 'raw_order_records'
    assert result.payload['closed_trades'] is None
    assert result.payload['raw_order_records'] == [{'id':1}]
    assert 'trades' not in result.payload
    assert result.payload['order_stream_complete'] is None


def order_stream():
    return [{'kind':kind,'signal_time':t,'fill_time':t+900,'price':p,'qty':'1','fees':'0','status':'filled','entry_id':str(i//2+1)}
            for i,(kind,t,p) in enumerate([('entry',1000,'10'),('exit',1900,'11'),('entry',2800,'11'),('exit',3700,'9'),('entry',4600,'8'),('exit',5500,'10')])]

def test_reconstruction_is_controlled_derived_not_native():
    r=reconstruct_controlled_orders(order_stream(),stream_complete=True,summary_trade_count=3)
    assert [t['pnl'] for t in r] == ['1','-2','2']

@pytest.mark.parametrize('problem',['truncated','unproven','partial','fees','unmatched','missing_price','wrong_summary'])
def test_reconstruction_rejects_incomplete_or_unsupported_semantics(problem):
    rows=order_stream(); complete=True;summary=3
    if problem=='truncated': rows.pop()
    if problem=='unproven': complete=False
    if problem=='partial': rows[1]['qty']='0.5'
    if problem=='fees': rows[0]['fees']='1'
    if problem=='unmatched': rows[1]['entry_id']='unknown'
    if problem=='missing_price': del rows[0]['price']
    if problem=='wrong_summary':summary=2
    with pytest.raises((ValueError,KeyError)):
        reconstruct_controlled_orders(rows,stream_complete=complete,summary_trade_count=summary)


def test_preserve_explicit_native_closed_trades_without_relabelling_raw_orders():
    b=CustomTradingViewMCPBackend(autostart=False)
    native=[{'entry_time_ms':1,'exit_time_ms':2,'qty':1}]
    b.call_tool=Mock(return_value=TVCallResult('data_get_trades',True,{'raw_order_records':[{'id':1}], 'closed_trades':native,'closed_trade_semantics':'native_reportData_trades'}))
    result=b.get_trades()
    assert result.payload['closed_trades']==native
    assert result.payload['raw_order_records']==[{'id':1}]
    assert result.payload['record_semantics']=='raw_order_records'


def test_pine_uses_only_six_pinned_timestamps_and_expected_pnl():
    m=json.loads(FIXTURE.read_text());s=(FIXTURE.parent/'fixture.pine').read_text()
    assert len(m['signal_timestamps'])==6 and len(set(m['signal_timestamps']))==6
    for t in m['signal_timestamps']: assert 'time == '+str(t*1000) in s
    assert 'bar_index' not in s and 'process_orders_on_close=true' in s
    assert m['expected_python_result']['net_profit']=='3.12'
    source=json.loads((FIXTURE.parent/'source-attestation.json').read_text())
    assert source['data_get_ohlcv']['genuine'] and source['chart_get_state']['genuine']
    assert json.loads((FIXTURE.parent/'bars.json').read_text()) == source['data_get_ohlcv']['payload']['bars'][:16]
