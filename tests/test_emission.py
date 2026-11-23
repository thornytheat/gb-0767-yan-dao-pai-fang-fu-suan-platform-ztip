from dataclasses import replace
from decimal import Decimal

from app.monitor.clock import MINUTE
from app.monitor.emission import account
from app.monitor.flow import choose_flows
from app.monitor.source import sample


def flow_row(line, timestamp, value, unit='Nm3/min', received=None):
    fields = {'stack': 'K-04', 'timestamp': timestamp, 'value': str(value),
              'unit': unit, 'received': received or timestamp}
    return {'source': 'flows', 'line': line, 'raw': list(fields.values()), 'fields': fields}


def valid_hour(count=60, dry=30):
    rows = [{'state': 'valid', 'code': 'VALID', 'late': False, 'dry': Decimal(dry)}] * count
    return rows + [{'state': 'missing', 'code': 'NO_READING', 'late': False}] * (60 - count)


def flows_for(window, minutes, nm3_min):
    return {window.start + m * MINUTE: {'nm3_min': Decimal(nm3_min)} for m in minutes}


def test_partial_excess_is_exceeded(dirty):
    # 已测 40 分钟合计 2.936 kg 已超 2.500 kg/h，其余 12 分钟缺数不补零，仍判超限
    e = dirty.hours['rows'][0]['emission']
    assert (e['code'], e['accounted'], e['pending'], e['exempt']) == ('EXCEEDED', 40, 12, 8)
    assert (e['kg'], e['limit_kg']) == ('2.936', '2.500')
    assert '只增不减' in e['basis']


def test_short_of_limit_with_gaps_is_pending(dirty):
    # 已测 44 分钟合计 1.980 kg 未超限，但 16 分钟缺数，暂不判达标
    e = dirty.hours['rows'][1]['emission']
    assert (e['code'], e['accounted'], e['pending']) == ('PENDING', 44, 16)
    assert e['kg'] == '1.980'


def test_full_coverage_is_compliant(clean):
    assert [row['emission']['code'] for row in clean.hours['rows']] == ['COMPLIANT', 'COMPLIANT']


def test_zero_flow_is_accounted_not_pending(clean):
    # 实测零流量是有效读数，参与核算；只有缺测才记缺数
    e = clean.hours['rows'][1]['emission']
    assert (e['accounted'], e['pending'], e['kg']) == (60, 0, '1.800')


def test_missing_flow_is_not_zero_filled(clean):
    # 若把 30 个缺测分钟补零，0.900 kg 会被误判达标；正确判定是缺数待判
    e = account(valid_hour(), flows_for(clean.window, range(30), 1000), clean.window)[0]
    assert (e['code'], e['accounted'], e['pending'], e['kg']) == ('PENDING', 30, 30, '0.900')


def test_lower_bound_excess_needs_no_backfill(clean):
    # 40 个已测分钟已合计 3.600 kg，其余 20 分钟缺数只增不减
    e = account(valid_hour(), flows_for(clean.window, range(40), 3000), clean.window)[0]
    assert (e['code'], e['pending']) == ('EXCEEDED', 20)


def test_all_exempt_hour(clean):
    rows = [{'state': 'exempt', 'code': 'EXEMPT', 'late': False}] * 60
    e = account(rows, {}, clean.window)[0]
    assert (e['code'], e['accounted'], e['exempt']) == ('EXEMPT', 0, 60)


def test_limit_boundary_is_strict(clean):
    window = replace(clean.window, emission_limit=Decimal('1.5'))
    e = account(valid_hour(dry=25), flows_for(window, range(60), 1000), window)[0]
    assert (e['code'], e['kg']) == ('COMPLIANT', '1.500')


def test_verdict_uses_full_precision_not_display(clean):
    # 合计 2.5004 kg 显示为 2.500 kg，判定仍按完整精度超限
    rows = valid_hour(1, dry=25004)
    e = account(rows, flows_for(clean.window, [0], 100), clean.window)[0]
    assert (e['code'], e['kg']) == ('EXCEEDED', '2.500')


def test_flow_unit_conversion(clean):
    selected, _ = choose_flows([flow_row(1, '2026-11-14T00:05Z', 90000, 'Nm3/h')], clean.window)
    assert selected[clean.window.start + 5 * MINUTE]['nm3_min'] == 1500


def test_flow_duplicate_and_conflict(clean):
    rows = [flow_row(1, '2026-11-14T00:05Z', 100, received='2026-11-14T00:06Z'),
            flow_row(2, '2026-11-14T00:05Z', 100, received='2026-11-14T00:07Z'),
            flow_row(3, '2026-11-14T00:06Z', 100),
            flow_row(4, '2026-11-14T00:06Z', 101)]
    selected, isolated = choose_flows(rows, clean.window)
    assert list(selected) == [clean.window.start + 5 * MINUTE]
    assert [(r['line'], r['code']) for r in isolated] == [(2, 'DUPLICATE'), (3, 'CONFLICT'), (4, 'CONFLICT')]


def test_flow_rejection_reasons(clean):
    rows = [flow_row(1, '2026-11-14T00:05Z', 100, 'm3/h'),
            flow_row(2, '2026-11-14T00:06Z', 100, received='2026-11-14T00:05Z'),
            flow_row(3, '2026-11-14T00:07Z', 100, received='2026-11-14T04:01Z'),
            flow_row(4, '2026-11-14T00:08Z', -1)]
    selected, isolated = choose_flows(rows, clean.window)
    assert selected == {}
    assert [r['code'] for r in isolated] == ['BAD_FLOW_UNIT', 'BAD_RECEIVED', 'AFTER_CUTOFF', 'NEGATIVE']


def test_sample_flow_isolation(dirty):
    assert [(r['line'], r['code']) for r in dirty.hours['flows_isolated']] == [
        (42, 'DUPLICATE'), (43, 'CONFLICT'), (44, 'CONFLICT'), (45, 'AFTER_CUTOFF')]


def test_backfill_recalculates_and_original_stays_archived(client):
    files = sample('dirty')
    first = client.post('/api/runs', json={'files': files}).json
    backfilled = files | {'flows': files['flows'].replace('2026-11-14T04:05Z', '2026-11-14T00:37Z')}
    second = client.post('/api/runs', json={'files': backfilled}).json
    assert first['run_id'] != second['run_id']
    original = client.get(f"/api/runs/{first['run_id']}/hours").json['rows'][0]['emission']
    recalced = client.get(f"/api/runs/{second['run_id']}/hours").json['rows'][0]['emission']
    assert (original['code'], original['accounted'], original['pending']) == ('EXCEEDED', 40, 12)
    assert (recalced['code'], recalced['accounted'], recalced['pending']) == ('EXCEEDED', 41, 11)
    retry = client.post('/api/runs', json={'files': backfilled}).json
    assert (retry['run_id'], retry['reused']) == (second['run_id'], True)
    assert len(client.get('/api/runs').json['runs']) == 2
