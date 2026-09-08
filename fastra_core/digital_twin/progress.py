# fastra_core\digital_twin\progress.py

from __future__ import annotations

import logging
import math
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from fastra_core.digital_twin.enums import IssueSeverity, IssueStatus, ProgressStatus, ReportType
from fastra_core.identity import Identity

logger = logging.getLogger("fastra_core.digital_twin.progress")


class EntityProgress(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        strict=True,
        frozen=True,
        allow_inf_nan=False,
    )

    entity_uuid: str = Field(..., min_length=1, max_length=128)
    entity_name: str = Field(..., min_length=2, max_length=255)
    work_item_code: str = Field(..., min_length=3, max_length=64, pattern=r"^[A-Z0-9\-\.\:]+$")
    planned_quantity: float = Field(..., ge=0.0)
    completed_quantity: float = Field(..., ge=0.0)
    unit: str = Field(default="m²", min_length=1, max_length=32)
    status: str = Field(default="IN_PROGRESS", min_length=1, max_length=64)
    percentage: float = Field(default=0.0, ge=0.0)

    @field_validator("entity_name", "work_item_code", "unit", mode="before")
    @classmethod
    def sanitize_strings(cls, value: Any) -> str:
        if not isinstance(value, str):
            raise TypeError("VALUE_MUST_BE_A_PURE_STRING_COERCION_FORBIDDEN")
        stripped = value.strip()
        if not stripped:
            raise ValueError("STRING_VALUE_CANNOT_BE_EMPTY_OR_WHITESPACE")
        return stripped

    @field_validator("planned_quantity", "completed_quantity", mode="before")
    @classmethod
    def validate_quantities_numeric(cls, value: Any) -> float:
        if isinstance(value, bool):
            raise TypeError("DATA_TYPE_COERCION_FORBIDDEN_BOOLEAN_NOT_ALLOWED")
        if not isinstance(value, (int, float)):
            raise TypeError("QUANTITY_MUST_BE_A_PURE_NUMERIC_TYPE")
        float_val = float(value)
        if math.isnan(float_val) or math.isinf(float_val) or float_val < 0.0:
            raise ValueError("QUANTITY_CANNOT_BE_NEGATIVE_OR_NUMERIC_ANOMALY")
        return float_val

    @model_validator(mode="after")
    def compute_percentage_safely(self) -> "EntityProgress":
        if self.planned_quantity > 0.0:
            calc_pct = round((self.completed_quantity / self.planned_quantity) * 100.0, 2)
            if math.isnan(calc_pct) or math.isinf(calc_pct):
                raise ValueError("NUMERIC_ANOMALY_DETECTED_PERCENTAGE_CALCULATION_CORRUPTED")
            object.__setattr__(self, "percentage", calc_pct)
        else:
            object.__setattr__(self, "percentage", 0.0)
        return self


class Issue(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        strict=True,
        frozen=True,
        allow_inf_nan=False,
    )

    issue_uuid: str = Field(
        default_factory=Identity.generate,
        pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    )
    description: str = Field(..., min_length=5, max_length=1024)
    severity: IssueSeverity = Field(default=IssueSeverity.LOW)
    status: IssueStatus = Field(default=IssueStatus.OPEN)
    reported_by: str = Field(..., min_length=3, max_length=128)
    photos: Tuple[str, ...] = Field(default_factory=tuple)

    @field_validator("issue_uuid", mode="after")
    @classmethod
    def verify_uuid_integrity(cls, value: str) -> str:
        if not Identity.is_valid(value):
            raise ValueError("UUID_INTEGRITY_COMPROMISED_INVALID_STRUCTURE")
        return value

    @field_validator("description", "reported_by", mode="before")
    @classmethod
    def sanitize_issue_strings(cls, value: Any) -> str:
        if not isinstance(value, str):
            raise TypeError("VALUE_MUST_BE_A_PURE_STRING_COERCION_FORBIDDEN")
        stripped = value.strip()
        if not stripped:
            raise ValueError("STRING_VALUE_CANNOT_BE_EMPTY_OR_WHITESPACE")
        return stripped

    @field_validator("photos", mode="before")
    @classmethod
    def validate_photo_uuids_collection(cls, value: Any) -> Tuple[str, ...]:
        if isinstance(value, bool):
            raise TypeError("DATA_TYPE_COERCION_FORBIDDEN_BOOLEAN_NOT_ALLOWED")
        if not isinstance(value, (list, tuple)):
            raise TypeError("PHOTOS_MUST_BE_A_LIST_OR_TUPLE")
        clean_photos: List[str] = []
        for idx, p in enumerate(value):
            if not isinstance(p, str) or not Identity.is_valid(p):
                raise ValueError(f"INVALID_PHOTO_UUID_STRUCTURE_AT_INDEX_{idx}: {p}")
            clean_photos.append(p)
        return tuple(clean_photos)


class MaterialDelivery(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        strict=True,
        frozen=True,
        allow_inf_nan=False,
    )

    material_uuid: str = Field(
        ...,
        pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    )
    quantity: float = Field(..., ge=0.0)
    unit: str = Field(..., min_length=1, max_length=32)
    delivery_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("material_uuid", mode="after")
    @classmethod
    def verify_uuid_integrity(cls, value: str) -> str:
        if not Identity.is_valid(value):
            raise ValueError("UUID_INTEGRITY_COMPROMISED_INVALID_STRUCTURE")
        return value

    @field_validator("unit", mode="before")
    @classmethod
    def sanitize_unit_string(cls, value: Any) -> str:
        if not isinstance(value, str):
            raise TypeError("VALUE_MUST_BE_A_PURE_STRING_COERCION_FORBIDDEN")
        stripped = value.strip()
        if not stripped:
            raise ValueError("MATERIAL_UNIT_CANNOT_BE_EMPTY")
        return stripped

    @field_validator("quantity", mode="before")
    @classmethod
    def validate_quantity_numeric(cls, value: Any) -> float:
        if isinstance(value, bool):
            raise TypeError("DATA_TYPE_COERCION_FORBIDDEN_BOOLEAN_NOT_ALLOWED")
        if not isinstance(value, (int, float)):
            raise TypeError("MATERIAL_QUANTITY_MUST_BE_A_PURE_NUMERIC_TYPE")
        float_val = float(value)
        if math.isnan(float_val) or math.isinf(float_val) or float_val < 0.0:
            raise ValueError("MATERIAL_QUANTITY_MUST_BE_FINITE_AND_NON_NEGATIVE")
        return float_val


class ProgressEntry(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        strict=True,
        frozen=True,
        allow_inf_nan=False,
    )

    project_uuid: str = Field(..., min_length=1, max_length=128)
    report_date: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    report_type: str = Field(default="DAILY", min_length=1, max_length=64)
    period_start: Optional[str] = Field(default=None)
    period_end: Optional[str] = Field(default=None)
    overall_progress_percentage: float = Field(default=0.0, ge=0.0, le=100.0)
    progress_entry_uuid: str = Field(default_factory=lambda: str(Identity.generate()), min_length=1, max_length=128)
    entity_progress: Tuple[EntityProgress, ...] = Field(default_factory=tuple)
    issues: Tuple[Issue, ...] = Field(default_factory=tuple)
    weather: Dict[str, Any] = Field(default_factory=dict)
    labor_on_site: Dict[str, Any] = Field(default_factory=dict)
    material_delivered: Tuple[MaterialDelivery, ...] = Field(default_factory=tuple)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("project_uuid", "progress_entry_uuid", "report_type", mode="before")
    @classmethod
    def sanitize_strings(cls, value: Any) -> str:
        if not isinstance(value, str):
            raise TypeError("VALUE_MUST_BE_A_PURE_STRING_COERCION_FORBIDDEN")
        stripped = value.strip()
        if not stripped:
            raise ValueError("STRING_VALUE_CANNOT_BE_EMPTY_OR_WHITESPACE")
        return stripped

    @field_validator("weather", "labor_on_site", "metadata", mode="before")
    @classmethod
    def validate_dictionaries_no_coercion(cls, value: Any) -> Dict[str, Any]:
        if not isinstance(value, dict):
            raise TypeError("PROGRESS_METADATA_MUST_BE_A_VALID_DICTIONARY")
        return value

    @field_validator("entity_progress", "issues", "material_delivered", mode="before")
    @classmethod
    def validate_tuples(cls, value: Any, info: Any) -> Tuple[Any, ...]:
        if not isinstance(value, (list, tuple)):
            raise TypeError("COLLECTION_MUST_BE_A_LIST_OR_TUPLE")
        field_name = info.field_name
        expected_type = {
            "entity_progress": EntityProgress,
            "issues": Issue,
            "material_delivered": MaterialDelivery,
        }[field_name]
        for idx, item in enumerate(value):
            if not isinstance(item, expected_type):
                raise TypeError(f"ITEM_AT_INDEX_{idx}_MUST_BE_{expected_type.__name__.upper()}")
        return tuple(value)


class ProgressStore(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        strict=True,
        frozen=False,
        allow_inf_nan=False,
    )

    entries: Dict[str, ProgressEntry] = Field(default_factory=dict)

    def add_entry(self, entry: ProgressEntry) -> ProgressEntry:
        if not isinstance(entry, ProgressEntry):
            raise TypeError("STORE_OPERATION_VIOLATION_ENTRY_MUST_BE_AN_INSTANCE_OF_PROGRESS_ENTRY")
        self.entries[entry.progress_entry_uuid] = entry
        return entry

    def get_entry(self, entry_uuid: str) -> Optional[ProgressEntry]:
        if not isinstance(entry_uuid, str):
            raise TypeError("ENTRY_UUID_MUST_BE_A_PURE_STRING")
        clean_uuid = entry_uuid.strip()
        if not clean_uuid:
            raise ValueError("ENTRY_UUID_CANNOT_BE_EMPTY_OR_WHITESPACE")
        return self.entries.get(clean_uuid)

    def get_entries(self, project_uuid: str) -> List[ProgressEntry]:
        if not isinstance(project_uuid, str) or not project_uuid.strip():
            raise ValueError(f"INVALID_QUERY_PROJECT_UUID_STRUCTURE: {project_uuid}")
        return [e for e in self.entries.values() if e.project_uuid == project_uuid]

    def calculate_overall_progress(
        self,
        entry: ProgressEntry,
        weight_map: Optional[Dict[str, float]] = None,
    ) -> float:
        if not isinstance(entry, ProgressEntry):
            raise TypeError("INPUT_MUST_BE_A_VALID_PROGRESS_ENTRY_INSTANCE")

        weighted_completed = 0.0
        weighted_planned = 0.0

        for ep in entry.entity_progress:
            weight = 1.0
            if weight_map is not None:
                if not isinstance(weight_map, dict):
                    raise TypeError("WEIGHT_MAP_MUST_BE_A_VALID_DICTIONARY")
                weight = weight_map.get(ep.work_item_code, 1.0)

            if isinstance(weight, bool) or not isinstance(weight, (int, float)) or weight < 0.0:
                raise ValueError(f"ILLEGAL_WEIGHT_VALUE_ASSIGNED_FOR_CODE_{ep.work_item_code}")

            weighted_completed += ep.completed_quantity * float(weight)
            weighted_planned += ep.planned_quantity * float(weight)

        if math.isnan(weighted_completed) or math.isinf(weighted_completed) or math.isnan(weighted_planned) or math.isinf(weighted_planned):
            raise ValueError("NUMERIC_ANOMALY_DETECTED_DURING_S_CURVE_AGGREGATION")

        if abs(weighted_planned) < 1e-12:
            return 0.0

        result = round((weighted_completed / weighted_planned) * 100.0, 2)
        return result

    def planned_vs_actual(
        self,
        planned_quantity: float,
        actual_quantity: float,
        planned_duration: float,
        actual_duration: float,
        planned_cost: float,
        actual_cost: float,
    ) -> Dict[str, Any]:
        params = {
            "planned_quantity": planned_quantity,
            "actual_quantity": actual_quantity,
            "planned_duration": planned_duration,
            "actual_duration": actual_duration,
            "planned_cost": planned_cost,
            "actual_cost": actual_cost,
        }
        for param_name, param_val in params.items():
            if isinstance(param_val, bool) or not isinstance(param_val, (int, float)):
                raise TypeError(f"EVM_PARAMETER_{param_name.upper()}_MUST_BE_PURE_NUMERIC")
            if math.isnan(param_val) or math.isinf(param_val):
                raise ValueError(f"NUMERIC_ANOMALY_DETECTED_AT_EVM_PARAMETER_{param_name.upper()}")

        qty_variance = float(actual_quantity - planned_quantity)
        dur_variance = float(actual_duration - planned_duration)
        cost_variance = float(actual_cost - planned_cost)

        cost_variance_pct = 0.0
        if float(planned_cost) > 0.0:
            cost_variance_pct = round((cost_variance / float(planned_cost)) * 100.0, 2)
            if math.isnan(cost_variance_pct) or math.isinf(cost_variance_pct):
                raise ValueError("NUMERIC_ANOMALY_DETECTED_IN_COST_VARIANCE_PERCENTAGE")

        return {
            "quantity_variance": qty_variance,
            "duration_variance_days": dur_variance,
            "cost_variance": cost_variance,
            "cost_variance_percentage": cost_variance_pct,
            "status": "OVER_BUDGET" if cost_variance > 0.0 else ("UNDER_BUDGET" if cost_variance < 0.0 else "ON_BUDGET"),
            "schedule_status": "BEHIND_SCHEDULE" if dur_variance > 0.0 else ("AHEAD_SCHEDULE" if dur_variance < 0.0 else "ON_SCHEDULE"),
        }