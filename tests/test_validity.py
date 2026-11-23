from app.monitor.clock import minute
from app.monitor.modes import mode_windows
from app.monitor.validity import minute_evidence


def test_shared_zone_conversion(dirty):
    # TRAP-11
    assert minute('2026-11-14T08:03+08:00') == minute('2026-11-14T00:03Z')
    row = dirty.validity['rows'][3]
    assert (row['local'], row['utc']) == ('11-14 08:03', '2026-11-14T00:03:00+00:00')


def test_overlap_priority(dirty):
    # TRAP-19
    selected, conflict, _ = dirty.corrected
    rows = dirty.ledgers['modes'][0]
    for records in (rows, rows[::-1]):
        intervals, _ = mode_windows(records, dirty.window)
        r = list(minute_evidence(dirty.window, selected, conflict, intervals))[3]
        assert (r['state'], r['mode'], [s['line'] for s in r['mode_sources']]) == ('exempt','SHUTDOWN',[3,2])


def test_half_open(dirty):
    # TRAP-23
    assert [r['state'] for r in dirty.validity['rows'][7:9]] == ['exempt', 'valid']


def test_no_record(dirty):
    r = dirty.validity['rows'][12]
    assert (r['code'],r['sources']) == ('NO_READING', [])


def test_status_fault(dirty):
    r = dirty.validity['rows'][18]
    assert (r['state'],r['code'],r['value']) == ('missing','STATUS_FAULT',None)


def test_isolated_mode(dirty):
    assert [(r['line'],r['code']) for r in dirty.validity['isolated_modes']] == [(4,'BAD_MODE')]
