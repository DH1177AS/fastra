"""
ACES-700 Human-in-the-Loop Verification Gate (hardened)
Menolak output dengan confidence di bawah threshold, validasi CCM ACES-200.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from fastra_core.ai.enums import ConfidenceFlag, HumanReviewAction, VerificationStatus
from fastra_core.ai.models import VisionResult, DrawingResult, LLMResult, PredictionResult


@dataclass
class VerificationResult:
    passed: bool
    status: VerificationStatus
    flags: List[str] = field(default_factory=list)
    confidence_check: bool = True
    completeness_check: bool = True
    consistency_check: bool = True
    needs_human_review: bool = True
    human_review_action: Optional[HumanReviewAction] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "status": self.status.value,
            "flags": self.flags,
            "confidence_check": self.confidence_check,
            "completeness_check": self.completeness_check,
            "consistency_check": self.consistency_check,
            "needs_human_review": self.needs_human_review,
            "human_review_action": self.human_review_action.value if self.human_review_action else None,
        }


class VerificationGate:
    """Gerbang verifikasi untuk output AI."""

    def __init__(self, thresholds: Optional[Dict[str, float]] = None) -> None:
        self.thresholds = thresholds or {
            "building_type": 0.80,
            "area_estimation": 0.60,
            "wall_detection": 0.85,
            "dimension_reading": 0.90,
            "price_forecast": 0.70,
        }

    def verify_vision(self, result: VisionResult) -> VerificationResult:
        flags = []
        confidence_ok = True
        for key, estimation in result.estimations.items():
            confidence = float(estimation.get("confidence", 0.0))
            threshold = self._threshold_for_vision(key)
            if confidence < threshold:
                flags.append(f"HIGH_UNCERTAINTY: {key} confidence {confidence:.2f} < threshold {threshold:.2f}")
                confidence_ok = False
        completeness_ok = bool(result.estimations)
        consistency_ok = True
        passed = confidence_ok and completeness_ok and consistency_ok
        status = VerificationStatus.NEEDS_HUMAN_REVIEW
        if not confidence_ok:
            status = VerificationStatus.FLAGGED_HIGH_UNCERTAINTY
            passed = False  # reject otomatis jika ada high uncertainty
        elif not completeness_ok:
            status = VerificationStatus.FLAGGED_INCOMPLETE
            passed = False
        return VerificationResult(
            passed=passed,
            status=status,
            flags=flags,
            confidence_check=confidence_ok,
            completeness_check=completeness_ok,
            consistency_check=consistency_ok,
        )

    def verify_drawing(self, result: DrawingResult) -> VerificationResult:
        flags = []
        confidence_ok = True
        for element_type, elements in result.detected_elements.items():
            for elem in elements:
                threshold = self.thresholds.get("wall_detection", 0.85)
                if elem.confidence < threshold:
                    flags.append(f"HIGH_UNCERTAINTY: {elem.proposed_uuid} ({elem.type}) confidence {elem.confidence:.2f}")
                    confidence_ok = False
        # Validasi CCM ACES-200: generated_ccm harus memiliki 'entities' atau 'relationships'
        ccm_valid = False
        if isinstance(result.generated_ccm, dict):
            if "entities" in result.generated_ccm or "relationships" in result.generated_ccm:
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
            flags.append("INVALID_CCM: generated_ccm harus memiliki 'entities' atau 'relationships'")
            passed = False
        return VerificationResult(
            passed=passed,
            status=status,
            flags=flags,
            confidence_check=confidence_ok,
            completeness_check=completeness_ok,
            consistency_check=consistency_ok,
        )

    def verify_llm(self, result: LLMResult) -> VerificationResult:
        flags = []
        completeness_ok = bool(result.output_dsl)
        consistency_ok = bool(result.references)
        passed = completeness_ok and consistency_ok and result.content_safe
        status = VerificationStatus.NEEDS_HUMAN_REVIEW
        if not result.content_safe:
            status = VerificationStatus.REJECTED
            flags.append("UNSAFE_CONTENT")
            passed = False
        elif not completeness_ok:
            status = VerificationStatus.FLAGGED_INCOMPLETE
            passed = False
        elif not consistency_ok:
            status = VerificationStatus.FLAGGED_INCONSISTENT
            passed = False
        return VerificationResult(
            passed=passed,
            status=status,
            flags=flags,
            confidence_check=True,
            completeness_check=completeness_ok,
            consistency_check=consistency_ok,
        )

    def verify_prediction(self, result: PredictionResult) -> VerificationResult:
        flags = []
        confidence_ok = True
        for pred in result.predictions:
            if pred.confidence_level is not None and pred.confidence_level < self.thresholds.get("price_forecast", 0.70):
                flags.append(f"HIGH_UNCERTAINTY: {pred.type} confidence_level {pred.confidence_level:.2f}")
                confidence_ok = False
            if pred.confidence_interval is None and pred.confidence_level is None:
                flags.append(f"INCOMPLETE: {pred.type} tidak memiliki confidence interval/level")
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
        return VerificationResult(
            passed=passed,
            status=status,
            flags=flags,
            confidence_check=confidence_ok,
            completeness_check=completeness_ok,
            consistency_check=consistency_ok,
        )

    def _threshold_for_vision(self, key: str) -> float:
        if "building_type" in key:
            return self.thresholds.get("building_type", 0.80)
        if "area" in key or "luas" in key:
            return self.thresholds.get("area_estimation", 0.60)
        return 0.70
