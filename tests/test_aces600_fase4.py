"""
Compliance tests untuk ACES-600 Fase 4:
ACTS-600-011, 012, 013, 014
"""
import pytest
from fastra_core.digital_twin import PhotoData, SnapshotStore, OfflineStore, SyncEngine


# ACTS-600-011: Photo: metadata lengkap
def test_photo_metadata_complete():
    photo = PhotoData(
        project_uuid="proj-001",
        capture_date="2026-08-15T14:30:00Z",
        capture_method="HP",
        captured_by="mandor-001",
        location={"latitude": -6.2, "longitude": 106.8, "elevation": 45.0},
        direction_degrees=270,
        entity_references=["wall-001", "wall-002"],
        tags=["dinding", "progres", "lantai-1"],
        file={"url": "https://storage.fastra.id/photos/proj-001/2026-08-15_143000.jpg",
              "hash": "sha256:abc123", "size_bytes": 2450000, "resolution": "4000x3000"},
        annotations=[{"type": "BOUNDING_BOX", "label": "Dinding Kamar", "coordinates": []}],
    )
    assert photo.photo_uuid is not None
    assert photo.project_uuid == "proj-001"
    assert photo.file["size_bytes"] == 2450000
    assert photo.location is not None
    assert photo.direction_degrees == 270
    assert len(photo.tags) == 3


# ACTS-600-012: Photo: entity reference valid
def test_photo_entity_reference_valid():
    store = SnapshotStore()
    ccm_state = {"entities": {"wall-001": {}, "wall-002": {}}}
    snap = store.create_snapshot(
        project_uuid="proj-001",
        snapshot_name="Desain",
        snapshot_type="CHECKPOINT",
        ccm_state=ccm_state,
    )
    photo_valid = PhotoData(
        project_uuid="proj-001",
        capture_date="2026-08-15T14:30:00Z",
        entity_references=["wall-001", "wall-002"],
    )
    assert photo_valid.validate_entity_references(snap) is True
    photo_invalid = PhotoData(
        project_uuid="proj-001",
        capture_date="2026-08-15T14:30:00Z",
        entity_references=["wall-999"],
    )
    assert photo_invalid.validate_entity_references(snap) is False


# ACTS-600-013: Offline: local storage berfungsi
def test_offline_local_storage():
    store = OfflineStore()
    store.save_record("PROGRESS", {"entity_uuid": "wall-001", "completed": 60.0})
    store.save_record("PHOTO", {"photo_uuid": "photo-001", "url": "..."})
    assert store.count_total() == 2
    assert store.count_pending() == 2
    record = store.get_record(list(store._records.keys())[0])
    assert record is not None
    assert record["record_type"] == "PROGRESS"


# ACTS-600-014: Sync: data offline tersinkronisasi
def test_sync_offline_data():
    offline = OfflineStore()
    offline.save_record("PROGRESS", {"entity_uuid": "wall-001", "completed": 60.0, "updated_at": "2026-08-15T10:00:00Z"})
    offline.save_record("PHOTO", {"photo_uuid": "photo-001", "updated_at": "2026-08-15T10:05:00Z"})

    engine = SyncEngine()
    result = engine.push(offline)

    assert result.pushed_count == 2
    assert result.pending_after == 0
    assert len(engine.server_store) == 2
    pulled = engine.pull()
    assert len(pulled) == 2
