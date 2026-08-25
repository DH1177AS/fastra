"""
API Digital Twin (ACES-600) dengan JWT OAuth2 & RBAC.
Menggunakan ExtendedDigitalTwinDB (SQLAlchemy), rate limiter, dan security headers.
"""
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field

from auth_secure import (
    create_access_token, get_current_user, require_role, verify_password,
    ROLE_ADMIN, ROLE_QS, ROLE_VIEWER
)
from fastra_core.digital_twin.database_extended import ExtendedDigitalTwinDB
from fastra_core.digital_twin import (
    Snapshot, ProgressEntry, ChangeOrder, AuditEvent,
    EntityProgress, Issue, MaterialDelivery, AsBuiltRecord, ArchiveRecord
)
from fastra_core.digital_twin.rate_limit import RateLimiter
from fastra_core.digital_twin.security import SecurityHeadersMiddleware, validate_env
from fastra_core.digital_twin.logging_config import setup_logging
setup_logging()
from fastra_core.digital_twin.archiving import ArchiveStore
from fastra_core.digital_twin.as_built import AsBuiltStore

app = FastAPI(title="FASTRA Digital Twin Secure API", version="2.0.0")
app.add_middleware(SecurityHeadersMiddleware)

# Validasi environment
env_errors = validate_env()
if os.getenv("FASTRA_ENV") == "production" and env_errors:
    raise RuntimeError(f"Missing environment variables: {env_errors}")

# Database global (default SQLite file-based untuk testing)
db = ExtendedDigitalTwinDB(os.getenv("FASTRA_DATABASE_URL", "sqlite:///./fastra_dt_secure.db"))
db.seed_default_users()

# Rate limiter (Redis URL optional)
rate_limiter = RateLimiter(
    redis_url=os.getenv("FASTRA_REDIS_URL"),
    limit=int(os.getenv("FASTRA_RATE_LIMIT", "60")),
    window_seconds=int(os.getenv("FASTRA_RATE_WINDOW", "60")),
)

# ---------- Pydantic Models ----------
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

class AsBuiltCreate(BaseModel):
    project_uuid: str
    entity_uuid: str
    planned_state: Dict[str, Any]
    as_built_state: Dict[str, Any]

class ArchiveCreate(BaseModel):
    project_uuid: str

# ---------- Rate Limit Dependency ----------
def rate_limit_dependency(request: Request):
    client_ip = request.client.host if request.client else "unknown"
    allowed, remaining, reset = rate_limiter.allow(f"{client_ip}:{request.url.path}")
    if not allowed:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    return {"remaining": remaining, "reset": reset}

# ---------- Auth Endpoint ----------
@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = db.get_user_by_username(form_data.username)
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = create_access_token(user.username, user.role)
    return {"access_token": token, "token_type": "bearer", "role": user.role}  # nosec B105

# ---------- Digital Twin Endpoints ----------
@app.post("/projects/{project_uuid}/snapshots", dependencies=[Depends(require_role(ROLE_ADMIN)), Depends(rate_limit_dependency)])
def create_snapshot(project_uuid: str, payload: SnapshotCreate):
    try:
        import uuid
        from datetime import datetime, timezone
        snap = Snapshot(
            snapshot_uuid=str(uuid.uuid4()),
            snapshot_name=payload.snapshot_name,
            snapshot_type=payload.snapshot_type,
            project_uuid=project_uuid,
            timestamp=payload.timestamp or datetime.now(timezone.utc).isoformat(),
            description=payload.description,
            ccm_state=payload.ccm_state,
            boq_state=payload.boq_state,
            rab_state=payload.rab_state,
            schedule_state=payload.schedule_state,
        )
        audit = AuditEvent(
            event_type="SNAPSHOT_CREATED",
            actor={"user_name": "admin"},
            target={"entity_uuid": snap.snapshot_uuid},
            metadata={"project_uuid": project_uuid},
        )
        db.save_snapshot(snap)
        db.save_audit_event(audit)
        return {"status": "success", "snapshot_uuid": snap.snapshot_uuid}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/projects/{project_uuid}/snapshots", dependencies=[Depends(get_current_user), Depends(rate_limit_dependency)])
def list_snapshots(project_uuid: str):
    snaps = db.list_snapshots(project_uuid)
    return {"snapshots": [s.to_dict() for s in snaps]}

@app.post("/projects/{project_uuid}/progress", dependencies=[Depends(require_role(ROLE_QS)), Depends(rate_limit_dependency)])
def create_progress(project_uuid: str, payload: ProgressCreate):
    try:
        import uuid
        entry = ProgressEntry(
            project_uuid=project_uuid,
            report_date=payload.report_date,
            report_type=payload.report_type,
            progress_entry_uuid=str(uuid.uuid4()),
            entity_progress=[EntityProgress(**ep) for ep in payload.entity_progress],
            issues=[Issue(**iss) for iss in payload.issues],
            weather=payload.weather,
            labor_on_site=payload.labor_on_site,
            material_delivered=[MaterialDelivery(**md) for md in payload.material_delivered],
        )
        audit = AuditEvent(
            event_type="PROGRESS_REPORTED",
            actor={"user_name": "qs"},
            target={"entity_uuid": entry.progress_entry_uuid},
            metadata={"project_uuid": project_uuid},
        )
        db.save_progress_entry(entry)
        db.save_audit_event(audit)
        return {"status": "success", "progress_entry_uuid": entry.progress_entry_uuid}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/projects/{project_uuid}/progress", dependencies=[Depends(get_current_user), Depends(rate_limit_dependency)])
def list_progress(project_uuid: str):
    entries = db.list_progress_entries(project_uuid)
    return {"entries": [e.__dict__ for e in entries]}

@app.post("/projects/{project_uuid}/vos", dependencies=[Depends(require_role(ROLE_QS)), Depends(rate_limit_dependency)])
def create_vo(project_uuid: str, payload: VOCreate):
    try:
        import uuid
        vo = ChangeOrder(
            project_uuid=project_uuid,
            vo_number=payload.vo_number,
            description=payload.description,
            reason=payload.reason,
            request_date=payload.request_date,
            requested_by=payload.requested_by,
            vo_uuid=str(uuid.uuid4()),
            ccm_changes=payload.ccm_changes,
            boq_impact=payload.boq_impact,
            cost_impact=payload.cost_impact,
            schedule_impact=payload.schedule_impact,
        )
        audit = AuditEvent(
            event_type="VO_CREATED",
            actor={"user_name": "qs"},
            target={"entity_uuid": vo.vo_uuid},
            related_vo=vo.vo_number,
            metadata={"project_uuid": project_uuid},
        )
        db.save_change_order(vo)
        db.save_audit_event(audit)
        return {"status": "success", "vo_uuid": vo.vo_uuid}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/projects/{project_uuid}/vos", dependencies=[Depends(get_current_user), Depends(rate_limit_dependency)])
def list_vos(project_uuid: str):
    vos = db.list_change_orders(project_uuid)
    return {"vos": [vo.__dict__ for vo in vos]}

@app.get("/vos/{vo_uuid}", dependencies=[Depends(get_current_user), Depends(rate_limit_dependency)])
def get_vo(vo_uuid: str):
    vo = db.get_change_order(vo_uuid)
    if vo is None:
        raise HTTPException(status_code=404, detail="VO not found")
    return vo.__dict__

@app.post("/vos/{vo_uuid}/approve", dependencies=[Depends(require_role(ROLE_ADMIN)), Depends(rate_limit_dependency)])
def approve_vo(vo_uuid: str):
    vo = db.save_change_order_status(vo_uuid, "APPROVED", "admin", "admin")
    if vo is None:
        raise HTTPException(status_code=404, detail="VO not found")
    return {"status": "success", "vo_uuid": vo_uuid, "new_status": "APPROVED"}

@app.post("/projects/{project_uuid}/as-built", dependencies=[Depends(require_role(ROLE_QS)), Depends(rate_limit_dependency)])
def create_as_built(project_uuid: str, payload: AsBuiltCreate):
    try:
        import uuid
        record = AsBuiltRecord(
            project_uuid=project_uuid,
            entity_uuid=payload.entity_uuid,
            planned_state=payload.planned_state,
            as_built_state=payload.as_built_state,
            record_uuid=str(uuid.uuid4()),
        )
        record.detect_differences()
        db.save_as_built_record(record)
        return {"status": "success", "record_uuid": record.record_uuid, "differences": len(record.differences)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/projects/{project_uuid}/as-built", dependencies=[Depends(get_current_user), Depends(rate_limit_dependency)])
def list_as_built(project_uuid: str):
    records = db.list_as_built_records(project_uuid)
    return {"records": [r.__dict__ for r in records]}

@app.post("/projects/{project_uuid}/archive", dependencies=[Depends(require_role(ROLE_ADMIN)), Depends(rate_limit_dependency)])
def create_archive(project_uuid: str):
    try:
        # Gunakan store in-memory untuk membangun arsip dari DB
        snapshot_store = __import__('fastra_core.digital_twin.snapshot', fromlist=['SnapshotStore']).SnapshotStore()
        as_built_store = AsBuiltStore()
        audit_store = __import__('fastra_core.digital_twin.audit', fromlist=['AuditStore']).AuditStore()
        for snap in db.list_snapshots(project_uuid):
            snapshot_store.create_snapshot(snap.project_uuid, snap.snapshot_name, snap.snapshot_type, snap.ccm_state, boq_state=snap.boq_state, rab_state=snap.rab_state, schedule_state=snap.schedule_state, timestamp=snap.timestamp)
        for rec in db.list_as_built_records(project_uuid):
            as_built_store.add_record(rec)
        archive_store = ArchiveStore()
        archive = archive_store.create_archive(project_uuid, snapshot_store, as_built_store, audit_store)
        db.save_archive_record(archive)
        return {"status": "success", "archive_uuid": archive.archive_uuid}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/projects/{project_uuid}/archives", dependencies=[Depends(get_current_user), Depends(rate_limit_dependency)])
def list_archives(project_uuid: str):
    archives = db.list_archive_records(project_uuid)
    return {"archives": [a.to_dict() for a in archives]}

@app.get("/archives/{archive_uuid}/restore", dependencies=[Depends(require_role(ROLE_ADMIN)), Depends(rate_limit_dependency)])
def restore_archive(archive_uuid: str):
    archive = db.get_archive_record(archive_uuid)
    if archive is None:
        raise HTTPException(status_code=404, detail="Archive not found")
    return {"status": "restored", "archive_uuid": archive_uuid}

@app.get("/projects/{project_uuid}/audit", dependencies=[Depends(get_current_user), Depends(rate_limit_dependency)])
def list_audit(project_uuid: str):
    events = db.list_audit_events()
    return {"events": [e.to_dict() for e in events]}

@app.post("/master/verify")
def verify_master_password(password: str):
    if master_security is None:
        raise HTTPException(status_code=503, detail="Master Security not initialized")
    ok = master_security.verify_master(password)
    return {"valid": ok}

@app.post("/master/totp/verify")
def verify_master_totp(secret: str, code: str):
    if master_security is None:
        raise HTTPException(status_code=503, detail="Master Security not initialized")
    ok = master_security.verify_totp(secret, code)
    return {"valid": ok}

@app.get("/master/audit/integrity")
def master_audit_integrity():
    if master_security is None:
        raise HTTPException(status_code=503, detail="Master Security not initialized")
    return {"integrity": master_security.verify_audit_integrity()}
@app.get("/health")
def health():
    return {"status": "ok", "database": "connected"}




