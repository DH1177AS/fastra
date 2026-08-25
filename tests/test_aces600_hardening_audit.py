"""
Test hardening Audit Trail anti-tamper (ACES-600 Fase 3 lanjutan).
"""
import pytest
from fastra_core.digital_twin import AuditStore


def test_audit_integrity_ok():
    store = AuditStore()
    store.record_event(
        event_type="ENTITY_MODIFIED",
        actor={"user_name": "Budi", "role": "QS"},
        target={"entity_uuid": "wall-001"},
        timestamp="2026-08-15T10:00:00Z",
    )
    store.record_event(
        event_type="VO_APPROVED",
        actor={"user_name": "Ani", "role": "MK"},
        target={"entity_uuid": "VO-005"},
        timestamp="2026-08-15T11:00:00Z",
    )
    assert store.count() == 2
    assert store.verify_integrity() is True


def test_audit_integrity_detects_modification():
    store = AuditStore()
    store.record_event(
        event_type="ENTITY_MODIFIED",
        actor={"user_name": "Budi", "role": "QS"},
        target={"entity_uuid": "wall-001"},
        timestamp="2026-08-15T10:00:00Z",
    )
    # Manipulasi langsung pada event pertama
    store._events[0].change_detail = {"field": "material", "new_value": "MUTATED"}
    assert store.verify_integrity() is False
