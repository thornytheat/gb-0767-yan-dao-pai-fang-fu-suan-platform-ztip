from decimal import Decimal

import pytest

from app.monitor.oxygen import correct


def test_units(clean):
    # TRAP-15
    assert {r['fields']['unit'] for r in clean.oxygen['rows'][:4]} == {'mg/Nm3','g/Nm3','µg/Nm3'}
    assert [r['reference_mg_nm3'] for r in clean.oxygen['rows'][:4]] == ['30.00'] * 4


def test_sentinel(dirty):
    # TRAP-07
    assert [(r['fields']['value'], r['reference_mg_nm3']) for r in dirty.oxygen['isolated']
            if r['code'] == 'MISSING_NUMBER'] == [('NULL', None)]


def test_bad_oxygen(dirty):
    bad = next(r for r in dirty.oxygen['isolated'] if r['code'] == 'BAD_OXYGEN')
    assert (bad['fields']['oxygen'], bad['reference_mg_nm3']) == ('21', None)


def test_nontrivial_wet_and_oxygen_conversion():
    fields = {'unit': 'mg/Nm3', 'basis': 'wet', 'value': '30', 'moisture': '25', 'oxygen': '11'}
    assert correct(fields, Decimal(10)) == (Decimal(40), Decimal(44))


def test_true_conflict_does_not_pick_last(dirty):
    # TRAP-14
    candidates = [r for r in dirty.oxygen['isolated'] if r['code'] == 'CONFLICT']
    assert [r['fields']['value'] for r in candidates] == ['0.03', '31']
    assert all(not r['utc'].endswith('00:17:00+00:00') for r in dirty.oxygen['rows'])


def test_boundaries_and_bad_unit():
    fields = {'unit': 'lb', 'basis': 'wet', 'value': '30', 'moisture': '100', 'oxygen': '0'}
    with pytest.raises(ValueError, match='BAD_UNIT'):
        correct(fields, Decimal(10))
    with pytest.raises(ValueError, match='BAD_MOISTURE'):
        correct(fields | {'unit':'mg/Nm3'}, Decimal(10))


def test_version_and_cutoff(dirty):
    # TRAP-13
    rows = {r['utc'][11:16]: r for r in dirty.oxygen['rows']}
    assert (rows['00:20']['revision'], rows['00:20']['reference_mg_nm3'], rows['00:20']['late']) == (2, '53.50', True)
    assert rows['01:43']['revision'] == 1
    assert any(r['code'] == 'AFTER_CUTOFF' and r['fields']['value'] == '200' for r in dirty.oxygen['isolated'])
