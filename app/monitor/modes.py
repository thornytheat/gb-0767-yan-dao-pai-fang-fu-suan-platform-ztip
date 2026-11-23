from app.monitor.clock import minute

PRIORITY = {'STARTUP': 1, 'SHUTDOWN': 2}


def mode_windows(rows, window):
    accepted, isolated = [], []
    for row in rows:
        fields = row['fields']
        try:
            start, end = minute(fields['start']), minute(fields['end'])
            if fields['stack'] != window.stack:
                raise ValueError('WRONG_STACK')
            if end <= start or fields['mode'] not in PRIORITY:
                raise ValueError('BAD_MODE')
            if end <= window.start or start >= window.end:
                raise ValueError('OUTSIDE_WINDOW')
        except ValueError as error:
            isolated.append(row | {'code': str(error)})
            continue
        accepted.append((start, end, fields['mode'], row))
    return accepted, isolated


def active_modes(windows, when):
    return sorted(((mode, row) for start, end, mode, row in windows if start <= when < end),
                  key=lambda x: (-PRIORITY[x[0]], x[1]['line']))
