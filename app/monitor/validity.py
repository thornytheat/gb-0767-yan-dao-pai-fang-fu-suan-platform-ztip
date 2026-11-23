from app.monitor.clock import MINUTE, local
from app.monitor.modes import active_modes


def minute_evidence(window, accepted, conflicts, intervals):
    for offset in range((window.end - window.start) // MINUTE):
        when = window.start + offset * MINUTE
        active = active_modes(intervals, when)
        reading = accepted.get(when)
        source = [reading] if reading else conflicts.get(when, [])
        base = {'utc': when.isoformat(), 'local': local(when), 'sources': source,
                'mode_sources': [row for _, row in active], 'late': bool(reading and reading['late'])}
        if active:
            yield base | {'state': 'exempt', 'code': 'EXEMPT', 'mode': active[0][0], 'value': None}
        elif not reading:
            yield base | {'state': 'missing', 'code': 'CONFLICT' if source else 'NO_READING', 'value': None}
        elif reading['fields']['status'] != 'OK' or reading['code'] != 'VALID':
            code = 'STATUS_FAULT' if reading['fields']['status'] != 'OK' else reading['code']
            yield base | {'state': 'missing', 'code': code, 'value': None}
        else:
            yield base | {'state': 'valid', 'code': 'VALID', 'value': reading['reference_raw']}
