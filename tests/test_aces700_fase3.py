"""
Compliance tests untuk ACES-700 Fase 3 + Hardening API Secure
"""
import pytest
from fastapi.testclient import TestClient
from api_ai import app

client = TestClient(app)

def login(username, password):
    resp = client.post("/v1/token", data={"username": username, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]

def test_health():
    resp = client.get("/v1/health")
    assert resp.status_code == 200

def test_vision_process():
    token = login("admin", "admin123")
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "model_version": "fastra-vision-v1.2.0",
        "input_photos": ["photo-001"],
        "estimations": {
            "building_type": {"value": "HOUSE", "confidence": 0.92},
            "estimated_area": {"value": 145.0, "confidence": 0.65},
        },
    }
    resp = client.post("/v1/ai/vision", json=payload, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["result_uuid"]
    assert data["event_uuid"]
    assert data["verification"]["needs_human_review"] is True

def test_vision_threshold_flag():
    token = login("admin", "admin123")
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "model_version": "fastra-vision-v1.2.0",
        "input_photos": ["photo-001"],
        "estimations": {
            "estimated_area": {"value": 145.0, "confidence": 0.30},
        },
    }
    resp = client.post("/v1/ai/vision", json=payload, headers=headers)
    assert resp.status_code == 200
    verification = resp.json()["verification"]
    assert verification["status"] == "FLAGGED_HIGH_UNCERTAINTY"
    assert verification["passed"] is False

def test_llm_no_direct_boq():
    token = login("qs", "qs123")
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "model_version": "fastra-llm-v1.0",
        "input_text": "Buatkan BOQ rumah",
        "output_dsl": "BOQ ITEM PEK.DIND.001 QUANTITY 100 UNIT m2",
        "references": ["ACES-300-001"],
    }
    resp = client.post("/v1/ai/llm", json=payload, headers=headers)
    assert resp.status_code == 400  # ditolak

def test_translate_to_dsl():
    token = login("qs", "qs123")
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.post("/v1/ai/translate", json={"text": "Rumah 2 lantai luas 150m² di Bandung"}, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "CREATE BUILDING TYPE HOUSE" in data["dsl_text"]

def test_ai_audit_records():
    token = login("admin", "admin123")
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.get("/v1/ai/audit", headers=headers)
    assert resp.status_code == 200
    events = resp.json()["events"]
    assert len(events) >= 1
