from dataclasses import replace
from decimal import Decimal

from app.monitor.hours import aggregate


def test_decimal_hour(dirty):
    # TRAP-10: 46 readings of 30 and one of 53.50.
    assert dirty.hours['rows'][0]['mg_nm3'] == '30.50'


def test_threshold_is_inclusive(dirty):
    assert aggregate(dirty.validity['rows'],replace(dirty.window,threshold=44))[1]['mg_nm3'] == '30.00'


def test_threshold_not_scaled_by_exemption(dirty):
    r = aggregate(dirty.validity['rows'],replace(dirty.window,threshold=48))[0]
    assert (r['exempt'], r['status'], r['mg_nm3']) == (8,'INSUFFICIENT',None)


def test_all_exempt(clean):
    r = aggregate([{'state':'exempt','code':'EXEMPT','late':False}]*60,clean.window)[0]
    assert (r['exempt'],r['status']) == (60,'EXEMPT')


def test_unrounded_minutes(clean):
    rows = [{'state':'valid','code':'VALID','late':False,'value':Decimal('1.0049')}] * 59
    rows += [rows[0] | {'value':Decimal('1.0149')}]
    assert aggregate(rows, clean.window)[0]['mg_nm3'] == '1.01'


def test_minute_conservation(dirty):
    assert dirty.hours['totals'] == {'scheduled':120,'valid':91,'exempt':8,'missing':21,'late':2}
    assert all(h['scheduled'] == h['valid']+h['exempt']+h['missing'] for h in dirty.hours['rows'])
