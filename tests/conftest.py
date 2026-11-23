import pytest

from app.main import create_app
from app.monitor.inspection import Inspection
from app.monitor.source import sample


@pytest.fixture(scope='session')
def dirty():
    return Inspection(sample('dirty'))


@pytest.fixture(scope='session')
def clean():
    return Inspection(sample('clean'))


@pytest.fixture
def client(tmp_path):
    return create_app(tmp_path / 'archive.sqlite').test_client()
