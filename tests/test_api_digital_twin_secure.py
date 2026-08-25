"""
Test API Digital Twin Secure (JWT OAuth2 & RBAC).
"""
import pytest
from fastapi.testclient import TestClient
from api_digital_twin_secure import app

client = TestClient(app)


def login(username: str, password: str) -> str:
    resp = client.post("/token", data={"username": username, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def test_health_public():
    resp = client.get("/health")
    assert resp.status_code == 200


def test_login_success():
    token = login("admin", "admin123")
    assert token is not None


def test_login_fail():
    resp = client.post("/token", data={"username": "admin", "password": "wrong"})
    assert resp.status_code == 401


def test_admin_can_create_snapshot():
    token = login("admin", "admin123")
    payload = {
        "project_uuid": "proj-secure-001",
        "snapshot_name": "Secure Snapshot",
        "snapshot_type": "CHECKPOINT",
        "ccm_state": {"entities": {"wall-001": {"length": 5.0}}},
    }
    resp = client.post(
        "/projects/proj-secure-001/snapshots",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "success"


def test_viewer_cannot_create_snapshot():
    token = login("viewer", "viewer123")
    payload = {
        "project_uuid": "proj-secure-001",
        "snapshot_name": "Forbidden",
        "snapshot_type": "CHECKPOINT",
        "ccm_state": {},
    }
    resp = client.post(
        "/projects/proj-secure-001/snapshots",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


def test_qs_can_create_progress():
    token = login("qs", "qs123")
    payload = {
        "project_uuid": "proj-secure-001",
        "report_date": "2026-08-24",
        "report_type": "WEEKLY",
        "entity_progress": [],
    }
    resp = client.post(
        "/projects/proj-secure-001/progress",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "success"
