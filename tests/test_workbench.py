from app.web import PAGES


def test_all_monitor_pages_have_server_rendered_evidence(client):
    assert '分钟有效性矩阵' in client.get('/').get_data(as_text=True)
    for slug,label in PAGES.items():
        response = client.get('/monitor/'+slug)
        assert response.status_code == 200, slug
        assert f'<h1>{label}</h1>' in response.get_data(as_text=True)


def test_export_link_after_archival(client):
    run_id = client.post('/api/runs',json={'sample':'dirty'}).json['run_id']
    page = client.get('/monitor/evidence?run='+run_id).get_data(as_text=True)
    assert f'/api/export/{run_id}' in page
    assert '分钟勾稽差额 <b>0</b>' in page
