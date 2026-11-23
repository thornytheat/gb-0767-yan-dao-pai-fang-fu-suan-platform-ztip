from app.monitor.reconcile import compare


def test_discrepancy(dirty):
    row = dirty.reports['rows'][0]
    assert (row['code'], row['difference_mg_nm3'], row['reports'][0]['fields']['ticket']) == ('DEVIATION','0.75','R-801')


def test_no_comparable_hour(dirty):
    row = dirty.reports['rows'][1]
    assert (row['code'], row['reported_mg_nm3'], row['difference_mg_nm3']) == ('NO_REFERENCE','31.00',None)


def test_end_report_outside(dirty):
    assert [(r['line'],r['code']) for r in dirty.reports['isolated']] == [(4,'OUTSIDE_REPORT')]


def test_equal_tolerance(clean):
    row = clean.ledgers['reports'][0][0]
    reports = [row | {'fields': row['fields'] | {'value':'29.50'}}]
    result,_ = compare(clean.hours['rows'],reports,clean.window)
    assert [(r['code'],r['difference_mg_nm3']) for r in result] == [('MATCH','0.50'),('NO_REPORT',None)]


def test_conflicting_reports(clean):
    row = clean.ledgers['reports'][0][0]
    result,_ = compare(clean.hours['rows'],[row,row | {'line':11,'fields':row['fields'] | {'value':'31'}}],clean.window)
    assert (result[0]['code'],[r['line'] for r in result[0]['reports']]) == ('REPORT_CONFLICT',[2,11])


def test_clean_agreement(clean):
    assert clean.reports['deviations'] == 0
    assert [r['code'] for r in clean.reports['rows']] == ['MATCH','MATCH']
