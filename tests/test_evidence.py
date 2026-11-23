from copy import deepcopy
from hashlib import sha256

import pytest

from app.archive.certificate import issue
from app.archive.manifest import canonical
from app.errors import InputError


@pytest.fixture
def exported(client):
    run = client.post('/api/runs',json={'sample':'dirty'}).json['run_id']
    return client.get('/api/export/'+run)


def test_download_contract(exported):
    assert exported.headers['Content-Disposition'].startswith('attachment; filename="monitor-')
    assert (exported.json['certificate'],exported.json['minute_balance']) == ('监测证据单',0)


def test_digest_independently_recalculable(exported):
    result = exported.json
    payload = {key:result[key] for key in ('manifest','originals','results')}
    assert result['sha256'] == sha256(canonical(payload).encode()).hexdigest()
    assert result['manifest']['sha256']['minutes'] == sha256(result['originals']['minutes'].encode()).hexdigest()


def test_evidence_preserves_source(exported):
    verdict = exported.json['results']['validity']['rows'][17]
    assert (verdict['code'],[r['line'] for r in verdict['sources']]) == ('CONFLICT',[18,19])


def test_tampered_file_rejected(exported):
    packet = deepcopy(exported.json)
    packet['originals']['minutes'] += 'garbage'
    with pytest.raises(InputError) as failure:
        issue(packet)
    assert failure.value.code == 'EVIDENCE_MISMATCH'


def test_unbalanced_file_rejected(exported):
    packet = deepcopy(exported.json)
    packet['results']['hours']['totals']['missing'] -= 1
    with pytest.raises(InputError) as failure:
        issue(packet)
    assert failure.value.code == 'EVIDENCE_UNBALANCED'


def test_missing_batch_never_downloads(client):
    r = client.get('/api/export/not-archived')
    assert (r.status_code,r.json['code'],r.headers.get('Content-Disposition')) == (404,'RUN_UNKNOWN',None)
