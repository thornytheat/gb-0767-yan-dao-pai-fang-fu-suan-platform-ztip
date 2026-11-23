from decimal import Decimal

from app.monitor.reports import index_reports
from app.numbers import display


def compare(hours, records, window):
    reports, isolated = index_reports(records, window)
    result = []
    for hour in hours:
        sources = reports.pop(hour['hour'], [])
        amounts = {row['amount'] for row in sources}
        reported = next(iter(amounts)) if len(amounts) == 1 else None
        difference = None
        if len(amounts) > 1:
            code = 'REPORT_CONFLICT'
        elif reported is None:
            code = 'NO_REPORT'
        elif hour['mg_nm3'] is None:
            code = 'NO_REFERENCE'
        else:
            difference = Decimal(hour['mg_nm3']) - Decimal(display(reported))
            code = 'MATCH' if abs(difference) <= window.tolerance else 'DEVIATION'
        result.append(hour | {'code': code, 'reported_mg_nm3': None if reported is None else display(reported),
                              'difference_mg_nm3': None if difference is None else display(difference), 'reports': sources})
    for excess in reports.values():
        isolated.extend(row | {'code': 'OUTSIDE_REPORT'} for row in excess)
    return result, isolated
