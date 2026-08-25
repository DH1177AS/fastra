"""
ACES-600 Digital Twin Persistence Layer
Implementasi store berbasis SQLite untuk menggantikan in-memory store.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastra_core.digital_twin.audit import AuditEvent
from fastra_core.digital_twin.change_order import ChangeOrder, ApprovalStep
from fastra_core.digital_twin.progress import ProgressEntry
from fastra_core.digital_twin.snapshot import Snapshot
from fastra_core.digital_twin.as_built import AsBuiltRecord
from fastra_core.digital_twin.archiving import ArchiveRecord


class SQLiteDigitalTwinDB:
    """Database SQLite untuk seluruh data Digital Twin."""

    def __init__(self, db_path: str = ":memory:") -> None:
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self) -> None:
        cursor = self.conn.cursor()
        cursor.execute("""
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
        """)
        cursor.execute("""
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
        """)
        cursor.execute("""
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
        """)
        cursor.execute("""
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
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS as_built_records (
                record_uuid TEXT PRIMARY KEY,
                project_uuid TEXT NOT NULL,
                entity_uuid TEXT NOT NULL,
                planned_state TEXT,
                as_built_state TEXT,
                differences TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS archive_records (
                archive_uuid TEXT PRIMARY KEY,
                project_uuid TEXT NOT NULL,
                archived_at TEXT NOT NULL,
                project_metadata TEXT,
                snapshots TEXT,
                as_built_records TEXT,
                audit_events TEXT,
                metadata TEXT
            )
        """)
        self.conn.commit()

    # ---------- SNAPSHOT ----------
    def save_snapshot(self, snap: Snapshot) -> None:
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO snapshots
            (snapshot_uuid, snapshot_name, snapshot_type, project_uuid, timestamp,
             description, ccm_state, boq_state, rab_state, schedule_state, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                snap.snapshot_uuid, snap.snapshot_name, snap.snapshot_type,
                snap.project_uuid, snap.timestamp, snap.description,
                json.dumps(snap.ccm_state, default=str),
                json.dumps(snap.boq_state, default=str) if snap.boq_state is not None else None,
                json.dumps(snap.rab_state, default=str) if snap.rab_state is not None else None,
                json.dumps(snap.schedule_state, default=str) if snap.schedule_state is not None else None,
                json.dumps(snap.metadata, default=str),
            ),
        )
        self.conn.commit()

    def get_snapshot(self, snapshot_uuid: str) -> Optional[Snapshot]:
        cursor = self.conn.cursor()
        row = cursor.execute("SELECT * FROM snapshots WHERE snapshot_uuid = ?", (snapshot_uuid,)).fetchone()
        if row is None:
            return None
        return Snapshot(
            snapshot_uuid=row["snapshot_uuid"],
            snapshot_name=row["snapshot_name"],
            snapshot_type=row["snapshot_type"],
            project_uuid=row["project_uuid"],
            timestamp=row["timestamp"],
            description=row["description"] or "",
            ccm_state=json.loads(row["ccm_state"]),
            boq_state=json.loads(row["boq_state"]) if row["boq_state"] else None,
            rab_state=json.loads(row["rab_state"]) if row["rab_state"] else None,
            schedule_state=json.loads(row["schedule_state"]) if row["schedule_state"] else None,
            metadata=json.loads(row["metadata"]) if row["metadata"] else {},
        )

    # ---------- AUDIT ----------
    def save_audit_event(self, event: AuditEvent) -> None:
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO audit_events
            (event_uuid, event_type, actor, target, change_detail, reason, related_vo,
             ip_address, user_agent, timestamp, metadata, prev_hash, hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event.event_uuid, event.event_type,
                json.dumps(event.actor, default=str),
                json.dumps(event.target, default=str),
                json.dumps(event.change_detail, default=str),
                event.reason, event.related_vo, event.ip_address, event.user_agent,
                event.timestamp, json.dumps(event.metadata, default=str),
                event.prev_hash, event.hash,
            ),
        )
        self.conn.commit()

    def get_audit_event(self, event_uuid: str) -> Optional[AuditEvent]:
        cursor = self.conn.cursor()
        row = cursor.execute("SELECT * FROM audit_events WHERE event_uuid = ?", (event_uuid,)).fetchone()
        if row is None:
            return None
        return AuditEvent(
            event_type=row["event_type"],
            actor=json.loads(row["actor"]),
            target=json.loads(row["target"]),
            change_detail=json.loads(row["change_detail"]) if row["change_detail"] else {},
            reason=row["reason"] or "",
            related_vo=row["related_vo"],
            ip_address=row["ip_address"],
            user_agent=row["user_agent"],
            timestamp=row["timestamp"],
            event_uuid=row["event_uuid"],
            metadata=json.loads(row["metadata"]) if row["metadata"] else {},
            prev_hash=row["prev_hash"] or "",
            hash=row["hash"] or "",
        )

    # ---------- PROGRESS ----------
    def save_progress_entry(self, entry: ProgressEntry) -> None:
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO progress_entries
            (progress_entry_uuid, project_uuid, report_date, report_type, period_start,
             period_end, overall_progress_percentage, entity_progress, issues, weather,
             labor_on_site, material_delivered, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                entry.progress_entry_uuid, entry.project_uuid, entry.report_date,
                entry.report_type, entry.period_start, entry.period_end,
                entry.overall_progress_percentage,
                json.dumps([ep.__dict__ for ep in entry.entity_progress], default=str),
                json.dumps([iss.__dict__ for iss in entry.issues], default=str),
                json.dumps(entry.weather, default=str),
                json.dumps(entry.labor_on_site, default=str),
                json.dumps([md.__dict__ for md in entry.material_delivered], default=str),
                json.dumps(entry.metadata, default=str),
            ),
        )
        self.conn.commit()

    # ---------- CHANGE ORDER ----------
    def save_change_order(self, vo: ChangeOrder) -> None:
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO change_orders
            (vo_uuid, project_uuid, vo_number, description, reason, request_date, requested_by,
             ccm_changes, boq_impact, cost_impact, schedule_impact, status, approval_chain,
             baseline_before, baseline_after, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                vo.vo_uuid, vo.project_uuid, vo.vo_number, vo.description, vo.reason,
                vo.request_date, vo.requested_by,
                json.dumps(vo.ccm_changes, default=str),
                json.dumps(vo.boq_impact, default=str),
                json.dumps(vo.cost_impact, default=str),
                json.dumps(vo.schedule_impact, default=str),
                vo.status,
                json.dumps([step.__dict__ for step in vo.approval_chain], default=str),
                vo.baseline_before, vo.baseline_after,
                json.dumps(vo.metadata, default=str),
            ),
        )
        self.conn.commit()

    # ---------- AS-BUILT ----------
    def save_as_built_record(self, record: AsBuiltRecord) -> None:
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO as_built_records
            (record_uuid, project_uuid, entity_uuid, planned_state, as_built_state, differences)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                record.record_uuid, record.project_uuid, record.entity_uuid,
                json.dumps(record.planned_state, default=str),
                json.dumps(record.as_built_state, default=str),
                json.dumps([d.__dict__ for d in record.differences], default=str),
            ),
        )
        self.conn.commit()

    # ---------- ARCHIVE ----------
    def save_archive_record(self, archive: ArchiveRecord) -> None:
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO archive_records
            (archive_uuid, project_uuid, archived_at, project_metadata, snapshots,
             as_built_records, audit_events, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                archive.archive_uuid, archive.project_uuid, archive.archived_at,
                json.dumps(archive.project_metadata, default=str),
                json.dumps(archive.snapshots, default=str),
                json.dumps(archive.as_built_records, default=str),
                json.dumps(archive.audit_events, default=str),
                json.dumps(archive.metadata, default=str),
            ),
        )
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()
