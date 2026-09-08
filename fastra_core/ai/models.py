# fastra_core\ai\models.py

from __future__ import annotations

import logging
import math
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from fastra_core.ai.enums import VerificationStatus  # not used but kept for potential future
from fastra_core.identity import Identity
from fastra_core.serialization.hash import canonical_hash

logger = logging.getLogger("fastra_core.ai.models")


class VisionResult(BaseModel):
    """
    Output Vision AI (Estimasi awal komponen struktural/material dari foto lapangan).
    Mengunci keutuhan data inferensi kognitif secara rigid menggunakan tuple immutable.
    """
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        strict=True,
        frozen=True,
        allow_inf_nan=False,
    )

    model_version: str = Field(..., min_length=1, max_length=32, pattern=r"^[a-zA-Z0-9\.\-\_]+$")
    input_photos: Tuple[str, ...] = Field(default_factory=tuple, description="Kumpulan UUID/Path foto input")
    estimations: Dict[str, Any] = Field(default_factory=dict, description="Peta estimasi kuantitas kognitif")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    result_uuid: str = Field(
        default_factory=Identity.generate,
        pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    )
    assumptions: Tuple[str, ...] = Field(default_factory=tuple)
    limitations: Tuple[str, ...] = Field(default_factory=tuple)
    suggested_actions: Tuple[str, ...] = Field(default_factory=tuple)

    @field_validator("result_uuid", mode="after")
    @classmethod
    def verify_uuid_integrity(cls, value: str) -> str:
        if value and not Identity.is_valid(value):
            logger.error("VISION_RESULT_INVALID_UUID: %s", value)
            raise ValueError("UUID_INTEGRITY_COMPROMISED_INVALID_STRUCTURE")
        return value

    @field_validator("model_version", mode="before")
    @classmethod
    def sanitize_model_version(cls, value: Any) -> str:
        if not isinstance(value, str):
            logger.error("MODEL_VERSION_MUST_BE_STRING: %r", value)
            raise TypeError("VALUE_MUST_BE_A_PURE_STRING_COERCION_FORBIDDEN")
        stripped = value.strip()
        if not stripped:
            logger.error("MODEL_VERSION_EMPTY")
            raise ValueError("STRING_VALUE_CANNOT_BE_EMPTY_OR_WHITESPACE")
        return stripped

    @field_validator("input_photos", "assumptions", "limitations", "suggested_actions", mode="before")
    @classmethod
    def validate_string_tuples(cls, value: Any) -> Tuple[str, ...]:
        if not isinstance(value, (list, tuple)):
            logger.error("TUPLE_FIELD_MUST_BE_LIST_OR_TUPLE: %r", value)
            raise TypeError("VALUE_MUST_BE_A_LIST_OR_TUPLE")
        clean_items: List[str] = []
        for idx, item in enumerate(value):
            if not isinstance(item, str):
                logger.error("TUPLE_ITEM_%d_NOT_STRING: %r", idx, item)
                raise TypeError("TUPLE_ITEMS_MUST_BE_PURE_STRINGS")
            stripped = item.strip()
            if not stripped:
                logger.error("TUPLE_ITEM_%d_EMPTY: %r", idx, item)
                raise ValueError("STRING_VALUE_CANNOT_BE_EMPTY_OR_WHITESPACE")
            clean_items.append(stripped)
        return tuple(clean_items)

    @field_validator("estimations", mode="before")
    @classmethod
    def validate_estimations_structure(cls, value: Any) -> Dict[str, Any]:
        if not isinstance(value, dict):
            logger.error("ESTIMATIONS_MUST_BE_DICT: %r", value)
            raise TypeError("ESTIMATIONS_MUST_BE_A_VALID_DICTIONARY")

        clean_estimations: Dict[str, Any] = {}
        for key, est in value.items():
            if not isinstance(key, str) or not key.strip():
                logger.error("ESTIMATION_KEY_INVALID: %r", key)
                raise ValueError("ESTIMATION_KEYS_MUST_BE_NON_EMPTY_STRINGS")
            if not isinstance(est, dict) or "confidence" not in est:
                logger.error("ESTIMATION_ITEM_MUST_CONTAIN_CONFIDENCE: %r", est)
                raise ValueError(f"Estimation item '{key}' must be a dictionary containing a 'confidence' key")

            conf = est["confidence"]
            if isinstance(conf, bool):
                logger.error("CONFIDENCE_BOOLEAN_REJECTED at key %s: %r", key, conf)
                raise TypeError(f"DATA_TYPE_COERCION_FORBIDDEN_BOOLEAN_NOT_ALLOWED_IN_CONFIDENCE_AT_{key}")
            if not isinstance(conf, (int, float)):
                logger.error("CONFIDENCE_NON_NUMERIC at key %s: %r", key, conf)
                raise TypeError(f"Confidence value for '{key}' must be a pure numeric type")

            float_conf = float(conf)
            if math.isnan(float_conf) or math.isinf(float_conf):
                logger.error("CONFIDENCE_NAN_OR_INF at key %s: %s", key, float_conf)
                raise ValueError(f"NUMERIC_ANOMALY_DETECTED_IN_CONFIDENCE_SCORE_AT_{key}")
            if not (0.0 <= float_conf <= 1.0):
                logger.error("CONFIDENCE_BOUNDARY_VIOLATION at key %s: %s", key, float_conf)
                raise ValueError(f"BOUNDARY_VIOLATION_CONFIDENCE_SCORE_MUST_BE_BETWEEN_0_AND_1_AT_{key}: {float_conf}")

            clean_estimations[key.strip()] = dict(est)
        return clean_estimations

    def input_hash(self) -> str:
        return canonical_hash(list(self.input_photos))

    def output_hash(self) -> str:
        return canonical_hash(self.estimations)


class DetectedElement(BaseModel):
    """
    Item elemen pekerjaan tunggal hasil pembacaan berkas blueprint spasial (Drawing Element Representation).
    """
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        strict=True,
        frozen=True,
        allow_inf_nan=False,
    )

    proposed_uuid: str = Field(..., min_length=3, max_length=128)
    type: str = Field(..., min_length=2, max_length=64)
    confidence: float = Field(..., ge=0.0, le=1.0)
    source: Optional[str] = Field(default=None, max_length=255)
    properties: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("proposed_uuid", "type", "source", mode="before")
    @classmethod
    def sanitize_strings(cls, value: Any) -> Any:
        if value is None:
            return None
        if not isinstance(value, str):
            logger.error("DETECTED_ELEMENT_STRING_COERCION_REJECTED: %r", value)
            raise TypeError("VALUE_MUST_BE_A_PURE_STRING_COERCION_FORBIDDEN")
        stripped = value.strip()
        if not stripped and value:
            logger.error("DETECTED_ELEMENT_WHITESPACE_ONLY_REJECTED")
            raise ValueError("STRING_CANNOT_CONSIST_OF_WHITESPACE_ONLY")
        return stripped

    @field_validator("confidence", mode="before")
    @classmethod
    def validate_confidence_numeric(cls, value: Any) -> float:
        if isinstance(value, bool):
            logger.error("CONFIDENCE_BOOLEAN_REJECTED: %r", value)
            raise TypeError("DATA_TYPE_COERCION_FORBIDDEN_BOOLEAN_NOT_ALLOWED")
        if not isinstance(value, (int, float)):
            logger.error("CONFIDENCE_NON_NUMERIC: %r", value)
            raise TypeError("CONFIDENCE_VALUE_MUST_BE_PURE_NUMERIC_TYPE")
        float_val = float(value)
        if math.isnan(float_val) or math.isinf(float_val):
            logger.error("CONFIDENCE_NAN_OR_INF: %s", float_val)
            raise ValueError("NUMERIC_ANOMALY_DETECTED_CANNOT_BE_NAN_OR_INFINITE")
        if not (0.0 <= float_val <= 1.0):
            logger.error("CONFIDENCE_BOUNDARY_VIOLATION: %s", float_val)
            raise ValueError("CONFIDENCE_MUST_BE_BETWEEN_0_AND_1")
        return float_val

    @field_validator("properties", mode="before")
    @classmethod
    def validate_properties_dict(cls, value: Any) -> Dict[str, Any]:
        if not isinstance(value, dict):
            logger.error("PROPERTIES_MUST_BE_DICT: %r", value)
            raise TypeError("PROPERTIES_MUST_BE_A_DICTIONARY")
        for k, v in value.items():
            if not isinstance(k, str) or not k.strip():
                logger.error("PROPERTIES_INVALID_KEY: %r", k)
                raise ValueError("PROPERTIES_KEYS_MUST_BE_NON_EMPTY_STRINGS")
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                if math.isnan(v) or math.isinf(v):
                    logger.error("PROPERTIES_NUMERIC_ANOMALY at key %s: %s", k, v)
                    raise ValueError(f"NUMERIC_ANOMALY_DETECTED_IN_PROPERTIES_AT_KEY_{k}")
        return value


class DrawingResult(BaseModel):
    """
    Output Drawing Reader AI (Ekstraksi elemen dasar dari gambar kerja).
    """
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        strict=True,
        frozen=True,
        allow_inf_nan=False,
    )

    model_version: str = Field(..., min_length=1, max_length=32, pattern=r"^[a-zA-Z0-9\.\-\_]+$")
    input_files: Tuple[str, ...] = Field(default_factory=tuple, description="Kumpulan UUID/Path berkas gambar input")
    detected_elements: Dict[str, Tuple[DetectedElement, ...]] = Field(
        ..., description="Peta elemen terdeteksi berdasarkan kategori"
    )
    detected_dimensions: Dict[str, Any] = Field(
        default_factory=dict, description="Dimensi terdeteksi dari gambar (mis. luas bangunan, lebar, tinggi)"
    )
    uncertainties: Tuple[Dict[str, Any], ...] = Field(
        default_factory=tuple, description="Daftar ketidakpastian/keraguan hasil ekstraksi"
    )
    generated_ccm: Dict[str, Any] = Field(
        default_factory=dict, description="CCM proposal yang dihasilkan dari gambar (entities, relationships)"
    )
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    result_uuid: str = Field(
        default_factory=Identity.generate,
        pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    )

    @field_validator("result_uuid", mode="after")
    @classmethod
    def verify_uuid_integrity(cls, value: str) -> str:
        if not Identity.is_valid(value):
            logger.error("DRAWING_RESULT_INVALID_UUID: %s", value)
            raise ValueError("UUID_INTEGRITY_COMPROMISED_INVALID_STRUCTURE")
        return value

    @field_validator("model_version", mode="before")
    @classmethod
    def sanitize_model_version(cls, value: Any) -> str:
        if not isinstance(value, str):
            logger.error("MODEL_VERSION_MUST_BE_STRING: %r", value)
            raise TypeError("VALUE_MUST_BE_A_PURE_STRING_COERCION_FORBIDDEN")
        stripped = value.strip()
        if not stripped:
            logger.error("MODEL_VERSION_EMPTY")
            raise ValueError("STRING_VALUE_CANNOT_BE_EMPTY_OR_WHITESPACE")
        return stripped

    @field_validator("input_files", mode="before")
    @classmethod
    def validate_input_files_tuple(cls, value: Any) -> Tuple[str, ...]:
        if not isinstance(value, (list, tuple)):
            logger.error("INPUT_FILES_MUST_BE_LIST_OR_TUPLE: %r", value)
            raise TypeError("VALUE_MUST_BE_A_LIST_OR_TUPLE")
        clean_files: List[str] = []
        for idx, item in enumerate(value):
            if not isinstance(item, str):
                logger.error("INPUT_FILE_%d_NOT_STRING: %r", idx, item)
                raise TypeError("INPUT_FILES_MUST_BE_PURE_STRINGS")
            stripped = item.strip()
            if not stripped:
                logger.error("INPUT_FILE_%d_EMPTY: %r", idx, item)
                raise ValueError("STRING_VALUE_CANNOT_BE_EMPTY_OR_WHITESPACE")
            clean_files.append(stripped)
        return tuple(clean_files)

    @field_validator("detected_elements", mode="before")
    @classmethod
    def validate_detected_elements(cls, value: Any) -> Dict[str, Tuple[DetectedElement, ...]]:
        if not isinstance(value, dict) or not value:
            logger.error("DETECTED_ELEMENTS_MUST_BE_NON_EMPTY_DICT: %r", value)
            raise ValueError("QUANTITY_CONSTRAINT_VIOLATION_DETECTED_ELEMENTS_CANNOT_BE_EMPTY_OR_NULL")

        clean_map: Dict[str, Tuple[DetectedElement, ...]] = {}
        for category, elements in value.items():
            if not isinstance(category, str) or not category.strip():
                logger.error("DETECTED_ELEMENTS_CATEGORY_INVALID: %r", category)
                raise ValueError("CATEGORY_KEYS_MUST_BE_NON_EMPTY_STRINGS")
            if not isinstance(elements, (list, tuple)):
                logger.error("CATEGORY_%s_ELEMENTS_NOT_LIST_OR_TUPLE: %r", category, elements)
                raise TypeError("DETECTED_ELEMENTS_VALUES_MUST_BE_LIST_OR_TUPLE")

            clean_elements: List[DetectedElement] = []
            for idx, elem in enumerate(elements):
                if not isinstance(elem, DetectedElement):
                    logger.error("ELEMENT_%d_UNDER_%s_NOT_DETECTED_ELEMENT: %r", idx, category, elem)
                    raise TypeError(f"DETECTED_ELEMENT_AT_{idx}_MUST_BE_DETECTED_ELEMENT_INSTANCE")
                clean_elements.append(elem)
            clean_map[category.strip()] = tuple(clean_elements)
        return clean_map

    def input_hash(self) -> str:
        return canonical_hash(list(self.input_files))

    def output_hash(self) -> str:
        serializable_elements = {
            k: [elem.model_dump() for elem in v]
            for k, v in self.detected_elements.items()
        }
        return canonical_hash({
            "detected_elements": serializable_elements,
            "detected_dimensions": self.detected_dimensions,
            "uncertainties": [u for u in self.uncertainties],
        })

    @field_validator("detected_dimensions", mode="before")
    @classmethod
    def validate_detected_dimensions(cls, value: Any) -> Dict[str, Any]:
        if not isinstance(value, dict):
            logger.error("DETECTED_DIMENSIONS_MUST_BE_DICT: %r", value)
            raise TypeError("DETECTED_DIMENSIONS_MUST_BE_A_VALID_DICTIONARY")
        for k, v in value.items():
            if not isinstance(k, str) or not k.strip():
                logger.error("DETECTED_DIMENSIONS_INVALID_KEY: %r", k)
                raise ValueError("DIMENSION_KEYS_MUST_BE_NON_EMPTY_STRINGS")
            if isinstance(v, bool):
                logger.error("DETECTED_DIMENSIONS_BOOLEAN_REJECTED at key %s: %r", k, v)
                raise TypeError("DATA_TYPE_COERCION_FORBIDDEN_BOOLEAN_NOT_ALLOWED")
            if isinstance(v, (int, float)):
                if math.isnan(v) or math.isinf(v):
                    logger.error("DETECTED_DIMENSIONS_NUMERIC_ANOMALY at key %s: %s", k, v)
                    raise ValueError(f"NUMERIC_ANOMALY_DETECTED_IN_DIMENSION_AT_KEY_{k}")
        return value

    @field_validator("uncertainties", mode="before")
    @classmethod
    def validate_uncertainties_tuple(cls, value: Any) -> Tuple[Dict[str, Any], ...]:
        if not isinstance(value, (list, tuple)):
            logger.error("UNCERTAINTIES_MUST_BE_LIST_OR_TUPLE: %r", value)
            raise TypeError("UNCERTAINTIES_MUST_BE_A_LIST_OR_TUPLE")
        clean_uncertainties: List[Dict[str, Any]] = []
        for idx, item in enumerate(value):
            if not isinstance(item, dict):
                logger.error("UNCERTAINTY_%d_NOT_DICT: %r", idx, item)
                raise TypeError(f"UNCERTAINTY_ITEM_AT_INDEX_{idx}_MUST_BE_A_DICTIONARY")
            for k, v in item.items():
                if not isinstance(k, str) or not k.strip():
                    logger.error("UNCERTAINTY_%d_INVALID_KEY: %r", idx, k)
                    raise ValueError(f"UNCERTAINTY_KEYS_MUST_BE_NON_EMPTY_STRINGS_AT_INDEX_{idx}")
                if isinstance(v, (int, float)) and not isinstance(v, bool):
                    if math.isnan(v) or math.isinf(v):
                        logger.error("UNCERTAINTY_%d_NUMERIC_ANOMALY at key %s: %s", idx, k, v)
                        raise ValueError(f"NUMERIC_ANOMALY_DETECTED_IN_UNCERTAINTY_AT_INDEX_{idx}_KEY_{k}")
            clean_uncertainties.append(item)
        return tuple(clean_uncertainties)

    @field_validator("generated_ccm", mode="before")
    @classmethod
    def validate_generated_ccm(cls, value: Any) -> Dict[str, Any]:
        if not isinstance(value, dict):
            logger.error("GENERATED_CCM_MUST_BE_DICT: %r", value)
            raise TypeError("GENERATED_CCM_MUST_BE_A_VALID_DICTIONARY")
        for k, v in value.items():
            if not isinstance(k, str) or not k.strip():
                logger.error("GENERATED_CCM_INVALID_KEY: %r", k)
                raise ValueError("GENERATED_CCM_KEYS_MUST_BE_NON_EMPTY_STRINGS")
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                if math.isnan(v) or math.isinf(v):
                    logger.error("GENERATED_CCM_NUMERIC_ANOMALY at key %s: %s", k, v)
                    raise ValueError(f"NUMERIC_ANOMALY_DETECTED_IN_GENERATED_CCM_AT_KEY_{k}")
        return value
    
class LLMResult(BaseModel):
    """
    Output LLM Assistant (Penerjemah asisten kognitif menuju Construction DSL).
    """
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        strict=True,
        frozen=True,
        allow_inf_nan=False,
    )

    model_version: str = Field(..., min_length=1, max_length=32, pattern=r"^[a-zA-Z0-9\.\-\_]+$")
    input_text: str = Field(..., min_length=2, max_length=4096)
    output_dsl: Optional[str] = Field(default=None, max_length=8192)
    explanation: Optional[str] = Field(default=None, max_length=8192)
    recommendations: Tuple[str, ...] = Field(default_factory=tuple)
    references: Tuple[str, ...] = Field(default_factory=tuple)
    contains_direct_boq: bool = Field(default=False)
    content_safe: bool = Field(default=True)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    result_uuid: str = Field(
        default_factory=Identity.generate,
        pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    )

    @field_validator("result_uuid", mode="after")
    @classmethod
    def verify_uuid_integrity(cls, value: str) -> str:
        if not Identity.is_valid(value):
            logger.error("LLM_RESULT_INVALID_UUID: %s", value)
            raise ValueError("UUID_INTEGRITY_COMPROMISED_INVALID_STRUCTURE")
        return value

    @field_validator("model_version", "input_text", "output_dsl", "explanation", mode="before")
    @classmethod
    def sanitize_strings(cls, value: Any) -> Any:
        if value is None:
            return None
        if not isinstance(value, str):
            logger.error("LLM_RESULT_STRING_COERCION_REJECTED: %r", value)
            raise TypeError("VALUE_MUST_BE_A_PURE_STRING_COERCION_FORBIDDEN")
        stripped = value.strip()
        if not stripped and value:
            logger.error("LLM_RESULT_WHITESPACE_ONLY_REJECTED")
            raise ValueError("STRING_CANNOT_CONSIST_OF_WHITESPACE_ONLY")
        return stripped

    @field_validator("recommendations", "references", mode="before")
    @classmethod
    def validate_string_tuples(cls, value: Any) -> Tuple[str, ...]:
        if not isinstance(value, (list, tuple)):
            logger.error("TUPLE_FIELD_MUST_BE_LIST_OR_TUPLE: %r", value)
            raise TypeError("VALUE_MUST_BE_A_LIST_OR_TUPLE")
        clean_items: List[str] = []
        for idx, item in enumerate(value):
            if not isinstance(item, str):
                logger.error("TUPLE_ITEM_%d_NOT_STRING: %r", idx, item)
                raise TypeError("TUPLE_ITEMS_MUST_BE_PURE_STRINGS")
            stripped = item.strip()
            if not stripped:
                logger.error("TUPLE_ITEM_%d_EMPTY: %r", idx, item)
                raise ValueError("STRING_VALUE_CANNOT_BE_EMPTY_OR_WHITESPACE")
            clean_items.append(stripped)
        return tuple(clean_items)

    @model_validator(mode="after")
    def execute_cognitive_safety_filters(self) -> "LLMResult":
        if self.contains_direct_boq:
            logger.error("COGNITIVE_COMPLIANCE_VIOLATION_LLM_OUTPUT_CANNOT_CONTAIN_DIRECT_BOQ")
            raise ValueError("COGNITIVE_COMPLIANCE_VIOLATION_LLM_OUTPUT_CANNOT_CONTAIN_DIRECT_BOQ")

        boq_indicators = ["BOQ", "BILL OF QUANTITY", "RAB", "GRAND TOTAL BIAYA"]
        combined_text = (
            (self.output_dsl or "") + " " +
            (self.explanation or "") + " " +
            " ".join(self.recommendations)
        ).upper()

        for indicator in boq_indicators:
            if indicator in combined_text:
                object.__setattr__(self, "contains_direct_boq", True)
                logger.error("DIRECT_BOQ_BYPASS_ATTEMPT_DETECTED_VIA_TOKEN_%s", indicator)
                raise ValueError(
                    f"COGNITIVE_COMPLIANCE_VIOLATION_DIRECT_BOQ_BYPASS_ATTEMPT_DETECTED_VIA_TOKEN_{indicator}"
                )

        forbidden_words = ["runtuh", "keruntuhan", "melanggar building code", "membahayakan struktur"]
        lowered_text = ((self.output_dsl or "").lower() + " " + (self.explanation or "").lower())
        for word in forbidden_words:
            if word in lowered_text:
                object.__setattr__(self, "content_safe", False)
                logger.error("STRUCTURAL_SAFETY_CONSTRAINT_VIOLATION_MUTED_AT_%s", word)
                raise ValueError(f"STRUCTURAL_SAFETY_CONSTRAINT_VIOLATION_OUTPUT_CONTAINS_DANGEROUS_TERMS_MUTED_AT_{word}")
        return self

    def input_hash(self) -> str:
        return canonical_hash(self.input_text)

    def output_hash(self) -> str:
        return canonical_hash({
            "output_dsl": self.output_dsl,
            "explanation": self.explanation,
            "recommendations": list(self.recommendations),
        })


class Prediction(BaseModel):
    """
    Item objek proyeksi perkiraan tunggal hasil ramalan model (Prediction Item Forecast Node).
    """
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        strict=True,
        frozen=True,
        allow_inf_nan=False,
    )

    type: str = Field(..., min_length=2, max_length=64, pattern=r"^[A-Z0-9\-_]+$")
    data: Dict[str, Any] = Field(default_factory=dict)
    confidence_interval: Optional[Tuple[float, float]] = Field(default=None)
    confidence_level: Optional[float] = Field(default=None, ge=0.0, le=1.0)

    @field_validator("type", mode="before")
    @classmethod
    def sanitize_type(cls, value: Any) -> str:
        if not isinstance(value, str):
            logger.error("PREDICTION_TYPE_NOT_STRING: %r", value)
            raise TypeError("VALUE_MUST_BE_A_PURE_STRING_COERCION_FORBIDDEN")
        stripped = value.strip()
        if not stripped:
            logger.error("PREDICTION_TYPE_EMPTY")
            raise ValueError("STRING_VALUE_CANNOT_BE_EMPTY_OR_WHITESPACE")
        return stripped

    @field_validator("data", mode="before")
    @classmethod
    def validate_data_dict(cls, value: Any) -> Dict[str, Any]:
        if not isinstance(value, dict):
            logger.error("PREDICTION_DATA_MUST_BE_DICT: %r", value)
            raise TypeError("DATA_MUST_BE_A_DICTIONARY")
        for k, v in value.items():
            if not isinstance(k, str) or not k.strip():
                logger.error("PREDICTION_DATA_INVALID_KEY: %r", k)
                raise ValueError("DATA_KEYS_MUST_BE_NON_EMPTY_STRINGS")
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                if math.isnan(v) or math.isinf(v):
                    logger.error("PREDICTION_DATA_NUMERIC_ANOMALY at key %s: %s", k, v)
                    raise ValueError(f"NUMERIC_ANOMALY_DETECTED_IN_DATA_AT_KEY_{k}")
        return value

    @field_validator("confidence_interval", mode="before")
    @classmethod
    def validate_confidence_interval(cls, value: Any) -> Optional[Tuple[float, float]]:
        if value is None:
            return None
        if not isinstance(value, (list, tuple)) or len(value) != 2:
            logger.error("CONFIDENCE_INTERVAL_INVALID: %r", value)
            raise ValueError("CONFIDENCE_INTERVAL_MUST_BE_A_TWO_ELEMENT_TUPLE")
        a, b = value
        if isinstance(a, bool) or isinstance(b, bool):
            logger.error("CONFIDENCE_INTERVAL_BOOLEAN_REJECTED")
            raise TypeError("DATA_TYPE_COERCION_FORBIDDEN_BOOLEAN_NOT_ALLOWED")
        if not all(isinstance(x, (int, float)) for x in (a, b)):
            logger.error("CONFIDENCE_INTERVAL_NON_NUMERIC: %r", value)
            raise TypeError("CONFIDENCE_INTERVAL_VALUES_MUST_BE_NUMERIC")
        fa, fb = float(a), float(b)
        if math.isnan(fa) or math.isinf(fa) or math.isnan(fb) or math.isinf(fb):
            logger.error("CONFIDENCE_INTERVAL_NAN_OR_INF: %s, %s", fa, fb)
            raise ValueError("CONFIDENCE_INTERVAL_CANNOT_CONTAIN_NAN_OR_INF")
        if fa > fb:
            logger.error("CONFIDENCE_INTERVAL_REVERSED: %s, %s", fa, fb)
            raise ValueError("CONFIDENCE_INTERVAL_LOWER_BOUND_MUST_NOT_EXCEED_UPPER_BOUND")
        return (fa, fb)

    @model_validator(mode="after")
    def verify_confidence_metric_presence(self) -> "Prediction":
        if self.confidence_interval is None and self.confidence_level is None:
            logger.error("PREDICTION_MUST_PROVIDE_INTERVAL_OR_LEVEL")
            raise ValueError("QUANTITATIVE_INTEGRITY_VIOLATION_PREDICTION_MUST_PROVIDE_INTERVAL_OR_LEVEL")
        return self


class PredictionResult(BaseModel):
    """
    Output Prediction AI (Model peramalan risiko deviasi rantai pasok, inflasi komoditas, dan optimasi jadwal).
    """
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        strict=True,
        frozen=True,
        allow_inf_nan=False,
    )

    model_version: str = Field(..., min_length=1, max_length=32, pattern=r"^[a-zA-Z0-9\.\-\_]+$")
    predictions: Tuple[Prediction, ...] = Field(..., description="Daftar objek mata rantai ramalan terhitung")
    recommendations: Tuple[str, ...] = Field(default_factory=tuple)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    result_uuid: str = Field(
        default_factory=Identity.generate,
        pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    )

    @field_validator("result_uuid", mode="after")
    @classmethod
    def verify_uuid_integrity(cls, value: str) -> str:
        if not Identity.is_valid(value):
            logger.error("PREDICTION_RESULT_INVALID_UUID: %s", value)
            raise ValueError("UUID_INTEGRITY_COMPROMISED_INVALID_STRUCTURE")
        return value

    @field_validator("model_version", mode="before")
    @classmethod
    def sanitize_model_version(cls, value: Any) -> str:
        if not isinstance(value, str):
            logger.error("MODEL_VERSION_MUST_BE_STRING: %r", value)
            raise TypeError("VALUE_MUST_BE_A_PURE_STRING_COERCION_FORBIDDEN")
        stripped = value.strip()
        if not stripped:
            logger.error("MODEL_VERSION_EMPTY")
            raise ValueError("STRING_VALUE_CANNOT_BE_EMPTY_OR_WHITESPACE")
        return stripped

    @field_validator("predictions", mode="before")
    @classmethod
    def validate_predictions_tuple(cls, value: Any) -> Tuple[Prediction, ...]:
        if not isinstance(value, (list, tuple)) or not value:
            logger.error("PREDICTIONS_MUST_BE_NON_EMPTY_LIST_OR_TUPLE: %r", value)
            raise ValueError("PREDICTIONS_CANNOT_BE_EMPTY")
        clean_predictions: List[Prediction] = []
        for idx, item in enumerate(value):
            if not isinstance(item, Prediction):
                logger.error("PREDICTION_%d_NOT_PREDICTION: %r", idx, item)
                raise TypeError(f"PREDICTION_AT_INDEX_{idx}_MUST_BE_PREDICTION_INSTANCE")
            clean_predictions.append(item)
        return tuple(clean_predictions)

    @field_validator("recommendations", mode="before")
    @classmethod
    def validate_recommendations_tuple(cls, value: Any) -> Tuple[str, ...]:
        if not isinstance(value, (list, tuple)):
            logger.error("RECOMMENDATIONS_MUST_BE_LIST_OR_TUPLE: %r", value)
            raise TypeError("VALUE_MUST_BE_A_LIST_OR_TUPLE")
        clean_recs: List[str] = []
        for idx, item in enumerate(value):
            if not isinstance(item, str):
                logger.error("RECOMMENDATION_%d_NOT_STRING: %r", idx, item)
                raise TypeError("RECOMMENDATIONS_MUST_BE_PURE_STRINGS")
            stripped = item.strip()
            if not stripped:
                logger.error("RECOMMENDATION_%d_EMPTY: %r", idx, item)
                raise ValueError("STRING_VALUE_CANNOT_BE_EMPTY_OR_WHITESPACE")
            clean_recs.append(stripped)
        return tuple(clean_recs)

    def input_hash(self) -> str:
        return canonical_hash([str(p.type).strip() for p in self.predictions])

    def output_hash(self) -> str:
        return canonical_hash([p.model_dump() for p in self.predictions])