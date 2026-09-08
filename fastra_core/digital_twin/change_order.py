# fastra_core/digital_twin/change_order.py

from __future__ import annotations

import logging
import math
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, Set

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from fastra_core.identity import Identity
from fastra_core.primitives.currency import Currency
from fastra_core.digital_twin.enums import VOStatus, ApprovalStatus
from .validators import LooseTimestamp, LooseUUID

logger = logging.getLogger("fastra_core.digital_twin.change_order")


class ApprovalStep(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        strict=True,
        frozen=True,
        allow_inf_nan=False,
    )

    role: str = Field(..., min_length=2, max_length=64)
    approved_by: str = Field(..., min_length=3, max_length=128)
    date: LooseTimestamp = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    status: str = Field(default="APPROVED", min_length=1, max_length=32)

    @field_validator("date", mode="before")
    @classmethod
    def coerce_date_to_iso(cls, value: Any) -> str:
        if isinstance(value, datetime):
            return value.isoformat()
        if not isinstance(value, str):
            raise TypeError("DATE_MUST_BE_STRING_OR_DATETIME")
        return value

    @field_validator("role", "approved_by", "status", mode="before")
    @classmethod
    def sanitize_strings(cls, value: Any) -> str:
        if not isinstance(value, str):
            raise TypeError("VALUE_MUST_BE_A_PURE_STRING_COERCION_FORBIDDEN")
        stripped = value.strip()
        if not stripped:
            raise ValueError("STRING_VALUE_CANNOT_BE_EMPTY_OR_WHITESPACE")
        return stripped


class ChangeOrder(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        strict=True,
        frozen=False,
        allow_inf_nan=False,
    )

    project_uuid: LooseUUID = Field(..., max_length=64)
    vo_number: str = Field(..., min_length=3, max_length=64, pattern=r"^[A-Za-z0-9\-\/]+$")
    description: str = Field(..., min_length=5, max_length=1024)
    reason: str = Field(..., min_length=1, max_length=1024)
    request_date: LooseTimestamp = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    requested_by: str = Field(..., min_length=1, max_length=128)
    vo_uuid: LooseUUID = Field(default_factory=lambda: str(Identity.generate()))
    ccm_changes: Dict[str, Any] = Field(default_factory=dict)
    boq_impact: Dict[str, Any] = Field(default_factory=dict)
    cost_impact: Dict[str, Any] = Field(default_factory=dict)
    schedule_impact: Dict[str, Any] = Field(default_factory=dict)
    status: VOStatus = Field(default=VOStatus.DRAFT)
    approval_chain: Tuple[ApprovalStep, ...] = Field(default_factory=tuple)
    baseline_before: Optional[str] = Field(
        default=None,
        pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$|^$",
    )
    baseline_after: Optional[str] = Field(
        default=None,
        pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$|^$",
    )
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("vo_number", "description", "reason", "requested_by", mode="before")
    @classmethod
    def sanitize_core_strings(cls, value: Any) -> str:
        if not isinstance(value, str):
            logger.error("CHANGE_ORDER_CORE_STRING_COERCION_REJECTED: %r", value)
            raise TypeError("VALUE_MUST_BE_A_PURE_STRING_COERCION_FORBIDDEN")
        stripped = value.strip()
        if not stripped:
            logger.error("CHANGE_ORDER_CORE_STRING_EMPTY_REJECTED")
            raise ValueError("CORE_STRING_VALUE_CANNOT_BE_EMPTY_OR_WHITESPACE")
        return stripped

    @field_validator("ccm_changes", "boq_impact", "cost_impact", "schedule_impact", "metadata", mode="before")
    @classmethod
    def validate_dictionaries_no_coercion(cls, value: Any) -> Dict[str, Any]:
        if not isinstance(value, dict):
            logger.error("CHANGE_ORDER_PAYLOAD_MUST_BE_DICT: %r", value)
            raise TypeError("IMPACT_PAYLOAD_DATA_MUST_BE_A_VALID_DICTIONARY")
        for k, v in value.items():
            if not isinstance(k, str) or not k.strip():
                logger.error("CHANGE_ORDER_PAYLOAD_INVALID_KEY: %r", k)
                raise ValueError("PAYLOAD_KEYS_MUST_BE_NON_EMPTY_STRINGS")
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                if math.isnan(v) or math.isinf(v):
                    logger.error("CHANGE_ORDER_PAYLOAD_NUMERIC_ANOMALY at key %s: %s", k, v)
                    raise ValueError(f"NUMERIC_ANOMALY_DETECTED_IN_CHANGE_ORDER_VALUE_AT_KEY_{k}")
        return value

    def calculate_cost_impact(self) -> float:
        additional_raw = self.cost_impact.get("additional_cost", 0.0)
        deduction_raw = self.cost_impact.get("deduction_cost", 0.0)

        if isinstance(additional_raw, Currency):
            additional = float(additional_raw.value)
        else:
            additional = float(additional_raw)

        if isinstance(deduction_raw, Currency):
            deduction = float(deduction_raw.value)
        else:
            deduction = float(deduction_raw)

        net_change = additional - deduction
        self.cost_impact["net_change"] = net_change
        return net_change

    def copy_with_calculated_cost(self) -> "ChangeOrder":
        additional_raw = self.cost_impact.get("additional_cost", 0.0)
        deduction_raw = self.cost_impact.get("deduction_cost", 0.0)

        if isinstance(additional_raw, Currency):
            additional = float(additional_raw.value)
        else:
            additional = float(additional_raw)

        if isinstance(deduction_raw, Currency):
            deduction = float(deduction_raw.value)
        else:
            deduction = float(deduction_raw)

        net_change = additional - deduction

        updated_cost_impact = dict(self.cost_impact)
        updated_cost_impact["net_change"] = net_change

        order_dump = self.model_dump()
        order_dump["cost_impact"] = updated_cost_impact
        return ChangeOrder.model_validate(order_dump)


class ChangeOrderStore(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        strict=True,
        frozen=False,
        allow_inf_nan=False,
    )

    vos: Dict[str, ChangeOrder] = Field(default_factory=dict)

    def add_vo(self, vo: ChangeOrder) -> ChangeOrder:
        if not isinstance(vo, ChangeOrder):
            logger.error("STORE_ADD_VO_INVALID_TYPE: %r", vo)
            raise TypeError("STORE_OPERATION_VIOLATION_VO_MUST_BE_AN_INSTANCE_OF_CHANGE_ORDER")

        processed_vo = vo.copy_with_calculated_cost()
        self.vos[processed_vo.vo_uuid] = processed_vo
        logger.info("Change order added: %s", processed_vo.vo_uuid)
        return processed_vo

    def get_vo(self, vo_uuid: str) -> Optional[ChangeOrder]:
        if not isinstance(vo_uuid, str):
            logger.error("GET_VO_UUID_NOT_STRING: %r", vo_uuid)
            raise TypeError("VO_UUID_MUST_BE_A_PURE_STRING")
        clean_uuid = vo_uuid.strip()
        if not clean_uuid:
            logger.error("GET_VO_UUID_EMPTY")
            raise ValueError("VO_UUID_CANNOT_BE_EMPTY_OR_WHITESPACE")
        if not Identity.is_valid(clean_uuid):
            logger.error("GET_VO_INVALID_UUID: %s", clean_uuid)
            raise ValueError("INVALID_VO_UUID_STRUCTURE")
        return self.vos.get(clean_uuid)

    def get_all_vos(self, project_uuid: str) -> List[ChangeOrder]:
        if not isinstance(project_uuid, str) or not Identity.is_valid(project_uuid):
            logger.error("GET_ALL_VOS_INVALID_PROJECT_UUID: %r", project_uuid)
            raise ValueError(f"INVALID_QUERY_PROJECT_UUID_STRUCTURE: {project_uuid}")
        return [v for v in self.vos.values() if v.project_uuid == project_uuid]

    def update_status(self, vo_uuid: str, new_status: VOStatus) -> bool:
        if not isinstance(new_status, VOStatus):
            logger.error("UPDATE_STATUS_INVALID_ENUM: %r", new_status)
            raise TypeError("TARGET_STATUS_MUST_BE_AN_INSTANCE_OF_VO_STATUS_ENUM")

        vo = self.get_vo(vo_uuid)
        if not vo:
            logger.warning("UPDATE_STATUS_VO_NOT_FOUND: %s", vo_uuid)
            return False

        vo_dump = vo.model_dump()
        vo_dump["status"] = new_status
        self.vos[vo_uuid] = ChangeOrder(**vo_dump)
        logger.info("Change order status updated: %s -> %s", vo_uuid, new_status.value)
        return True

    def add_approval(self, vo_uuid: str, role: str, approved_by: str, date: str, status: str = "APPROVED") -> bool:
        vo = self.get_vo(vo_uuid)
        if not vo:
            logger.warning("ADD_APPROVAL_VO_NOT_FOUND: %s", vo_uuid)
            return False

        new_step = ApprovalStep(
            role=role,
            approved_by=approved_by,
            date=date,
            status=status,
        )

        extended_chain = list(vo.approval_chain)
        extended_chain.append(new_step)

        vo_dump = vo.model_dump()
        vo_dump["approval_chain"] = tuple(extended_chain)
        self.vos[vo_uuid] = ChangeOrder(**vo_dump)
        logger.info("Approval added to VO %s by %s", vo_uuid, approved_by)
        return True
