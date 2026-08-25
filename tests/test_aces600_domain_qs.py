"""
Test Domain QS lanjutan: progress weighting, VO propagation, as-built finalization, restore.
"""
import pytest
from fastra_core.digital_twin.database_extended import ExtendedDigitalTwinDB
from fastra_core.digital_twin.domain_qs import QSDomainService
from fastra_core.digital_twin import Snapshot, ChangeOrder, AsBuiltRecord, AuditEvent
from datetime import datetime, timezone


@pytest.fixture
def db():
    database = ExtendedDigitalTwinDB("sqlite:///:memory:")
    database.seed_default_users()
    yield database
    database.close()


def test_progress_weight_map(db):
    # Snapshot dengan BOQ berisi biaya
    snap = Snapshot(
        snapshot_uuid="snap-weight",
        snapshot_name="Baseline",
        snapshot_type="CHECKPOINT",
        project_uuid="proj-weight",
        timestamp="2026-08-24T10:00:00Z",
        ccm_state={"entities": {}},
        boq_state={
            "divisions": {
                "DIV-1": {
                    "items": [
                        {"item_code": "PEK.DIND.001", "quantity": 10, "subtotal": 5000000},
                        {"item_code": "PEK.STR.001", "quantity": 5, "subtotal": 5000000},
                    ]
                }
            }
        },
    )
    db.save_snapshot(snap)
    service = QSDomainService(db)
    weights = service.calculate_progress_weight_map("proj-weight")
    assert abs(weights["PEK.DIND.001"] - 0.5) < 1e-6
    assert abs(weights["PEK.STR.001"] - 0.5) < 1e-6


def test_vo_propagation(db):
    vo = ChangeOrder(
        project_uuid="proj-vo",
        vo_number="VO-100",
        description="Test VO",
        reason="Test",
        request_date="2026-08-24",
        requested_by="Owner",
        vo_uuid="vo-100",
        cost_impact={"additional_cost": 15000000.0, "deduction_cost": 2000000.0},
    )
    db.save_change_order(vo)
    service = QSDomainService(db)
    result = service.propagate_vo("vo-100")
    assert result["net_change"] == 13000000.0
    assert result["status"] == "DRAFT"


def test_finalize_as_built(db):
    snap = Snapshot(
        snapshot_uuid="snap-asbuilt",
        snapshot_name="Design",
        snapshot_type="CHECKPOINT",
        project_uuid="proj-asbuilt",
        timestamp="2026-08-24T10:00:00Z",
        ccm_state={"entities": {"wall-001": {"length": 5.0}}},
    )
    db.save_snapshot(snap)
    service = QSDomainService(db)
    as_built_snapshot = service.finalize_as_built(
        "proj-asbuilt",
        as_built_entity_states={"wall-001": {"length": 5.1}},
    )
    assert as_built_snapshot.snapshot_type == "AS_BUILT"
    assert as_built_snapshot.ccm_state["entities"]["wall-001"]["length"] == 5.1
    # Ensure it was saved
    snaps = db.list_snapshots("proj-asbuilt")
    assert any(s.snapshot_uuid == as_built_snapshot.snapshot_uuid for s in snaps)


def test_restore_archive(db):
    # Create snapshot and archive
    snap = Snapshot(
        snapshot_uuid="snap-archive",
        snapshot_name="Archived",
        snapshot_type="CHECKPOINT",
        project_uuid="proj-archive",
        timestamp="2026-08-24T10:00:00Z",
        ccm_state={"entities": {"wall-001": {}}},
    )
    db.save_snapshot(snap)
    from fastra_core.digital_twin.archiving import ArchiveStore
    from fastra_core.digital_twin import AsBuiltStore, AuditStore
    snapshot_store = __import__('fastra_core.digital_twin.snapshot', fromlist=['SnapshotStore']).SnapshotStore()
    snapshot_store.create_snapshot(
        snap.project_uuid, snap.snapshot_name, snap.snapshot_type, snap.ccm_state,
        timestamp=snap.timestamp,
    )
    archive_store = ArchiveStore()
    archive = archive_store.create_archive(
        snap.project_uuid, snapshot_store, AsBuiltStore(), AuditStore(),
        archived_at="2026-08-24T10:00:00Z",
    )
    db.save_archive_record(archive)

    service = QSDomainService(db)
    restored_count = service.restore_archive(archive.archive_uuid)
    assert restored_count >= 1
    # Snapshot should be present again
    snaps = db.list_snapshots("proj-archive")
    assert any(s.snapshot_name == "Archived" for s in snaps)
