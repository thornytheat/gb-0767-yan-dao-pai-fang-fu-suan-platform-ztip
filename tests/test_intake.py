import pytest

from app.errors import InputError
from app.monitor.reader import read_csv
from app.monitor.schema import HEADERS


def test_bom(dirty):
    # TRAP-02
    assert dirty.ledgers['minutes'][0][0]['fields']['stack'] == 'K-04'


def test_repeated_header(dirty):
    # TRAP-04
    f = dirty.intake['files'][0]
    assert (f['input'], f['parsed'], f['headers'], f['isolated']) == (109, 107, 1, 1)


def test_bad_columns(dirty):
    # TRAP-05
    assert dirty.intake['files'][0]['rejected'] == [
        {'source': 'minutes', 'line': 29, 'raw': ['K-04', 'truncated', '30', 'extra'], 'code': 'COLUMN_COUNT'}]


def test_empty_states():
    header = ','.join(HEADERS['reports'])
    assert read_csv(header, 'reports')[1]['state'] == 'header_only'
    assert read_csv(header + '\n\n', 'reports')[1]['state'] == 'no_usable_rows'
    with pytest.raises(InputError) as failure:
        read_csv('', 'reports')
    assert failure.value.code == 'EMPTY_FILE'


def test_multiline_and_reordered_headers():
    rows, _ = read_csv('ticket,value,stack,hour\r\n"R\nA",0,K,H\nR2,2,K,H', 'reports')
    assert [(x['line'], x['fields']['ticket']) for x in rows] == [(2, 'R\nA'), (4, 'R2')]


def test_sample_not_found(client):
    response = client.get('/api/samples/none/intake')
    assert (response.status_code, response.json['code']) == (404, 'SAMPLE_UNKNOWN')
