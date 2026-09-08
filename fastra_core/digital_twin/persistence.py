# fastra_core\digital_twin\persistence.py

from __future__ import annotations

import json
import logging
import math
import sqlite3
import threading
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastra_core.digital_twin.archiving import ArchiveRecord
from fastra_core.digital_twin.as_built import AsBuiltRecord, AsBuiltDifference
from fastra_core.digital_twin.audit import AuditEvent
from fastra_core.digital_twin.change_order import ChangeOrder, ApprovalStep
from fastra_core.digital_twin.progress import ProgressEntry, EntityProgress, Issue, MaterialDelivery
from fastra_core.digital_twin.snapshot import Snapshot
from fastra_core.identity import Identity
from fastra_core.serialization.canonical_json import to_json

logger = logging.getLogger("fastra_core.digital_twin.persistence")


class SQLiteDigitalTwinDB:
    """Database SQLite murni untuk seluruh ekosistem data Digital Twin."""

    def __init__(self, db_path: str = ":memory:") -> None:
        if not isinstance(db_path, str) or not db_path.strip():
            raise ValueError("PERSISTENCE_ERROR_DATABASE_PATH_CANNOT_BE_NULL_OR_EMPTY")

        self._lock = threading.Lock()
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row

        if db_path != ":memory:":
            self.conn.execute("PRAGMA journal_mode=WAL;")

        self._create_tables()
        logger.info("SQLite persistence layer initialized: %s", db_path)

    def _create_tables(self) -> None:
        with self._lock:
            cursor = self.conn.cursor()
            try:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS snapshots (
                        snapshot_uuid TEXT PRIMARY KEY,
                        snapshot_name TEXT NOT NULL,
                        snapshot_type TEXT NOT NULL,
                        project_uuid TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        description TEXT,
                        ccm_state TEXT NOT NULL,
                        boq_state TEXT,
                        rab_state TEXT,
                        schedule_state TEXT,
                        metadata TEXT
                    )
                    """
                )
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS audit_events (
                        event_uuid TEXT PRIMARY KEY,
                        event_type TEXT NOT NULL,
                        actor TEXT NOT NULL,
                        target TEXT NOT NULL,
                        change_detail TEXT,
                        reason TEXT,
                        related_vo TEXT,
                        ip_address TEXT,
                        user_agent TEXT,
                        timestamp TEXT NOT NULL,
                        metadata TEXT,
                        prev_hash TEXT,
                        hash TEXT
                    )
                    """
                )
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS progress_entries (
                        progress_entry_uuid TEXT PRIMARY KEY,
                        project_uuid TEXT NOT NULL,
                        report_date TEXT NOT NULL,
                        report_type TEXT NOT NULL,
                        period_start TEXT,
                        period_end TEXT,
                        overall_progress_percentage REAL,
                        entity_progress TEXT,
                        issues TEXT,
                        weather TEXT,
                        labor_on_site TEXT,
                        material_delivered TEXT,
                        metadata TEXT
                    )
                    """
                )
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS change_orders (
                        vo_uuid TEXT PRIMARY KEY,
                        project_uuid TEXT NOT NULL,
                        vo_number TEXT NOT NULL,
                        description TEXT,
                        reason TEXT,
                        request_date TEXT,
                        requested_by TEXT,
                        ccm_changes TEXT,
                        boq_impact TEXT,
                        cost_impact TEXT,
                        schedule_impact TEXT,
                        status TEXT,
                        approval_chain TEXT,
                        baseline_before TEXT,
                        baseline_after TEXT,
                        metadata TEXT
                    )
                    """
                )
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS as_built_records (
                        record_uuid TEXT PRIMARY KEY,
                        project_uuid TEXT NOT NULL,
                        entity_uuid TEXT NOT NULL,
                        planned_state TEXT,
                        as_built_state TEXT,
                        differences TEXT
                    )
                    """
                )
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS archive_records (
                        archive_uuid TEXT PRIMARY KEY,
                        project_uuid TEXT NOT NULL,
                        archived_at TEXT NOT NULL,
                        project_metadata TEXT,
                        snapshots TEXT,
                        as_built_records TEXT,
                        audit_events TEXT,
                        metadata TEXT,
                        checksum TEXT
                    )
                    """
                )
                self.conn.commit()
            except sqlite3.Error as exc:
                self.conn.rollback()
                logger.error("DATABASE_INITIALIZATION_FAILED: %s", exc)
                raise RuntimeError(f"DATABASE_INITIALIZATION_FAILED: {exc}") from exc

    def _verify_numeric_integrity(self, node: Any) -> None:
        """Rekursif memeriksa anomali floating-point (NaN/inf) sebelum serialisasi."""
        if node is None:
            return
        if isinstance(node, dict):
            for v in node.values():
                self._verify_numeric_integrity(v)
        elif isinstance(node, (list, tuple, set)):
            for item in node:
                self._verify_numeric_integrity(item)
        elif isinstance(node, (int, float)) and not isinstance(node, bool):
            if math.isnan(node) or math.isinf(node):
                raise ValueError("NUMERIC_ANOMALY_DETECTED_PERSISTENCE_STATE_CONTAINS_NAN_OR_INFINITE_VALUE")

    def _sanitize_json_loads(self, raw_str: Optional[str]) -> Any:
        """Aman memuat JSON dari database, menolak NaN/Inf."""
        if not raw_str or not raw_str.strip():
            return {}
        try:
            parsed = json.loads(raw_str)
        except (json.JSONDecodeError, TypeError) as exc:
            logger.error("INVALID_JSON_IN_DATABASE: %r", raw_str)
            raise ValueError(f"DATABASE_JSON_CORRUPTION: {exc}") from exc
        self._verify_numeric_integrity(parsed)
        return parsed

    # ---------- SNAPSHOT OPERATIONS ----------
    def save_snapshot(self, snap: Snapshot) -> None:
        if not isinstance(snap, Snapshot):
            logger.error("SAVE_SNAPSHOT_INVALID_TYPE: %r", snap)
            raise TypeError("PERSISTENCE_VIOLATION_INPUT_MUST_BE_AN_INSTANCE_OF_SNAPSHOT_CLASS")

        if not isinstance(snap.project_uuid, str) or not snap.project_uuid.strip() or not isinstance(snap.snapshot_uuid, str) or not snap.snapshot_uuid.strip():
            logger.error("SAVE_SNAPSHOT_INVALID_UUID: project=%s snap=%s", snap.project_uuid, snap.snapshot_uuid)
            raise ValueError("INTEGRITY_VIOLATION_INVALID_UUID_STRUCTURE_IN_SNAPSHOT_PAYLOAD")

        self._verify_numeric_integrity(snap.ccm_state)
        self._verify_numeric_integrity(snap.boq_state)
        self._verify_numeric_integrity(snap.rab_state)
        self._verify_numeric_integrity(snap.schedule_state)
        self._verify_numeric_integrity(snap.metadata)

        with self._lock:
            cursor = self.conn.cursor()
            try:
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO snapshots
                    (snapshot_uuid, snapshot_name, snapshot_type, project_uuid, timestamp,
                     description, ccm_state, boq_state, rab_state, schedule_state, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        snap.snapshot_uuid,
                        snap.snapshot_name.strip(),
                        snap.snapshot_type.value if hasattr(snap.snapshot_type, "value") else str(snap.snapshot_type),
                        snap.project_uuid,
                        snap.timestamp.isoformat() if isinstance(snap.timestamp, datetime) else str(snap.timestamp),
                        snap.description.strip() if snap.description else "",
                        to_json(snap.ccm_state),
                        to_json(snap.boq_state) if snap.boq_state is not None else None,
                        to_json(snap.rab_state) if snap.rab_state is not None else None,
                        to_json(snap.schedule_state) if snap.schedule_state is not None else None,
                        to_json(snap.metadata),
                    ),
                )
                self.conn.commit()
                logger.info("Snapshot saved: %s", snap.snapshot_uuid)
            except sqlite3.Error as exc:
                self.conn.rollback()
                logger.error("DATABASE_TRANSACTION_FAILED_SNAPSHOT_SAVE: %s", exc)
                raise RuntimeError(f"DATABASE_TRANSACTION_FAILED_SNAPSHOT_SAVE_ABORTED: {exc}") from exc

    def get_snapshot(self, snapshot_uuid: str) -> Optional[Snapshot]:
        if not isinstance(snapshot_uuid, str) or not snapshot_uuid.strip():
            logger.warning("GET_SNAPSHOT_INVALID_UUID: %r", snapshot_uuid)
            return None

        with self._lock:
            cursor = self.conn.cursor()
            row = cursor.execute("SELECT * FROM snapshots WHERE snapshot_uuid = ?", (snapshot_uuid,)).fetchone()
            if row is None:
                return None

            snapshot_payload = {
                "snapshot_uuid": row["snapshot_uuid"],
                "snapshot_name": row["snapshot_name"],
                "snapshot_type": row["snapshot_type"],
                "project_uuid": row["project_uuid"],
                "timestamp": row["timestamp"],
                "description": row["description"] or "",
                "ccm_state": self._sanitize_json_loads(row["ccm_state"]),
                "boq_state": self._sanitize_json_loads(row["boq_state"]) if row["boq_state"] else None,
                "rab_state": self._sanitize_json_loads(row["rab_state"]) if row["rab_state"] else None,
                "schedule_state": self._sanitize_json_loads(row["schedule_state"]) if row["schedule_state"] else None,
                "metadata": self._sanitize_json_loads(row["metadata"]) if row["metadata"] else {},
            }
            return Snapshot(**snapshot_payload)

    # ---------- AUDIT OPERATIONS ----------
    def save_audit_event(self, event: AuditEvent) -> None:
        if not isinstance(event, AuditEvent):
            logger.error("SAVE_AUDIT_EVENT_INVALID_TYPE: %r", event)
            raise TypeError("PERSISTENCE_VIOLATION_INPUT_MUST_BE_AN_INSTANCE_OF_AUDIT_EVENT_CLASS")

        self._verify_numeric_integrity(event.actor)
        self._verify_numeric_integrity(event.target)
        self._verify_numeric_integrity(event.change_detail)
        self._verify_numeric_integrity(event.metadata)

        with self._lock:
            cursor = self.conn.cursor()
            try:
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO audit_events
                    (event_uuid, event_type, actor, target, change_detail, reason, related_vo,
                     ip_address, user_agent, timestamp, metadata, prev_hash, hash)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        event.event_uuid,
                        event.event_type,
                        to_json(event.actor),
                        to_json(event.target),
                        to_json(event.change_detail),
                        event.reason.strip() if event.reason else "",
                        event.related_vo,
                        event.ip_address,
                        event.user_agent,
                        event.timestamp.isoformat() if isinstance(event.timestamp, datetime) else str(event.timestamp),
                        to_json(event.metadata),
                        event.prev_hash,
                        event.hash,
                    ),
                )
                self.conn.commit()
                logger.info("Audit event saved: %s", event.event_uuid)
            except sqlite3.Error as exc:
                self.conn.rollback()
                logger.error("DATABASE_TRANSACTION_FAILED_AUDIT_EVENT_SAVE: %s", exc)
                raise RuntimeError(f"DATABASE_TRANSACTION_FAILED_AUDIT_EVENT_SAVE_ABORTED: {exc}") from exc

    def get_audit_event(self, event_uuid: str) -> Optional[AuditEvent]:
        if not isinstance(event_uuid, str) or not Identity.is_valid(event_uuid):
            logger.warning("GET_AUDIT_EVENT_INVALID_UUID: %r", event_uuid)
            return None

        with self._lock:
            cursor = self.conn.cursor()
            row = cursor.execute("SELECT * FROM audit_events WHERE event_uuid = ?", (event_uuid,)).fetchone()
            if row is None:
                return None

            audit_payload = {
                "event_type": row["event_type"],
                "actor": self._sanitize_json_loads(row["actor"]),
                "target": self._sanitize_json_loads(row["target"]),
                "change_detail": self._sanitize_json_loads(row["change_detail"])
                if row["change_detail"]
                else {},
                "reason": row["reason"] or "",
                "related_vo": row["related_vo"],
                "ip_address": row["ip_address"],
                "user_agent": row["user_agent"],
                "timestamp": str(row["timestamp"]),
                "event_uuid": row["event_uuid"],
                "metadata": self._sanitize_json_loads(row["metadata"]) if row["metadata"] else {},
                "prev_hash": row["prev_hash"] or "",
                "hash": row["hash"] or "",
            }
            return AuditEvent(**audit_payload)

    # ---------- PROGRESS OPERATIONS ----------
    def save_progress_entry(self, entry: ProgressEntry) -> None:
        if not isinstance(entry, ProgressEntry):
            logger.error("SAVE_PROGRESS_ENTRY_INVALID_TYPE: %r", entry)
            raise TypeError("PERSISTENCE_VIOLATION_INPUT_MUST_BE_AN_INSTANCE_OF_PROGRESS_ENTRY_CLASS")

        self._verify_numeric_integrity(entry.weather)
        self._verify_numeric_integrity(entry.labor_on_site)
        self._verify_numeric_integrity(entry.metadata)

        with self._lock:
            cursor = self.conn.cursor()
            try:
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO progress_entries
                    (progress_entry_uuid, project_uuid, report_date, report_type, period_start,
                     period_end, overall_progress_percentage, entity_progress, issues, weather,
                     labor_on_site, material_delivered, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        entry.progress_entry_uuid,
                        entry.project_uuid,
                        entry.report_date.isoformat()
                        if isinstance(entry.report_date, datetime)
                        else str(entry.report_date),
                        entry.report_type.value if hasattr(entry.report_type, "value") else str(entry.report_type),
                        entry.period_start.isoformat()
                        if isinstance(entry.period_start, datetime)
                        else str(entry.period_start),
                        entry.period_end.isoformat()
                        if isinstance(entry.period_end, datetime)
                        else str(entry.period_end),
                        float(entry.overall_progress_percentage),
                        to_json([ep.model_dump(mode="json") for ep in entry.entity_progress]),
                        to_json([iss.model_dump(mode="json") for iss in entry.issues]),
                        to_json(entry.weather),
                        to_json(entry.labor_on_site),
                        to_json([md.model_dump(mode="json") for md in entry.material_delivered]),
                        to_json(entry.metadata),
                    ),
                )
                self.conn.commit()
                logger.info("Progress entry saved: %s", entry.progress_entry_uuid)
            except sqlite3.Error as exc:
                self.conn.rollback()
                logger.error("DATABASE_TRANSACTION_FAILED_PROGRESS_ENTRY_SAVE: %s", exc)
                raise RuntimeError(f"DATABASE_TRANSACTION_FAILED_PROGRESS_ENTRY_SAVE_ABORTED: {exc}") from exc

    # ---------- CHANGE ORDER (VO) OPERATIONS ----------
    def save_change_order(self, vo: ChangeOrder) -> None:
        if not isinstance(vo, ChangeOrder):
            logger.error("SAVE_CHANGE_ORDER_INVALID_TYPE: %r", vo)
            raise TypeError("PERSISTENCE_VIOLATION_INPUT_MUST_BE_AN_INSTANCE_OF_CHANGE_ORDER_CLASS")

        self._verify_numeric_integrity(vo.ccm_changes)
        self._verify_numeric_integrity(vo.boq_impact)
        self._verify_numeric_integrity(vo.schedule_impact)
        self._verify_numeric_integrity(vo.metadata)

        with self._lock:
            cursor = self.conn.cursor()
            try:
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO change_orders
                    (vo_uuid, project_uuid, vo_number, description, reason, request_date, requested_by,
                     ccm_changes, boq_impact, cost_impact, schedule_impact, status, approval_chain,
                     baseline_before, baseline_after, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        vo.vo_uuid,
                        vo.project_uuid,
                        vo.vo_number.strip(),
                        vo.description.strip(),
                        vo.reason.strip(),
                        vo.request_date.isoformat()
                        if isinstance(vo.request_date, datetime)
                        else str(vo.request_date),
                        vo.requested_by.strip(),
                        to_json(vo.ccm_changes),
                        to_json(vo.boq_impact),
                        to_json({k: v.model_dump(mode="json") for k, v in vo.cost_impact.items()}),
                        to_json(vo.schedule_impact),
                        vo.status.value if hasattr(vo.status, "value") else str(vo.status),
                        to_json([step.model_dump(mode="json") for step in vo.approval_chain]),
                        vo.baseline_before,
                        vo.baseline_after,
                        to_json(vo.metadata),
                    ),
                )
                self.conn.commit()
                logger.info("Change order saved: %s", vo.vo_uuid)
            except sqlite3.Error as exc:
                self.conn.rollback()
                logger.error("DATABASE_TRANSACTION_FAILED_CHANGE_ORDER_SAVE: %s", exc)
                raise RuntimeError(f"DATABASE_TRANSACTION_FAILED_CHANGE_ORDER_SAVE_ABORTED: {exc}") from exc

    # ---------- AS-BUILT CAPTURE OPERATIONS ----------
    def save_as_built_record(self, record: AsBuiltRecord) -> None:
        if not isinstance(record, AsBuiltRecord):
            logger.error("SAVE_AS_BUILT_RECORD_INVALID_TYPE: %r", record)
            raise TypeError("PERSISTENCE_VIOLATION_INPUT_MUST_BE_AN_INSTANCE_OF_AS_BUILT_RECORD_CLASS")

        self._verify_numeric_integrity(record.planned_state)
        self._verify_numeric_integrity(record.as_built_state)

        with self._lock:
            cursor = self.conn.cursor()
            try:
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO as_built_records
                    (record_uuid, project_uuid, entity_uuid, planned_state, as_built_state, differences)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        record.record_uuid,
                        record.project_uuid,
                        record.entity_uuid,
                        to_json(record.planned_state),
                        to_json(record.as_built_state),
                        to_json([d.model_dump(mode="json") for d in record.differences]),
                    ),
                )
                self.conn.commit()
                logger.info("As-built record saved: %s", record.record_uuid)
            except sqlite3.Error as exc:
                self.conn.rollback()
                logger.error("DATABASE_TRANSACTION_FAILED_AS_BUILT_RECORD_SAVE: %s", exc)
                raise RuntimeError(f"DATABASE_TRANSACTION_FAILED_AS_BUILT_RECORD_SAVE_ABORTED: {exc}") from exc

    # ---------- DIGITAL TWIN ARCHIVING OPERATIONS ----------
    def save_archive_record(self, archive: ArchiveRecord) -> None:
        if not isinstance(archive, ArchiveRecord):
            logger.error("SAVE_ARCHIVE_RECORD_INVALID_TYPE: %r", archive)
            raise TypeError("PERSISTENCE_VIOLATION_INPUT_MUST_BE_AN_INSTANCE_OF_ARCHIVE_RECORD_CLASS")

        if not archive.verify_integrity():
            logger.error("CRYPTOGRAPHIC_INTEGRITY_VIOLATION: %s", archive.archive_uuid)
            raise ValueError(
                f"CRYPTOGRAPHIC_INTEGRITY_VIOLATION_CANNOT_SAVE_CORRUPTED_ARCHIVE: {archive.archive_uuid}"
            )

        with self._lock:
            cursor = self.conn.cursor()
            try:
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO archive_records
                    (archive_uuid, project_uuid, archived_at, project_metadata, snapshots,
                     as_built_records, audit_events, metadata, checksum)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        archive.archive_uuid,
                        archive.project_uuid,
                        archive.archived_at.isoformat()
                        if isinstance(archive.archived_at, datetime)
                        else str(archive.archived_at),
                        to_json(archive.project_metadata),
                        to_json([s for s in archive.snapshots]),
                        to_json([r for r in archive.as_built_records]),
                        to_json([e for e in archive.audit_events]),
                        to_json(archive.metadata),
                        archive.checksum,
                    ),
                )
                self.conn.commit()
                logger.info("Archive record saved: %s", archive.archive_uuid)
            except sqlite3.Error as exc:
                self.conn.rollback()
                logger.error("DATABASE_TRANSACTION_FAILED_ARCHIVE_RECORD_SAVE: %s", exc)
                raise RuntimeError(f"DATABASE_TRANSACTION_FAILED_ARCHIVE_RECORD_SAVE_ABORTED: {exc}") from exc

    # ---------- LIST OPERATIONS (OPTIONAL BUT USEFUL) ----------
    def list_snapshots(self, project_uuid: str) -> List[Snapshot]:
        if not isinstance(project_uuid, str) or not project_uuid.strip():
            raise ValueError(f"INVALID_PROJECT_UUID: {project_uuid}")

        with self._lock:
            cursor = self.conn.cursor()
            rows = cursor.execute(
                "SELECT * FROM snapshots WHERE project_uuid = ?", (project_uuid,)
            ).fetchall()
            return [self.get_snapshot(row["snapshot_uuid"]) for row in rows if row]

    def list_audit_events(self) -> List[AuditEvent]:
        with self._lock:
            cursor = self.conn.cursor()
            rows = cursor.execute("SELECT * FROM audit_events").fetchall()
            return [self.get_audit_event(row["event_uuid"]) for row in rows if row]

    def list_progress_entries(self, project_uuid: str) -> List[ProgressEntry]:
        # Similar implementation would be needed if used elsewhere
        raise NotImplementedError("Not implemented in this layer")

    def list_change_orders(self, project_uuid: str) -> List[ChangeOrder]:
        # Similar implementation
        raise NotImplementedError("Not implemented in this layer")

    def list_as_built_records(self, project_uuid: str) -> List[AsBuiltRecord]:
        # Similar implementation
        raise NotImplementedError("Not implemented in this layer")

    def list_archive_records(self, project_uuid: str) -> List[ArchiveRecord]:
        # Similar implementation
        raise NotImplementedError("Not implemented in this layer")

    def close(self) -> None:
        """Menutup koneksi mesin database SQLite secara bersih."""
        with self._lock:
            self.conn.close()
            logger.info("SQLite connection closed")