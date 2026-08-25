"""
Test hardening offline-first dan archiving nyata.
"""
import pytest
from fastra_core.digital_twin import SQLiteOfflineStore, SyncEngine, ArchiveStore, SnapshotStore, AsBuiltStore, AuditStore


def test_sqlite_offline_store_persists():
    store = SQLiteOfflineStore(":memory:")
    store.save_record("PROGRESS", {"entity_uuid": "wall-001", "completed": 60.0}, created_at="2026-08-24T10:00:00Z")
    store.save_record("PHOTO", {"photo_uuid": "photo-001"}, created_at="2026-08-24T10:05:00Z")
    assert store.count_total() == 2
    assert store.count_pending() == 2
    pending = store.get_pending_records()
    assert len(pending) == 2
    store.mark_synced(pending[0]["local_id"])
    assert store.count_pending() == 1
    store.close()


def test_archive_checksum_restore():
    snap_store = SnapshotStore()
    asb_store = AsBuiltStore()
    audit_store = AuditStore()
    snap_store.create_snapshot(
        project_uuid="proj-001",
        snapshot_name="Final",
        snapshot_type="AS_BUILT",
        ccm_state={"entities": {"wall-001": {"length": 5.1}}},
        timestamp="2026-08-24T10:00:00Z",
    )
    archive_store = ArchiveStore()
    archive = archive_store.create_archive(
        project_uuid="proj-001",
        snapshot_store=snap_store,
        as_built_store=asb_store,
        audit_store=audit_store,
        archived_at="2026-08-24T10:00:00Z",
    )
    assert archive.checksum != ""
    restored = archive_store.restore_archive(archive.archive_uuid)
    assert restored is not None
    assert restored.project_uuid == "proj-001"
    assert restored.snapshots[0]["snapshot_name"] == "Final"
