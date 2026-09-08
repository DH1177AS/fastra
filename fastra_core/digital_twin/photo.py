from __future__ import annotations

import logging
import math
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, ConfigDict, Field, field_validator

from fastra_core.digital_twin.snapshot import Snapshot
from fastra_core.identity import Identity

logger = logging.getLogger("fastra_core.digital_twin.photo")


class PhotoData(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        strict=True,
        frozen=True,
        allow_inf_nan=False,
    )

    project_uuid: str = Field(..., min_length=1, max_length=64)
    capture_date: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    photo_uuid: str = Field(
        default_factory=Identity.generate,
        pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    )
    capture_method: str = Field(default="HP", min_length=2, max_length=64)
    captured_by: str = Field(default="Unknown", min_length=3, max_length=128)
    location: Optional[Dict[str, float]] = Field(
        default=None, description="Koordinat GPS terikat: latitude, longitude, altitude"
    )
    direction_degrees: Optional[float] = Field(
        default=None, ge=0.0, lt=360.0, description="Arah kompas pengambilan foto"
    )
    entity_references: Tuple[str, ...] = Field(
        default_factory=tuple, description="Kumpulan UUID entitas spasial penyusun"
    )
    tags: Tuple[str, ...] = Field(default_factory=tuple)
    file: Dict[str, Any] = Field(default_factory=dict, description="Metadata binari berkas penyimpanan")
    annotations: Tuple[Dict[str, Any], ...] = Field(
        default_factory=tuple, description="Informasi markup spasial / bounding boxes"
    )

    @field_validator("photo_uuid", mode="after")
    @classmethod
    def verify_uuid_integrity(cls, value: str) -> str:
        if not Identity.is_valid(value):
            logger.error("UUID_INTEGRITY_COMPROMISED: %s", value)
            raise ValueError("UUID_INTEGRITY_COMPROMISED_INVALID_STRUCTURE")
        return value

    @field_validator("capture_method", "captured_by", mode="before")
    @classmethod
    def sanitize_strings(cls, value: Any) -> str:
        if not isinstance(value, str):
            logger.error("PHOTO_STRING_COERCION_REJECTED: %r", value)
            raise TypeError("VALUE_MUST_BE_A_PURE_STRING_COERCION_FORBIDDEN")
        stripped = value.strip()
        if not stripped:
            logger.error("PHOTO_STRING_EMPTY_OR_WHITESPACE_REJECTED")
            raise ValueError("STRING_VALUE_CANNOT_BE_EMPTY_OR_WHITESPACE")
        return stripped

    @field_validator("direction_degrees", mode="before")
    @classmethod
    def validate_direction_numeric(cls, value: Any) -> Optional[float]:
        if value is None:
            return None
        if isinstance(value, bool):
            logger.error("DIRECTION_BOOLEAN_REJECTED: %r", value)
            raise TypeError("DATA_TYPE_COERCION_FORBIDDEN_BOOLEAN_NOT_ALLOWED")
        if not isinstance(value, (int, float)):
            logger.error("DIRECTION_NON_NUMERIC_REJECTED: %r", value)
            raise TypeError("DIRECTION_DEGREES_MUST_BE_PURE_NUMERIC_TYPE")
        float_val = float(value)
        if math.isnan(float_val) or math.isinf(float_val):
            logger.error("DIRECTION_NAN_OR_INF_REJECTED: %s", float_val)
            raise ValueError("NUMERIC_ANOMALY_DETECTED_DIRECTION_CANNOT_BE_NAN_OR_INFINITE")
        if not (0.0 <= float_val < 360.0):
            logger.error("DIRECTION_BOUNDARY_VIOLATION: %s", float_val)
            raise ValueError(
                f"BOUNDARY_VIOLATION_DIRECTION_MUST_BE_BETWEEN_0_AND_360_DEGREES: {float_val}"
            )
        return float_val

    @field_validator("location", mode="before")
    @classmethod
    def validate_geospatial_coordinates(cls, value: Any) -> Optional[Dict[str, float]]:
        if value is None:
            return None
        if not isinstance(value, dict):
            logger.error("LOCATION_MUST_BE_DICT: %r", value)
            raise TypeError("LOCATION_METADATA_MUST_BE_A_VALID_DICTIONARY")

        required_keys = {"latitude", "longitude"}
        if not required_keys.issubset(value.keys()):
            logger.error("LOCATION_MISSING_REQUIRED_KEYS: %s", value.keys())
            raise ValueError("LOCATION_MISSING_REQUIRED_GEOSPATIAL_KEYS_LATITUDE_LONGITUDE")

        validated_location: Dict[str, float] = {}
        for k, v in value.items():
            if not isinstance(k, str) or not k.strip():
                logger.error("LOCATION_INVALID_KEY: %r", k)
                raise ValueError("GEOSPATIAL_KEYS_MUST_BE_NON_EMPTY_STRINGS")
            if isinstance(v, bool) or not isinstance(v, (int, float)):
                logger.error("LOCATION_NON_NUMERIC_VALUE at key %s: %r", k, v)
                raise TypeError(f"GEOSPATIAL_COORDINATE_VALUE_MUST_BE_NUMERIC_AT_KEY_{k}")
            float_v = float(v)
            if math.isnan(float_v) or math.isinf(float_v):
                logger.error("LOCATION_NAN_OR_INF at key %s: %s", k, float_v)
                raise ValueError(f"NUMERIC_ANOMALY_DETECTED_AT_GEOSPATIAL_KEY_{k}")

            k_clean = k.strip()
            if k_clean == "latitude" and not (-90.0 <= float_v <= 90.0):
                logger.error("LATITUDE_BOUNDARY_VIOLATION: %s", float_v)
                raise ValueError(f"GEOSPATIAL_BOUNDARY_VIOLATION_LATITUDE_MUST_BE_BETWEEN_-90_AND_90: {float_v}")
            if k_clean == "longitude" and not (-180.0 <= float_v <= 180.0):
                logger.error("LONGITUDE_BOUNDARY_VIOLATION: %s", float_v)
                raise ValueError(
                    f"GEOSPATIAL_BOUNDARY_VIOLATION_LONGITUDE_MUST_BE_BETWEEN_-180_AND_180: {float_v}"
                )
            if k_clean == "altitude" and float_v < -11000.0:
                logger.error("ALTITUDE_BOUNDARY_VIOLATION: %s", float_v)
                raise ValueError("GEOSPATIAL_BOUNDARY_VIOLATION_ALTITUDE_TOO_LOW")

            validated_location[k_clean] = float_v
        return validated_location

    @field_validator("entity_references", "tags", mode="before")
    @classmethod
    def validate_string_tuples(cls, value: Any) -> Tuple[str, ...]:
        if not isinstance(value, (list, tuple)):
            logger.error("TUPLE_FIELD_MUST_BE_LIST_OR_TUPLE: %r", value)
            raise TypeError("VALUE_MUST_BE_A_LIST_OR_TUPLE")
        clean_values: List[str] = []
        for idx, item in enumerate(value):
            if not isinstance(item, str):
                logger.error("TUPLE_ITEM_%d_NOT_STRING: %r", idx, item)
                raise TypeError("TUPLE_ITEMS_MUST_BE_PURE_STRINGS")
            stripped = item.strip()
            if not stripped:
                logger.error("TUPLE_ITEM_%d_EMPTY: %r", idx, item)
                raise ValueError("STRING_VALUE_CANNOT_BE_EMPTY_OR_WHITESPACE")
            clean_values.append(stripped)
        return tuple(clean_values)

    @field_validator("file", mode="before")
    @classmethod
    def validate_file_metadata(cls, value: Any) -> Dict[str, Any]:
        if not isinstance(value, dict):
            logger.error("FILE_MUST_BE_DICT: %r", value)
            raise TypeError("FILE_METADATA_MUST_BE_A_VALID_DICTIONARY")
        for k, v in value.items():
            if not isinstance(k, str) or not k.strip():
                logger.error("FILE_INVALID_KEY: %r", k)
                raise ValueError("FILE_METADATA_KEYS_MUST_BE_NON_EMPTY_STRINGS")
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                if math.isnan(v) or math.isinf(v):
                    logger.error("FILE_NUMERIC_ANOMALY at key %s: %s", k, v)
                    raise ValueError(f"NUMERIC_ANOMALY_DETECTED_IN_FILE_METADATA_AT_KEY_{k}")
        return value

    @field_validator("annotations", mode="before")
    @classmethod
    def validate_annotations(cls, value: Any) -> Tuple[Dict[str, Any], ...]:
        if not isinstance(value, (list, tuple)):
            logger.error("ANNOTATIONS_MUST_BE_LIST_OR_TUPLE: %r", value)
            raise TypeError("ANNOTATIONS_MUST_BE_A_LIST_OR_TUPLE")
        clean_annotations: List[Dict[str, Any]] = []
        for idx, item in enumerate(value):
            if not isinstance(item, dict):
                logger.error("ANNOTATION_%d_NOT_DICT: %r", idx, item)
                raise TypeError(f"ANNOTATION_ITEM_AT_INDEX_{idx}_MUST_BE_A_DICTIONARY")
            for k, v in item.items():
                if not isinstance(k, str) or not k.strip():
                    logger.error("ANNOTATION_%d_INVALID_KEY: %r", idx, k)
                    raise ValueError(f"ANNOTATION_KEYS_MUST_BE_NON_EMPTY_STRINGS_AT_INDEX_{idx}")
                if isinstance(v, (int, float)) and not isinstance(v, bool):
                    if math.isnan(v) or math.isinf(v):
                        logger.error("ANNOTATION_%d_NUMERIC_ANOMALY at key %s: %s", idx, k, v)
                        raise ValueError(
                            f"NUMERIC_ANOMALY_DETECTED_IN_ANNOTATION_AT_INDEX_{idx}_KEY_{k}"
                        )
            clean_annotations.append(item)
        return tuple(clean_annotations)

    def validate_entity_references(self, snapshot: Snapshot) -> bool:
        if not isinstance(snapshot, Snapshot):
            logger.error("SNAPSHOT_INPUT_MUST_BE_A_SNAPSHOT_INSTANCE")
            raise TypeError("SNAPSHOT_INPUT_MUST_BE_AN_INSTANCE_OF_SNAPSHOT_CLASS")

        entities = snapshot.ccm_state.get("entities", {})
        if not isinstance(entities, dict):
            logger.warning("SNAPSHOT_ENTITIES_IS_NOT_A_DICT")
            return False

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
            "entity_references": list(self.entity_references),
            "tags": list(self.tags),
            "file": self.file,
            "annotations": [dict(ann) for ann in self.annotations],
        }