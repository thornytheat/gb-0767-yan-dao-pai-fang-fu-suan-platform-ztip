from collections import Counter
from decimal import localcontext

from app.monitor.clock import HOUR, local
from app.numbers import display


def aggregate(minutes, window):
    result = []
    for index in range(0, len(minutes), 60):
        hour = window.start + (index // 60) * HOUR
        items = minutes[index:index + 60]
        counts = Counter(item['state'] for item in items)
        values = [item['value'] for item in items if item['state'] == 'valid']
        state = 'EXEMPT' if counts['exempt'] == 60 else 'VALID' if len(values) >= window.threshold else 'INSUFFICIENT'
        with localcontext() as ctx:
            ctx.prec = 40
            average = sum(values) / len(values) if state == 'VALID' else None
        result.append({'hour': hour.isoformat(), 'local': local(hour), 'scheduled': len(items),
                       'valid': counts['valid'], 'exempt': counts['exempt'], 'missing': counts['missing'],
                       'late': sum(item['late'] for item in items if item['state'] == 'valid'),
                       'status': state, 'threshold': window.threshold,
                       'mg_nm3': None if average is None else display(average),
                       'quality': dict(Counter(item['code'] for item in items))})
    return result
