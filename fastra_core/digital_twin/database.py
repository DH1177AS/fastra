"""
FASTRA Digital Twin Database Layer (SQLAlchemy)
Mendukung SQLite untuk development/test dan PostgreSQL untuk produksi.
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional

from sqlalchemy import Column, String, Text, Float, create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from fastra_core.digital_twin.snapshot import Snapshot
from fastra_core.digital_twin.audit import AuditEvent
from fastra_core.digital_twin.progress import ProgressEntry
from fastra_core.digital_twin.change_order import ChangeOrder
from fastra_core.digital_twin.as_built import AsBuiltRecord
from fastra_core.digital_twin.archiving import ArchiveRecord


class Base(DeclarativeBase):
    pass


class SnapshotORM(Base):
    __tablename__ = "snapshots"
    snapshot_uuid = Column(String, primary_key=True)
    snapshot_name = Column(String, nullable=False)
    snapshot_type = Column(String, nullable=False)
    project_uuid = Column(String, nullable=False, index=True)
    timestamp = Column(String, nullable=False)
    description = Column(Text, default="")
    ccm_state = Column(Text, nullable=False)  # JSON
    boq_state = Column(Text, nullable=True)
    rab_state = Column(Text, nullable=True)
    schedule_state = Column(Text, nullable=True)
    extra_metadata = Column(Text, default="{}")


class AuditEventORM(Base):
    __tablename__ = "audit_events"
    event_uuid = Column(String, primary_key=True)
    event_type = Column(String, nullable=False)
    actor = Column(Text, nullable=False)  # JSON
    target = Column(Text, nullable=False)  # JSON
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


class SQLAlchemyDigitalTwinDB:
    """Database layer menggunakan SQLAlchemy, mendukung SQLite & PostgreSQL."""

    def __init__(self, database_url: str | None = None) -> None:
        url = database_url or os.getenv("FASTRA_DATABASE_URL", "sqlite:///:memory:")
        if url is None: raise ValueError("database_url is None")
        self.engine = create_engine(url, future=True)
        self.SessionLocal = sessionmaker(bind=self.engine, expire_on_commit=False)
        Base.metadata.create_all(self.engine)

    def _session(self):
        return self.SessionLocal()

    # ----- SNAPSHOT -----
    def save_snapshot(self, snap: Snapshot) -> None:
        session = self._session()
        try:
            orm = SnapshotORM(
                snapshot_uuid=snap.snapshot_uuid,
                snapshot_name=snap.snapshot_name,
                snapshot_type=snap.snapshot_type,
                project_uuid=snap.project_uuid,
                timestamp=snap.timestamp,
                description=snap.description,
                ccm_state=json.dumps(snap.ccm_state, default=str),
                boq_state=json.dumps(snap.boq_state, default=str) if snap.boq_state is not None else None,
                rab_state=json.dumps(snap.rab_state, default=str) if snap.rab_state is not None else None,
                schedule_state=json.dumps(snap.schedule_state, default=str) if snap.schedule_state is not None else None,
                extra_metadata=json.dumps(snap.metadata, default=str),
            )
            session.merge(orm)
            session.commit()
        finally:
            session.close()

    def get_snapshot(self, snapshot_uuid: str) -> Optional[Snapshot]:
        session = self._session()
        try:
            row = session.query(SnapshotORM).filter(SnapshotORM.snapshot_uuid == snapshot_uuid).first()
            if row is None:
                return None
            return Snapshot(
                snapshot_uuid=row.snapshot_uuid,
                snapshot_name=row.snapshot_name,
                snapshot_type=row.snapshot_type,
                project_uuid=row.project_uuid,
                timestamp=row.timestamp,
                description=row.description or "",
                ccm_state=json.loads(row.ccm_state),
                boq_state=json.loads(row.boq_state) if row.boq_state else None,
                rab_state=json.loads(row.rab_state) if row.rab_state else None,
                schedule_state=json.loads(row.schedule_state) if row.schedule_state else None,
                metadata=json.loads(row.extra_metadata) if row.extra_metadata else {},
            )
        finally:
            session.close()

    # ----- AUDIT -----
    def save_audit_event(self, event: AuditEvent) -> None:
        session = self._session()
        try:
            orm = AuditEventORM(
                event_uuid=event.event_uuid,
                event_type=event.event_type,
                actor=json.dumps(event.actor, default=str),
                target=json.dumps(event.target, default=str),
                change_detail=json.dumps(event.change_detail, default=str),
                reason=event.reason,
                related_vo=event.related_vo,
                ip_address=event.ip_address,
                user_agent=event.user_agent,
                timestamp=event.timestamp,
                extra_metadata=json.dumps(event.metadata, default=str),
                prev_hash=event.prev_hash,
                hash=event.hash,
            )
            session.merge(orm)
            session.commit()
        finally:
            session.close()

    def get_audit_event(self, event_uuid: str) -> Optional[AuditEvent]:
        session = self._session()
        try:
            row = session.query(AuditEventORM).filter(AuditEventORM.event_uuid == event_uuid).first()
            if row is None:
                return None
            return AuditEvent(
                event_type=row.event_type,
                actor=json.loads(row.actor),
                target=json.loads(row.target),
                change_detail=json.loads(row.change_detail) if row.change_detail else {},
                reason=row.reason or "",
                related_vo=row.related_vo,
                ip_address=row.ip_address,
                user_agent=row.user_agent,
                timestamp=row.timestamp,
                event_uuid=row.event_uuid,
                metadata=json.loads(row.extra_metadata) if row.extra_metadata else {},
                prev_hash=row.prev_hash or "",
                hash=row.hash or "",
            )
        finally:
            session.close()

    # ----- PROGRESS -----
    def save_progress_entry(self, entry: ProgressEntry) -> None:
        session = self._session()
        try:
            orm = ProgressEntryORM(
                progress_entry_uuid=entry.progress_entry_uuid,
                project_uuid=entry.project_uuid,
                report_date=entry.report_date,
                report_type=entry.report_type,
                period_start=entry.period_start,
                period_end=entry.period_end,
                overall_progress_percentage=entry.overall_progress_percentage,
                entity_progress=json.dumps([ep.__dict__ for ep in entry.entity_progress], default=str),
                issues=json.dumps([iss.__dict__ for iss in entry.issues], default=str),
                weather=json.dumps(entry.weather, default=str),
                labor_on_site=json.dumps(entry.labor_on_site, default=str),
                material_delivered=json.dumps([md.__dict__ for md in entry.material_delivered], default=str),
                extra_metadata=json.dumps(entry.metadata, default=str),
            )
            session.merge(orm)
            session.commit()
        finally:
            session.close()

    # ----- CHANGE ORDER -----
    def save_change_order(self, vo: ChangeOrder) -> None:
        session = self._session()
        try:
            orm = ChangeOrderORM(
                vo_uuid=vo.vo_uuid,
                project_uuid=vo.project_uuid,
                vo_number=vo.vo_number,
                description=vo.description,
                reason=vo.reason,
                request_date=vo.request_date,
                requested_by=vo.requested_by,
                ccm_changes=json.dumps(vo.ccm_changes, default=str),
                boq_impact=json.dumps(vo.boq_impact, default=str),
                cost_impact=json.dumps(vo.cost_impact, default=str),
                schedule_impact=json.dumps(vo.schedule_impact, default=str),
                status=vo.status,
                approval_chain=json.dumps([step.__dict__ for step in vo.approval_chain], default=str),
                baseline_before=vo.baseline_before,
                baseline_after=vo.baseline_after,
                extra_metadata=json.dumps(vo.metadata, default=str),
            )
            session.merge(orm)
            session.commit()
        finally:
            session.close()

    # ----- AS-BUILT -----
    def save_as_built_record(self, record: AsBuiltRecord) -> None:
        session = self._session()
        try:
            orm = AsBuiltRecordORM(
                record_uuid=record.record_uuid,
                project_uuid=record.project_uuid,
                entity_uuid=record.entity_uuid,
                planned_state=json.dumps(record.planned_state, default=str),
                as_built_state=json.dumps(record.as_built_state, default=str),
                differences=json.dumps([d.__dict__ for d in record.differences], default=str),
            )
            session.merge(orm)
            session.commit()
        finally:
            session.close()

    # ----- ARCHIVE -----
    def save_archive_record(self, archive: ArchiveRecord) -> None:
        session = self._session()
        try:
            orm = ArchiveRecordORM(
                archive_uuid=archive.archive_uuid,
                project_uuid=archive.project_uuid,
                archived_at=archive.archived_at,
                project_metadata=json.dumps(archive.project_metadata, default=str),
                snapshots=json.dumps(archive.snapshots, default=str),
                as_built_records=json.dumps(archive.as_built_records, default=str),
                audit_events=json.dumps(archive.audit_events, default=str),
                extra_metadata=json.dumps(archive.metadata, default=str),
                checksum=archive.checksum,
            )
            session.merge(orm)
            session.commit()
        finally:
            session.close()

    def close(self) -> None:
        self.engine.dispose()



class AIEventORM(Base):
    __tablename__ = "ai_events"
    event_uuid = Column(String, primary_key=True)
    ai_component = Column(String, nullable=False)
    model_name = Column(String, nullable=False)
    model_version = Column(String, nullable=False)
    input_hash = Column(String, nullable=False)
    output_hash = Column(String, nullable=False)
    confidence_scores = Column(Text, default="{}")
    timestamp = Column(String, nullable=False)
    human_review = Column(Text, nullable=True)
    pipeline_entry = Column(Text, nullable=True)
