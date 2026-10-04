"""Compare existing controlled-fixture evidence in equivalent timestamp domains.

The TV fields are native reportData execution-bar labels (milliseconds).
Python's legacy fill_time is a derived close-boundary, not a TV-native instant.
No live API calls, fabricated native times, or authority adjudication occur here.
"""
from decimal import Decimal

SIGNALS = (1791037800, 1791039600, 1791041400, 1791043200, 1791045000, 1791046800)


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _decimal(value):
    number = Decimal(str(value))
    _require(number.is_finite(), 'Finite economic values required')
    return number


def compare_capture(packet):
    """Fail closed on the pinned 3-long fixture; leave raw capture unchanged."""
    py = packet['python']
    tv = packet['tv_trades']
    summary = packet['tv_summary']
    _require(packet['directive'] == 5982350057, 'Exact immutable capture required')
    _require(py['closed_trade_count'] == summary['total_trades'] == 3, 'Three trades required')
    _require(len(py['trades']) == len(tv['closed_trades']) == 3, 'Complete trade count required')
    _require(tv['closed_trade_semantics'] == 'native_reportData_trades', 'Native closed trades required')
    _require(tv['closed_trade_stream_complete'] is True and tv['order_stream_complete'] is True and tv['truncated'] is False, 'Complete native streams required')
    _require(tv['total_available_closed_trades'] == 3, 'Native total count mismatch')
    orders = tv['raw_order_records']
    _require(len(orders) == tv['raw_order_record_count'] == tv['total_available_order_records'] == 6, 'Six raw orders required')
    _require([r['tm'] for r in orders] == list(range(6)), 'Unexpected raw-order time domain; no epoch inference permitted')
    _require(summary['strategy_name'] == tv['strategy_name'] == 'Hermes TV Timestamp 3L Fixture', 'Exact fixture strategy required')
    domain_checks = []
    python_derived_close_boundaries = []
    pnl_total = Decimal(0)
    for index, (expected, actual) in enumerate(zip(py['trades'], tv['closed_trades'])):
        raw = actual['raw_native_trade']
        _require(raw['e']['tp'] == 'le' and raw['x']['tp'] == 'lx', 'Long entry/exit required')
        for side, native_side in [('entry', 'e'), ('exit', 'x')]:
            signal = expected[side + '_signal_time']
            derived = expected[side + '_fill_time']
            native_ms = actual[side + '_time_ms']
            _require(type(signal) is int and type(derived) is int and type(native_ms) is int, 'Integer timestamp domains required')
            _require(signal == SIGNALS[index * 2 + (side == 'exit')], 'Pinned signal-bar identity mismatch')
            _require(derived == signal + 900, 'Python derived close-boundary mismatch')
            _require(native_ms == raw[native_side]['tm'] == signal * 1000, 'Native execution-bar identity mismatch')
            _require(_decimal(actual[side + '_price']) == _decimal(raw[native_side]['p']) == _decimal(expected[side + '_price']), 'Price mismatch')
            domain_checks.append(True)
            python_derived_close_boundaries.append(derived)
        _require(_decimal(actual['qty']) == _decimal(raw['q']) == _decimal(expected['qty']) == 1, 'Quantity mismatch')
        _require(_decimal(actual['native_reported_pnl']) == _decimal(raw['tp']['v']) == _decimal(expected['pnl']), 'PnL mismatch')
        _require(_decimal(actual['native_commission']) == _decimal(raw['cm']) == 0, 'Unexpected commission')
        _require(_decimal(expected['pnl']) == _decimal(expected['exit_price']) - _decimal(expected['entry_price']), 'Derived economics mismatch')
        pnl_total += _decimal(expected['pnl'])
    _require(pnl_total == _decimal(py['net_profit']) == Decimal('3.12'), 'Python pinned net profit mismatch')
    diff = abs(_decimal(summary['net_profit']) - pnl_total)
    _require(diff <= Decimal('0.000001'), 'TV net-profit tolerance exceeded')
    return {
        'equivalent_domain_parity': 'PASS',
        'native_time_matches_signal_bar_open': domain_checks,
        'python_derived_close_boundaries': python_derived_close_boundaries,
        'tv_native_report_time_domain': 'EXECUTION_BAR_OPEN_LABEL_MILLISECONDS',
        'native_wall_clock_close_instant_exposed': False,
        'raw_order_time_semantic': 'NON_EPOCH_ORDINAL_UNSUPPORTED_FOR_TIMESTAMP_PARITY',
        'trade_count': 3,
        'raw_order_count': 6,
        'prices_quantity_direction_pnl_match': True,
        'net_profit_abs_diff': str(diff),
        'certification_authority': 'CONTROLLER_ADJUDICATION_REQUIRED',
    }
