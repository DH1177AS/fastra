# fastra_core/api_digital_twin_secure.py

"""
API Digital Twin (ACES-600) dengan JWT OAuth2 & RBAC.
Menggunakan ExtendedDigitalTwinDB (SQLAlchemy), rate limiter, dan security headers.
Seluruh modul telah di-hardening dengan Pydantic v2, logging terstruktur,
dan prinsip DTO → Pydantic → Domain Logic → DB.
"""

from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    UUID4,
    field_validator,
    model_validator,
)

from auth_secure import (
    ROLE_ADMIN,
    ROLE_QS,
    ROLE_VIEWER,
    create_access_token,
    get_current_user,
    require_role,
    verify_password,
)
from fastra_core.digital_twin.archiving import ArchiveStore
from fastra_core.digital_twin.as_built import AsBuiltStore
from fastra_core.digital_twin.audit import AuditStore
from fastra_core.digital_twin.database_extended import ExtendedDigitalTwinDB
from fastra_core.digital_twin.logging_config import setup_logging
from fastra_core.digital_twin.rate_limit import RateLimiter
from fastra_core.digital_twin.security import (
    SecurityHeadersMiddleware,
    validate_env,
)
from fastra_core.digital_twin.snapshot import SnapshotStore
from fastra_core.digital_twin.transaction import atomic
from fastra_core.security_master import MasterSecurity

# Model domain internal (asumsikan sudah di-hardening di modul digital_twin)
from fastra_core.digital_twin import (
    ArchiveRecord,
    AsBuiltRecord,
    AuditEvent,
    ChangeOrder,
    EntityProgress,
    Issue,
    MaterialDelivery,
    ProgressEntry,
    Snapshot,
)

load_dotenv()
setup_logging()

logger = logging.getLogger("fastra_core.api_digital_twin_secure")
TOKEN_TYPE_BEARER = "bearer"  # nosec B105

app = FastAPI(title="FASTRA Digital Twin Secure API", version="2.0.0")

# ------------------------------------------------------------------------------
# CORS & Security Middleware
# ------------------------------------------------------------------------------
cors_origins = os.getenv("FASTRA_CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SecurityHeadersMiddleware)

# ------------------------------------------------------------------------------
# Environment validation (fail-fast di production)
# ------------------------------------------------------------------------------
env_errors = validate_env()
if env_errors:
    if os.getenv("FASTRA_ENV", "").strip().lower() == "production":
        raise RuntimeError(f"Critical environment validation failed: {env_errors}")
    else:
        logger.warning("Environment validation issues (non-production): %s", env_errors)
        
# ------------------------------------------------------------------------------
# Database & core services
# ------------------------------------------------------------------------------
db = ExtendedDigitalTwinDB(
    os.getenv("FASTRA_DATABASE_URL", "sqlite:///./fastra_dt_secure.db")
)
db.seed_default_users()

master_security: Optional[MasterSecurity] = None
try:
    master_security = MasterSecurity()
    logger.info("MasterSecurity initialized successfully")
except Exception as exc:
    logger.error("Master Security initialization failed: %s", exc, exc_info=True)

rate_limiter = RateLimiter(
    redis_url=os.getenv("FASTRA_REDIS_URL"),
    limit=int(os.getenv("FASTRA_RATE_LIMIT", "60")),
    window_seconds=int(os.getenv("FASTRA_RATE_WINDOW", "60")),
)

# ------------------------------------------------------------------------------
# 1. LAYER DTO & PYDANTIC VALIDATOR (STRICT)
# ------------------------------------------------------------------------------


class StrictBaseModel(BaseModel):
    """Base class untuk semua DTO dengan strict mode dan anti‑coercion."""

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
    snapshot_type: str = Field(..., min_length=1, max_length=50)
    ccm_state: Dict[str, Any]
    boq_state: Optional[Dict[str, Any]] = None
    rab_state: Optional[Dict[str, Any]] = None
    schedule_state: Optional[Dict[str, Any]] = None
    description: str = Field(default="", max_length=1000)
    timestamp: Optional[str] = None

    @field_validator("snapshot_name", "snapshot_type")
    @classmethod
    def _no_whitespace_only(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("value_must_not_be_blank")
        return value

    @field_validator("timestamp")
    @classmethod
    def _validate_timestamp_format(cls, value: Optional[str]) -> Optional[str]:
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
    report_type: str = Field(..., min_length=1, max_length=50)
    entity_progress: List[Dict[str, Any]] = Field(default_factory=list)
    issues: List[Dict[str, Any]] = Field(default_factory=list)
    weather: Dict[str, Any] = Field(default_factory=dict)
    labor_on_site: Dict[str, int] = Field(default_factory=dict)
    material_delivered: List[Dict[str, Any]] = Field(default_factory=list)

    @field_validator("report_date")
    @classmethod
    def _validate_report_date_format(cls, value: str) -> str:
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
    description: str = Field(..., min_length=1, max_length=2000)
    reason: str = Field(..., min_length=1, max_length=1000)
    request_date: str
    requested_by: str = Field(..., min_length=1, max_length=255)
    ccm_changes: Dict[str, Any] = Field(default_factory=dict)
    boq_impact: Dict[str, Any] = Field(default_factory=dict)
    cost_impact: Dict[str, Decimal] = Field(default_factory=dict)
    schedule_impact: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("request_date")
    @classmethod
    def _validate_request_date_format(cls, value: str) -> str:
        try:
            datetime.strptime(value, "%Y-%m-%d")
        except ValueError as exc:
            raise ValueError("request_date_must_be_yyyy_mm_dd_format") from exc
        return value

    @field_validator("cost_impact", mode="before")
    @classmethod
    def _convert_cost_values_to_decimal(cls, value: Any) -> Any:
        if not isinstance(value, dict):
            raise TypeError("cost_impact_must_be_a_dictionary")
        converted: Dict[str, Decimal] = {}
        for key, val in value.items():
            if not isinstance(key, str) or not key.strip():
                raise ValueError("cost_impact_key_must_be_non_empty_string")
            try:
                if isinstance(val, str):
                    # hapus simbol mata uang dan spasi
                    cleaned = val.replace("Rp", "").replace("IDR", "").strip()
                    decimal_val = Decimal(cleaned)
                elif isinstance(val, (int, float, Decimal)):
                    decimal_val = Decimal(str(val))
                else:
                    raise TypeError("cost_impact_value_must_be_numeric")
                if not decimal_val.is_finite():
                    raise ValueError("cost_impact_value_must_be_finite")
                converted[key.strip()] = decimal_val
            except (InvalidOperation, ValueError, TypeError) as exc:
                raise ValueError(f"invalid_cost_impact_for_key_{key}") from exc
        return converted


class AsBuiltCreate(StrictBaseModel):
    project_uuid: str = Field(..., min_length=1, max_length=128)
    entity_uuid: str = Field(..., min_length=1, max_length=128)
    planned_state: Dict[str, Any]
    as_built_state: Dict[str, Any]


class ArchiveCreate(StrictBaseModel):
    project_uuid: str = Field(..., min_length=1, max_length=128)


class MasterVerifyRequest(StrictBaseModel):
    password: str = Field(..., min_length=1, max_length=512)


class TOTPVerifyRequest(StrictBaseModel):
    secret: str = Field(..., min_length=1, max_length=128)
    code: str = Field(..., min_length=6, max_length=8)


# ------------------------------------------------------------------------------
# 2. LAYER DOMAIN MODEL & CORE INFRASTRUCTURE
# ------------------------------------------------------------------------------


class TokenResponseDomain:
    """Model representasi domain murni untuk token akses keamanan."""

    def __init__(self, access_token: str, token_type: str, role: str) -> None:
        self.access_token: str = access_token
        self.token_type: str = token_type
        self.role: str = role

    def to_transport(self) -> Dict[str, str]:
        return {
            "access_token": self.access_token,
            "token_type": self.token_type,
            "role": self.role,
        }


class SnapshotPersistenceDomain:
    """Model representasi bisnis untuk hasil persistensi Snapshot Digital Twin."""

    def __init__(self, status: str, snapshot_uuid: str) -> None:
        self.status: str = status
        self.snapshot_uuid: str = snapshot_uuid

    def to_transport(self) -> Dict[str, str]:
        return {
            "status": self.status,
            "snapshot_uuid": self.snapshot_uuid,
        }


class SnapshotListDomain:
    """Model koleksi domain murni untuk data list snapshot entitas."""

    def __init__(self, snapshots: List[Snapshot]) -> None:
        self.snapshots: List[Snapshot] = snapshots

    def to_transport(self) -> Dict[str, List[Dict[str, Any]]]:
        return {
            "snapshots": [
                s.to_dict() if hasattr(s, "to_dict") else s.model_dump()
                for s in self.snapshots
            ]
        }


class ProgressPersistenceDomain:
    """Model representasi bisnis untuk hasil persistensi Progress Laporan Lapangan."""

    def __init__(self, status: str, progress_entry_uuid: str) -> None:
        self.status: str = status
        self.progress_entry_uuid: str = progress_entry_uuid

    def to_transport(self) -> Dict[str, str]:
        return {
            "status": self.status,
            "progress_entry_uuid": self.progress_entry_uuid,
        }


class ProgressListDomain:
    """Model koleksi domain untuk mengamankan data list progress entries."""

    def __init__(self, entries: List[ProgressEntry]) -> None:
        self.entries: List[ProgressEntry] = entries

    def to_transport(self) -> Dict[str, List[Dict[str, Any]]]:
        serialized: List[Dict[str, Any]] = []
        for entry in self.entries:
            if hasattr(entry, "model_dump"):
                serialized.append(entry.model_dump())
            elif hasattr(entry, "to_dict"):
                serialized.append(entry.to_dict())
            else:
                # fallback defensive: hindari kebocoran __dict__
                serialized.append(
                    {
                        "project_uuid": getattr(entry, "project_uuid", ""),
                        "report_date": getattr(entry, "report_date", ""),
                        "report_type": getattr(entry, "report_type", ""),
                        "progress_entry_uuid": getattr(
                            entry, "progress_entry_uuid", ""
                        ),
                        "entity_progress": getattr(entry, "entity_progress", []),
                        "issues": getattr(entry, "issues", []),
                        "weather": getattr(entry, "weather", {}),
                        "labor_on_site": getattr(entry, "labor_on_site", {}),
                        "material_delivered": getattr(
                            entry, "material_delivered", []
                        ),
                    }
                )
        return {"entries": serialized}


class ChangeOrderDomain:
    """Model representasi bisnis murni untuk entitas Change Order / Variation Order."""

    def __init__(self, vo_entity: ChangeOrder) -> None:
        self.vo_uuid: str = getattr(vo_entity, "vo_uuid", "")
        self.project_uuid: str = getattr(vo_entity, "project_uuid", "")
        self.vo_number: str = getattr(vo_entity, "vo_number", "")
        self.description: str = getattr(vo_entity, "description", "")
        self.reason: str = getattr(vo_entity, "reason", "")
        self.request_date: str = getattr(vo_entity, "request_date", "")
        self.requested_by: str = getattr(vo_entity, "requested_by", "")
        self.ccm_changes: Dict[str, Any] = getattr(vo_entity, "ccm_changes", {})
        self.boq_impact: Dict[str, Any] = getattr(vo_entity, "boq_impact", {})
        self.cost_impact: Dict[str, Any] = getattr(vo_entity, "cost_impact", {})
        self.schedule_impact: Dict[str, Any] = getattr(
            vo_entity, "schedule_impact", {}
        )
        self.status: str = getattr(vo_entity, "status", "PENDING")

    def to_transport(self) -> Dict[str, Any]:
        return {
            "vo_uuid": self.vo_uuid,
            "project_uuid": self.project_uuid,
            "vo_number": self.vo_number,
            "description": self.description,
            "reason": self.reason,
            "request_date": self.request_date,
            "requested_by": self.requested_by,
            "ccm_changes": self.ccm_changes,
            "boq_impact": self.boq_impact,
            "cost_impact": self.cost_impact,
            "schedule_impact": self.schedule_impact,
            "status": self.status,
        }


class AsBuiltDomain:
    """Model representasi bisnis murni untuk entitas As-Built Record."""

    def __init__(self, record_entity: AsBuiltRecord) -> None:
        self.record_uuid: str = getattr(record_entity, "record_uuid", "")
        self.project_uuid: str = getattr(record_entity, "project_uuid", "")
        self.entity_uuid: str = getattr(record_entity, "entity_uuid", "")
        self.planned_state: Dict[str, Any] = getattr(
            record_entity, "planned_state", {}
        )
        self.as_built_state: Dict[str, Any] = getattr(
            record_entity, "as_built_state", {}
        )
        self.differences: List[Any] = getattr(record_entity, "differences", [])

    def to_transport(self) -> Dict[str, Any]:
        return {
            "record_uuid": self.record_uuid,
            "project_uuid": self.project_uuid,
            "entity_uuid": self.entity_uuid,
            "planned_state": self.planned_state,
            "as_built_state": self.as_built_state,
            "differences_count": len(self.differences),
        }


# ------------------------------------------------------------------------------
# 3. INTERCEPTOR & DEPENDENCY LAYER
# ------------------------------------------------------------------------------


def _parse_uuid(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise HTTPException(status_code=400, detail=f"invalid_{field_name}_uuid_format")
    return value.strip()


def rate_limit_dependency(request: Request) -> Dict[str, int]:
    client_ip = request.client.host if request.client else "unknown"
    allowed, remaining, reset = rate_limiter.allow(
        f"{client_ip}:{request.url.path}"
    )
    if not allowed:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    return {"remaining": remaining, "reset": reset}


# ------------------------------------------------------------------------------
# 4. CONTROLLER / ENDPOINTS INTERACTION
# ------------------------------------------------------------------------------


@app.post("/token", response_model=Dict[str, str])
def login(form_data: OAuth2PasswordRequestForm = Depends()) -> Dict[str, str]:
    user = db.get_user_by_username(form_data.username)
    if not user or not verify_password(form_data.password, user.password_hash):
        logger.warning("Failed login attempt for user: %s", form_data.username)
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = create_access_token(user.username, user.role)
    token_domain = TokenResponseDomain(
        access_token=token,
        token_type=TOKEN_TYPE_BEARER,
        role=user.role,
    )
    logger.info("User %s logged in successfully", user.username)
    return token_domain.to_transport()


@app.post(
    "/projects/{project_uuid}/snapshots",
    response_model=Dict[str, str],
    dependencies=[Depends(require_role(ROLE_ADMIN)), Depends(rate_limit_dependency)],
)
def create_snapshot(
    project_uuid: str, payload: SnapshotCreate
) -> Dict[str, str]:
    validated_project_uuid = _parse_uuid(project_uuid, "project")
    if validated_project_uuid != payload.project_uuid:
        raise HTTPException(
            status_code=400, detail="project_uuid_mismatch_with_payload"
        )

    try:
        generated_snapshot_uuid = str(uuid.uuid4())
        current_timestamp = payload.timestamp or datetime.now(timezone.utc).isoformat()

        snap = Snapshot(
            snapshot_uuid=generated_snapshot_uuid,
            snapshot_name=payload.snapshot_name,
            snapshot_type=payload.snapshot_type,
            project_uuid=str(validated_project_uuid),
            timestamp=current_timestamp,
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
            metadata={"project_uuid": str(validated_project_uuid)},
        )

        with atomic(db):
            db.save_snapshot(snap)
            db.save_audit_event(audit)

        persistence_domain = SnapshotPersistenceDomain(
            status="success", snapshot_uuid=snap.snapshot_uuid
        )
        logger.info("Snapshot %s created for project %s", snap.snapshot_uuid, project_uuid)
        return persistence_domain.to_transport()
    except Exception as exc:
        logger.exception("Error creating snapshot: %s", exc)
        raise HTTPException(status_code=400, detail="snapshot_creation_failed") from exc


@app.get(
    "/projects/{project_uuid}/snapshots",
    response_model=Dict[str, List[Dict[str, Any]]],
    dependencies=[Depends(get_current_user), Depends(rate_limit_dependency)],
)
def list_snapshots(project_uuid: str) -> Dict[str, List[Dict[str, Any]]]:
    validated_project_uuid = _parse_uuid(project_uuid, "project")
    snaps = db.list_snapshots(str(validated_project_uuid))
    list_domain = SnapshotListDomain(snapshots=snaps)
    return list_domain.to_transport()


@app.post(
    "/projects/{project_uuid}/progress",
    response_model=Dict[str, str],
    dependencies=[Depends(require_role(ROLE_QS)), Depends(rate_limit_dependency)],
)
def create_progress(
    project_uuid: str, payload: ProgressCreate
) -> Dict[str, str]:
    validated_project_uuid = _parse_uuid(project_uuid, "project")
    if validated_project_uuid != payload.project_uuid:
        raise HTTPException(
            status_code=400, detail="project_uuid_mismatch_with_payload"
        )

    try:
        generated_progress_uuid = str(uuid.uuid4())

        entry = ProgressEntry(
            project_uuid=str(validated_project_uuid),
            report_date=payload.report_date,
            report_type=payload.report_type,
            progress_entry_uuid=generated_progress_uuid,
            entity_progress=[
                EntityProgress.model_validate(ep) for ep in payload.entity_progress
            ],
            issues=[Issue.model_validate(iss) for iss in payload.issues],
            weather=payload.weather,
            labor_on_site=payload.labor_on_site,
            material_delivered=[
                MaterialDelivery.model_validate(md) for md in payload.material_delivered
            ],
        )

        audit = AuditEvent(
            event_type="PROGRESS_REPORTED",
            actor={"user_name": "qs"},
            target={"entity_uuid": entry.progress_entry_uuid},
            metadata={"project_uuid": str(validated_project_uuid)},
        )

        with atomic(db):
            db.save_progress_entry(entry)
            db.save_audit_event(audit)

        persistence_domain = ProgressPersistenceDomain(
            status="success", progress_entry_uuid=entry.progress_entry_uuid
        )
        logger.info(
            "Progress entry %s created for project %s",
            entry.progress_entry_uuid,
            project_uuid,
        )
        return persistence_domain.to_transport()
    except Exception as exc:
        logger.exception("Error creating progress entry: %s", exc)
        raise HTTPException(status_code=400, detail="progress_creation_failed") from exc


@app.get(
    "/projects/{project_uuid}/progress",
    response_model=Dict[str, List[Dict[str, Any]]],
    dependencies=[Depends(get_current_user), Depends(rate_limit_dependency)],
)
def list_progress(project_uuid: str) -> Dict[str, List[Dict[str, Any]]]:
    validated_project_uuid = _parse_uuid(project_uuid, "project")
    entries = db.list_progress_entries(str(validated_project_uuid))
    list_domain = ProgressListDomain(entries=entries)
    return list_domain.to_transport()


@app.post(
    "/projects/{project_uuid}/vos",
    response_model=Dict[str, str],
    dependencies=[Depends(require_role(ROLE_QS)), Depends(rate_limit_dependency)],
)
def create_vo(project_uuid: str, payload: VOCreate) -> Dict[str, str]:
    validated_project_uuid = _parse_uuid(project_uuid, "project")
    if validated_project_uuid != payload.project_uuid:
        raise HTTPException(
            status_code=400, detail="project_uuid_mismatch_with_payload"
        )

    try:
        generated_vo_uuid = str(uuid.uuid4())

        vo = ChangeOrder(
            project_uuid=str(validated_project_uuid),
            vo_number=payload.vo_number,
            description=payload.description,
            reason=payload.reason,
            request_date=payload.request_date,
            requested_by=payload.requested_by,
            vo_uuid=generated_vo_uuid,
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
            metadata={"project_uuid": str(validated_project_uuid)},
        )

        with atomic(db):
            db.save_change_order(vo)
            db.save_audit_event(audit)

        logger.info("VO %s created for project %s", vo.vo_uuid, project_uuid)
        return {"status": "success", "vo_uuid": vo.vo_uuid}
    except Exception as exc:
        logger.exception("Error creating VO: %s", exc)
        raise HTTPException(status_code=400, detail="vo_creation_failed") from exc


@app.get(
    "/projects/{project_uuid}/vos",
    response_model=Dict[str, List[Dict[str, Any]]],
    dependencies=[Depends(get_current_user), Depends(rate_limit_dependency)],
)
def list_vos(project_uuid: str) -> Dict[str, List[Dict[str, Any]]]:
    validated_project_uuid = _parse_uuid(project_uuid, "project")
    vos = db.list_change_orders(str(validated_project_uuid))
    return {"vos": [ChangeOrderDomain(vo).to_transport() for vo in vos]}


@app.get(
    "/vos/{vo_uuid}",
    response_model=Dict[str, Any],
    dependencies=[Depends(get_current_user), Depends(rate_limit_dependency)],
)
def get_vo(vo_uuid: str) -> Dict[str, Any]:
    validated_vo_uuid = _parse_uuid(vo_uuid, "vo")
    vo = db.get_change_order(str(validated_vo_uuid))
    if vo is None:
        raise HTTPException(status_code=404, detail="VO not found")
    return ChangeOrderDomain(vo).to_transport()


@app.post(
    "/vos/{vo_uuid}/approve",
    response_model=Dict[str, str],
    dependencies=[Depends(require_role(ROLE_ADMIN)), Depends(rate_limit_dependency)],
)
def approve_vo(vo_uuid: str) -> Dict[str, str]:
    validated_vo_uuid = _parse_uuid(vo_uuid, "vo")
    vo = db.save_change_order_status(
        str(validated_vo_uuid), "APPROVED", "admin", "admin"
    )
    if vo is None:
        raise HTTPException(status_code=404, detail="VO not found")
    logger.info("VO %s approved", validated_vo_uuid)
    return {
        "status": "success",
        "vo_uuid": str(validated_vo_uuid),
        "new_status": "APPROVED",
    }


@app.post(
    "/projects/{project_uuid}/as-built",
    response_model=Dict[str, Any],
    dependencies=[Depends(require_role(ROLE_QS)), Depends(rate_limit_dependency)],
)
def create_as_built(
    project_uuid: str, payload: AsBuiltCreate
) -> Dict[str, Any]:
    validated_project_uuid = _parse_uuid(project_uuid, "project")
    if validated_project_uuid != payload.project_uuid:
        raise HTTPException(
            status_code=400, detail="project_uuid_mismatch_with_payload"
        )

    try:
        generated_record_uuid = str(uuid.uuid4())
        record = AsBuiltRecord(
            project_uuid=str(validated_project_uuid),
            entity_uuid=str(payload.entity_uuid),
            planned_state=payload.planned_state,
            as_built_state=payload.as_built_state,
            record_uuid=generated_record_uuid,
        )
        record = record.compute_differences()

        with atomic(db):
            db.save_as_built_record(record)

        logger.info(
            "As-built record %s created for project %s",
            record.record_uuid,
            project_uuid,
        )
        return {
            "status": "success",
            "record_uuid": record.record_uuid,
            "differences": len(record.differences),
        }
    except Exception as exc:
        logger.exception("Error creating as-built record: %s", exc)
        raise HTTPException(
            status_code=400, detail="as_built_creation_failed"
        ) from exc


@app.get(
    "/projects/{project_uuid}/as-built",
    response_model=Dict[str, List[Dict[str, Any]]],
    dependencies=[Depends(get_current_user), Depends(rate_limit_dependency)],
)
def list_as_built(project_uuid: str) -> Dict[str, List[Dict[str, Any]]]:
    validated_project_uuid = _parse_uuid(project_uuid, "project")
    records = db.list_as_built_records(str(validated_project_uuid))
    return {"records": [AsBuiltDomain(r).to_transport() for r in records]}


@app.post(
    "/projects/{project_uuid}/archive",
    response_model=Dict[str, str],
    dependencies=[Depends(require_role(ROLE_ADMIN)), Depends(rate_limit_dependency)],
)
def create_archive(project_uuid: str) -> Dict[str, str]:
    validated_project_uuid = _parse_uuid(project_uuid, "project")
    try:
        # Inisialisasi store yang diperlukan (statis, bukan dynamic import)
        snapshot_store = SnapshotStore()
        as_built_store = AsBuiltStore()
        audit_store = AuditStore()
        archive_store = ArchiveStore()

        for snap in db.list_snapshots(str(validated_project_uuid)):
            snapshot_store.create_snapshot(
                snap.project_uuid,
                snap.snapshot_name,
                snap.snapshot_type,
                snap.ccm_state,
                boq_state=snap.boq_state,
                rab_state=snap.rab_state,
                schedule_state=snap.schedule_state,
                timestamp=snap.timestamp,
            )

        for rec in db.list_as_built_records(str(validated_project_uuid)):
            as_built_store.add_record(rec)

        archive = archive_store.create_archive(
            str(validated_project_uuid),
            snapshot_store,
            as_built_store,
            audit_store,
        )
        db.save_archive_record(archive)

        logger.info(
            "Archive %s created for project %s",
            archive.archive_uuid,
            project_uuid,
        )
        return {
            "status": "success",
            "archive_uuid": str(archive.archive_uuid),
        }
    except Exception as exc:
        logger.exception("Error creating archive: %s", exc)
        raise HTTPException(status_code=400, detail="archive_creation_failed") from exc


@app.get(
    "/projects/{project_uuid}/archives",
    response_model=Dict[str, List[Dict[str, Any]]],
    dependencies=[Depends(get_current_user), Depends(rate_limit_dependency)],
)
def list_archives(project_uuid: str) -> Dict[str, List[Dict[str, Any]]]:
    validated_project_uuid = _parse_uuid(project_uuid, "project")
    archives = db.list_archive_records(str(validated_project_uuid))
    return {
        "archives": [
            a.to_dict() if hasattr(a, "to_dict") else a.model_dump()
            for a in archives
        ]
    }


@app.get(
    "/archives/{archive_uuid}/restore",
    response_model=Dict[str, str],
    dependencies=[Depends(require_role(ROLE_ADMIN)), Depends(rate_limit_dependency)],
)
def restore_archive(archive_uuid: str) -> Dict[str, str]:
    validated_archive_uuid = _parse_uuid(archive_uuid, "archive")
    archive = db.get_archive_record(str(validated_archive_uuid))
    if archive is None:
        raise HTTPException(status_code=404, detail="Archive not found")
    logger.info("Archive %s restore requested", validated_archive_uuid)
    return {
        "status": "restored",
        "archive_uuid": str(validated_archive_uuid),
    }


@app.get(
    "/projects/{project_uuid}/audit",
    response_model=Dict[str, List[Dict[str, Any]]],
    dependencies=[Depends(get_current_user), Depends(rate_limit_dependency)],
)
def list_audit(project_uuid: str) -> Dict[str, List[Dict[str, Any]]]:
    validated_project_uuid = _parse_uuid(project_uuid, "project")
    events = db.list_audit_events()
    return {
        "events": [
            e.to_dict() if hasattr(e, "to_dict") else e.model_dump()
            for e in events
        ]
    }


@app.post(
    "/master/verify",
    response_model=Dict[str, bool],
    dependencies=[Depends(rate_limit_dependency)],
)
def verify_master_password(payload: MasterVerifyRequest) -> Dict[str, bool]:
    if master_security is None:
        raise HTTPException(status_code=503, detail="Master Security not initialized")
    ok = master_security.verify_master(payload.password)
    return {"valid": ok}


@app.post(
    "/master/totp/verify",
    response_model=Dict[str, bool],
    dependencies=[Depends(rate_limit_dependency)],
)
def verify_master_totp(payload: TOTPVerifyRequest) -> Dict[str, bool]:
    if master_security is None:
        raise HTTPException(status_code=503, detail="Master Security not initialized")
    ok = master_security.verify_totp(payload.secret, payload.code)
    return {"valid": ok}


@app.get(
    "/master/audit/integrity",
    response_model=Dict[str, Any],
    dependencies=[Depends(require_role(ROLE_ADMIN)), Depends(rate_limit_dependency)],
)
def master_audit_integrity() -> Dict[str, Any]:
    if master_security is None:
        raise HTTPException(status_code=503, detail="Master Security not initialized")
    return {"integrity": master_security.verify_audit_integrity()}


@app.get("/health", response_model=Dict[str, str])
def health() -> Dict[str, str]:
    return {"status": "ok"}