"""
API Digital Twin (ACES-600)
Endpoint FastAPI untuk snapshot, progress, VO, audit, dan archive.
Dilengkapi autentikasi API key dan rate limiter in-memory.
"""
from __future__ import annotations

import os
import time
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Depends, Request
from pydantic import BaseModel, Field

from fastra_core.digital_twin import (
    SnapshotStore, ProgressStore, ChangeOrderStore, AuditStore, ArchiveStore,
    AsBuiltStore, Snapshot, ProgressEntry, ChangeOrder, AuditEvent,
    EntityProgress, Issue, MaterialDelivery
)


app = FastAPI(title="FASTRA Digital Twin API", version="1.0.0")

# ---------------- Simulated stores (can be replaced with SQLite) ----------------
snapshot_store = SnapshotStore()
progress_store = ProgressStore()
vo_store = ChangeOrderStore()
audit_store = AuditStore()
archive_store = ArchiveStore()
as_built_store = AsBuiltStore()

# ---------------- API Key & Rate Limiter ----------------
API_KEY = os.getenv("FASTRA_DT_API_KEY", "dev-api-key")
RATE_LIMIT: Dict[str, float] = {}
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX_REQUESTS = 60

def api_key_auth(request: Request) -> str:
    key = request.headers.get("X-API-Key", "")
    if key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

def rate_limiter(request: Request) -> None:
    now = time.time()
    client_ip = request.client.host if request.client else "unknown"
    key = f"{client_ip}:{now // RATE_LIMIT_WINDOW}"
    current = RATE_LIMIT.get(key, 0)
    if current >= RATE_LIMIT_MAX_REQUESTS:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    RATE_LIMIT[key] = current + 1

# ---------------- Pydantic Models ----------------
class SnapshotCreate(BaseModel):
    project_uuid: str
    snapshot_name: str
    snapshot_type: str
    ccm_state: Dict[str, Any]
    boq_state: Optional[Dict[str, Any]] = None
    rab_state: Optional[Dict[str, Any]] = None
    schedule_state: Optional[Dict[str, Any]] = None
    description: str = ""
    timestamp: Optional[str] = None

class ProgressCreate(BaseModel):
    project_uuid: str
    report_date: str
    report_type: str
    entity_progress: List[Dict[str, Any]] = Field(default_factory=list)
    issues: List[Dict[str, Any]] = Field(default_factory=list)
    weather: Dict[str, Any] = Field(default_factory=dict)
    labor_on_site: Dict[str, int] = Field(default_factory=dict)
    material_delivered: List[Dict[str, Any]] = Field(default_factory=list)

class VOCreate(BaseModel):
    project_uuid: str
    vo_number: str
    description: str
    reason: str
    request_date: str
    requested_by: str
    ccm_changes: Dict[str, Any] = Field(default_factory=dict)
    boq_impact: Dict[str, Any] = Field(default_factory=dict)
    cost_impact: Dict[str, float] = Field(default_factory=dict)
    schedule_impact: Dict[str, Any] = Field(default_factory=dict)

class AuditQuery(BaseModel):
    project_uuid: str

# ---------------- Endpoints ----------------
@app.post("/projects/{project_uuid}/snapshots", dependencies=[Depends(api_key_auth), Depends(rate_limiter)])
def create_snapshot(project_uuid: str, payload: SnapshotCreate):
    try:
        snap = snapshot_store.create_snapshot(
            project_uuid=project_uuid,
            snapshot_name=payload.snapshot_name,
            snapshot_type=payload.snapshot_type,
            ccm_state=payload.ccm_state,
            boq_state=payload.boq_state,
            rab_state=payload.rab_state,
            schedule_state=payload.schedule_state,
            description=payload.description,
            timestamp=payload.timestamp,
        )
        audit_store.record_event(
            event_type="SNAPSHOT_CREATED",
            actor={"user_name": "API"},
            target={"entity_uuid": snap.snapshot_uuid},
            timestamp=snap.timestamp,
            metadata={"project_uuid": project_uuid},
        )
        return {"status": "success", "snapshot_uuid": snap.snapshot_uuid}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/projects/{project_uuid}/snapshots", dependencies=[Depends(api_key_auth), Depends(rate_limiter)])
def list_snapshots(project_uuid: str):
    snaps = snapshot_store.get_all_snapshots(project_uuid)
    return {"snapshots": [s.to_dict() for s in snaps]}

@app.post("/projects/{project_uuid}/progress", dependencies=[Depends(api_key_auth), Depends(rate_limiter)])
def create_progress(project_uuid: str, payload: ProgressCreate):
    try:
        entry = ProgressEntry(
            project_uuid=project_uuid,
            report_date=payload.report_date,
            report_type=payload.report_type,
            entity_progress=[EntityProgress(**ep) for ep in payload.entity_progress],
            issues=[Issue(**iss) for iss in payload.issues],
            weather=payload.weather,
            labor_on_site=payload.labor_on_site,
            material_delivered=[MaterialDelivery(**md) for md in payload.material_delivered],
        )
        progress_store.add_entry(entry)
        audit_store.record_event(
            event_type="PROGRESS_REPORTED",
            actor={"user_name": "API"},
            target={"entity_uuid": entry.progress_entry_uuid},
            metadata={"project_uuid": project_uuid},
        )
        return {"status": "success", "progress_entry_uuid": entry.progress_entry_uuid}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/projects/{project_uuid}/progress", dependencies=[Depends(api_key_auth), Depends(rate_limiter)])
def list_progress(project_uuid: str):
    entries = progress_store.get_entries(project_uuid)
    return {"entries": [e.__dict__ for e in entries]}

@app.post("/projects/{project_uuid}/vos", dependencies=[Depends(api_key_auth), Depends(rate_limiter)])
def create_vo(project_uuid: str, payload: VOCreate):
    try:
        vo = ChangeOrder(
            project_uuid=project_uuid,
            vo_number=payload.vo_number,
            description=payload.description,
            reason=payload.reason,
            request_date=payload.request_date,
            requested_by=payload.requested_by,
            ccm_changes=payload.ccm_changes,
            boq_impact=payload.boq_impact,
            cost_impact=payload.cost_impact,
            schedule_impact=payload.schedule_impact,
        )
        vo_store.add_vo(vo)
        audit_store.record_event(
            event_type="VO_CREATED",
            actor={"user_name": "API"},
            target={"entity_uuid": vo.vo_uuid},
            related_vo=vo.vo_number,
            metadata={"project_uuid": project_uuid},
        )
        return {"status": "success", "vo_uuid": vo.vo_uuid}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/projects/{project_uuid}/audit", dependencies=[Depends(api_key_auth), Depends(rate_limiter)])
def list_audit(project_uuid: str):
    events = [e.to_dict() for e in audit_store.get_all_events() if e.metadata.get("project_uuid") == project_uuid or e.target.get("project_uuid") == project_uuid]
    return {"events": events}

@app.post("/projects/{project_uuid}/archive", dependencies=[Depends(api_key_auth), Depends(rate_limiter)])
def create_archive(project_uuid: str):
    try:
        archive = archive_store.create_archive(
            project_uuid=project_uuid,
            snapshot_store=snapshot_store,
            as_built_store=as_built_store,
            audit_store=audit_store,
        )
        return {"status": "success", "archive_uuid": archive.archive_uuid}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/health", dependencies=[Depends(rate_limiter)])
def health():
    return {"status": "ok"}
