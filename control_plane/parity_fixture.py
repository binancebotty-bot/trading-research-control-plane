"""Timestamp-pinned fixture only; derived trades are never native tester trades."""
from decimal import Decimal
import hashlib
import json
from pathlib import Path


def reconstruct_controlled_orders(rows, *, stream_complete, summary_trade_count):
    if stream_complete is not True or summary_trade_count != 3 or len(rows) != 6:
        raise ValueError('Complete six-record controlled stream and native summary of 3 required')
    trades=[];last_time=None
    for i in range(0,6,2):
        entry,exit=rows[i:i+2]
        if entry['kind'] != 'entry' or exit['kind'] != 'exit' or entry['entry_id'] != exit['entry_id']:
            raise ValueError('Expected matched one-entry one-exit long pair')
        for row in (entry,exit):
            if Decimal(str(row['qty'])) != 1 or Decimal(str(row['fees'])) != 0 or row['status'] != 'filled':
                raise ValueError('Partial fills, quantities, fees or unfilled records unsupported')
            if not isinstance(row['signal_time'],int) or not isinstance(row['fill_time'],int):
                raise ValueError('Integer UTC timestamps required')
            if row['fill_time'] != row['signal_time']+900 or (last_time is not None and row['signal_time'] <= last_time):
                raise ValueError('Strict order and 15-minute bar-close execution required')
            last_time=row['signal_time']
            price=Decimal(str(row['price']))
            if not price.is_finite() or price <= 0: raise ValueError('Invalid price')
        trades.append({'entry_signal_time':entry['signal_time'],'exit_signal_time':exit['signal_time'],
                       'entry_fill_time':entry['fill_time'],'exit_fill_time':exit['fill_time'],
                       'entry_price':str(Decimal(str(entry['price']))),'exit_price':str(Decimal(str(exit['price']))),
                       'qty':'1','pnl':str(Decimal(str(exit['price']))-Decimal(str(entry['price'])))})
    return trades


def run_fixture(manifest_path):
    path=Path(manifest_path);manifest=json.loads(path.read_text())
    for name,key in [('bars.json','data_sha256'),('fixture.pine','pine_sha256')]:
        if hashlib.sha256((path.parent/name).read_bytes()).hexdigest() != manifest[key]:
            raise ValueError('Fixture hash mismatch: '+name)
    bars=json.loads((path.parent/'bars.json').read_text())
    lookup={b['time']:b for b in bars}
    if len(lookup) != len(bars):raise ValueError('Duplicate bars')
    rows=[]
    for i,t in enumerate(manifest['signal_timestamps']):
        rows.append({'kind':'entry' if i%2==0 else 'exit','signal_time':t,'fill_time':t+900,
                     'price':str(lookup[t]['close']),'qty':'1','fees':'0','status':'filled','entry_id':str(i//2+1)})
    trades=reconstruct_controlled_orders(rows,stream_complete=True,summary_trade_count=3)
    return {'record_semantics':'derived_controlled_closed_trades','closed_trade_count':len(trades),
            'trades':trades,'net_profit':str(sum((Decimal(t['pnl']) for t in trades),Decimal(0)))}
