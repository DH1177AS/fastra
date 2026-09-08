# fastra_core\ai\verification.py

from __future__ import annotations

import logging
import math
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, ConfigDict, Field, field_validator

from fastra_core.ai.enums import HumanReviewAction, VerificationStatus
from fastra_core.ai.models import DrawingResult, LLMResult, PredictionResult, VisionResult

logger = logging.getLogger("fastra_core.ai.verification")


class VerificationResult(BaseModel):
    """
    Model Value Object laporan kelayakan hasil gerbang otomasi verifikasi kognitif AI.
    Menjamin kedaulatan data orkestrasi lewat imutabilitas murni (frozen=True).
    """
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        strict=True,
        frozen=True,
        allow_inf_nan=False,
    )

    passed: bool = Field(..., description="Flag kelayakan peluncuran data kognitif AI")
    status: VerificationStatus = Field(..., description="Status formal tata kelola kepatuhan")
    flags: Tuple[str, ...] = Field(default_factory=tuple, description="Koleksi token indikator kegagalan")
    confidence_check: bool = Field(default=True)
    completeness_check: bool = Field(default=True)
    consistency_check: bool = Field(default=True)
    needs_human_review: bool = Field(default=True)
    human_review_action: Optional[HumanReviewAction] = Field(default=None)

    @field_validator("passed", "confidence_check", "completeness_check", "consistency_check", "needs_human_review", mode="before")
    @classmethod
    def validate_strict_bool_fields(cls, value: Any) -> bool:
        if not isinstance(value, bool):
            logger.error("BOOLEAN_FIELD_MUST_BE_STRICT_BOOL: %r", value)
            raise TypeError("DATA_TYPE_COERCION_FORBIDDEN_BOOLEAN_NOT_ALLOWED")
        return value

    @field_validator("flags", mode="before")
    @classmethod
    def validate_flags_collection(cls, value: Any) -> Tuple[str, ...]:
        if isinstance(value, bool):
            logger.error("FLAGS_BOOLEAN_REJECTED: %r", value)
            raise TypeError("DATA_TYPE_COERCION_FORBIDDEN_BOOLEAN_NOT_ALLOWED")
        if not isinstance(value, (list, tuple)):
            logger.error("FLAGS_MUST_BE_LIST_OR_TUPLE: %r", value)
            raise TypeError("FLAGS_MUST_BE_A_VALID_COLLECTION_CONTAINER")
        clean_flags: List[str] = []
        for idx, item in enumerate(value):
            if not isinstance(item, str):
                logger.error("FLAG_ITEM_%d_NOT_STRING: %r", idx, item)
                raise TypeError("FLAG_ITEMS_MUST_BE_PURE_STRINGS")
            stripped = item.strip()
            if not stripped:
                logger.error("FLAG_ITEM_%d_EMPTY: %r", idx, item)
                raise ValueError("FLAG_STRING_CANNOT_BE_EMPTY_OR_WHITESPACE")
            clean_flags.append(stripped)
        return tuple(clean_flags)

    def to_dict(self) -> Dict[str, Any]:
        """
        Mengekspor struktur internal data log ke dalam bentuk primitif terikat JSON.
        """
        return {
            "passed": self.passed,
            "status": self.status.value if hasattr(self.status, "value") else str(self.status),
            "flags": list(self.flags),
            "confidence_check": self.confidence_check,
            "completeness_check": self.completeness_check,
            "consistency_check": self.consistency_check,
            "needs_human_review": self.needs_human_review,
            "human_review_action": self.human_review_action.value if self.human_review_action else None,
        }


class VerificationGate(BaseModel):
    """
    Gerbang Penyaring Otorisasi Otomatis Hasil Inferensi Model AI (Verification Gate Engine).
    Mengevaluasi batas ambang kepastian kuantitatif secara fail-fast dan strict.
    """
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        strict=True,
        frozen=True,
        allow_inf_nan=False,
    )

    thresholds: Dict[str, float] = Field(
        default_factory=lambda: {
            "building_type": 0.80,
            "area_estimation": 0.60,
            "wall_detection": 0.85,
            "dimension_reading": 0.90,
            "price_forecast": 0.70,
        },
        description="Matriks ambang batas konfidensi untuk berbagai tipe estimasi",
    )

    @field_validator("thresholds", mode="before")
    @classmethod
    def validate_thresholds_matrix(cls, value: Any) -> Dict[str, float]:
        if not isinstance(value, dict):
            logger.error("THRESHOLDS_MUST_BE_DICT: %r", value)
            raise TypeError("THRESHOLDS_MUST_BE_A_VALID_DICTIONARY")

        clean_matrix: Dict[str, float] = {}
        for k, v in value.items():
            if not isinstance(k, str) or not k.strip():
                logger.error("THRESHOLD_KEY_INVALID: %r", k)
                raise ValueError("THRESHOLD_KEYS_MUST_BE_NON_EMPTY_STRINGS")
            if isinstance(v, bool):
                logger.error("THRESHOLD_VALUE_BOOLEAN at key %s: %r", k, v)
                raise TypeError(f"DATA_TYPE_COERCION_FORBIDDEN_BOOLEAN_NOT_ALLOWED_AT_KEY_{k}")
            if not isinstance(v, (int, float)):
                logger.error("THRESHOLD_VALUE_NON_NUMERIC at key %s: %r", k, v)
                raise TypeError(f"Threshold value for '{k}' must be a pure numeric type")
            float_val = float(v)
            if math.isnan(float_val) or math.isinf(float_val) or not (0.0 <= float_val <= 1.0):
                logger.error("THRESHOLD_BOUND_VIOLATION at key %s: %s", k, float_val)
                raise ValueError(f"NUMERIC_ANOMALY_DETECTED_IN_THRESHOLD_BOUND_FOR_KEY_{k}")
            clean_matrix[k.strip()] = float_val
        return clean_matrix

    def verify_vision(self, result: VisionResult) -> VerificationResult:
        """
        Memverifikasi hasil inferensi model Vision AI terhadap batas ambang konfidensi.
        """
        if not isinstance(result, VisionResult):
            logger.error("VERIFY_VISION_INVALID_TYPE: %r", result)
            raise TypeError("INPUT_MUST_BE_AN_INSTANCE_OF_VISION_RESULT")

        flags_list: List[str] = []
        confidence_ok = True

        for key, estimation in result.estimations.items():
            if not isinstance(estimation, dict):
                logger.warning("VISION_ESTIMATION_ITEM_NOT_DICT at key %s: %r", key, estimation)
                continue
            try:
                confidence = float(estimation.get("confidence", 0.0))
            except (TypeError, ValueError) as exc:
                logger.error("VISION_CONFIDENCE_CONVERSION_FAILED at key %s: %s", key, exc)
                raise ValueError(f"INVALID_CONFIDENCE_VALUE_AT_KEY_{key}") from exc

            if math.isnan(confidence) or math.isinf(confidence):
                logger.error("VISION_CONFIDENCE_NAN_OR_INF at key %s: %s", key, confidence)
                raise ValueError(f"NUMERIC_ANOMALY_DETECTED_IN_VISION_CONFIDENCE_FOR_KEY_{key}")

            threshold = self._threshold_for_vision(key)
            if confidence < threshold:
                flags_list.append(f"HIGH_UNCERTAINTY: {key} confidence {confidence:.2f} < threshold {threshold:.2f}")
                confidence_ok = False

        completeness_ok = bool(result.estimations)
        consistency_ok = True
        passed = confidence_ok and completeness_ok and consistency_ok
        status = VerificationStatus.NEEDS_HUMAN_REVIEW

        if not confidence_ok:
            status = VerificationStatus.FLAGGED_HIGH_UNCERTAINTY
            passed = False
        elif not completeness_ok:
            status = VerificationStatus.FLAGGED_INCOMPLETE
            passed = False

        logger.debug("Vision verification: passed=%s status=%s flags=%d", passed, status.value, len(flags_list))
        return VerificationResult(
            passed=passed,
            status=status,
            flags=tuple(flags_list),
            confidence_check=confidence_ok,
            completeness_check=completeness_ok,
            consistency_check=consistency_ok,
        )

    def verify_drawing(self, result: DrawingResult) -> VerificationResult:
        """
        Memverifikasi hasil Drawing Reader AI berdasarkan kepatuhan struktural ACES-200.
        """
        if not isinstance(result, DrawingResult):
            logger.error("VERIFY_DRAWING_INVALID_TYPE: %r", result)
            raise TypeError("INPUT_MUST_BE_AN_INSTANCE_OF_DRAWING_RESULT")

        flags_list: List[str] = []
        confidence_ok = True

        for element_type, elements in result.detected_elements.items():
            if not isinstance(elements, (list, tuple)):
                logger.warning("DRAWING_ELEMENTS_NOT_LIST_OR_TUPLE at key %s: %r", element_type, elements)
                continue
            for elem in elements:
                threshold = self.thresholds.get("wall_detection", 0.85)
                if math.isnan(elem.confidence) or math.isinf(elem.confidence):
                    logger.error("DRAWING_ELEMENT_CONFIDENCE_NAN_OR_INF: %s", elem.proposed_uuid)
                    raise ValueError(f"NUMERIC_ANOMALY_DETECTED_IN_DRAWING_CONFIDENCE_FOR_{elem.proposed_uuid}")
                if elem.confidence < threshold:
                    flags_list.append(f"HIGH_UNCERTAINTY: {elem.proposed_uuid} ({elem.type}) confidence {elem.confidence:.2f}")
                    confidence_ok = False

        ccm_valid = False
        generated_ccm = getattr(result, "generated_ccm", None)
        if isinstance(generated_ccm, dict):
            has_entities = "entities" in generated_ccm and isinstance(generated_ccm["entities"], dict) and bool(generated_ccm["entities"])
            has_relationships = "relationships" in generated_ccm and isinstance(generated_ccm["relationships"], (list, tuple, dict))
            if has_entities or has_relationships:
                ccm_valid = True

        completeness_ok = ccm_valid
        consistency_ok = True
        passed = confidence_ok and completeness_ok and consistency_ok
        status = VerificationStatus.NEEDS_HUMAN_REVIEW

        if not confidence_ok:
            status = VerificationStatus.FLAGGED_HIGH_UNCERTAINTY
            passed = False
        elif not completeness_ok:
            status = VerificationStatus.FLAGGED_INCOMPLETE
            flags_list.append("INVALID_CCM_STRUCTURE: generated_ccm must possess non-empty relational 'entities' or 'relationships' fields compliant with ACES-200.")
            passed = False

        logger.debug("Drawing verification: passed=%s status=%s flags=%d", passed, status.value, len(flags_list))
        return VerificationResult(
            passed=passed,
            status=status,
            flags=tuple(flags_list),
            confidence_check=confidence_ok,
            completeness_check=completeness_ok,
            consistency_check=consistency_ok,
        )

    def verify_llm(self, result: LLMResult) -> VerificationResult:
        if not isinstance(result, LLMResult):
            logger.error("VERIFY_LLM_INVALID_TYPE: %r", result)
            raise TypeError("INPUT_MUST_BE_AN_INSTANCE_OF_LLM_RESULT")

        flags_list: List[str] = []
        completeness_ok = bool(result.output_dsl and str(result.output_dsl).strip())
        consistency_ok = bool(result.references)
        passed = completeness_ok and consistency_ok and result.content_safe
        status = VerificationStatus.NEEDS_HUMAN_REVIEW

        if not result.content_safe:
            status = VerificationStatus.REJECTED
            flags_list.append("UNSAFE_CONTENT_VIOLATION_DETECTED")
            passed = False
        elif not completeness_ok:
            status = VerificationStatus.FLAGGED_INCOMPLETE
            passed = False
        elif not consistency_ok:
            status = VerificationStatus.FLAGGED_INCONSISTENT
            passed = False

        logger.debug("LLM verification: passed=%s status=%s flags=%d", passed, status.value, len(flags_list))
        return VerificationResult(
            passed=passed,
            status=status,
            flags=tuple(flags_list),
            confidence_check=True,
            completeness_check=completeness_ok,
            consistency_check=consistency_ok,
        )

    def verify_prediction(self, result: PredictionResult) -> VerificationResult:
        if not isinstance(result, PredictionResult):
            logger.error("VERIFY_PREDICTION_INVALID_TYPE: %r", result)
            raise TypeError("INPUT_MUST_BE_AN_INSTANCE_OF_PREDICTION_RESULT")

        flags_list: List[str] = []
        confidence_ok = True

        for pred in result.predictions:
            threshold = self.thresholds.get("price_forecast", 0.70)
            if pred.confidence_level is not None:
                if math.isnan(pred.confidence_level) or math.isinf(pred.confidence_level):
                    logger.error("PREDICTION_CONFIDENCE_NAN_OR_INF: %s", pred.type)
                    raise ValueError(f"NUMERIC_ANOMALY_DETECTED_IN_PREDICTION_CONFIDENCE_FOR_{pred.type}")
                if pred.confidence_level < threshold:
                    flags_list.append(f"HIGH_UNCERTAINTY: {pred.type} confidence_level {pred.confidence_level:.2f}")
                    confidence_ok = False
            if pred.confidence_interval is None and pred.confidence_level is None:
                flags_list.append(f"INCOMPLETE: {pred.type} requires a structured confidence interval or level metrics")
                confidence_ok = False

        completeness_ok = bool(result.predictions)
        consistency_ok = True
        passed = confidence_ok and completeness_ok and consistency_ok
        status = VerificationStatus.NEEDS_HUMAN_REVIEW

        if not confidence_ok:
            status = VerificationStatus.FLAGGED_HIGH_UNCERTAINTY
            passed = False
        elif not completeness_ok:
            status = VerificationStatus.FLAGGED_INCOMPLETE
            passed = False

        logger.debug("Prediction verification: passed=%s status=%s flags=%d", passed, status.value, len(flags_list))
        return VerificationResult(
            passed=passed,
            status=status,
            flags=tuple(flags_list),
            confidence_check=confidence_ok,
            completeness_check=completeness_ok,
            consistency_check=consistency_ok,
        )

    def _threshold_for_vision(self, key: str) -> float:
        """
        Menentukan ambang batas konfidensi yang sesuai untuk tipe estimasi vision.
        """
        if not isinstance(key, str):
            logger.warning("THRESHOLD_KEY_NOT_STRING: %r", key)
            return 0.70
        lowered_key = key.lower()
        if "building_type" in lowered_key:
            return self.thresholds.get("building_type", 0.80)
        if "area" in lowered_key or "luas" in lowered_key:
            return self.thresholds.get("area_estimation", 0.60)
        return 0.70