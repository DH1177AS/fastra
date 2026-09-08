# fastra_core\digital_twin\database.py

from __future__ import annotations

import json
import logging
import math
import os
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import Column, Float, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from fastra_core.digital_twin.archiving import ArchiveRecord
from fastra_core.digital_twin.as_built import AsBuiltRecord
from fastra_core.digital_twin.audit import AuditEvent
from fastra_core.digital_twin.change_order import ChangeOrder
from fastra_core.digital_twin.progress import ProgressEntry
from fastra_core.digital_twin.snapshot import Snapshot
from fastra_core.identity import Identity
from fastra_core.serialization.canonical_json import to_json
from fastra_core.primitives.currency import Currency

logger = logging.getLogger("fastra_core.digital_twin.database")


class Base(DeclarativeBase):
    """Base class deklaratif dasar untuk pemetaan SQLAlchemy ORM."""


class SnapshotORM(Base):
    __tablename__ = "snapshots"
    snapshot_uuid = Column(String, primary_key=True)
    snapshot_name = Column(String, nullable=False)
    snapshot_type = Column(String, nullable=False)
    project_uuid = Column(String, nullable=False, index=True)
    timestamp = Column(String, nullable=False)
    description = Column(Text, default="")
    ccm_state = Column(Text, nullable=False)
    boq_state = Column(Text, nullable=True)
    rab_state = Column(Text, nullable=True)
    schedule_state = Column(Text, nullable=True)
    extra_metadata = Column(Text, default="{}")


class AuditEventORM(Base):
    __tablename__ = "audit_events"
    event_uuid = Column(String, primary_key=True)
    event_type = Column(String, nullable=False)
    actor = Column(Text, nullable=False)
    target = Column(Text, nullable=False)
    change_detail = Column(Text, default="{}")
    reason = Column(Text, default="")
    related_vo = Column(String, nullable=True)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    timestamp = Column(String, nullable=False, index=True)
    extra_metadata = Column(Text, default="{}")
    prev_hash = Column(String, default="")
    hash = Column(String, default="")


class ProgressEntryORM(Base):
    __tablename__ = "progress_entries"
    progress_entry_uuid = Column(String, primary_key=True)
    project_uuid = Column(String, nullable=False, index=True)
    report_date = Column(String, nullable=False)
    report_type = Column(String, nullable=False)
    period_start = Column(String, nullable=True)
    period_end = Column(String, nullable=True)
    overall_progress_percentage = Column(Float, default=0.0)
    entity_progress = Column(Text, default="[]")
    issues = Column(Text, default="[]")
    weather = Column(Text, default="{}")
    labor_on_site = Column(Text, default="{}")
    material_delivered = Column(Text, default="[]")
    extra_metadata = Column(Text, default="{}")


class ChangeOrderORM(Base):
    __tablename__ = "change_orders"
    vo_uuid = Column(String, primary_key=True)
    project_uuid = Column(String, nullable=False, index=True)
    vo_number = Column(String, nullable=False)
    description = Column(Text, default="")
    reason = Column(Text, default="")
    request_date = Column(String, nullable=False)
    requested_by = Column(String, default="")
    ccm_changes = Column(Text, default="{}")
    boq_impact = Column(Text, default="{}")
    cost_impact = Column(Text, default="{}")
    schedule_impact = Column(Text, default="{}")
    status = Column(String, default="DRAFT")
    approval_chain = Column(Text, default="[]")
    baseline_before = Column(String, nullable=True)
    baseline_after = Column(String, nullable=True)
    extra_metadata = Column(Text, default="{}")


class AsBuiltRecordORM(Base):
    __tablename__ = "as_built_records"
    record_uuid = Column(String, primary_key=True)
    project_uuid = Column(String, nullable=False, index=True)
    entity_uuid = Column(String, nullable=False)
    planned_state = Column(Text, default="{}")
    as_built_state = Column(Text, default="{}")
    differences = Column(Text, default="[]")


class ArchiveRecordORM(Base):
    __tablename__ = "archive_records"
    archive_uuid = Column(String, primary_key=True)
    project_uuid = Column(String, nullable=False, index=True)
    archived_at = Column(String, nullable=False)
    project_metadata = Column(Text, default="{}")
    snapshots = Column(Text, default="[]")
    as_built_records = Column(Text, default="[]")
    audit_events = Column(Text, default="[]")
    extra_metadata = Column(Text, default="{}")
    checksum = Column(String, default="")


class AIEventORM(Base):
    """Representasi tabel relasional database untuk log aktivitas model AI."""
    __tablename__ = "ai_events"
    event_uuid = Column(String, primary_key=True)
    ai_component = Column(String, nullable=False)
    prompt_payload = Column(Text, default="{}")
    response_payload = Column(Text, default="{}")
    execution_time_ms = Column(Float, default=0.0)
    timestamp = Column(String, nullable=False, index=True)


class SQLAlchemyDigitalTwinDB:
    """Database layer menggunakan SQLAlchemy, mendukung SQLite & PostgreSQL."""

    def __init__(self, database_url: str | None = None) -> None:
        url = database_url or os.getenv("FASTRA_DATABASE_URL", "sqlite:///:memory:")
        if not url:
            raise ValueError("KNOWLEDGE_GRAPH_DB_ERROR_DATABASE_URL_CANNOT_BE_NULL")

        self.engine = create_engine(url, future=True, pool_pre_ping=True)
        self.SessionLocal = sessionmaker(bind=self.engine, expire_on_commit=False)
        Base.metadata.create_all(self.engine)
        logger.info("Database engine initialized: %s", self.engine.url)

    def _session(self):
        return self.SessionLocal()

    def _verify_state_numeric_integrity(self, state_dict: Optional[Dict[str, Any]]) -> None:
        """Rekursif memeriksa anomali floating-point (NaN/inf) sebelum serialisasi."""
        if not state_dict:
            return

        def _walk(node: Any) -> None:
            if isinstance(node, dict):
                for v in node.values():
                    _walk(v)
            elif isinstance(node, (list, tuple, set)):
                for item in node:
                    _walk(item)
            elif isinstance(node, (int, float)) and not isinstance(node, bool):
                if math.isnan(node) or math.isinf(node):
                    raise ValueError("NUMERIC_ANOMALY_DETECTED_STATE_CONTAINS_NAN_OR_INFINITE_VALUE")

        _walk(state_dict)

    def _sanitize_json_loads(self, raw_str: Optional[str]) -> Any:
        """Aman memuat JSON dari database dan menolak NaN/Inf."""
        if not raw_str or not raw_str.strip():
            return {}
        try:
            parsed = json.loads(raw_str)
        except (json.JSONDecodeError, TypeError) as exc:
            logger.error("INVALID_JSON_IN_DATABASE: %r", raw_str)
            raise ValueError(f"DATABASE_JSON_CORRUPTION: {exc}") from exc

        def _check(node: Any) -> None:
            if isinstance(node, dict):
                for v in node.values():
                    _check(v)
            elif isinstance(node, (list, tuple)):
                for item in node:
                    _check(item)
            elif isinstance(node, (int, float)) and not isinstance(node, bool):
                if math.isnan(node) or math.isinf(node):
                    raise ValueError("NUMERIC_ANOMALY_DETECTED_DURING_DATABASE_JSON_HYDRATION")

        _check(parsed)
        return parsed

    # ----- SNAPSHOT OPERATIONS -----
    def save_snapshot(self, snap: Snapshot) -> None:
        if not isinstance(snap, Snapshot):
            logger.error("SAVE_SNAPSHOT_INVALID_TYPE: %r", snap)
            raise TypeError("STORE_OPERATION_VIOLATION_INPUT_MUST_BE_AN_INSTANCE_OF_SNAPSHOT_CLASS")

        if not snap.project_uuid or not snap.project_uuid.strip():
            logger.error("SAVE_SNAPSHOT_INVALID_PROJECT_UUID: %s", snap.project_uuid)
            raise ValueError("INVALID_PROJECT_UUID")

        if not snap.snapshot_uuid or not snap.snapshot_uuid.strip():
            logger.error("SAVE_SNAPSHOT_INVALID_SNAPSHOT_UUID: %s", snap.snapshot_uuid)
            raise ValueError("INVALID_SNAPSHOT_UUID")

        self._verify_state_numeric_integrity(snap.ccm_state)
        self._verify_state_numeric_integrity(snap.boq_state)
        self._verify_state_numeric_integrity(snap.rab_state)
        self._verify_state_numeric_integrity(snap.schedule_state)
        self._verify_state_numeric_integrity(snap.metadata)

        session = self._session()
        try:
            orm = SnapshotORM(
                snapshot_uuid=snap.snapshot_uuid,
                snapshot_name=snap.snapshot_name.strip(),
                snapshot_type=snap.snapshot_type.strip(),
                project_uuid=snap.project_uuid,
                timestamp=str(snap.timestamp),
                description=snap.description.strip() if snap.description else "",
                ccm_state=to_json(snap.ccm_state),
                boq_state=to_json(snap.boq_state) if snap.boq_state is not None else None,
                rab_state=to_json(snap.rab_state) if snap.rab_state is not None else None,
                schedule_state=to_json(snap.schedule_state) if snap.schedule_state is not None else None,
                extra_metadata=to_json(snap.metadata),
            )
            session.merge(orm)
            session.commit()
            logger.info("Snapshot saved: %s", snap.snapshot_uuid)
        except Exception as exc:
            session.rollback()
            logger.error("DATABASE_TRANSACTION_FAILED_SNAPSHOT_SAVE: %s", exc)
            raise RuntimeError(f"DATABASE_TRANSACTION_FAILED_SNAPSHOT_SAVE_ABORTED: {exc}") from exc
        finally:
            session.close()

    def get_snapshot(self, snapshot_uuid: str) -> Optional[Snapshot]:
        if not isinstance(snapshot_uuid, str) or not snapshot_uuid.strip():
            logger.warning("GET_SNAPSHOT_INVALID_UUID: %r", snapshot_uuid)
            return None
        session = self._session()
        try:
            row = session.query(SnapshotORM).filter(SnapshotORM.snapshot_uuid == snapshot_uuid).first()
            if row is None:
                return None

            snapshot_payload = {
                "snapshot_uuid": row.snapshot_uuid,
                "snapshot_name": row.snapshot_name,
                "snapshot_type": row.snapshot_type,
                "project_uuid": row.project_uuid,
                "timestamp": row.timestamp,
                "description": row.description or "",
                "ccm_state": self._sanitize_json_loads(row.ccm_state),
                "boq_state": self._sanitize_json_loads(row.boq_state) if row.boq_state else None,
                "rab_state": self._sanitize_json_loads(row.rab_state) if row.rab_state else None,
                "schedule_state": self._sanitize_json_loads(row.schedule_state) if row.schedule_state else None,
                "metadata": self._sanitize_json_loads(row.extra_metadata) if row.extra_metadata else {},
            }
            return Snapshot(**snapshot_payload)
        finally:
            session.close()

    # ----- AUDIT OPERATIONS -----
    def save_audit_event(self, event: AuditEvent) -> None:
        if not isinstance(event, AuditEvent):
            logger.error("SAVE_AUDIT_EVENT_INVALID_TYPE: %r", event)
            raise TypeError("STORE_OPERATION_VIOLATION_INPUT_MUST_BE_AN_INSTANCE_OF_AUDIT_EVENT_CLASS")

        self._verify_state_numeric_integrity(event.actor)
        self._verify_state_numeric_integrity(event.target)
        self._verify_state_numeric_integrity(event.change_detail)
        self._verify_state_numeric_integrity(event.metadata)

        session = self._session()
        try:
            orm = AuditEventORM(
                event_uuid=event.event_uuid,
                event_type=event.event_type,
                actor=to_json(event.actor),
                target=to_json(event.target),
                change_detail=to_json(event.change_detail),
                reason=event.reason.strip() if event.reason else "",
                related_vo=event.related_vo,
                ip_address=event.ip_address,
                user_agent=event.user_agent,
                timestamp=str(event.timestamp),
                extra_metadata=to_json(event.metadata),
                prev_hash=event.prev_hash,
                hash=event.hash,
            )
            session.merge(orm)
            session.commit()
            logger.info("Audit event saved: %s", event.event_uuid)
        except Exception as exc:
            session.rollback()
            logger.error("DATABASE_TRANSACTION_FAILED_AUDIT_EVENT_SAVE: %s", exc)
            raise RuntimeError(f"DATABASE_TRANSACTION_FAILED_AUDIT_EVENT_SAVE_ABORTED: {exc}") from exc
        finally:
            session.close()

    def get_audit_event(self, event_uuid: str) -> Optional[AuditEvent]:
        if not isinstance(event_uuid, str) or not Identity.is_valid(event_uuid):
            logger.warning("GET_AUDIT_EVENT_INVALID_UUID: %r", event_uuid)
            return None
        session = self._session()
        try:
            row = session.query(AuditEventORM).filter(AuditEventORM.event_uuid == event_uuid).first()
            if row is None:
                return None

            audit_payload = {
                "event_type": row.event_type,
                "actor": self._sanitize_json_loads(row.actor),
                "target": self._sanitize_json_loads(row.target),
                "change_detail": self._sanitize_json_loads(row.change_detail) if row.change_detail else {},
                "reason": row.reason or "",
                "related_vo": row.related_vo,
                "ip_address": row.ip_address,
                "user_agent": row.user_agent,
                "timestamp": row.timestamp,
                "event_uuid": row.event_uuid,
                "metadata": self._sanitize_json_loads(row.extra_metadata) if row.extra_metadata else {},
                "prev_hash": row.prev_hash or "",
                "hash": row.hash or "",
            }
            return AuditEvent(**audit_payload)
        finally:
            session.close()

    # ----- PROGRESS OPERATIONS -----
    def save_progress_entry(self, entry: ProgressEntry) -> None:
        if not isinstance(entry, ProgressEntry):
            logger.error("SAVE_PROGRESS_ENTRY_INVALID_TYPE: %r", entry)
            raise TypeError("STORE_OPERATION_VIOLATION_INPUT_MUST_BE_AN_INSTANCE_OF_PROGRESS_ENTRY_CLASS")

        self._verify_state_numeric_integrity(entry.weather)
        self._verify_state_numeric_integrity(entry.labor_on_site)
        self._verify_state_numeric_integrity(entry.metadata)

        session = self._session()
        try:
            orm = ProgressEntryORM(
                progress_entry_uuid=entry.progress_entry_uuid,
                project_uuid=entry.project_uuid,
                report_date=str(entry.report_date),
                report_type=entry.report_type,
                period_start=str(entry.period_start),
                period_end=str(entry.period_end),
                overall_progress_percentage=float(entry.overall_progress_percentage),
                entity_progress=to_json([ep.model_dump(mode="json") for ep in entry.entity_progress]),
                issues=to_json([iss.model_dump(mode="json") for iss in entry.issues]),
                weather=to_json(entry.weather),
                labor_on_site=to_json(entry.labor_on_site),
                material_delivered=to_json([md.model_dump(mode="json") for md in entry.material_delivered]),
                extra_metadata=to_json(entry.metadata),
            )
            session.merge(orm)
            session.commit()
            logger.info("Progress entry saved: %s", entry.progress_entry_uuid)
        except Exception as exc:
            session.rollback()
            logger.error("DATABASE_TRANSACTION_FAILED_PROGRESS_ENTRY_SAVE: %s", exc)
            raise RuntimeError(f"DATABASE_TRANSACTION_FAILED_PROGRESS_ENTRY_SAVE_ABORTED: {exc}") from exc
        finally:
            session.close()

    # ----- CHANGE ORDER (VO) OPERATIONS -----
    def save_change_order(self, vo: ChangeOrder) -> None:
        if not isinstance(vo, ChangeOrder):
            logger.error("SAVE_CHANGE_ORDER_INVALID_TYPE: %r", vo)
            raise TypeError("STORE_OPERATION_VIOLATION_INPUT_MUST_BE_AN_INSTANCE_OF_CHANGE_ORDER_CLASS")

        self._verify_state_numeric_integrity(vo.ccm_changes)
        self._verify_state_numeric_integrity(vo.boq_impact)
        self._verify_state_numeric_integrity(vo.schedule_impact)
        self._verify_state_numeric_integrity(vo.metadata)

        session = self._session()
        try:
            orm = ChangeOrderORM(
                vo_uuid=vo.vo_uuid,
                project_uuid=vo.project_uuid,
                vo_number=vo.vo_number.strip(),
                description=vo.description.strip(),
                reason=vo.reason.strip(),
                request_date=str(vo.request_date),
                requested_by=vo.requested_by.strip(),
                ccm_changes=to_json(vo.ccm_changes),
                boq_impact=to_json(vo.boq_impact),
                cost_impact=to_json({k: v.model_dump(mode="json") if isinstance(v, Currency) else v for k, v in vo.cost_impact.items()}),
                schedule_impact=to_json(vo.schedule_impact),
                status=vo.status.value if hasattr(vo.status, "value") else str(vo.status),
                approval_chain=to_json([step.model_dump(mode="json") for step in vo.approval_chain]),
                baseline_before=vo.baseline_before,
                baseline_after=vo.baseline_after,
                extra_metadata=to_json(vo.metadata),
            )
            session.merge(orm)
            session.commit()
            logger.info("Change order saved: %s", vo.vo_uuid)
        except Exception as exc:
            session.rollback()
            logger.error("DATABASE_TRANSACTION_FAILED_CHANGE_ORDER_SAVE: %s", exc)
            raise RuntimeError(f"DATABASE_TRANSACTION_FAILED_CHANGE_ORDER_SAVE_ABORTED: {exc}") from exc
        finally:
            session.close()

    # ----- AS-BUILT CAPTURE OPERATIONS -----
    def save_as_built_record(self, record: AsBuiltRecord) -> None:
        if not isinstance(record, AsBuiltRecord):
            logger.error("SAVE_AS_BUILT_RECORD_INVALID_TYPE: %r", record)
            raise TypeError("STORE_OPERATION_VIOLATION_INPUT_MUST_BE_AN_INSTANCE_OF_AS_BUILT_RECORD_CLASS")

        self._verify_state_numeric_integrity(record.planned_state)
        self._verify_state_numeric_integrity(record.as_built_state)

        session = self._session()
        try:
            orm = AsBuiltRecordORM(
                record_uuid=record.record_uuid,
                project_uuid=record.project_uuid,
                entity_uuid=record.entity_uuid,
                planned_state=to_json(record.planned_state),
                as_built_state=to_json(record.as_built_state),
                differences=to_json([d.model_dump(mode="json") for d in record.differences]),
            )
            session.merge(orm)
            session.commit()
            logger.info("As-built record saved: %s", record.record_uuid)
        except Exception as exc:
            session.rollback()
            logger.error("DATABASE_TRANSACTION_FAILED_AS_BUILT_RECORD_SAVE: %s", exc)
            raise RuntimeError(f"DATABASE_TRANSACTION_FAILED_AS_BUILT_RECORD_SAVE_ABORTED: {exc}") from exc
        finally:
            session.close()

    # ----- DIGITAL TWIN ARCHIVING OPERATIONS -----
    def save_archive_record(self, archive: ArchiveRecord) -> None:
        if not isinstance(archive, ArchiveRecord):
            logger.error("SAVE_ARCHIVE_RECORD_INVALID_TYPE: %r", archive)
            raise TypeError("STORE_OPERATION_VIOLATION_INPUT_MUST_BE_AN_INSTANCE_OF_ARCHIVE_RECORD_CLASS")

        if not archive.verify_integrity():
            logger.error("CRYPTOGRAPHIC_INTEGRITY_VIOLATION: %s", archive.archive_uuid)
            raise ValueError(f"CRYPTOGRAPHIC_INTEGRITY_VIOLATION_CANNOT_SAVE_CORRUPTED_ARCHIVE: {archive.archive_uuid}")

        session = self._session()
        try:
            orm = ArchiveRecordORM(
                archive_uuid=archive.archive_uuid,
                project_uuid=archive.project_uuid,
                archived_at=str(archive.archived_at),
                project_metadata=to_json(archive.project_metadata),
                snapshots=to_json([s for s in archive.snapshots]),
                as_built_records=to_json([r for r in archive.as_built_records]),
                audit_events=to_json([e for e in archive.audit_events]),
                extra_metadata=to_json(archive.metadata),
                checksum=archive.checksum,
            )
            session.merge(orm)
            session.commit()
            logger.info("Archive record saved: %s", archive.archive_uuid)
        except Exception as exc:
            session.rollback()
            logger.error("DATABASE_TRANSACTION_FAILED_ARCHIVE_RECORD_SAVE: %s", exc)
            raise RuntimeError(f"DATABASE_TRANSACTION_FAILED_ARCHIVE_RECORD_SAVE_ABORTED: {exc}") from exc
        finally:
            session.close()

    def close(self) -> None:
        """Menutup pool koneksi mesin database secara bersih."""
        self.engine.dispose()
        logger.info("Database engine disposed")