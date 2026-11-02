import importlib
import os
import pytest
from fastapi.testclient import TestClient

@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv('CONTROL_TOWER_API_KEY','A_VALID_TEST_ONLY_SECRET_1234567890123456789')
    monkeypatch.setenv('ALLOWED_HOSTS','localhost,127.0.0.1,testserver')
    import app.main
    importlib.reload(app.main)
    return TestClient(app.main.app)

def test_unauthorized(client):
    r = client.get('/api/dashboard')
    assert r.status_code == 401
    assert r.headers['cache-control'] == 'no-store'

def test_valid_api_key(client):
    r = client.get('/api/dashboard',headers={'X-API-Key':'A_VALID_TEST_ONLY_SECRET_1234567890123456789'})
    assert r.status_code == 200
    assert r.json()['overview']['orders_total']==12
    assert "default-src 'none'" in r.headers['content-security-policy']

def test_invalid_key(client):
    assert client.get('/api/alerts',headers={'X-API-Key':'bad'}).status_code==401

def test_public_page_and_health(client):
    assert client.get('/').status_code == 200
    assert client.get('/health').json()['status']=='ok'
