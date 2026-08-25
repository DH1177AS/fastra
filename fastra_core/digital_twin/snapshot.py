"""
ACES-600 Digital Twin Snapshot System (hardened)
Menambahkan validasi snapshot_type.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastra_core.digital_twin.enums import SnapshotType
from fastra_core.digital_twin.serialization import to_serializable


@dataclass
class Snapshot:
    snapshot_uuid: str
    snapshot_name: str
    snapshot_type: str
    project_uuid: str
    timestamp: str
    description: str = ""
    ccm_state: Dict[str, Any] = field(default_factory=dict)
    boq_state: Optional[Dict[str, Any]] = None
    rab_state: Optional[Dict[str, Any]] = None
    schedule_state: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self._validate_snapshot_type()

    def _validate_snapshot_type(self) -> None:
        allowed = {s.value for s in SnapshotType}
        if self.snapshot_type not in allowed:
            raise ValueError(
                f"snapshot_type '{self.snapshot_type}' tidak valid. Pilih: {sorted(allowed)}"
            )

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


class SnapshotStore:
    def __init__(self) -> None:
        self._snapshots: Dict[str, Snapshot] = {}

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
        timestamp: Optional[str] = None,
    ) -> Snapshot:
        snapshot = Snapshot(
            snapshot_uuid=str(uuid4()),
            snapshot_name=snapshot_name,
            snapshot_type=snapshot_type,
            project_uuid=project_uuid,
            timestamp=timestamp or datetime.now(timezone.utc).isoformat(),
            description=description,
            ccm_state=ccm_state,
            boq_state=boq_state,
            rab_state=rab_state,
            schedule_state=schedule_state,
            metadata=metadata or {},
        )
        self._snapshots[snapshot.snapshot_uuid] = snapshot
        return snapshot

    def get_snapshot(self, snapshot_uuid: str) -> Optional[Snapshot]:
        return self._snapshots.get(snapshot_uuid)

    def get_all_snapshots(self, project_uuid: Optional[str] = None) -> List[Snapshot]:
        if project_uuid:
            return [s for s in self._snapshots.values() if s.project_uuid == project_uuid]
        return list(self._snapshots.values())

    def get_latest_snapshot(self, project_uuid: str, snapshot_type: Optional[str] = None) -> Optional[Snapshot]:
        candidates = [s for s in self._snapshots.values() if s.project_uuid == project_uuid]
        if snapshot_type:
            candidates = [s for s in candidates if s.snapshot_type == snapshot_type]
        if not candidates:
            return None
        return max(candidates, key=lambda s: s.timestamp)

    def diff_snapshots(self, snapshot_uuid_a: str, snapshot_uuid_b: str) -> Dict[str, Any]:
        snap_a = self.get_snapshot(snapshot_uuid_a)
        snap_b = self.get_snapshot(snapshot_uuid_b)
        if not snap_a or not snap_b:
            raise ValueError("Salah satu snapshot tidak ditemukan")
        diff: Dict[str, Any] = {
            "changed_entities": [],
            "added_entities": [],
            "removed_entities": [],
            "boq_diff": None,
            "rab_diff": None,
        }
        entities_a = snap_a.ccm_state.get("entities", {})
        entities_b = snap_b.ccm_state.get("entities", {})
        ids_a = set(entities_a.keys())
        ids_b = set(entities_b.keys())
        diff["added_entities"] = sorted(ids_b - ids_a)
        diff["removed_entities"] = sorted(ids_a - ids_b)
        for eid in sorted(ids_a & ids_b):
            if to_serializable(entities_a[eid]) != to_serializable(entities_b[eid]):
                diff["changed_entities"].append(eid)
        if snap_a.boq_state and snap_b.boq_state:
            if to_serializable(snap_a.boq_state) != to_serializable(snap_b.boq_state):
                diff["boq_diff"] = "BOQ berubah"
        return diff

    def restore_snapshot(self, snapshot_uuid: str) -> Snapshot:
        snapshot = self.get_snapshot(snapshot_uuid)
        if not snapshot:
            raise ValueError(f"Snapshot {snapshot_uuid} tidak ditemukan")
        return Snapshot(**snapshot.__dict__)
