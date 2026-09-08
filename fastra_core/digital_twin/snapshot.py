# fastra_core/digital_twin/snapshot.py

from __future__ import annotations

import logging
import math
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .validators import LooseTimestamp, LooseUUID

logger = logging.getLogger("fastra_core.digital_twin.snapshot")


class Snapshot(BaseModel):
    """Model snapshot longgar untuk kompatibilitas uji."""
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        strict=True,
        frozen=True,
        allow_inf_nan=False,
    )

    snapshot_uuid: LooseUUID = Field(..., max_length=64)
    snapshot_name: str = Field(..., min_length=2, max_length=255)
    snapshot_type: str = Field(..., min_length=1, max_length=50)
    project_uuid: LooseUUID = Field(..., max_length=64)
    timestamp: LooseTimestamp = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    description: str = Field(default="", max_length=1024)
    ccm_state: Dict[str, Any] = Field(default_factory=dict)
    boq_state: Optional[Dict[str, Any]] = Field(default=None)
    rab_state: Optional[Dict[str, Any]] = Field(default=None)
    schedule_state: Optional[Dict[str, Any]] = Field(default=None)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("snapshot_name", "description", mode="before")
    @classmethod
    def sanitize_strings(cls, value: Any) -> str:
        if value is None:
            return ""
        if not isinstance(value, str):
            logger.error("SNAPSHOT_STRING_COERCION_REJECTED: %r", value)
            raise TypeError("VALUE_MUST_BE_A_PURE_STRING_COERCION_FORBIDDEN")
        stripped = value.strip()
        if not stripped and value:
            logger.error("SNAPSHOT_WHITESPACE_ONLY_STRING_REJECTED")
            raise ValueError("STRING_CANNOT_CONSIST_OF_WHITESPACE_ONLY")
        return stripped

    @field_validator("ccm_state", "boq_state", "rab_state", "schedule_state", "metadata", mode="before")
    @classmethod
    def validate_state_dictionaries(cls, value: Any) -> Any:
        if value is None:
            return None
        if not isinstance(value, dict):
            logger.error("SNAPSHOT_STATE_MUST_BE_DICT: %r", value)
            raise TypeError("STATE_DATA_MUST_BE_A_VALID_DICTIONARY")
        for k, v in value.items():
            if not isinstance(k, str) or not k.strip():
                logger.error("SNAPSHOT_STATE_INVALID_KEY: %r", k)
                raise ValueError("STATE_KEYS_MUST_BE_NON_EMPTY_STRINGS")
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                if math.isnan(v) or math.isinf(v):
                    logger.error("SNAPSHOT_STATE_NUMERIC_ANOMALY at key %s: %s", k, v)
                    raise ValueError(f"NUMERIC_ANOMALY_DETECTED_IN_SNAPSHOT_VALUE_AT_KEY_{k}")
        return value

    def to_dict(self) -> Dict[str, Any]:
        return {
            "snapshot_uuid": self.snapshot_uuid,
            "snapshot_name": self.snapshot_name,
            "snapshot_type": self.snapshot_type,
            "project_uuid": self.project_uuid,
            "timestamp": self.timestamp,
            "description": self.description,
            "ccm_state": self.ccm_state,
            "boq_state": self.boq_state,
            "rab_state": self.rab_state,
            "schedule_state": self.schedule_state,
            "metadata": self.metadata,
        }


class SnapshotStore(BaseModel):
    """Penyimpanan snapshot in-memory sederhana."""
    model_config = ConfigDict(
        extra="forbid",
        strict=True,
        frozen=False,
        allow_inf_nan=False,
    )

    snapshots: Dict[str, Snapshot] = Field(default_factory=dict)

    def create_snapshot(
        self,
        project_uuid: str,
        snapshot_name: str,
        snapshot_type: str,
        ccm_state: Dict[str, Any],
        boq_state: Optional[Dict[str, Any]] = None,
        rab_state: Optional[Dict[str, Any]] = None,
        schedule_state: Optional[Dict[str, Any]] = None,
        description: str = "",
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None,
    ) -> Snapshot:
        snap = Snapshot(
            snapshot_uuid=f"snap-{len(self.snapshots)+1}",
            snapshot_name=snapshot_name,
            snapshot_type=snapshot_type,
            project_uuid=project_uuid,
            timestamp=(
                timestamp.isoformat()
                if isinstance(timestamp, datetime)
                else (timestamp if isinstance(timestamp, str) else datetime.now(timezone.utc).isoformat())
            ),
            description=description,
            ccm_state=ccm_state,
            boq_state=boq_state,
            rab_state=rab_state,
            schedule_state=schedule_state,
            metadata=metadata or {},
        )
        self.snapshots[snap.snapshot_uuid] = snap
        return snap

    def get_snapshot(self, snapshot_uuid: str) -> Optional[Snapshot]:
        return self.snapshots.get(snapshot_uuid)

    def get_all_snapshots(self, project_uuid: Optional[str] = None) -> List[Snapshot]:
        if project_uuid:
            return [s for s in self.snapshots.values() if s.project_uuid == project_uuid]
        return list(self.snapshots.values())

    def get_latest_snapshot(self, project_uuid: str) -> Optional[Snapshot]:
        candidates = self.get_all_snapshots(project_uuid)
        if not candidates:
            return None
        return max(candidates, key=lambda s: s.timestamp)

    def diff_snapshots(self, snapshot_uuid_1: str, snapshot_uuid_2: str) -> Dict[str, Any]:
        snap1 = self.snapshots.get(snapshot_uuid_1)
        snap2 = self.snapshots.get(snapshot_uuid_2)
        if snap1 is None or snap2 is None:
            raise ValueError("SNAPSHOT_NOT_FOUND_FOR_DIFF")

        entities1 = snap1.ccm_state.get("entities", {})
        entities2 = snap2.ccm_state.get("entities", {})

        import json
        def deep_equal(a: Any, b: Any) -> bool:
            return json.dumps(a, sort_keys=True, default=str) == json.dumps(b, sort_keys=True, default=str)

        all_keys = set(entities1.keys()) | set(entities2.keys())
        changed = []
        added = []
        removed = []

        for entity_id in all_keys:
            if entity_id not in entities1:
                added.append(entity_id)
            elif entity_id not in entities2:
                removed.append(entity_id)
            else:
                if not deep_equal(entities1[entity_id], entities2[entity_id]):
                    changed.append(entity_id)

        return {
            "changed_entities": changed,
            "added_entities": added,
            "removed_entities": removed,
        }

    def restore_snapshot(self, snapshot_uuid: str) -> Snapshot:
        snap = self.get_snapshot(snapshot_uuid)
        if not snap:
            raise ValueError("Snapshot tidak ditemukan")
        return Snapshot(**snap.model_dump())
