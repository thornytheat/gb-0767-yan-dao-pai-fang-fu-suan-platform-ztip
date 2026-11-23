from concurrent.futures import ThreadPoolExecutor

from app.archive.run import archive_run
from app.archive.store import Archive
from app.main import create_app
from app.monitor.source import sample


def test_replay_preserves_manifest(client):
    body = {'sample':'dirty'}
    a,b = (client.post('/api/runs',json=body).json for _ in range(2))
    assert [a['reused'],b['reused']] == [False,True]
    assert a['manifest'] == b['manifest']
    assert len(client.get('/api/runs').json['runs']) == 1


def test_rollback_bad_header(client):
    corrupt = sample('dirty') | {'reports':'bad,header'}
    response = client.post('/api/runs',json={'files':corrupt})
    assert (response.status_code,response.json['code']) == (422,'BAD_HEADER')
    assert client.get('/api/runs').json == {'runs':[]}


def test_two_workers_insert_once(tmp_path):
    store = Archive(tmp_path / 'a.sqlite')
    with ThreadPoolExecutor(2) as pool:
        outcomes = list(pool.map(lambda _: archive_run(store,{'sample':'dirty'}), range(2)))
    assert sorted(flag for _,flag in outcomes) == [False,True]
    assert outcomes[0][0] == outcomes[1][0]


def test_restart_stability(tmp_path):
    path = tmp_path / 'persist.sqlite'
    first = create_app(path).test_client()
    identifier = first.post('/api/runs',json={'sample':'dirty'}).json['run_id']
    route = f'/api/runs/{identifier}/reports'
    assert create_app(path).test_client().get(route).data == first.get(route).data


def test_changed_content_separate_batch(client):
    files = sample('clean')
    a = client.post('/api/runs',json={'files':files}).json
    b = client.post('/api/runs',json={'files':files | {'reports':files['reports']+'\r\n'}}).json
    assert a['run_id'] != b['run_id']
    assert len(client.get('/api/runs').json['runs']) == 2


def test_bad_packet_recoverable(client):
    assert client.post('/api/runs',json={'files':{}}).json['code'] == 'BAD_PACKET'
    assert client.post('/api/runs',json={'sample':'clean'}).json['totals']['valid'] == 116
