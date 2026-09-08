from __future__ import annotations

import logging
import math
from typing import Any, Dict, List, Optional, Tuple, Set

from pydantic import BaseModel, ConfigDict, Field, field_validator

from fastra_core.identity import Identity
from .validators import LooseUUID
from .validators import LooseUUID

logger = logging.getLogger("fastra_core.digital_twin.as_built")


class AsBuiltDifference(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        strict=True,
        frozen=True,
        allow_inf_nan=False,
    )

    entity_uuid: LooseUUID = Field(..., max_length=64)
    field: str = Field(..., min_length=1, max_length=128)
    planned_value: Any = Field(default=None)
    as_built_value: Any = Field(default=None)
    description: str = Field(default="", max_length=512)

    @field_validator("field", "description", mode="before")
    @classmethod
    def sanitize_strings(cls, value: Any) -> Any:
        if value is None:
            return ""
        if not isinstance(value, str):
            logger.error("AS_BUILT_DIFFERENCE_STRING_COERCION_REJECTED: %r", value)
            raise TypeError("VALUE_MUST_BE_A_PURE_STRING_COERCION_FORBIDDEN")
        stripped = value.strip()
        if not stripped and value:
            logger.error("AS_BUILT_DIFFERENCE_WHITESPACE_ONLY_STRING_REJECTED")
            raise ValueError("STRING_CANNOT_CONSIST_OF_WHITESPACE_ONLY")
        return stripped

    @field_validator("planned_value", "as_built_value", mode="before")
    @classmethod
    def validate_comparison_values(cls, value: Any) -> Any:
        if isinstance(value, float):
            if math.isnan(value) or math.isinf(value):
                logger.error("AS_BUILT_DIFFERENCE_NUMERIC_ANOMALY: %s", value)
                raise ValueError("NUMERIC_ANOMALY_DETECTED_CANNOT_STORE_NAN_OR_INFINITE")
        return value


class AsBuiltRecord(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        strict=True,
        frozen=True,
        allow_inf_nan=False,
    )

    project_uuid: LooseUUID = Field(..., max_length=64)
    entity_uuid: LooseUUID = Field(..., max_length=64)
    planned_state: Dict[str, Any] = Field(default_factory=dict)
    as_built_state: Dict[str, Any] = Field(default_factory=dict)
    record_uuid: str = Field(
        default_factory=Identity.generate,
        pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    )
    differences: Tuple[AsBuiltDifference, ...] = Field(default_factory=tuple)

    @field_validator("planned_state", "as_built_state", mode="before")
    @classmethod
    def validate_state_dictionaries(cls, value: Any) -> Dict[str, Any]:
        if not isinstance(value, dict):
            logger.error("AS_BUILT_STATE_MUST_BE_DICT: %r", value)
            raise TypeError("STATE_DATA_MUST_BE_A_VALID_DICTIONARY")
        for k, v in value.items():
            if not isinstance(k, str) or not k.strip():
                logger.error("AS_BUILT_STATE_INVALID_KEY: %r", k)
                raise ValueError("STATE_KEYS_MUST_BE_NON_EMPTY_STRINGS")
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                if math.isnan(v) or math.isinf(v):
                    logger.error("AS_BUILT_STATE_NUMERIC_ANOMALY at key %s: %s", k, v)
                    raise ValueError(f"NUMERIC_ANOMALY_DETECTED_IN_STATE_VALUE_AT_KEY_{k}")
        return value

    @field_validator("differences", mode="before")
    @classmethod
    def validate_differences_tuple(cls, value: Any) -> Tuple[AsBuiltDifference, ...]:
        if not isinstance(value, (list, tuple)):
            logger.error("AS_BUILT_DIFFERENCES_MUST_BE_LIST_OR_TUPLE: %r", value)
            raise TypeError("DIFFERENCES_MUST_BE_A_LIST_OR_TUPLE")
        for idx, item in enumerate(value):
            if not isinstance(item, AsBuiltDifference):
                logger.error("AS_BUILT_DIFFERENCE_ITEM_%d_INVALID_TYPE: %r", idx, item)
                raise TypeError(f"DIFFERENCE_ITEM_AT_INDEX_{idx}_MUST_BE_AS_BUILT_DIFFERENCE")
        return tuple(value)

    def compute_differences(self) -> "AsBuiltRecord":
        computed_diffs: List[AsBuiltDifference] = []

        all_keys: Set[str] = set(self.planned_state.keys()) | set(self.as_built_state.keys())
        sorted_keys = sorted(all_keys)

        for key in sorted_keys:
            planned_val = self.planned_state.get(key)
            as_built_val = self.as_built_state.get(key)

            if planned_val != as_built_val:
                diff_payload = {
                    "entity_uuid": self.entity_uuid,
                    "field": key,
                    "planned_value": planned_val,
                    "as_built_value": as_built_val,
                    "description": f"Perubahan material/spasial terdeteksi pada atribut: {key}",
                }
                computed_diffs.append(AsBuiltDifference.model_validate(diff_payload))

        record_dump = self.model_dump()
        record_dump["differences"] = tuple(computed_diffs)

        return AsBuiltRecord.model_validate(record_dump)


class AsBuiltStore(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        strict=True,
        frozen=False,
        allow_inf_nan=False,
    )

    records: Dict[str, AsBuiltRecord] = Field(default_factory=dict)

    def add_record(self, record: AsBuiltRecord) -> AsBuiltRecord:
        if not isinstance(record, AsBuiltRecord):
            logger.error("AS_BUILT_STORE_ADD_RECORD_INVALID_TYPE: %r", record)
            raise TypeError("STORE_OPERATION_VIOLATION_RECORD_MUST_BE_AN_INSTANCE_OF_AS_BUILT_RECORD")

        processed_record = record.compute_differences()

        self.records[processed_record.record_uuid] = processed_record
        logger.info("As-built record added: %s", processed_record.record_uuid)
        return processed_record

    def get_record(self, record_uuid: str) -> Optional[AsBuiltRecord]:
        if not isinstance(record_uuid, str):
            logger.error("AS_BUILT_STORE_GET_RECORD_UUID_NOT_STRING: %r", record_uuid)
            raise TypeError("RECORD_UUID_MUST_BE_A_PURE_STRING")
        clean_uuid = record_uuid.strip()
        if not clean_uuid:
            logger.error("AS_BUILT_STORE_GET_RECORD_UUID_EMPTY")
            raise ValueError("RECORD_UUID_CANNOT_BE_EMPTY_OR_WHITESPACE")
        if not Identity.is_valid(clean_uuid):
            logger.error("AS_BUILT_STORE_GET_RECORD_INVALID_UUID: %s", clean_uuid)
            raise ValueError("INVALID_RECORD_UUID_STRUCTURE")
        return self.records.get(clean_uuid)

    def get_all_records(self, project_uuid: str) -> List[AsBuiltRecord]:
        if not isinstance(project_uuid, str) or not project_uuid.strip():
            logger.error("AS_BUILT_STORE_QUERY_INVALID_PROJECT_UUID: %r", project_uuid)
            raise ValueError(f"INVALID_QUERY_PROJECT_UUID_STRUCTURE: {project_uuid}")
        return [r for r in self.records.values() if r.project_uuid == project_uuid]

