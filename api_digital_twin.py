"""
API Digital Twin (ACES-600) dengan API key sederhana dan rate limiter in-memory.
"""

from __future__ import annotations

import hmac
import logging
import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import Depends, FastAPI, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field, field_validator

from fastra_core.digital_twin import (
    ArchiveStore,
    AsBuiltStore,
    AuditEvent,
    AuditStore,
    ChangeOrder,
    ChangeOrderStore,
    EntityProgress,
    Issue,
    MaterialDelivery,
    ProgressEntry,
    ProgressStore,
    Snapshot,
    SnapshotStore,
)

logger = logging.getLogger("fastra_core.api_digital_twin_production")

app = FastAPI(title="FASTRA Digital Twin API Secure", version="2.0.0")

snapshot_store = SnapshotStore()
progress_store = ProgressStore()
vo_store = ChangeOrderStore()
audit_store = AuditStore()
archive_store = ArchiveStore()
as_built_store = AsBuiltStore()

API_KEY_ENV = "dev-api-key"

RATE_LIMIT_WINDOW_SECONDS = 60
RATE_LIMIT_MAX_REQUESTS = 60
RATE_LIMIT_REGISTRY: Dict[str, Dict[int, int]] = {}


def _prune_rate_limit(ip: str, current_window: int) -> None:
    if ip not in RATE_LIMIT_REGISTRY:
        return
    expired_windows = [
        win for win in RATE_LIMIT_REGISTRY[ip].keys() if win < current_window - 1
    ]
    for win in expired_windows:
        del RATE_LIMIT_REGISTRY[ip][win]
    if not RATE_LIMIT_REGISTRY[ip]:
        del RATE_LIMIT_REGISTRY[ip]


def api_key_auth(request: Request) -> str:
    key_input = request.headers.get("X-API-Key", "")
    if not key_input.strip():
        raise HTTPException(status_code=401, detail="Missing API key credentials")
    if not hmac.compare_digest(key_input.encode("utf-8"), API_KEY_ENV.encode("utf-8")):
        logger.warning("Invalid API key attempt from %s", request.client.host if request.client else "unknown")
        raise HTTPException(status_code=401, detail="Invalid API key credentials")
    return key_input


def rate_limiter(request: Request) -> None:
    now = time.time()
    current_window = int(now // RATE_LIMIT_WINDOW_SECONDS)
    client_ip = request.client.host if request.client else "unknown"
    _prune_rate_limit(client_ip, current_window)
    ip_windows = RATE_LIMIT_REGISTRY.setdefault(client_ip, {})
    current_count = ip_windows.get(current_window, 0)
    if current_count >= RATE_LIMIT_MAX_REQUESTS:
        logger.warning("Rate limit exceeded for IP %s", client_ip)
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    ip_windows[current_window] = current_count + 1


class StrictBaseModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        strict=True,
        frozen=True,
        allow_inf_nan=False,
        populate_by_name=False,
        arbitrary_types_allowed=False,
    )


class SnapshotCreate(StrictBaseModel):
    project_uuid: str = Field(..., min_length=1, max_length=128)
    snapshot_name: str = Field(..., min_length=1, max_length=255)
    snapshot_type: str = Field(..., min_length=1, max_length=100)
    ccm_state: Dict[str, Any]
    boq_state: Optional[Dict[str, Any]] = None
    rab_state: Optional[Dict[str, Any]] = None
    schedule_state: Optional[Dict[str, Any]] = None
    description: str = Field(default="", max_length=2000)
    timestamp: Optional[str] = None

    @field_validator("snapshot_name", "snapshot_type")
    @classmethod
    def _no_whitespace_only(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("value_must_not_be_blank")
        return value

    @field_validator("timestamp")
    @classmethod
    def _validate_timestamp_iso(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        try:
            datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("timestamp_must_be_a_valid_iso_8601_format") from exc
        return value


class ProgressCreate(StrictBaseModel):
    project_uuid: str = Field(..., min_length=1, max_length=128)
    report_date: str
    report_type: str = Field(..., min_length=1, max_length=100)
    entity_progress: List[Dict[str, Any]] = Field(default_factory=list)
    issues: List[Dict[str, Any]] = Field(default_factory=list)
    weather: Dict[str, Any] = Field(default_factory=dict)
    labor_on_site: Dict[str, int] = Field(default_factory=dict)
    material_delivered: List[Dict[str, Any]] = Field(default_factory=list)

    @field_validator("report_date")
    @classmethod
    def _validate_date_format(cls, value: str) -> str:
        try:
            datetime.strptime(value, "%Y-%m-%d")
        except ValueError as exc:
            raise ValueError("report_date_must_be_yyyy_mm_dd_format") from exc
        return value

    @field_validator("labor_on_site")
    @classmethod
    def _validate_labor_counts(cls, value: Dict[str, int]) -> Dict[str, int]:
        if any(v < 0 for v in value.values()):
            raise ValueError("labor_count_must_be_non_negative")
        return value


class VOCreate(StrictBaseModel):
    project_uuid: str = Field(..., min_length=1, max_length=128)
    vo_number: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1, max_length=4000)
    reason: str = Field(..., min_length=1, max_length=2000)
    request_date: str
    requested_by: str = Field(..., min_length=1, max_length=255)
    ccm_changes: Dict[str, Any] = Field(default_factory=dict)
    boq_impact: Dict[str, Any] = Field(default_factory=dict)
    cost_impact: Dict[str, float] = Field(default_factory=dict)
    schedule_impact: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("request_date")
    @classmethod
    def _validate_request_date_format(cls, value: str) -> str:
        try:
            datetime.strptime(value, "%Y-%m-%d")
        except ValueError as exc:
            raise ValueError("request_date_must_be_yyyy_mm_dd_format") from exc
        return value


def _parse_uuid(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise HTTPException(status_code=400, detail=f"invalid_{field_name}_uuid_format")
    return value.strip()


@app.post(
    "/projects/{project_uuid}/snapshots",
    response_model=Dict[str, str],
    dependencies=[Depends(api_key_auth), Depends(rate_limiter)],
)
def create_snapshot(project_uuid: str, payload: SnapshotCreate) -> Dict[str, str]:
    validated_project_uuid = _parse_uuid(project_uuid, "project")
    if validated_project_uuid != payload.project_uuid:
        raise HTTPException(status_code=400, detail="project_uuid_mismatch_with_payload")

    try:
        snap = snapshot_store.create_snapshot(
            project_uuid=validated_project_uuid,
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
            target={"entity_uuid": getattr(snap, "snapshot_uuid", "")},
            timestamp=getattr(snap, "timestamp", ""),
            metadata={"project_uuid": validated_project_uuid},
        )
        return {"status": "success", "snapshot_uuid": getattr(snap, "snapshot_uuid", "")}
    except Exception as exc:
        logger.exception("Error creating snapshot: %s", exc)
        raise HTTPException(status_code=400, detail="snapshot_creation_failed") from exc


@app.get(
    "/projects/{project_uuid}/snapshots",
    response_model=Dict[str, List[Dict[str, Any]]],
    dependencies=[Depends(api_key_auth), Depends(rate_limiter)],
)
def list_snapshots(project_uuid: str) -> Dict[str, List[Dict[str, Any]]]:
    validated_project_uuid = _parse_uuid(project_uuid, "project")
    snaps = snapshot_store.get_all_snapshots(validated_project_uuid)
    return {
        "snapshots": [
            s.to_dict() if hasattr(s, "to_dict") else s.model_dump() for s in snaps
        ]
    }


@app.post(
    "/projects/{project_uuid}/progress",
    response_model=Dict[str, str],
    dependencies=[Depends(api_key_auth), Depends(rate_limiter)],
)
def create_progress(project_uuid: str, payload: ProgressCreate) -> Dict[str, str]:
    validated_project_uuid = _parse_uuid(project_uuid, "project")
    if validated_project_uuid != payload.project_uuid:
        raise HTTPException(status_code=400, detail="project_uuid_mismatch_with_payload")

    try:
        entry = ProgressEntry(
            project_uuid=validated_project_uuid,
            report_date=payload.report_date,
            report_type=payload.report_type,
            entity_progress=[EntityProgress.model_validate(ep) for ep in payload.entity_progress],
            issues=[Issue.model_validate(iss) for iss in payload.issues],
            weather=payload.weather,
            labor_on_site=payload.labor_on_site,
            material_delivered=[MaterialDelivery.model_validate(md) for md in payload.material_delivered],
        )
        progress_store.add_entry(entry)
        audit_store.record_event(
            event_type="PROGRESS_REPORTED",
            actor={"user_name": "API"},
            target={"entity_uuid": getattr(entry, "progress_entry_uuid", "")},
            metadata={"project_uuid": validated_project_uuid},
        )
        return {"status": "success", "progress_entry_uuid": getattr(entry, "progress_entry_uuid", "")}
    except Exception as exc:
        logger.exception("Error creating progress entry: %s", exc)
        raise HTTPException(status_code=400, detail="progress_creation_failed") from exc


@app.get(
    "/projects/{project_uuid}/progress",
    response_model=Dict[str, List[Dict[str, Any]]],
    dependencies=[Depends(api_key_auth), Depends(rate_limiter)],
)
def list_progress(project_uuid: str) -> Dict[str, List[Dict[str, Any]]]:
    validated_project_uuid = _parse_uuid(project_uuid, "project")
    entries = progress_store.get_entries(validated_project_uuid)
    return {"entries": [e.model_dump() for e in entries]}


@app.post(
    "/projects/{project_uuid}/vos",
    response_model=Dict[str, str],
    dependencies=[Depends(api_key_auth), Depends(rate_limiter)],
)
def create_vo(project_uuid: str, payload: VOCreate) -> Dict[str, str]:
    validated_project_uuid = _parse_uuid(project_uuid, "project")
    if validated_project_uuid != payload.project_uuid:
        raise HTTPException(status_code=400, detail="project_uuid_mismatch_with_payload")

    try:
        vo = ChangeOrder(
            project_uuid=validated_project_uuid,
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
            target={"entity_uuid": getattr(vo, "vo_uuid", "")},
            related_vo=payload.vo_number,
            metadata={"project_uuid": validated_project_uuid},
        )
        return {"status": "success", "vo_uuid": getattr(vo, "vo_uuid", "")}
    except Exception as exc:
        logger.exception("Error creating VO: %s", exc)
        raise HTTPException(status_code=400, detail="vo_creation_failed") from exc


@app.get(
    "/projects/{project_uuid}/vos",
    response_model=Dict[str, List[Dict[str, Any]]],
    dependencies=[Depends(api_key_auth), Depends(rate_limiter)],
)
def list_vos(project_uuid: str) -> Dict[str, List[Dict[str, Any]]]:
    validated_project_uuid = _parse_uuid(project_uuid, "project")
    vos = vo_store.get_all_vos(validated_project_uuid)
    return {"vos": [vo.model_dump() for vo in vos]}


@app.get(
    "/projects/{project_uuid}/audit",
    response_model=Dict[str, List[Dict[str, Any]]],
    dependencies=[Depends(api_key_auth), Depends(rate_limiter)],
)
def list_audit(project_uuid: str) -> Dict[str, List[Dict[str, Any]]]:
    validated_project_uuid = _parse_uuid(project_uuid, "project")
    events = audit_store.get_all_events()
    return {"events": [e.to_dict() for e in events]}


@app.post(
    "/projects/{project_uuid}/archive",
    response_model=Dict[str, str],
    dependencies=[Depends(api_key_auth), Depends(rate_limiter)],
)
def create_archive(project_uuid: str) -> Dict[str, str]:
    validated_project_uuid = _parse_uuid(project_uuid, "project")
    try:
        archive = archive_store.create_archive(
            project_uuid=validated_project_uuid,
            snapshot_store=snapshot_store,
            as_built_store=as_built_store,
            audit_store=audit_store,
        )
        return {"status": "success", "archive_uuid": getattr(archive, "archive_uuid", "")}
    except Exception as exc:
        logger.exception("Error creating archive: %s", exc)
        raise HTTPException(status_code=400, detail="archive_creation_failed") from exc


@app.get("/health", response_model=Dict[str, str], dependencies=[Depends(rate_limiter)])
def health() -> Dict[str, str]:
    return {"status": "ok"}