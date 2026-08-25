"""
ACES-600 As-Built Capture (dasar)
Membandingkan kondisi as-planned vs as-built dan mendeteksi perbedaan.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List
from uuid import uuid4


@dataclass
class AsBuiltDifference:
    entity_uuid: str
    field: str
    planned_value: Any
    as_built_value: Any
    description: str = ""


@dataclass
class AsBuiltRecord:
    project_uuid: str
    entity_uuid: str
    planned_state: Dict[str, Any]
    as_built_state: Dict[str, Any]
    record_uuid: str = field(default_factory=lambda: str(uuid4()))
    differences: List[AsBuiltDifference] = field(default_factory=list)

    def detect_differences(self) -> List[AsBuiltDifference]:
        """Deteksi perbedaan field antara planned dan as_built."""
        diffs = []
        for key in sorted(set(self.planned_state.keys()) | set(self.as_built_state.keys())):
            planned_val = self.planned_state.get(key)
            as_built_val = self.as_built_state.get(key)
            if planned_val != as_built_val:
                diffs.append(AsBuiltDifference(
                    entity_uuid=self.entity_uuid,
                    field=key,
                    planned_value=planned_val,
                    as_built_value=as_built_val,
                    description=f"Perubahan pada {key}"
                ))
        self.differences = diffs
        return diffs


class AsBuiltStore:
    """Penyimpanan As-Built record in-memory (Fase 2)."""

    def __init__(self) -> None:
        self._records: Dict[str, AsBuiltRecord] = {}

    def add_record(self, record: AsBuiltRecord) -> AsBuiltRecord:
        record.detect_differences()
        self._records[record.record_uuid] = record
        return record

    def get_record(self, record_uuid: str) -> AsBuiltRecord | None:
        return self._records.get(record_uuid)

    def get_all_records(self, project_uuid: str) -> List[AsBuiltRecord]:
        return [r for r in self._records.values() if r.project_uuid == project_uuid]
