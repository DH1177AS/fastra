# fastra_core/digital_twin/audit.py

from __future__ import annotations

import logging
import math
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from fastra_core.identity import Identity
from fastra_core.serialization.hash import canonical_hash
from fastra_core.digital_twin.enums import EventType

logger = logging.getLogger("fastra_core.digital_twin.audit")


class AuditEvent(BaseModel):
  
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        strict=True,
        frozen=False,
        allow_inf_nan=False,
    )

    event_type: str = Field(..., min_length=2, max_length=64)
    actor: Dict[str, Any] = Field(default_factory=dict)
    target: Dict[str, Any] = Field(default_factory=dict)
    change_detail: Dict[str, Any] = Field(default_factory=dict)
    reason: str = Field(default="", max_length=512)
    related_vo: Optional[str] = Field(default=None, max_length=128)
    ip_address: Optional[str] = Field(
        default=None,
        pattern=r"^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$|^([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}$",
    )
    user_agent: Optional[str] = Field(default=None, max_length=512)
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    event_uuid: str = Field(default_factory=lambda: str(Identity.generate()), min_length=1, max_length=64)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    prev_hash: str = Field(default="", max_length=64)
    hash: str = Field(default="", max_length=64)

    @field_validator("event_type", mode="after")
    @classmethod
    def verify_event_type_against_enum(cls, value: str) -> str:
        allowed = {e.value for e in EventType}
        if value not in allowed:
            raise ValueError(f"ILLEGAL_AUDIT_EVENT_TYPE: '{value}'")
        return value

    @field_validator("actor", "target", "change_detail", "metadata", mode="before")
    @classmethod
    def validate_dictionaries_no_coercion(cls, value: Any) -> Dict[str, Any]:
        if not isinstance(value, dict):
            raise TypeError("AUDIT_PAYLOAD_DATA_MUST_BE_A_VALID_DICTIONARY")
        for k, v in value.items():
            if not isinstance(k, str) or not k.strip():
                raise ValueError("PAYLOAD_KEYS_MUST_BE_NON_EMPTY_STRINGS")
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                if math.isnan(v) or math.isinf(v):
                    raise ValueError(f"NUMERIC_ANOMALY_DETECTED_IN_AUDIT_VALUE_AT_KEY_{k}")
        return value

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

    def compute_canonical_hash(self) -> str:
        base_data = self.to_dict()
        base_data.pop("hash", None)
        return canonical_hash(base_data)


class AuditStore(BaseModel):
   
    model_config = ConfigDict(
        extra="forbid",
        strict=True,
        frozen=False,
        allow_inf_nan=False,
    )

    events: List[AuditEvent] = Field(default_factory=list)
    
    @property
    def _events(self):
        return self.events
    
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
        timestamp: Optional[datetime | str] = None,
        event_uuid: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AuditEvent:
       
        if timestamp is not None:
            if isinstance(timestamp, datetime):
                timestamp_str = timestamp.isoformat()
            elif isinstance(timestamp, str):
                timestamp_str = timestamp
            else:
                raise TypeError("TIMESTAMP_MUST_BE_STRING_OR_DATETIME")
        else:
            timestamp_str = datetime.now(timezone.utc).isoformat()

        last_hash = self.events[-1].hash if self.events else ""

        temp_event_data = {
            "event_type": event_type,
            "actor": dict(actor),
            "target": dict(target),
            "change_detail": dict(change_detail) if change_detail is not None else {},
            "reason": reason,
            "related_vo": related_vo,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "timestamp": timestamp_str,
            "event_uuid": event_uuid or str(Identity.generate()),
            "metadata": dict(metadata) if metadata is not None else {},
            "prev_hash": last_hash,
            "hash": "0" * 64,
        }

        interim_event = AuditEvent.model_validate(temp_event_data)
        computed_signature = interim_event.compute_canonical_hash()

        final_data = interim_event.model_dump()
        final_data["hash"] = computed_signature
        final_event = AuditEvent.model_validate(final_data)
        self.events.append(final_event)
        return final_event

    def verify_integrity(self) -> bool:
        for i, event in enumerate(self.events):
            expected_prev = self.events[i - 1].hash if i > 0 else ""
            if event.prev_hash != expected_prev:
                return False
            if event.compute_canonical_hash() != event.hash:
                return False
        return True

    def get_all_events(self) -> List[AuditEvent]:
        return list(self.events)

    def get_events_by_actor(self, actor_name: str) -> List[AuditEvent]:
        return [e for e in self.events if e.actor.get("user_name") == actor_name]

    def get_events_by_entity(self, entity_uuid: str) -> List[AuditEvent]:
        return [e for e in self.events if e.target.get("entity_uuid") == entity_uuid]

    def get_events_by_type(self, event_type: str) -> List[AuditEvent]:
        return [e for e in self.events if e.event_type == event_type]

    def get_events_by_date_range(self, start: str, end: str) -> List[AuditEvent]:
        """Filter events berdasarkan string timestamp ISO."""
        return [e for e in self.events if start <= e.timestamp <= end]

    def get_events_by_related_vo(self, vo_number: str) -> List[AuditEvent]:
        return [e for e in self.events if e.related_vo == vo_number]

    def count(self) -> int:
        return len(self.events)