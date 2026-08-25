"""
FASTRA Digital Twin Database Extended
Menambahkan User model, list methods, dan query untuk API.
"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from sqlalchemy import Column, String, Text, Float
from sqlalchemy.orm import sessionmaker

from fastra_core.digital_twin.database import Base, SQLAlchemyDigitalTwinDB
from fastra_core.digital_twin.snapshot import Snapshot
from fastra_core.digital_twin.audit import AuditEvent
from fastra_core.digital_twin.progress import ProgressEntry
from fastra_core.digital_twin.change_order import ChangeOrder
from fastra_core.digital_twin.as_built import AsBuiltRecord
from fastra_core.digital_twin.archiving import ArchiveRecord


class UserORM(Base):
    __tablename__ = "users"
    username = Column(String, primary_key=True)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False)
    extra_metadata = Column(Text, default="{}")


class ExtendedDigitalTwinDB(SQLAlchemyDigitalTwinDB):
    """
    Versi extended dengan User methods dan list query.
    """

    def __init__(self, database_url: Optional[str] = None):
        super().__init__(database_url)
        Base.metadata.create_all(self.engine)

    # ---------- USER ----------
    def create_user(self, username: str, password_hash: str, role: str) -> None:
        session = self._session()
        try:
            user = UserORM(username=username, password_hash=password_hash, role=role)
            session.merge(user)
            session.commit()
        finally:
            session.close()

    def get_user_by_username(self, username: str) -> Optional[UserORM]:
        session = self._session()
        try:
            return session.query(UserORM).filter(UserORM.username == username).first()
        finally:
            session.close()

    def list_users(self) -> List[UserORM]:
        session = self._session()
        try:
            return session.query(UserORM).all()
        finally:
            session.close()

    def seed_default_users(self) -> None:
        """Seed user default untuk development/testing."""
        import bcrypt
        if self.get_user_by_username("admin") is None:
            self.create_user("admin", bcrypt.hashpw(b"admin123", bcrypt.gensalt()).decode(), "admin")
        if self.get_user_by_username("qs") is None:
            self.create_user("qs", bcrypt.hashpw(b"qs123", bcrypt.gensalt()).decode(), "qs")
        if self.get_user_by_username("viewer") is None:
            self.create_user("viewer", bcrypt.hashpw(b"viewer123", bcrypt.gensalt()).decode(), "viewer")

    # ---------- LIST SNAPSHOT ----------
    def list_snapshots(self, project_uuid: str) -> List[Snapshot]:
        session = self._session()
        try:
            from fastra_core.digital_twin.database import SnapshotORM
            rows = session.query(SnapshotORM).filter(SnapshotORM.project_uuid == project_uuid).all()
            return [
                Snapshot(
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
                for row in rows
            ]
        finally:
            session.close()

    # ---------- LIST PROGRESS ----------
    def list_progress_entries(self, project_uuid: str) -> List[ProgressEntry]:
        session = self._session()
        try:
            from fastra_core.digital_twin.database import ProgressEntryORM
            rows = session.query(ProgressEntryORM).filter(ProgressEntryORM.project_uuid == project_uuid).all()
            result = []
            for row in rows:
                entry = ProgressEntry(
                    project_uuid=row.project_uuid,
                    report_date=row.report_date,
                    report_type=row.report_type,
                    period_start=row.period_start,
                    period_end=row.period_end,
                    overall_progress_percentage=row.overall_progress_percentage,
                    progress_entry_uuid=row.progress_entry_uuid,
                )
                from fastra_core.digital_twin.progress import EntityProgress, Issue, MaterialDelivery
                entry.entity_progress = [EntityProgress(**ep) for ep in json.loads(row.entity_progress or "[]")]
                entry.issues = [Issue(**iss) for iss in json.loads(row.issues or "[]")]
                entry.weather = json.loads(row.weather or "{}")
                entry.labor_on_site = json.loads(row.labor_on_site or "{}")
                entry.material_delivered = [MaterialDelivery(**md) for md in json.loads(row.material_delivered or "[]")]
                entry.metadata = json.loads(row.extra_metadata or "{}")
                result.append(entry)
            return result
        finally:
            session.close()

    # ---------- LIST AUDIT ----------
    def list_audit_events(self) -> List[AuditEvent]:
        session = self._session()
        try:
            from fastra_core.digital_twin.database import AuditEventORM
            rows = session.query(AuditEventORM).all()
            return [
                AuditEvent(
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
                for row in rows
            ]
        finally:
            session.close()

    # ---------- LIST CHANGE ORDER ----------
    def list_change_orders(self, project_uuid: str) -> List[ChangeOrder]:
        session = self._session()
        try:
            from fastra_core.digital_twin.database import ChangeOrderORM
            rows = session.query(ChangeOrderORM).filter(ChangeOrderORM.project_uuid == project_uuid).all()
            result = []
            for row in rows:
                vo = ChangeOrder(
                    project_uuid=row.project_uuid,
                    vo_number=row.vo_number,
                    description=row.description or "",
                    reason=row.reason or "",
                    request_date=row.request_date,
                    requested_by=row.requested_by or "",
                    vo_uuid=row.vo_uuid,
                    ccm_changes=json.loads(row.ccm_changes or "{}"),
                    boq_impact=json.loads(row.boq_impact or "{}"),
                    cost_impact=json.loads(row.cost_impact or "{}"),
                    schedule_impact=json.loads(row.schedule_impact or "{}"),
                    status=row.status,
                    baseline_before=row.baseline_before,
                    baseline_after=row.baseline_after,
                    metadata=json.loads(row.extra_metadata or "{}"),
                )
                from fastra_core.digital_twin.change_order import ApprovalStep
                vo.approval_chain = [ApprovalStep(**step) for step in json.loads(row.approval_chain or "[]")]
                result.append(vo)
            return result
        finally:
            session.close()

    def get_change_order(self, vo_uuid: str) -> Optional[ChangeOrder]:
        session = self._session()
        try:
            from fastra_core.digital_twin.database import ChangeOrderORM
            row = session.query(ChangeOrderORM).filter(ChangeOrderORM.vo_uuid == vo_uuid).first()
            if row is None:
                return None
            vo = ChangeOrder(
                project_uuid=row.project_uuid,
                vo_number=row.vo_number,
                description=row.description or "",
                reason=row.reason or "",
                request_date=row.request_date,
                requested_by=row.requested_by or "",
                vo_uuid=row.vo_uuid,
                ccm_changes=json.loads(row.ccm_changes or "{}"),
                boq_impact=json.loads(row.boq_impact or "{}"),
                cost_impact=json.loads(row.cost_impact or "{}"),
                schedule_impact=json.loads(row.schedule_impact or "{}"),
                status=row.status,
                baseline_before=row.baseline_before,
                baseline_after=row.baseline_after,
                metadata=json.loads(row.extra_metadata or "{}"),
            )
            from fastra_core.digital_twin.change_order import ApprovalStep
            vo.approval_chain = [ApprovalStep(**step) for step in json.loads(row.approval_chain or "[]")]
            return vo
        finally:
            session.close()

    def save_change_order_status(self, vo_uuid: str, new_status: str, approved_by: str, role: str) -> Optional[ChangeOrder]:
        vo = self.get_change_order(vo_uuid)
        if vo is None:
            return None
        from datetime import datetime, timezone
        from fastra_core.digital_twin.change_order import ApprovalStep
        vo.status = new_status
        vo.approval_chain.append(ApprovalStep(role=role, approved_by=approved_by, date=datetime.now(timezone.utc).isoformat()))
        session = self._session()
        try:
            from fastra_core.digital_twin.database import ChangeOrderORM
            orm = session.query(ChangeOrderORM).filter(ChangeOrderORM.vo_uuid == vo_uuid).first()
            if orm:
                orm.status = new_status
                orm.approval_chain = json.dumps([step.__dict__ for step in vo.approval_chain], default=str)
                session.commit()
        finally:
            session.close()
        return vo

    # ---------- AS-BUILT ----------
    def save_as_built_record(self, record: AsBuiltRecord) -> None:
        session = self._session()
        try:
            from fastra_core.digital_twin.database import AsBuiltRecordORM
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

    def list_as_built_records(self, project_uuid: str) -> List[AsBuiltRecord]:
        session = self._session()
        try:
            from fastra_core.digital_twin.database import AsBuiltRecordORM
            rows = session.query(AsBuiltRecordORM).filter(AsBuiltRecordORM.project_uuid == project_uuid).all()
            result = []
            for row in rows:
                rec = AsBuiltRecord(
                    project_uuid=row.project_uuid,
                    entity_uuid=row.entity_uuid,
                    planned_state=json.loads(row.planned_state or "{}"),
                    as_built_state=json.loads(row.as_built_state or "{}"),
                    record_uuid=row.record_uuid,
                )
                from fastra_core.digital_twin.as_built import AsBuiltDifference
                rec.differences = [AsBuiltDifference(**d) for d in json.loads(row.differences or "[]")]
                result.append(rec)
            return result
        finally:
            session.close()

    # ---------- ARCHIVE ----------
    def save_archive_record(self, archive: ArchiveRecord) -> None:
        session = self._session()
        try:
            from fastra_core.digital_twin.database import ArchiveRecordORM
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

    def list_archive_records(self, project_uuid: str) -> List[ArchiveRecord]:
        session = self._session()
        try:
            from fastra_core.digital_twin.database import ArchiveRecordORM
            rows = session.query(ArchiveRecordORM).filter(ArchiveRecordORM.project_uuid == project_uuid).all()
            result = []
            for row in rows:
                rec = ArchiveRecord(
                    archive_uuid=row.archive_uuid,
                    project_uuid=row.project_uuid,
                    archived_at=row.archived_at,
                    project_metadata=json.loads(row.project_metadata or "{}"),
                    snapshots=json.loads(row.snapshots or "[]"),
                    as_built_records=json.loads(row.as_built_records or "[]"),
                    audit_events=json.loads(row.audit_events or "[]"),
                    metadata=json.loads(row.extra_metadata or "{}"),
                    checksum=row.checksum or "",
                )
                result.append(rec)
            return result
        finally:
            session.close()

    def save_ai_event(self, event) -> None:
        session = self._session()
        try:
            from fastra_core.digital_twin.database import AIEventORM
            orm = AIEventORM(
                event_uuid=event.event_uuid,
                ai_component=event.ai_component.value if hasattr(event.ai_component, 'value') else str(event.ai_component),
                model_name=event.model_name,
                model_version=event.model_version,
                input_hash=event.input_hash,
                output_hash=event.output_hash,
                confidence_scores=json.dumps(event.confidence_scores, default=str),
                timestamp=event.timestamp,
                human_review=json.dumps(event.human_review, default=str) if event.human_review else None,
                pipeline_entry=json.dumps(event.pipeline_entry, default=str) if event.pipeline_entry else None,
            )
            session.merge(orm)
            session.commit()
        finally:
            session.close()
    def get_archive_record(self, archive_uuid: str) -> Optional[ArchiveRecord]:
        session = self._session()
        try:
            from fastra_core.digital_twin.database import ArchiveRecordORM
            row = session.query(ArchiveRecordORM).filter(ArchiveRecordORM.archive_uuid == archive_uuid).first()
            if row is None:
                return None
            return ArchiveRecord(
                archive_uuid=row.archive_uuid,
                project_uuid=row.project_uuid,
                archived_at=row.archived_at,
                project_metadata=json.loads(row.project_metadata or "{}"),
                snapshots=json.loads(row.snapshots or "[]"),
                as_built_records=json.loads(row.as_built_records or "[]"),
                audit_events=json.loads(row.audit_events or "[]"),
                metadata=json.loads(row.extra_metadata or "{}"),
                checksum=row.checksum or "",
            )
        finally:
            session.close()

