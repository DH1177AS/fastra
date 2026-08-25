"""
ACES-700 AI Service (hardened)
Mengorkestrasi output AI, verifikasi, pencatatan audit, dan penyimpanan DB.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastra_core.ai.models import VisionResult, DrawingResult, LLMResult, PredictionResult
from fastra_core.ai.verification import VerificationGate, VerificationResult
from fastra_core.ai.audit import AIEventLog, AIEventStore
from fastra_core.ai.enums import AIComponent


class AIService:
    """Mengelola siklus output AI: verifikasi -> audit -> database."""

    def __init__(self, event_store: Optional[AIEventStore] = None, db: Optional[Any] = None) -> None:
        self.gate = VerificationGate()
        self.event_store = event_store or AIEventStore()
        self.db = db

    def _record_event(self, event: AIEventLog) -> str:
        self.event_store.record_event(event)
        if self.db is not None:
            self.db.save_ai_event(event)
        return event.event_uuid

    def process_vision(self, result: VisionResult) -> Dict[str, Any]:
        verification = self.gate.verify_vision(result)
        event = AIEventLog(
            ai_component=AIComponent.VISION_AI,
            model_name="fastra-vision",
            model_version=result.model_version,
            input_hash=result.input_hash(),
            output_hash=result.output_hash(),
            confidence_scores={
                key: float(est.get("confidence", 0.0))
                for key, est in result.estimations.items()
                if isinstance(est, dict)
            },
        )
        event_uuid = self._record_event(event)
        return {
            "result_uuid": result.result_uuid,
            "verification": verification.to_dict(),
            "event_uuid": event_uuid,
        }

    def process_drawing(self, result: DrawingResult) -> Dict[str, Any]:
        verification = self.gate.verify_drawing(result)
        confidences = {}
        for elements in result.detected_elements.values():
            for elem in elements:
                confidences[elem.proposed_uuid] = elem.confidence
        event = AIEventLog(
            ai_component=AIComponent.DRAWING_AI,
            model_name="fastra-drawing",
            model_version=result.model_version,
            input_hash=result.input_hash(),
            output_hash=result.output_hash(),
            confidence_scores=confidences,
        )
        event_uuid = self._record_event(event)
        return {
            "result_uuid": result.result_uuid,
            "verification": verification.to_dict(),
            "event_uuid": event_uuid,
        }

    def process_llm(self, result: LLMResult) -> Dict[str, Any]:
        verification = self.gate.verify_llm(result)
        event = AIEventLog(
            ai_component=AIComponent.LLM_ASSISTANT,
            model_name="fastra-llm",
            model_version=result.model_version,
            input_hash=result.input_hash(),
            output_hash=result.output_hash(),
            confidence_scores={},
        )
        event_uuid = self._record_event(event)
        return {
            "result_uuid": result.result_uuid,
            "verification": verification.to_dict(),
            "event_uuid": event_uuid,
        }

    def process_prediction(self, result: PredictionResult) -> Dict[str, Any]:
        verification = self.gate.verify_prediction(result)
        confidences = {}
        for pred in result.predictions:
            if pred.confidence_level is not None:
                confidences[pred.type] = pred.confidence_level
        event = AIEventLog(
            ai_component=AIComponent.PREDICTION_AI,
            model_name="fastra-predict",
            model_version=result.model_version,
            input_hash=result.input_hash(),
            output_hash=result.output_hash(),
            confidence_scores=confidences,
        )
        event_uuid = self._record_event(event)
        return {
            "result_uuid": result.result_uuid,
            "verification": verification.to_dict(),
            "event_uuid": event_uuid,
        }

    def record_human_review(self, event_uuid: str, approved: bool, modifications: List[str]) -> bool:
        """Catat human review ke event log dan database."""
        for event in self.event_store.get_all():
            if event.event_uuid == event_uuid:
                event.human_review = {
                    "approved": approved,
                    "modifications": modifications,
                    "review_timestamp": __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),
                }
                if self.db is not None:
                    self.db.save_ai_event(event)  # update
                return True
        return False

    def get_audit_events(self) -> List[Dict[str, Any]]:
        return [e.to_dict() for e in self.event_store.get_all()]
