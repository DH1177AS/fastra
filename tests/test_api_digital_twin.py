"""
Test API Digital Twin (ACES-600 hardening).
"""
import pytest
from fastapi.testclient import TestClient
from api_digital_twin import app

client = TestClient(app)
API_KEY = "dev-api-key"
HEADERS = {"X-API-Key": API_KEY}


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_create_snapshot_success():
    payload = {
        "project_uuid": "proj-api-001",
        "snapshot_name": "API Snapshot",
        "snapshot_type": "CHECKPOINT",
        "ccm_state": {"entities": {"wall-001": {"length": 5.0}}},
    }
    resp = client.post("/projects/proj-api-001/snapshots", json=payload, headers=HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["snapshot_uuid"] is not None


def test_list_snapshots():
    resp = client.get("/projects/proj-api-001/snapshots", headers=HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["snapshots"]) >= 1


def test_invalid_api_key():
    resp = client.post("/projects/proj-api-001/snapshots", json={}, headers={"X-API-Key": "wrong-key"})
    assert resp.status_code == 401


def test_create_progress():
    payload = {
        "project_uuid": "proj-api-001",
        "report_date": "2026-08-24",
        "report_type": "WEEKLY",
        "entity_progress": [
            {"entity_uuid": "wall-001", "entity_name": "Dinding", "work_item_code": "PEK.DIND.001",
             "planned_quantity": 100.0, "completed_quantity": 50.0, "unit": "m²", "status": "IN_PROGRESS"}
        ],
    }
    resp = client.post("/projects/proj-api-001/progress", json=payload, headers=HEADERS)
    assert resp.status_code == 200
    assert resp.json()["status"] == "success"


def test_audit_records_api_events():
    resp = client.get("/projects/proj-api-001/audit", headers=HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["events"]) >= 2  # snapshot + progress events
