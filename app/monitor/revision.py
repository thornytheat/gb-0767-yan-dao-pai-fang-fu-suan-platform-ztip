from collections import defaultdict
from datetime import timedelta

from app.monitor.clock import instant, minute

MEASURES = ('value', 'unit', 'basis', 'moisture', 'oxygen', 'status')


def choose(rows, window):
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
            revision = fields['revision']
            if not revision.isascii() or not revision.isdecimal() or len(revision) > 6 or received < when:
                raise ValueError('BAD_REVISION')
        except ValueError as error:
            isolated.append(row | {'code': str(error)})
            continue
        by_minute[when].append((int(revision), received, row))

    selected = {}
    conflicts = {}
    for when, candidates in sorted(by_minute.items()):
        top = max(item[0] for item in candidates)
        active = sorted((item for item in candidates if item[0] == top), key=lambda x: (x[1], x[2]['line']))
        older = [row | {'code': 'SUPERSEDED'} for rev, _, row in candidates if rev < top]
        isolated.extend(older)
        signatures = {tuple(item[2]['fields'][key] for key in MEASURES) for item in active}
        if len(signatures) > 1:
            conflicts[when] = [row | {'code': 'CONFLICT'} for _, _, row in active]
            isolated.extend(conflicts[when])
            continue
        _, received, row = active[0]
        selected[when] = row | {'late': received - when > timedelta(minutes=5), 'revision': top}
        isolated.extend(row | {'code': 'DUPLICATE'} for _, _, row in active[1:])
    return selected, conflicts, sorted(isolated, key=lambda row: row['line'])
