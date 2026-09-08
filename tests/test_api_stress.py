"""
Stress test API FASTRA - konkurensi, rate limiting, payload, autentikasi.
"""
import os
import sys
import uuid
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import api_secure
from api_secure import app, limiter


@pytest.fixture(autouse=True)
def reset_rate_limiter():
   
    limiter.store = {}
    old_max = api_secure.RATE_MAX
    old_window = api_secure.RATE_WINDOW
    api_secure.RATE_MAX = 5
    api_secure.RATE_WINDOW = 60
    yield
    api_secure.RATE_MAX = old_max
    api_secure.RATE_WINDOW = old_window
    limiter.store = {}


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def _make_wall_ccm():
    uid = str(uuid.uuid4())
    return {
        "ccm_version": "1.0.0",
        "project_uuid": str(uuid.uuid4()),
        "entities": [
            {
                "uuid": uid,
                "entity_type": "Physical",
                "type": "Wall",
                "name": "Wall Stress",
                "geometry": {
                    "axis_line": {"points": [{"x":0,"y":0,"z":0},{"x":5,"y":0,"z":0}]},
                    "height": 3.5,
                    "thickness": 0.15
                },
                "construction_type": "BATA_MERAH",
                "openings": []
            }
        ],
        "relationships": []
    }


def test_api_key_valid_and_compile(client):
    ccm = _make_wall_ccm()
    payload = {"region": "JAKARTA", "ccm": ccm}
    headers = {"X-API-Key": api_secure.API_KEY}
    resp = client.post("/estimate-rab", json=payload, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"


def test_api_key_invalid(client):
    ccm = _make_wall_ccm()
    payload = {"region": "JAKARTA", "ccm": ccm}
    headers = {"X-API-Key": "wrong-key"}
    resp = client.post("/estimate-rab", json=payload, headers=headers)
    assert resp.status_code == 401


def test_missing_api_key(client):
    ccm = _make_wall_ccm()
    payload = {"region": "JAKARTA", "ccm": ccm}
    resp = client.post("/estimate-rab", json=payload)
    assert resp.status_code == 401


def test_rate_limiter_blocks_after_limit(client):
    ccm = _make_wall_ccm()
    payload = {"region": "JAKARTA", "ccm": ccm}
    headers = {"X-API-Key": api_secure.API_KEY}
    statuses = []
    for _ in range(6):
        resp = client.post("/estimate-rab", json=payload, headers=headers)
        statuses.append(resp.status_code)
    assert 429 in statuses
    assert statuses[-1] == 429


def test_concurrent_requests(client):
    ccm = _make_wall_ccm()
    payload = {"region": "JAKARTA", "ccm": ccm}
    headers = {"X-API-Key": api_secure.API_KEY}

    def send_request(_):
        return client.post("/estimate-rab", json=payload, headers=headers).status_code

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(send_request, i) for i in range(8)]
        results = [f.result() for f in as_completed(futures)]
    assert all(code in (200, 429) for code in results)


def test_payload_too_large(client):
    large_string = "x" * 1_500_000  # 1.5 MB
    payload = {"region": "JAKARTA", "ccm": {"_large": large_string}}
    headers = {"X-API-Key": api_secure.API_KEY}
    resp = client.post("/estimate-rab", json=payload, headers=headers)
    assert resp.status_code == 413


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
