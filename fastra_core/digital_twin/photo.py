"""
ACES-600 Digital Twin Photo Data Capture
Menyimpan metadata foto lapangan dan validasi referensi entity.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastra_core.digital_twin.snapshot import Snapshot


@dataclass
class PhotoData:
    project_uuid: str
    capture_date: str
    photo_uuid: str = field(default_factory=lambda: str(uuid4()))
    capture_method: str = "HP"
    captured_by: str = ""
    location: Optional[Dict[str, float]] = None
    direction_degrees: Optional[float] = None
    entity_references: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    file: Dict[str, Any] = field(default_factory=dict)
    annotations: List[Dict[str, Any]] = field(default_factory=list)

    def validate_entity_references(self, snapshot: Snapshot) -> bool:
        """Memastikan semua entity_references ada di ccm_state snapshot."""
        entities = snapshot.ccm_state.get("entities", {})
        return all(eid in entities for eid in self.entity_references)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "photo_uuid": self.photo_uuid,
            "project_uuid": self.project_uuid,
            "capture_date": self.capture_date,
            "capture_method": self.capture_method,
            "captured_by": self.captured_by,
            "location": self.location,
            "direction_degrees": self.direction_degrees,
            "entity_references": self.entity_references,
            "tags": self.tags,
            "file": self.file,
            "annotations": self.annotations,
        }
