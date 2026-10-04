import copy
import json
from pathlib import Path
import pytest

from control_plane import parity_timestamp_domains as domains

PROOF = Path(__file__).parents[1] / 'proofs/live_e2e_parity_20261004_5982350057/public-proof.json'


def payload():
    return json.loads(PROOF.read_text())


def test_equivalent_domains_from_immutable_native_capture():
    p = payload()
    out = domains.compare_capture(p)
    assert out['equivalent_domain_parity'] == 'PASS'
    assert out['native_time_matches_signal_bar_open'] == [True] * 6
    assert out['raw_order_time_semantic'] == 'NON_EPOCH_ORDINAL_UNSUPPORTED_FOR_TIMESTAMP_PARITY'
    assert 'native_fill_time' not in json.dumps(out)


def test_old_close_boundary_comparison_fails():
    p = payload()
    assert all(t['entry_time_ms'] != py['entry_fill_time'] * 1000 for py, t in zip(p['python']['trades'], p['tv_trades']['closed_trades']))


@pytest.mark.parametrize('field', ['entry_time_ms', 'exit_time_ms'])
def test_one_bar_native_time_mismatch_fails(field):
    p = payload()
    p['tv_trades']['closed_trades'][0][field] += 900000
    with pytest.raises(ValueError):
        domains.compare_capture(p)


@pytest.mark.parametrize('field', ['entry_price', 'exit_price', 'qty', 'native_reported_pnl'])
def test_economic_mismatch_fails(field):
    p = payload()
    p['tv_trades']['closed_trades'][0][field] += 1
    with pytest.raises(ValueError):
        domains.compare_capture(p)


def test_raw_order_ordinals_cannot_be_epoch_time():
    p = payload()
    for i, trade in enumerate(p['tv_trades']['closed_trades']):
        trade['entry_time_ms'] = p['tv_trades']['raw_order_records'][i * 2]['tm']
        trade['exit_time_ms'] = p['tv_trades']['raw_order_records'][i * 2 + 1]['tm']
    with pytest.raises(ValueError):
        domains.compare_capture(p)


@pytest.mark.parametrize('field', ['closed_trade_stream_complete', 'order_stream_complete'])
def test_incomplete_capture_fails(field):
    p = payload()
    p['tv_trades'][field] = False
    with pytest.raises(ValueError):
        domains.compare_capture(p)


def test_modified_raw_native_time_cannot_hide_behind_projection():
    p = payload()
    p['tv_trades']['closed_trades'][0]['raw_native_trade']['e']['tm'] += 900000
    with pytest.raises(ValueError):
        domains.compare_capture(p)


def test_non_long_direction_fails():
    p = payload()
    p['tv_trades']['closed_trades'][0]['raw_native_trade']['e']['tp'] = 'se'
    with pytest.raises(ValueError):
        domains.compare_capture(p)


def test_profit_summary_mismatch_fails():
    p = payload()
    p['tv_summary']['net_profit'] += 1
    with pytest.raises(ValueError):
        domains.compare_capture(p)
