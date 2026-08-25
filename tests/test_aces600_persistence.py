"""
Test persistensi SQLite untuk Digital Twin (menutup celah #1).
"""
import pytest
from fastra_core.digital_twin import (
    SQLiteDigitalTwinDB, Snapshot, AuditEvent, ProgressEntry, EntityProgress,
    ChangeOrder, AsBuiltRecord, ArchiveRecord
)


def test_sqlite_snapshot_persists():
    db = SQLiteDigitalTwinDB(":memory:")
    snap = Snapshot(
        snapshot_uuid="snap-001",
        snapshot_name="Baseline",
        snapshot_type="BASELINE",
        project_uuid="proj-001",
        timestamp="2026-08-24T10:00:00Z",
        ccm_state={"entities": {"wall-001": {"length": 5.0}}},
    )
    db.save_snapshot(snap)
    loaded = db.get_snapshot("snap-001")
    assert loaded is not None
    assert loaded.snapshot_name == "Baseline"
    assert loaded.ccm_state["entities"]["wall-001"]["length"] == 5.0
    db.close()


def test_sqlite_audit_event_persists():
    db = SQLiteDigitalTwinDB(":memory:")
    event = AuditEvent(
        event_type="ENTITY_MODIFIED",
        actor={"user_name": "Budi"},
        target={"entity_uuid": "wall-001"},
        timestamp="2026-08-24T10:00:00Z",
    )
    db.save_audit_event(event)
    loaded = db.get_audit_event(event.event_uuid)
    assert loaded is not None
    assert loaded.event_type == "ENTITY_MODIFIED"
    assert loaded.actor["user_name"] == "Budi"
    db.close()
