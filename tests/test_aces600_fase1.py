"""
Compliance tests untuk ACES-600 Fase 1:
ACTS-600-001, 002, 003, 004, 005, 017, 020
"""
import pytest
from fastra_core.digital_twin import Version, VersionGraph, SnapshotStore


# ACTS-600-001: Versioning: entity version increment benar
def test_version_increment():
    v = Version(1, 2, 3)
    assert v.next_patch() == Version(1, 2, 4)
    assert v.next_minor() == Version(1, 3, 0)
    assert v.next_major() == Version(2, 0, 0)


# ACTS-600-002: Versioning: MAJOR.MINOR.PATCH valid
def test_version_parse_valid():
    v = Version.parse("1.2.3")
    assert v.major == 1 and v.minor == 2 and v.patch == 3
    with pytest.raises(Exception):
        Version.parse("1.2")
    with pytest.raises(Exception):
        Version.parse("abc")


# ACTS-600-003: Snapshot: merekam seluruh state CCM
def test_snapshot_records_ccm_state():
    store = SnapshotStore()
    ccm_state = {
        "entities": {
            "wall-001": {"id": "wall-001", "type": "Wall", "length": 5.0},
            "column-001": {"id": "column-001", "type": "Column", "width": 0.3},
        },
        "relationships": [("wall-001", "column-001")],
    }
    snap = store.create_snapshot(
        project_uuid="proj-001",
        snapshot_name="Desain Konsep",
        snapshot_type="BASELINE",
        ccm_state=ccm_state,
    )
    retrieved = store.get_snapshot(snap.snapshot_uuid)
    assert retrieved is not None
    assert retrieved.ccm_state == ccm_state
    assert retrieved.ccm_state["entities"]["wall-001"]["length"] == 5.0


# ACTS-600-004: Snapshot: dapat direstore
def test_snapshot_restore():
    store = SnapshotStore()
    ccm_state = {"entities": {"wall-001": {"id": "wall-001"}}}
    snap = store.create_snapshot(
        project_uuid="proj-001",
        snapshot_name="Checkpoint",
        snapshot_type="CHECKPOINT",
        ccm_state=ccm_state,
    )
    restored = store.restore_snapshot(snap.snapshot_uuid)
    assert restored.snapshot_uuid == snap.snapshot_uuid
    assert restored.ccm_state == ccm_state
    assert restored.snapshot_name == "Checkpoint"


# ACTS-600-005: Baseline: diff antar baseline benar
def test_baseline_diff():
    store = SnapshotStore()
    # Baseline 1
    store.create_snapshot(
        project_uuid="proj-001",
        snapshot_name="Desain Awal",
        snapshot_type="BASELINE",
        ccm_state={"entities": {"wall-001": {"length": 5.0}, "wall-002": {"length": 3.0}}},
    )
    # Baseline 2
    store.create_snapshot(
        project_uuid="proj-001",
        snapshot_name="Desain Revisi",
        snapshot_type="BASELINE",
        ccm_state={"entities": {"wall-001": {"length": 5.5}, "wall-003": {"length": 2.0}}},
    )
    snapshots = store.get_all_snapshots(project_uuid="proj-001")
    assert len(snapshots) == 2
    diff = store.diff_snapshots(snapshots[0].snapshot_uuid, snapshots[1].snapshot_uuid)
    assert "wall-001" in diff["changed_entities"]
    assert "wall-002" in diff["removed_entities"]
    assert "wall-003" in diff["added_entities"]


# ACTS-600-017: Branch: merge berhasil
def test_branch_merge():
    graph = VersionGraph()
    # Versi awal di main
    v1 = graph.add_version("CCM", "wall-001", Version(1, 0, 0), branch="main")
    # Buat branch alt-facade dari v1
    graph.add_version("CCM", "wall-001", Version(1, 1, 0), parent_id=v1.id, branch="alt-facade")
    # Merge kembali ke main
    merged = graph.merge("alt-facade", "main")
    assert merged is not None
    assert merged.branch == "main"
    assert merged.version.minor == 1  # minor naik dari main head v1 (1.0.0 -> 1.1.0)
    assert merged.parent_id == v1.id
    assert merged.metadata.get("merged_from") == "alt-facade"


# ACTS-600-020: Query: state pada tanggal tertentu
def test_query_state_by_timestamp():
    store = SnapshotStore()
    snap1 = store.create_snapshot(
        project_uuid="proj-001",
        snapshot_name="Snapshot 1",
        snapshot_type="CHECKPOINT",
        ccm_state={"entities": {"wall-001": {"length": 5.0}}},
        timestamp="2026-08-01T10:00:00Z",
    )
    store.create_snapshot(
        project_uuid="proj-001",
        snapshot_name="Snapshot 2",
        snapshot_type="CHECKPOINT",
        ccm_state={"entities": {"wall-001": {"length": 6.0}}},
        timestamp="2026-08-15T10:00:00Z",
    )
    # Query: state pada tanggal tertentu => pilih snapshot terdekat sebelum tanggal tsb.
    target_ts = "2026-08-10T00:00:00Z"
    candidates = [s for s in store.get_all_snapshots("proj-001") if s.timestamp <= target_ts]
    latest = max(candidates, key=lambda s: s.timestamp)
    assert latest.snapshot_uuid == snap1.snapshot_uuid
    assert latest.ccm_state["entities"]["wall-001"]["length"] == 5.0
