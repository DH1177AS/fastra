"""
ACES-600 Digital Twin Change Order (VO) Management (hardened)
Validasi status VO dan approval status.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastra_core.digital_twin.enums import VOStatus, ApprovalStatus


@dataclass
class ApprovalStep:
    role: str
    approved_by: str
    date: str
    status: str = ApprovalStatus.APPROVED.value

    def __post_init__(self) -> None:
        allowed = {s.value for s in ApprovalStatus}
        if self.status not in allowed:
            raise ValueError(f"status approval '{self.status}' tidak valid. Pilih: {sorted(allowed)}")


@dataclass
class ChangeOrder:
    project_uuid: str
    vo_number: str
    description: str
    reason: str
    request_date: str
    requested_by: str
    vo_uuid: str = field(default_factory=lambda: str(uuid4()))
    ccm_changes: Dict[str, Any] = field(default_factory=dict)
    boq_impact: Dict[str, Any] = field(default_factory=dict)
    cost_impact: Dict[str, float] = field(default_factory=dict)
    schedule_impact: Dict[str, Any] = field(default_factory=dict)
    status: str = VOStatus.DRAFT.value
    approval_chain: List[ApprovalStep] = field(default_factory=list)
    baseline_before: Optional[str] = None
    baseline_after: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        allowed = {s.value for s in VOStatus}
        if self.status not in allowed:
            raise ValueError(f"status VO '{self.status}' tidak valid. Pilih: {sorted(allowed)}")

    def calculate_cost_impact(self) -> float:
        additional = self.cost_impact.get("additional_cost", 0.0)
        deduction = self.cost_impact.get("deduction_cost", 0.0)
        net = additional - deduction
        self.cost_impact["net_change"] = net
        return net


class ChangeOrderStore:
    def __init__(self) -> None:
        self._vos: Dict[str, ChangeOrder] = {}

    def add_vo(self, vo: ChangeOrder) -> ChangeOrder:
        self._vos[vo.vo_uuid] = vo
        return vo

    def get_vo(self, vo_uuid: str) -> Optional[ChangeOrder]:
        return self._vos.get(vo_uuid)

    def get_all_vos(self, project_uuid: str) -> List[ChangeOrder]:
        return [v for v in self._vos.values() if v.project_uuid == project_uuid]

    def update_status(self, vo_uuid: str, new_status: str) -> bool:
        allowed = {s.value for s in VOStatus}
        if new_status not in allowed:
            raise ValueError(f"new_status '{new_status}' tidak valid")
        vo = self.get_vo(vo_uuid)
        if not vo:
            return False
        vo.status = new_status
        return True

    def add_approval(self, vo_uuid: str, role: str, approved_by: str, date: str, status: str = ApprovalStatus.APPROVED.value) -> bool:
        vo = self.get_vo(vo_uuid)
        if not vo:
            return False
        vo.approval_chain.append(ApprovalStep(role=role, approved_by=approved_by, date=date, status=status))
        return True
