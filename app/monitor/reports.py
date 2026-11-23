from collections import defaultdict

from app.monitor.clock import minute
from app.numbers import number


def index_reports(records, window):
    reports = defaultdict(list)
    isolated = []
    for row in records:
        fields = row['fields']
        try:
            hour = minute(fields['hour'])
            if fields['stack'] != window.stack:
                raise ValueError('WRONG_STACK')
            if hour.minute:
                raise ValueError('BAD_TIME')
            value = number(fields['value'])
            if value < 0:
                raise ValueError('NEGATIVE')
        except ValueError as error:
            isolated.append(row | {'code': str(error)})
            continue
        reports[hour.isoformat()].append(row | {'amount': value})
    return reports, isolated
