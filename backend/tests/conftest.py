import os
import tempfile
from pathlib import Path
os.environ['MODE']='fixture'
os.environ['DATABASE_URL']='sqlite:///'+str(Path(tempfile.mkdtemp(prefix='eventops-tests-'))/'test.sqlite')
os.environ['DEMO_PASSWORD']='test-secret-for-fixtures'
os.environ['WORKER_ENABLED']='false'
from app.db import initialize, DB, Base, engine
import pytest
@pytest.fixture(autouse=True)
def reset_database():
    Base.metadata.drop_all(engine);initialize()
    yield
@pytest.fixture
def db():
    with DB() as session: yield session
@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    from app.main import app
    with TestClient(app) as c:
        c.headers['origin']='http://localhost:5173'
        yield c
@pytest.fixture
def signed_in(client):
    assert client.post('/api/session',json={'username':'operator','password':'test-secret-for-fixtures'}).status_code==200
    return client
