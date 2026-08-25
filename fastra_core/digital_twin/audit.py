"""
ACES-600 Digital Twin Audit Trail (hardened + anti-tamper)
Event log append-only dengan hash chain dan event_uuid injection.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastra_core.digital_twin.enums import EventType


@dataclass
class AuditEvent:
    event_type: str
    actor: Dict[str, Any]
    target: Dict[str, Any]
    change_detail: Dict[str, Any] = field(default_factory=dict)
    reason: str = ""
    related_vo: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    event_uuid: str = field(default_factory=lambda: str(uuid4()))
    metadata: Dict[str, Any] = field(default_factory=dict)
    prev_hash: str = ""
    hash: str = ""

    def __post_init__(self) -> None:
        allowed = {e.value for e in EventType}
        if self.event_type not in allowed:
            raise ValueError(f"event_type '{self.event_type}' tidak valid. Pilih: {sorted(allowed)}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_uuid": self.event_uuid,
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "actor": self.actor,
            "target": self.target,
            "change_detail": self.change_detail,
            "reason": self.reason,
            "related_vo": self.related_vo,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "metadata": self.metadata,
            "prev_hash": self.prev_hash,
            "hash": self.hash,
        }


class AuditStore:
    """Penyimpanan event log append-only dengan hash chain."""

    def __init__(self) -> None:
        self._events: List[AuditEvent] = []

    def _compute_hash(self, event: AuditEvent) -> str:
        """Hitung SHA-256 dari event (tanpa field hash)."""
        data = event.to_dict()
        data.pop("hash", None)
        canonical = json.dumps(data, sort_keys=True, default=str).encode("utf-8")
        return hashlib.sha256(canonical).hexdigest()

    def record_event(
        self,
        event_type: str,
        actor: Dict[str, Any],
        target: Dict[str, Any],
        change_detail: Optional[Dict[str, Any]] = None,
        reason: str = "",
        related_vo: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        timestamp: Optional[str] = None,
        event_uuid: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AuditEvent:
        """Mencatat event baru (append-only) dan menghitung hash chain."""
        event = AuditEvent(
            event_type=event_type,
            actor=actor,
            target=target,
            change_detail=change_detail or {},
            reason=reason,
            related_vo=related_vo,
            ip_address=ip_address,
            user_agent=user_agent,
            timestamp=timestamp or datetime.now(timezone.utc).isoformat(),
            event_uuid=event_uuid or str(uuid4()),
            metadata=metadata or {},
        )
        if self._events:
            event.prev_hash = self._events[-1].hash
        else:
            event.prev_hash = ""
        event.hash = self._compute_hash(event)
        self._events.append(event)
        return event

    def verify_integrity(self) -> bool:
        """Verifikasi integritas hash chain. Mengembalikan True jika tidak ada manipulasi."""
        for i, event in enumerate(self._events):
            expected_prev = self._events[i - 1].hash if i > 0 else ""
            if event.prev_hash != expected_prev:
                return False
            recomputed_hash = self._compute_hash(event)
            if recomputed_hash != event.hash:
                return False
        return True

    def get_all_events(self) -> List[AuditEvent]:
        return list(self._events)

    def get_events_by_actor(self, actor_name: str) -> List[AuditEvent]:
        return [e for e in self._events if e.actor.get("user_name") == actor_name]

    def get_events_by_entity(self, entity_uuid: str) -> List[AuditEvent]:
        return [e for e in self._events if e.target.get("entity_uuid") == entity_uuid]

    def get_events_by_type(self, event_type: str) -> List[AuditEvent]:
        return [e for e in self._events if e.event_type == event_type]

    def get_events_by_date_range(self, start: str, end: str) -> List[AuditEvent]:
        return [e for e in self._events if start <= e.timestamp <= end]

    def get_events_by_related_vo(self, vo_number: str) -> List[AuditEvent]:
        return [e for e in self._events if e.related_vo == vo_number]

    def count(self) -> int:
        return len(self._events)
