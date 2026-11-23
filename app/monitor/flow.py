from collections import defaultdict
from decimal import localcontext

from app.monitor.clock import instant, minute
from app.numbers import number

UNITS = ('Nm3/min', 'Nm3/h')


def choose_flows(rows, window):
    """标况干流量按分钟采信：同分钟同值择最早收件，异值整组冲突不采信。"""
    by_minute = defaultdict(list)
    isolated = []
    for row in rows:
        fields = row['fields']
        try:
            when, received = minute(fields['timestamp']), instant(fields['received'])
            if fields['stack'] != window.stack:
                raise ValueError('WRONG_STACK')
            if not window.start <= when < window.end:
                raise ValueError('OUTSIDE_WINDOW')
            if received > window.cutoff:
                raise ValueError('AFTER_CUTOFF')
            if received < when:
                raise ValueError('BAD_RECEIVED')
            value = number(fields['value'])
            if value < 0:
                raise ValueError('NEGATIVE')
            if fields['unit'] not in UNITS:
                raise ValueError('BAD_FLOW_UNIT')
        except ValueError as error:
            isolated.append(row | {'code': str(error)})
            continue
        by_minute[when].append((received, value, fields['unit'], row))
    selected = {}
    with localcontext() as ctx:
        ctx.prec = 40
        for when, candidates in sorted(by_minute.items()):
            normed = sorted(
                ((received, value if unit == 'Nm3/min' else value / 60, row)
                 for received, value, unit, row in candidates),
                key=lambda item: (item[0], item[2]['line']))
            if len({item[1] for item in normed}) > 1:
                isolated.extend(item[2] | {'code': 'CONFLICT'} for item in normed)
                continue
            selected[when] = normed[0][2] | {'nm3_min': normed[0][1]}
            isolated.extend(item[2] | {'code': 'DUPLICATE'} for item in normed[1:])
    return selected, sorted(isolated, key=lambda row: row['line'])
