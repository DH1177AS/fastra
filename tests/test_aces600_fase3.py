"""
Compliance tests untuk ACES-600 Fase 3:
ACTS-600-015, 016, 019
"""
import pytest
from fastra_core.digital_twin import AuditStore, SnapshotStore, QueryEngine


# ACTS-600-015: Audit Trail: setiap perubahan tercatat
def test_audit_trail_records_every_change():
    store = AuditStore()
    store.record_event(
        event_type="ENTITY_MODIFIED",
        actor={"user_name": "Budi", "role": "QS"},
        target={"entity_uuid": "wall-001", "entity_type": "Wall"},
        change_detail={"field": "construction_type", "old_value": "BATA_MERAH", "new_value": "BATA_RINGAN"},
        reason="Value engineering"
    )
    store.record_event(
        event_type="VO_APPROVED",
        actor={"user_name": "Ani", "role": "Konsultan MK"},
        target={"entity_uuid": "VO-005"},
        change_detail={"status": "APPROVED"}
    )
    assert store.count() == 2
    events = store.get_all_events()
    assert events[0].event_type == "ENTITY_MODIFIED"
    assert events[1].event_type == "VO_APPROVED"


# ACTS-600-016: Audit Trail: query historis berfungsi
def test_audit_trail_query_historical():
    store = AuditStore()
    store.record_event(
        event_type="ENTITY_MODIFIED",
        actor={"user_name": "Budi", "role": "QS"},
        target={"entity_uuid": "wall-001"},
        timestamp="2026-08-01T10:00:00Z"
    )
    store.record_event(
        event_type="ENTITY_MODIFIED",
        actor={"user_name": "Ani", "role": "MK"},
        target={"entity_uuid": "wall-001"},
        timestamp="2026-08-02T10:00:00Z"
    )
    store.record_event(
        event_type="VO_APPROVED",
        actor={"user_name": "Joko", "role": "Owner"},
        target={"entity_uuid": "VO-005"},
        timestamp="2026-08-03T10:00:00Z"
    )
    # Query by entity
    wall_events = store.get_events_by_entity("wall-001")
    assert len(wall_events) == 2
    # Query by date range
    range_events = store.get_events_by_date_range("2026-08-01T00:00:00Z", "2026-08-02T23:59:59Z")
    assert len(range_events) == 2
    # Query by actor
    budi_events = store.get_events_by_actor("Budi")
    assert len(budi_events) == 1


# ACTS-600-019: Traceability: end-to-end dari RAB ke CCM
def test_trace_rab_to_ccm():
    snap_store = SnapshotStore()
    audit_store = AuditStore()
    # Snapshot dengan ccm_state dan boq_state
    ccm_state = {
        "entities": {
            "wall-001": {"id": "wall-001", "type": "Wall", "length": 5.0},
            "wall-002": {"id": "wall-002", "type": "Wall", "length": 3.0},
        },
        "relationships": []
    }
    boq_state = {
        "divisions": {
            "DIV-1": {
                "division_code": "DIV-1",
                "division_name": "Dinding",
                "items": [
                    {
                        "item_code": "PEK.DIND.001",
                        "description": "Pasangan Bata",
                        "quantity": 100.0,
                        "unit": "m²",
                        "source_entities": ["wall-001", "wall-002"],
                    }
                ],
                "subtotal": 0.0,
            }
        }
    }
    snap = snap_store.create_snapshot(
        project_uuid="proj-001",
        snapshot_name="Baseline 1",
        snapshot_type="BASELINE",
        ccm_state=ccm_state,
        boq_state=boq_state,
        timestamp="2026-08-01T10:00:00Z",
    )
    engine = QueryEngine(snap_store, audit_store)
    entities = engine.trace_rab_to_ccm(snap.snapshot_uuid, "PEK.DIND.001")
    assert entities == ["wall-001", "wall-002"]
