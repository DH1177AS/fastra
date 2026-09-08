# fastra_core\digital_twin\database_extended.py

from __future__ import annotations

import json
import logging
import math
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import Column, String, Text
from sqlalchemy.orm import sessionmaker

from fastra_core.identity import Identity
from fastra_core.primitives.currency import Currency
from fastra_core.digital_twin.database import Base, SQLAlchemyDigitalTwinDB
from fastra_core.digital_twin.snapshot import Snapshot
from fastra_core.digital_twin.audit import AuditEvent
from fastra_core.digital_twin.progress import ProgressEntry, EntityProgress, Issue, MaterialDelivery
from fastra_core.digital_twin.change_order import ChangeOrder, ApprovalStep
from fastra_core.digital_twin.as_built import AsBuiltRecord, AsBuiltDifference
from fastra_core.digital_twin.archiving import ArchiveRecord
from fastra_core.digital_twin.enums import VOStatus, ApprovalStatus

logger = logging.getLogger("fastra_core.digital_twin.database_extended")


class UserORM(Base):
    __tablename__ = "users"
    username = Column(String, primary_key=True)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False)
    extra_metadata = Column(Text, default="{}")


class ExtendedDigitalTwinDB(SQLAlchemyDigitalTwinDB):
    """
    Versi perluasan (extended) infrastruktur database digital twin.
    Menyediakan method manajemen otentikasi User dan pipeline query data koleksi lintas domain.
    """

    def __init__(self, database_url: Optional[str] = None):
        super().__init__(database_url)
        Base.metadata.create_all(self.engine)

    def _sanitize_json_loads(self, raw_str: Optional[str]) -> Any:
        """
        Mengevaluasi hasil de-serialisasi data teks menjadi objek JSON murni.
        Menghentikan anomali data floating-point rusak (NaN/inf) semenjak hulu.
        """
        if not raw_str or not raw_str.strip():
            return {}
        try:
            parsed = json.loads(raw_str)
        except (json.JSONDecodeError, TypeError):
            logger.error("INVALID_JSON_IN_DATABASE: %r", raw_str)
            return {}

        def _traverse_and_check(node: Any) -> None:
            if isinstance(node, dict):
                for k, v in node.items():
                    _traverse_and_check(v)
            elif isinstance(node, list):
                for item in node:
                    _traverse_and_check(item)
            elif isinstance(node, (int, float)) and not isinstance(node, bool):
                if math.isnan(node) or math.isinf(node):
                    raise ValueError("NUMERIC_ANOMALY_DETECTED_DURING_DATABASE_JSON_HYDRATION")

        _traverse_and_check(parsed)
        return parsed

    @staticmethod
    def _convert_currency_impact(impact: Dict[str, Any]) -> Dict[str, Currency]:
        """
        Rekonstruksi objek Currency dari representasi JSON database.
        Menerima dict yang berisi pasangan kunci-nilai berupa:
        - dict dengan key 'value' dan 'unit' (hasil model_dump)
        - string angka (jika disimpan sebagai string)
        """
        result: Dict[str, Currency] = {}
        for key, raw_value in impact.items():
            if not isinstance(key, str):
                continue
            if isinstance(raw_value, dict):
                val = raw_value.get("value")
                unit = raw_value.get("unit")
                if val is not None and unit is not None:
                    try:
                        result[key] = Currency(value=val, unit=unit)
                    except Exception as exc:
                        logger.error("FAILED_TO_RECONSTRUCT_CURRENCY at key %s: %s", key, exc)
                        raise
                else:
                    logger.error("MALFORMED_CURRENCY_DICT at key %s", key)
                    raise ValueError(f"MALFORMED_CURRENCY_DICT_AT_KEY_{key}")
            elif isinstance(raw_value, (str, int, float)) and not isinstance(raw_value, bool):
                # Coba parse sebagai string angka dengan unit default IDR
                try:
                    result[key] = Currency.from_numeric_safe(str(raw_value))
                except Exception as exc:
                    logger.error("FAILED_TO_PARSE_CURRENCY_STRING at key %s: %s", key, exc)
                    raise
            else:
                logger.error("UNSUPPORTED_CURRENCY_VALUE_TYPE at key %s: %r", key, raw_value)
                raise TypeError(f"UNSUPPORTED_CURRENCY_VALUE_TYPE_AT_KEY_{key}")
        return result

    # ---------- USER OPERATIONS ----------
    def create_user(self, username: str, password_hash: str, role: str) -> None:
        if not isinstance(username, str) or not username.strip():
            raise ValueError("USERNAME_MUST_BE_A_PURE_NON_EMPTY_STRING")
        if not isinstance(password_hash, str) or not password_hash.strip():
            raise ValueError("PASSWORD_HASH_MUST_BE_A_PURE_NON_EMPTY_STRING")
        if not isinstance(role, str) or role.strip() not in {"admin", "qs", "viewer"}:
            logger.error("ILLEGAL_USER_ROLE_ASSIGNMENT: %s", role)
            raise ValueError(f"ILLEGAL_USER_ROLE_ASSIGNMENT_ATTEMPTED: '{role}'")

        session = self._session()
        try:
            user = UserORM(
                username=username.strip(),
                password_hash=password_hash.strip(),
                role=role.strip(),
            )
            session.merge(user)
            session.commit()
        except Exception as transaction_exception:
            session.rollback()
            logger.error("DATABASE_TRANSACTION_FAILED_USER_MERGE: %s", transaction_exception)
            raise RuntimeError(f"DATABASE_TRANSACTION_FAILED_USER_MERGE_ABORTED: {str(transaction_exception)}") from transaction_exception
        finally:
            session.close()

    def get_user_by_username(self, username: str) -> Optional[UserORM]:
        if not isinstance(username, str) or not username.strip():
            return None
        session = self._session()
        try:
            user_node = session.query(UserORM).filter(UserORM.username == username.strip()).first()
            if user_node:
                session.expunge(user_node)
            return user_node
        finally:
            session.close()

    def list_users(self) -> List[UserORM]:
        session = self._session()
        try:
            users_list = session.query(UserORM).all()
            for user in users_list:
                session.expunge(user)
            return users_list
        finally:
            session.close()

    def seed_default_users(self) -> None:
        import bcrypt

        default_roles = [
            ("admin", "admin123", "admin"),
            ("qs", "qs123", "qs"),
            ("viewer", "viewer123", "viewer"),
        ]
        for username, plain_pass, role in default_roles:
            if self.get_user_by_username(username) is None:
                hashed_bytes = bcrypt.hashpw(plain_pass.encode("utf-8"), bcrypt.gensalt())
                self.create_user(username, hashed_bytes.decode("utf-8"), role)

    # ---------- SNAPSHOT DATA RETRIEVAL ----------
    def list_snapshots(self, project_uuid: str) -> List[Snapshot]:
        if not isinstance(project_uuid, str) or not project_uuid.strip():
            raise ValueError(f"DATABASE_QUERY_VIOLATION_INVALID_PROJECT_UUID_STRUCTURE: {project_uuid}")

        session = self._session()
        try:
            from fastra_core.digital_twin.database import SnapshotORM
            rows = session.query(SnapshotORM).filter(SnapshotORM.project_uuid == project_uuid).all()

            validated_snapshots: List[Snapshot] = []
            for row in rows:
                snapshot_payload = {
                    "snapshot_uuid": row.snapshot_uuid,
                    "snapshot_name": row.snapshot_name,
                    "snapshot_type": row.snapshot_type,
                    "project_uuid": row.project_uuid,
                    "timestamp": str(row.timestamp),
                    "description": row.description or "",
                    "ccm_state": self._sanitize_json_loads(row.ccm_state),
                    "boq_state": self._sanitize_json_loads(row.boq_state) if row.boq_state else None,
                    "rab_state": self._sanitize_json_loads(row.rab_state) if row.rab_state else None,
                    "schedule_state": self._sanitize_json_loads(row.schedule_state) if row.schedule_state else None,
                    "metadata": self._sanitize_json_loads(row.extra_metadata) if row.extra_metadata else {},
                }
                validated_snapshots.append(Snapshot(**snapshot_payload))

            return validated_snapshots
        finally:
            session.close()

    # ---------- PROGRESS RECORDS RETRIEVAL ----------
    def list_progress_entries(self, project_uuid: str) -> List[ProgressEntry]:
        if not isinstance(project_uuid, str) or not project_uuid.strip():
            raise ValueError(f"DATABASE_QUERY_VIOLATION_INVALID_PROJECT_UUID_STRUCTURE: {project_uuid}")

        session = self._session()
        try:
            from fastra_core.digital_twin.database import ProgressEntryORM
            rows = session.query(ProgressEntryORM).filter(ProgressEntryORM.project_uuid == project_uuid).all()

            validated_entries: List[ProgressEntry] = []
            for row in rows:
                raw_ep = self._sanitize_json_loads(row.entity_progress or "[]")
                raw_iss = self._sanitize_json_loads(row.issues or "[]")
                raw_md = self._sanitize_json_loads(row.material_delivered or "[]")

                progress_payload = {
                    "project_uuid": row.project_uuid,
                    "report_date": str(row.report_date),
                    "report_type": row.report_type,
                    "period_start": str(row.period_start),
                    "period_end": str(row.period_end),
                    "overall_progress_percentage": float(row.overall_progress_percentage),
                    "progress_entry_uuid": row.progress_entry_uuid,
                    "entity_progress": tuple(EntityProgress(**ep) for ep in raw_ep) if isinstance(raw_ep, list) else (),
                    "issues": tuple(Issue(**iss) for iss in raw_iss) if isinstance(raw_iss, list) else (),
                    "weather": self._sanitize_json_loads(row.weather or "{}"),
                    "labor_on_site": self._sanitize_json_loads(row.labor_on_site or "{}"),
                    "material_delivered": tuple(MaterialDelivery(**md) for md in raw_md) if isinstance(raw_md, list) else (),
                    "metadata": self._sanitize_json_loads(row.extra_metadata or "{}"),
                }
                validated_entries.append(ProgressEntry(**progress_payload))

            return validated_entries
        finally:
            session.close()

    # ---------- AUDIT TRAIL RETRIEVAL ----------
    def list_audit_events(self) -> List[AuditEvent]:
        session = self._session()
        try:
            from fastra_core.digital_twin.database import AuditEventORM
            rows = session.query(AuditEventORM).all()

            validated_events: List[AuditEvent] = []
            for row in rows:
                audit_payload = {
                    "event_type": row.event_type,
                    "actor": self._sanitize_json_loads(row.actor),
                    "target": self._sanitize_json_loads(row.target),
                    "change_detail": self._sanitize_json_loads(row.change_detail) if row.change_detail else {},
                    "reason": row.reason or "",
                    "related_vo": row.related_vo,
                    "ip_address": row.ip_address,
                    "user_agent": row.user_agent,
                    "timestamp": str(row.timestamp),
                    "event_uuid": row.event_uuid,
                    "metadata": self._sanitize_json_loads(row.extra_metadata) if row.extra_metadata else {},
                    "prev_hash": row.prev_hash or "",
                    "hash": row.hash or "",
                }
                validated_events.append(AuditEvent(**audit_payload))

            return validated_events
        finally:
            session.close()

    # ---------- CHANGE ORDER (VO) OPERATIONS ----------
    def list_change_orders(self, project_uuid: str) -> List[ChangeOrder]:
        if not isinstance(project_uuid, str) or not project_uuid.strip():
            raise ValueError(f"DATABASE_QUERY_VIOLATION_INVALID_PROJECT_UUID_STRUCTURE: {project_uuid}")

        session = self._session()
        try:
            from fastra_core.digital_twin.database import ChangeOrderORM
            rows = session.query(ChangeOrderORM).filter(ChangeOrderORM.project_uuid == project_uuid).all()

            validated_vos: List[ChangeOrder] = []
            for row in rows:
                raw_approval = self._sanitize_json_loads(row.approval_chain or "[]")
                raw_cost_impact = self._sanitize_json_loads(row.cost_impact or "{}")
                cost_impact_dict = self._convert_currency_impact(raw_cost_impact)

                vo_payload = {
                    "project_uuid": row.project_uuid,
                    "vo_number": row.vo_number,
                    "description": row.description or "",
                    "reason": row.reason or "",
                    "request_date": str(row.request_date),
                    "requested_by": row.requested_by or "",
                    "vo_uuid": row.vo_uuid,
                    "ccm_changes": self._sanitize_json_loads(row.ccm_changes or "{}"),
                    "boq_impact": self._sanitize_json_loads(row.boq_impact or "{}"),
                    "cost_impact": cost_impact_dict,
                    "schedule_impact": self._sanitize_json_loads(row.schedule_impact or "{}"),
                    "status": VOStatus(row.status),
                    "baseline_before": row.baseline_before,
                    "baseline_after": row.baseline_after,
                    "approval_chain": tuple(ApprovalStep(**step) for step in raw_approval) if isinstance(raw_approval, list) else (),
                    "metadata": self._sanitize_json_loads(row.extra_metadata or "{}"),
                }
                validated_vos.append(ChangeOrder(**vo_payload))

            return validated_vos
        finally:
            session.close()

    def get_change_order(self, vo_uuid: str) -> Optional[ChangeOrder]:
        if not isinstance(vo_uuid, str) or not vo_uuid.strip():
            return None

        session = self._session()
        try:
            from fastra_core.digital_twin.database import ChangeOrderORM
            row = session.query(ChangeOrderORM).filter(ChangeOrderORM.vo_uuid == vo_uuid).first()
            if row is None:
                return None

            raw_approval = self._sanitize_json_loads(row.approval_chain or "[]")
            raw_cost_impact = self._sanitize_json_loads(row.cost_impact or "{}")
            cost_impact_dict = self._convert_currency_impact(raw_cost_impact)

            vo_payload = {
                "project_uuid": row.project_uuid,
                "vo_number": row.vo_number,
                "description": row.description or "",
                "reason": row.reason or "",
                "request_date": str(row.request_date),
                "requested_by": row.requested_by or "",
                "vo_uuid": row.vo_uuid,
                "ccm_changes": self._sanitize_json_loads(row.ccm_changes or "{}"),
                "boq_impact": self._sanitize_json_loads(row.boq_impact or "{}"),
                "cost_impact": cost_impact_dict,
                "schedule_impact": self._sanitize_json_loads(row.schedule_impact or "{}"),
                "status": VOStatus(row.status),
                "baseline_before": row.baseline_before,
                "baseline_after": row.baseline_after,
                "approval_chain": tuple(ApprovalStep(**step) for step in raw_approval)
                if isinstance(raw_approval, list)
                else (),
                "metadata": self._sanitize_json_loads(row.extra_metadata or "{}"),
            }
            return ChangeOrder.model_validate(vo_payload)
        finally:
            session.close()

    def save_change_order_status(self, vo_uuid: str, new_status: str, approved_by: str, role: str) -> Optional[ChangeOrder]:
        vo = self.get_change_order(vo_uuid)
        if vo is None:
            return None

        from fastra_core.digital_twin.enums import VOStatus, ApprovalStatus

        try:
            enum_status = VOStatus(new_status)
            enum_app_status = ApprovalStatus.APPROVED
        except ValueError as exc:
            logger.error("ILLEGAL_STATUS_TRANSITION_VALUE: %s", new_status)
            raise ValueError(f"ILLEGAL_STATUS_TRANSITION_VALUE: '{new_status}'") from exc

        new_step = ApprovalStep(
            role=role,
            approved_by=approved_by,
            date=datetime.now(timezone.utc),
            status=enum_app_status,
        )

        extended_chain = list(vo.approval_chain)
        extended_chain.append(new_step)

        vo_dump = vo.model_dump()
        vo_dump["status"] = enum_status
        vo_dump["approval_chain"] = tuple(extended_chain)
        updated_vo = ChangeOrder(**vo_dump)

        session = self._session()
        try:
            from fastra_core.digital_twin.database import ChangeOrderORM
            orm = session.query(ChangeOrderORM).filter(ChangeOrderORM.vo_uuid == vo_uuid).first()
            if orm:
                orm.status = updated_vo.status.value
                # Serialisasi approval_chain ke JSON dengan format mode="json" untuk mempertahankan tanggal
                orm.approval_chain = json.dumps(
                    [step.model_dump(mode="json") for step in updated_vo.approval_chain],
                    separators=(",", ":"),
                )
                session.commit()
            return updated_vo
        except Exception as write_exception:
            session.rollback()
            logger.error("DATABASE_TRANSACTION_FAILED_CHANGE_ORDER_STATUS_SAVE: %s", write_exception)
            raise RuntimeError(
                f"DATABASE_TRANSACTION_FAILED_CHANGE_ORDER_STATUS_SAVE_ABORTED: {str(write_exception)}"
            ) from write_exception
        finally:
            session.close()

    # ---------- AS-BUILT CAPTURE OPERATIONS ----------
    def save_as_built_record(self, record: AsBuiltRecord) -> None:
        if not isinstance(record, AsBuiltRecord):
            raise TypeError("STORE_OPERATION_VIOLATION_RECORD_MUST_BE_AN_INSTANCE_OF_AS_BUILT_RECORD")

        session = self._session()
        try:
            from fastra_core.digital_twin.database import AsBuiltRecordORM

            orm = AsBuiltRecordORM(
                record_uuid=record.record_uuid,
                project_uuid=record.project_uuid,
                entity_uuid=record.entity_uuid,
                planned_state=json.dumps(record.planned_state, separators=(",", ":")),
                as_built_state=json.dumps(record.as_built_state, separators=(",", ":")),
                differences=json.dumps(
                    [d.model_dump(mode="json") for d in record.differences],
                    separators=(",", ":"),
                ),
            )
            session.merge(orm)
            session.commit()
        except Exception as write_exception:
            session.rollback()
            logger.error("DATABASE_TRANSACTION_FAILED_AS_BUILT_RECORD_SAVE: %s", write_exception)
            raise RuntimeError(
                f"DATABASE_TRANSACTION_FAILED_AS_BUILT_RECORD_SAVE_ABORTED: {str(write_exception)}"
            ) from write_exception
        finally:
            session.close()

    def list_as_built_records(self, project_uuid: str) -> List[AsBuiltRecord]:
        if not isinstance(project_uuid, str) or not project_uuid.strip():
            raise ValueError(f"DATABASE_QUERY_VIOLATION_INVALID_PROJECT_UUID_STRUCTURE: {project_uuid}")

        session = self._session()
        try:
            from fastra_core.digital_twin.database import AsBuiltRecordORM
            rows = session.query(AsBuiltRecordORM).filter(AsBuiltRecordORM.project_uuid == project_uuid).all()

            validated_records: List[AsBuiltRecord] = []
            for row in rows:
                raw_diffs = self._sanitize_json_loads(row.differences or "[]")

                record_payload = {
                    "project_uuid": row.project_uuid,
                    "entity_uuid": row.entity_uuid,
                    "planned_state": self._sanitize_json_loads(row.planned_state or "{}"),
                    "as_built_state": self._sanitize_json_loads(row.as_built_state or "{}"),
                    "record_uuid": row.record_uuid,
                    "differences": tuple(AsBuiltDifference(**d) for d in raw_diffs)
                    if isinstance(raw_diffs, list)
                    else (),
                }
                validated_records.append(AsBuiltRecord(**record_payload))

            return validated_records
        finally:
            session.close()

    # ---------- DIGITAL TWIN ARCHIVING OPERATIONS ----------
    def save_archive_record(self, archive: ArchiveRecord) -> None:
        if not isinstance(archive, ArchiveRecord):
            raise TypeError("STORE_OPERATION_VIOLATION_ARCHIVE_MUST_BE_AN_INSTANCE_OF_ARCHIVE_RECORD")

        if not archive.verify_integrity():
            logger.error("CRYPTOGRAPHIC_INTEGRITY_VIOLATION_CANNOT_SAVE_CORRUPTED_ARCHIVE: %s", archive.archive_uuid)
            raise ValueError(
                f"CRYPTOGRAPHIC_INTEGRITY_VIOLATION_CANNOT_SAVE_CORRUPTED_ARCHIVE: {archive.archive_uuid}"
            )

        session = self._session()
        try:
            from fastra_core.digital_twin.database import ArchiveRecordORM

            orm = ArchiveRecordORM(
                archive_uuid=archive.archive_uuid,
                project_uuid=archive.project_uuid,
                archived_at=archive.archived_at,
                project_metadata=json.dumps(archive.project_metadata, separators=(",", ":")),
                snapshots=json.dumps([s for s in archive.snapshots], separators=(",", ":")),
                as_built_records=json.dumps([r for r in archive.as_built_records], separators=(",", ":")),
                audit_events=json.dumps([e for e in archive.audit_events], separators=(",", ":")),
                extra_metadata=json.dumps(archive.metadata, separators=(",", ":")),
                checksum=archive.checksum,
            )
            session.merge(orm)
            session.commit()
        except Exception as write_exception:
            session.rollback()
            logger.error("DATABASE_TRANSACTION_FAILED_ARCHIVE_RECORD_SAVE: %s", write_exception)
            raise RuntimeError(
                f"DATABASE_TRANSACTION_FAILED_ARCHIVE_RECORD_SAVE_ABORTED: {str(write_exception)}"
            ) from write_exception
        finally:
            session.close()

    def list_archive_records(self, project_uuid: str) -> List[ArchiveRecord]:
        if not isinstance(project_uuid, str) or not project_uuid.strip():
            raise ValueError(f"DATABASE_QUERY_VIOLATION_INVALID_PROJECT_UUID_STRUCTURE: {project_uuid}")

        session = self._session()
        try:
            from fastra_core.digital_twin.database import ArchiveRecordORM
            rows = session.query(ArchiveRecordORM).filter(ArchiveRecordORM.project_uuid == project_uuid).all()

            validated_archives: List[ArchiveRecord] = []
            for row in rows:
                raw_snapshots = self._sanitize_json_loads(row.snapshots or "[]")
                raw_as_built = self._sanitize_json_loads(row.as_built_records or "[]")
                raw_audit = self._sanitize_json_loads(row.audit_events or "[]")

                archive_payload = {
                    "archive_uuid": row.archive_uuid,
                    "project_uuid": row.project_uuid,
                    "archived_at": row.archived_at,
                    "project_metadata": self._sanitize_json_loads(row.project_metadata or "{}"),
                    "snapshots": raw_snapshots,
                    "as_built_records": raw_as_built,
                    "audit_events": raw_audit,
                    "metadata": self._sanitize_json_loads(row.extra_metadata or "{}"),
                    "checksum": row.checksum or "",
                }
                archive_instance = ArchiveRecord(**archive_payload)

                if not archive_instance.verify_integrity():
                    logger.error(
                        "DATABASE_CORRUPTION_DETECTED_ARCHIVE_RECORD_CHECKSUM_MISMATCH: %s",
                        row.archive_uuid,
                    )
                    raise ValueError(
                        f"DATABASE_CORRUPTION_DETECTED_ARCHIVE_RECORD_CHECKSUM_MISMATCH: {row.archive_uuid}"
                    )

                validated_archives.append(archive_instance)

            return validated_archives
        finally:
            session.close()

    def get_archive_record(self, archive_uuid: str) -> Optional[ArchiveRecord]:
        if not isinstance(archive_uuid, str) or not archive_uuid.strip():
            return None

        session = self._session()
        try:
            from fastra_core.digital_twin.database import ArchiveRecordORM
            row = session.query(ArchiveRecordORM).filter(ArchiveRecordORM.archive_uuid == archive_uuid).first()
            if row is None:
                return None

            raw_snapshots = self._sanitize_json_loads(row.snapshots or "[]")
            raw_as_built = self._sanitize_json_loads(row.as_built_records or "[]")
            raw_audit = self._sanitize_json_loads(row.audit_events or "[]")

            archive_payload = {
                "archive_uuid": row.archive_uuid,
                "project_uuid": row.project_uuid,
                "archived_at": row.archived_at,
                "project_metadata": self._sanitize_json_loads(row.project_metadata or "{}"),
                "snapshots": raw_snapshots,
                "as_built_records": raw_as_built,
                "audit_events": raw_audit,
                "metadata": self._sanitize_json_loads(row.extra_metadata or "{}"),
                "checksum": row.checksum or "",
            }
            return ArchiveRecord.model_validate(archive_payload)
        finally:
            session.close()
            
    def save_ai_event(self, event: Any) -> None:
        if event is None:
            raise TypeError("AI_EVENT_OBJECT_CANNOT_BE_NULL")

        session = self._session()
        try:
            from fastra_core.digital_twin.database import AIEventORM

            component_value = event.ai_component.value if hasattr(event.ai_component, "value") else str(event.ai_component)

            orm = AIEventORM(
                event_uuid=event.event_uuid,
                ai_component=component_value,
                prompt_payload=json.dumps(
                    event.prompt_payload if isinstance(event.prompt_payload, dict) else {},
                    separators=(",", ":"),
                ),
                response_payload=json.dumps(
                    event.response_payload if isinstance(event.response_payload, dict) else {},
                    separators=(",", ":"),
                ),
                execution_time_ms=float(event.execution_time_ms),
                timestamp=str(event.timestamp),
            )
            session.merge(orm)
            session.commit()
        except Exception as write_exception:
            session.rollback()
            logger.error("DATABASE_TRANSACTION_FAILED_AI_EVENT_SAVE: %s", write_exception)
            raise RuntimeError(
                f"DATABASE_TRANSACTION_FAILED_AI_EVENT_SAVE_ABORTED: {str(write_exception)}"
            ) from write_exception
        finally:
            session.close()