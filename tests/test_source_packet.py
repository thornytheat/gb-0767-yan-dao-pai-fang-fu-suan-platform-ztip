import json

from app.monitor.source import sample


def test_semantically_bad_window_is_atomic(client):
    files = sample('dirty')
    window = json.loads(files['window']) | {'threshold':0}
    response = client.post('/api/runs',json={'files':files | {'window':json.dumps(window)}})
    assert (response.status_code,response.json['code']) == (422,'BAD_WINDOW')
    assert client.get('/api/runs').json == {'runs':[]}


def test_clean_and_dirty_preview_use_same_endpoint(client):
    rows = [client.get(f'/api/samples/{name}/hours').json['rows'][1]['status'] for name in ('clean','dirty')]
    assert rows == ['VALID','INSUFFICIENT']
