"""
Test API Digital Twin Secure untuk endpoint VO, As-Built, dan Archive.
"""
import pytest
from fastapi.testclient import TestClient
from api_digital_twin_secure import app

client = TestClient(app)

def login(username: str, password: str) -> str:
    resp = client.post("/token", data={"username": username, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]

def test_create_list_vo():
    token = login("qs", "qs123")
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "project_uuid": "proj-p1",
        "vo_number": "VO-001",
        "description": "Penambahan kanopi",
        "reason": "Permintaan owner",
        "request_date": "2026-08-24",
        "requested_by": "Owner",
    }
    resp = client.post("/projects/proj-p1/vos", json=payload, headers=headers)
    assert resp.status_code == 200
    vo_uuid = resp.json()["vo_uuid"]

    # list
    resp = client.get("/projects/proj-p1/vos", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()["vos"]) >= 1

    # get
    resp = client.get(f"/vos/{vo_uuid}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["vo_number"] == "VO-001"

def test_approve_vo_admin():
    token_qs = login("qs", "qs123")
    headers_qs = {"Authorization": f"Bearer {token_qs}"}
    payload = {
        "project_uuid": "proj-p1",
        "vo_number": "VO-002",
        "description": "Perubahan material",
        "reason": "VE",
        "request_date": "2026-08-24",
        "requested_by": "QS",
    }
    resp = client.post("/projects/proj-p1/vos", json=payload, headers=headers_qs)
    vo_uuid = resp.json()["vo_uuid"]

    token_admin = login("admin", "admin123")
    headers_admin = {"Authorization": f"Bearer {token_admin}"}
    resp = client.post(f"/vos/{vo_uuid}/approve", headers=headers_admin)
    assert resp.status_code == 200
    assert resp.json()["new_status"] == "APPROVED"

def test_create_list_as_built():
    token = login("qs", "qs123")
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "project_uuid": "proj-p1",
        "entity_uuid": "wall-001",
        "planned_state": {"length": 5.0},
        "as_built_state": {"length": 5.1},
    }
    resp = client.post("/projects/proj-p1/as-built", json=payload, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["differences"] == 1

    resp = client.get("/projects/proj-p1/as-built", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()["records"]) >= 1

def test_create_list_archive():
    token = login("admin", "admin123")
    headers = {"Authorization": f"Bearer {token}"}
    # create snapshot first
    snap_payload = {
        "project_uuid": "proj-p1",
        "snapshot_name": "For Archive",
        "snapshot_type": "CHECKPOINT",
        "ccm_state": {"entities": {}},
    }
    client.post("/projects/proj-p1/snapshots", json=snap_payload, headers=headers)

    resp = client.post("/projects/proj-p1/archive", headers=headers)
    assert resp.status_code == 200
    archive_uuid = resp.json()["archive_uuid"]

    resp = client.get("/projects/proj-p1/archives", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()["archives"]) >= 1
