"""
Compliance tests untuk ACES-600 Fase 5:
ACTS-600-018
"""
import pytest
from fastra_core.digital_twin import (
    SnapshotStore, AsBuiltStore, AuditStore, ArchiveStore
)


def test_archiving_and_restore():
    # Siapkan store
    snap_store = SnapshotStore()
    as_built_store = AsBuiltStore()
    audit_store = AuditStore()

    # Tambah snapshot
    snap_store.create_snapshot(
        project_uuid="proj-001",
        snapshot_name="Baseline Final",
        snapshot_type="AS_BUILT",
        ccm_state={"entities": {"wall-001": {"length": 5.1}}},
        timestamp="2026-08-20T10:00:00Z",
    )

    # Tambah as-built record
    from fastra_core.digital_twin import AsBuiltRecord
    record = AsBuiltRecord(
        project_uuid="proj-001",
        entity_uuid="wall-001",
        planned_state={"length": 5.0},
        as_built_state={"length": 5.1},
    )
    as_built_store.add_record(record)

    # Tambah audit event
    audit_store.record_event(
        event_type="PROJECT_COMPLETED",
        actor={"user_name": "System"},
        target={"project_uuid": "proj-001"},
        timestamp="2026-08-20T10:00:00Z",
    )

    # Buat arsip
    archive_store = ArchiveStore()
    archive = archive_store.create_archive(
        project_uuid="proj-001",
        snapshot_store=snap_store,
        as_built_store=as_built_store,
        audit_store=audit_store,
        project_metadata={"name": "Proyek Test"},
    )

    assert archive.project_uuid == "proj-001"
    assert len(archive.snapshots) == 1
    assert len(archive.as_built_records) == 1
    assert len(archive.audit_events) == 1

    # Restore
    restored = archive_store.restore_archive(archive.archive_uuid)
    assert restored is not None
    assert restored.project_uuid == "proj-001"
    assert restored.snapshots[0]["snapshot_name"] == "Baseline Final"
    assert restored.as_built_records[0]["entity_uuid"] == "wall-001"
