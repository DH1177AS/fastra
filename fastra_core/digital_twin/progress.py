"""
ACES-600 Digital Twin Progress Tracking (hardened)
Validasi report_type, status, severity, dan determinisme.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastra_core.digital_twin.enums import ReportType, ProgressStatus, IssueSeverity, IssueStatus


@dataclass
class EntityProgress:
    entity_uuid: str
    entity_name: str
    work_item_code: str
    planned_quantity: float
    completed_quantity: float
    unit: str = "m²"
    status: str = ProgressStatus.IN_PROGRESS.value
    percentage: float = 0.0

    def __post_init__(self) -> None:
        allowed = {s.value for s in ProgressStatus}
        if self.status not in allowed:
            raise ValueError(f"status '{self.status}' tidak valid. Pilih: {sorted(allowed)}")
        if self.planned_quantity > 0:
            self.percentage = round((self.completed_quantity / self.planned_quantity) * 100, 2)
        else:
            self.percentage = 0.0


@dataclass
class Issue:
    issue_uuid: str = field(default_factory=lambda: str(uuid4()))
    description: str = ""
    severity: str = IssueSeverity.LOW.value
    status: str = IssueStatus.OPEN.value
    reported_by: str = ""
    photos: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        allowed_severity = {s.value for s in IssueSeverity}
        allowed_status = {s.value for s in IssueStatus}
        if self.severity not in allowed_severity:
            raise ValueError(f"severity '{self.severity}' tidak valid. Pilih: {sorted(allowed_severity)}")
        if self.status not in allowed_status:
            raise ValueError(f"status '{self.status}' tidak valid. Pilih: {sorted(allowed_status)}")


@dataclass
class MaterialDelivery:
    material_uuid: str
    quantity: float
    unit: str
    delivery_date: str


@dataclass
class ProgressEntry:
    project_uuid: str
    report_date: str
    report_type: str
    progress_entry_uuid: str = field(default_factory=lambda: str(uuid4()))
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    overall_progress_percentage: float = 0.0
    entity_progress: List[EntityProgress] = field(default_factory=list)
    issues: List[Issue] = field(default_factory=list)
    weather: Dict[str, Any] = field(default_factory=dict)
    labor_on_site: Dict[str, int] = field(default_factory=dict)
    material_delivered: List[MaterialDelivery] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        allowed = {r.value for r in ReportType}
        if self.report_type not in allowed:
            raise ValueError(f"report_type '{self.report_type}' tidak valid. Pilih: {sorted(allowed)}")


class ProgressStore:
    def __init__(self) -> None:
        self._entries: Dict[str, ProgressEntry] = {}

    def add_entry(self, entry: ProgressEntry) -> ProgressEntry:
        self._entries[entry.progress_entry_uuid] = entry
        return entry

    def get_entry(self, entry_uuid: str) -> Optional[ProgressEntry]:
        return self._entries.get(entry_uuid)

    def get_entries(self, project_uuid: str) -> List[ProgressEntry]:
        return [e for e in self._entries.values() if e.project_uuid == project_uuid]

    def calculate_overall_progress(
        self,
        entry: ProgressEntry,
        weight_map: Optional[Dict[str, float]] = None,
    ) -> float:
        weighted_completed = 0.0
        weighted_planned = 0.0
        for ep in entry.entity_progress:
            weight = weight_map.get(ep.work_item_code, 1.0) if weight_map else 1.0
            weighted_completed += ep.completed_quantity * weight
            weighted_planned += ep.planned_quantity * weight
        if weighted_planned == 0:
            return 0.0
        return round((weighted_completed / weighted_planned) * 100, 2)

    def planned_vs_actual(
        self,
        planned_quantity: float,
        actual_quantity: float,
        planned_duration: float,
        actual_duration: float,
        planned_cost: float,
        actual_cost: float,
    ) -> Dict[str, Any]:
        qty_variance = actual_quantity - planned_quantity
        dur_variance = actual_duration - planned_duration
        cost_variance = actual_cost - planned_cost
        cost_variance_pct = round((cost_variance / planned_cost) * 100, 2) if planned_cost > 0 else 0.0
        return {
            "quantity_variance": qty_variance,
            "duration_variance_days": dur_variance,
            "cost_variance": cost_variance,
            "cost_variance_percentage": cost_variance_pct,
            "status": "OVER_BUDGET" if cost_variance > 0 else ("UNDER_BUDGET" if cost_variance < 0 else "ON_BUDGET"),
            "schedule_status": "BEHIND_SCHEDULE" if dur_variance > 0 else ("AHEAD_SCHEDULE" if dur_variance < 0 else "ON_SCHEDULE"),
        }
