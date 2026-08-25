"""
Test hardening determinisme dan concurrency ringan untuk Digital Twin.
"""
import uuid
import pytest
from fastra_core.digital_twin import AuditStore, SnapshotStore, SyncEngine, OfflineStore


def test_audit_timestamp_injection_deterministic():
    store1 = AuditStore()
    store2 = AuditStore()
    for i in range(5):
        event_id = str(uuid.uuid4())
        store1.record_event(
            event_type="ENTITY_MODIFIED",
            actor={"user_name": "Budi"},
            target={"entity_uuid": f"wall-{i}"},
            timestamp="2026-08-24T10:00:00Z",
            event_uuid=event_id,
        )
        store2.record_event(
            event_type="ENTITY_MODIFIED",
            actor={"user_name": "Budi"},
            target={"entity_uuid": f"wall-{i}"},
            timestamp="2026-08-24T10:00:00Z",
            event_uuid=event_id,
        )
    # Hash chain harus identik karena semua field identik
    assert store1.verify_integrity() is True
    assert store2.verify_integrity() is True
    assert store1._events[-1].hash == store2._events[-1].hash


def test_sync_engine_idempotent_push():
    offline = OfflineStore()
    offline.save_record("PROGRESS", {"entity_uuid": "wall-001"}, created_at="2026-08-24T10:00:00Z")
    engine = SyncEngine()
    result1 = engine.push(offline)
    result2 = engine.push(offline)  # kedua push seharusnya tidak menduplikasi
    assert result1.pushed_count == 1
    assert result2.pushed_count == 0
    assert len(engine.server_store) == 1
