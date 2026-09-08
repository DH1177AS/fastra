# fastra_core\ai\ai_service.py

from __future__ import annotations

import logging
import math
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastra_core.ai.audit import AIEventLog, AIEventStore
from fastra_core.ai.enums import AIComponent
from fastra_core.ai.models import DrawingResult, LLMResult, PredictionResult, VisionResult
from fastra_core.ai.verification import VerificationGate, VerificationResult
from fastra_core.identity import Identity

logger = logging.getLogger("fastra_core.ai.ai_service")


class AIService:
    """
    Manajer Siklus Hidup Penilai Kognitif AI (AI Output Lifecycle Orchestrator).
    Mengeksekusi rangkaian verifikasi gerbang (Verification Gates) -> Audit Logging -> Database Layer.
    """

    def __init__(
        self,
        event_store: Optional[AIEventStore] = None,
        db: Optional[Any] = None,
    ) -> None:
        self.gate = VerificationGate()
        self.event_store = event_store if event_store is not None else AIEventStore()
        self.db = db

        if not isinstance(self.event_store, AIEventStore):
            logger.error("INVALID_EVENT_STORE_TYPE: %r", self.event_store)
            raise TypeError("EVENT_STORE_MUST_BE_AN_INSTANCE_OF_AI_EVENT_STORE")

        if self.db is not None and not hasattr(self.db, "save_ai_event"):
            logger.error("INVALID_DB_INSTANCE_MISSING_save_ai_event: %r", self.db)
            raise AttributeError("DATABASE_MUST_IMPLEMENT_save_ai_event_METHOD")

    @staticmethod
    def _sanitize_confidence_scores(confidences: Dict[str, float]) -> Dict[str, float]:
        """
        Menapis nilai skor probabilitas kognitif secara fail-fast dan strict.
        Melarang keras nilai anomali floating-point IEEE 754 (NaN/inf) atau nilai di luar rentang [0.0, 1.0].
        """
        if not isinstance(confidences, dict):
            logger.error("CONFIDENCE_SCORES_MUST_BE_DICT: %r", confidences)
            raise TypeError("CONFIDENCE_SCORES_MUST_BE_A_DICTIONARY")

        clean_scores: Dict[str, float] = {}
        for k, v in confidences.items():
            if not isinstance(k, str) or not k.strip():
                logger.error("CONFIDENCE_SCORE_INVALID_KEY: %r", k)
                raise ValueError("CONFIDENCE_SCORE_KEYS_MUST_BE_PURE_NON_EMPTY_STRINGS")

            if isinstance(v, bool):
                logger.error("CONFIDENCE_SCORE_BOOLEAN_REJECTED at key %s: %r", k, v)
                raise TypeError("DATA_TYPE_COERCION_FORBIDDEN_BOOLEAN_NOT_ALLOWED_IN_CONFIDENCE")

            if not isinstance(v, (int, float)):
                logger.error("CONFIDENCE_SCORE_NON_NUMERIC at key %s: %r", k, v)
                raise TypeError("CONFIDENCE_SCORE_MUST_BE_PURE_NUMERIC_TYPE")

            float_val = float(v)
            if math.isnan(float_val) or math.isinf(float_val):
                logger.error("CONFIDENCE_SCORE_NAN_OR_INF at key %s: %s", k, float_val)
                raise ValueError(f"NUMERIC_ANOMALY_DETECTED_IN_AI_CONFIDENCE_SCORE_AT_KEY_{k}")

            if not (0.0 <= float_val <= 1.0):
                logger.error("CONFIDENCE_SCORE_BOUNDARY_VIOLATION at key %s: %s", k, float_val)
                raise ValueError(f"BOUNDARY_VIOLATION_CONFIDENCE_SCORE_MUST_BE_BETWEEN_0_AND_1: {float_val}")

            clean_scores[k.strip()] = float_val
        return clean_scores

    @staticmethod
    def _extract_confidence_scores_for_event(
        result: VisionResult | DrawingResult | PredictionResult | LLMResult,
    ) -> Dict[str, float]:
        """
        Ekstraksi skor keyakinan dari berbagai model hasil AI.
        Selalu mengembalikan dict string->float; bila tidak ada skor, dict kosong.
        """
        raw: Dict[str, float] = {}

        if isinstance(result, VisionResult):
            estimations = getattr(result, "estimations", None)
            if isinstance(estimations, dict):
                for key, est in estimations.items():
                    if isinstance(est, dict) and "confidence" in est:
                        raw[str(key)] = float(est["confidence"])

        elif isinstance(result, DrawingResult):
            detected_elements = getattr(result, "detected_elements", None)
            if isinstance(detected_elements, dict):
                for elements in detected_elements.values():
                    if isinstance(elements, (list, tuple)):
                        for elem in elements:
                            if hasattr(elem, "proposed_uuid") and hasattr(elem, "confidence"):
                                raw[str(elem.proposed_uuid)] = float(elem.confidence)

        elif isinstance(result, PredictionResult):
            predictions = getattr(result, "predictions", None)
            if isinstance(predictions, (list, tuple)):
                for pred in predictions:
                    if hasattr(pred, "type") and hasattr(pred, "confidence_level"):
                        if pred.confidence_level is not None:
                            raw[str(pred.type)] = float(pred.confidence_level)

        # LLMResult sengaja mengembalikan dict kosong karena tidak memiliki confidence scores
        return raw

    def _record_event_atomic(self, event: AIEventLog) -> str:
        """
        Pencatatan transaksional atomik log aktivitas kecerdasan buatan.
        Mencegah pemrosesan parsial terpolusi jika media basis data hulu runtuh.
        """
        if not isinstance(event, AIEventLog):
            logger.error("RECORD_EVENT_INVALID_TYPE: %r", event)
            raise TypeError("RECORD_OPERATION_VIOLATION_INPUT_MUST_BE_AN_INSTANCE_OF_AI_EVENT_LOG")

        # 1. Komit menuju in-memory store append-only
        self.event_store.record_event(event)

        # 2. Sinkronisasi persisten menuju physical database layer
        if self.db is not None:
            try:
                self.db.save_ai_event(event)
            except Exception as db_exception:
                logger.error("AI_DATABASE_TRANSACTION_FAILED: %s", db_exception)
                raise RuntimeError(
                    f"CRITICAL_AI_DATABASE_TRANSACTION_FAILED_EVENT_LOG_ABORTED: {db_exception}"
                ) from db_exception

        logger.info("AI event recorded: %s", event.event_uuid)
        return event.event_uuid

    def _build_event_payload(
        self,
        component: AIComponent,
        model_name: str,
        model_version: str,
        input_hash: str,
        output_hash: str,
        confidence_scores: Dict[str, float],
    ) -> Dict[str, Any]:
        """Membangun payload event yang konsisten dengan validasi ketat."""
        if not isinstance(component, AIComponent):
            raise TypeError("COMPONENT_MUST_BE_AN_INSTANCE_OF_AI_COMPONENT_ENUM")
        if not all(isinstance(x, str) and x.strip() for x in [model_name, model_version, input_hash, output_hash]):
            raise ValueError("MODEL_NAME, MODEL_VERSION, INPUT_HASH, AND OUTPUT_HASH MUST BE NON-EMPTY STRINGS")

        return {
            "ai_component": component,
            "model_name": model_name.strip(),
            "model_version": model_version.strip(),
            "input_hash": input_hash.strip(),
            "output_hash": output_hash.strip(),
            "confidence_scores": self._sanitize_confidence_scores(confidence_scores),
        }

    def process_vision(self, result: VisionResult) -> Dict[str, Any]:
        if not isinstance(result, VisionResult):
            logger.error("PROCESS_VISION_INVALID_RESULT: %r", result)
            raise TypeError("AI_SERVICE_VIOLATION_INPUT_MUST_BE_AN_INSTANCE_OF_VISION_RESULT")

        verification: VerificationResult = self.gate.verify_vision(result)
        raw_confidences = self._extract_confidence_scores_for_event(result)
        sanitized_confidences = self._sanitize_confidence_scores(raw_confidences)

        event_payload = self._build_event_payload(
            component=AIComponent.VISION_AI,
            model_name="fastra-vision",
            model_version=str(result.model_version).strip(),
            input_hash=result.input_hash(),
            output_hash=result.output_hash(),
            confidence_scores=sanitized_confidences,
        )

        event = AIEventLog(**event_payload)
        event_uuid = self._record_event_atomic(event)

        return {
            "result_uuid": result.result_uuid,
            "verification": verification.to_dict(),
            "event_uuid": event_uuid,
        }

    def process_drawing(self, result: DrawingResult) -> Dict[str, Any]:
        if not isinstance(result, DrawingResult):
            logger.error("PROCESS_DRAWING_INVALID_RESULT: %r", result)
            raise TypeError("AI_SERVICE_VIOLATION_INPUT_MUST_BE_AN_INSTANCE_OF_DRAWING_RESULT")

        verification: VerificationResult = self.gate.verify_drawing(result)
        raw_confidences = self._extract_confidence_scores_for_event(result)
        sanitized_confidences = self._sanitize_confidence_scores(raw_confidences)

        input_hash = result.input_hash()
        if not input_hash or not input_hash.strip():
            input_hash = "EMPTY_HASH"

        event_payload = self._build_event_payload(
            component=AIComponent.DRAWING_AI,
            model_name="fastra-drawing",
            model_version=str(result.model_version).strip(),
            input_hash=input_hash,
            output_hash=result.output_hash(),
            confidence_scores=sanitized_confidences,
        )

        event = AIEventLog(**event_payload)
        event_uuid = self._record_event_atomic(event)

        return {
            "result_uuid": result.result_uuid,
            "verification": verification.to_dict(),
            "event_uuid": event_uuid,
        }

    def process_llm(self, result: LLMResult) -> Dict[str, Any]:
        if not isinstance(result, LLMResult):
            logger.error("PROCESS_LLM_INVALID_RESULT: %r", result)
            raise TypeError("AI_SERVICE_VIOLATION_INPUT_MUST_BE_AN_INSTANCE_OF_LLM_RESULT")

        verification: VerificationResult = self.gate.verify_llm(result)

        event_payload = self._build_event_payload(
            component=AIComponent.LLM_ASSISTANT,
            model_name="fastra-llm",
            model_version=str(result.model_version).strip(),
            input_hash=result.input_hash(),
            output_hash=result.output_hash(),
            confidence_scores={},
        )

        event = AIEventLog(**event_payload)
        event_uuid = self._record_event_atomic(event)

        return {
            "result_uuid": result.result_uuid,
            "verification": verification.to_dict(),
            "event_uuid": event_uuid,
        }

    def process_prediction(self, result: PredictionResult) -> Dict[str, Any]:
        if not isinstance(result, PredictionResult):
            logger.error("PROCESS_PREDICTION_INVALID_RESULT: %r", result)
            raise TypeError("AI_SERVICE_VIOLATION_INPUT_MUST_BE_AN_INSTANCE_OF_PREDICTION_RESULT")

        verification: VerificationResult = self.gate.verify_prediction(result)
        raw_confidences = self._extract_confidence_scores_for_event(result)
        sanitized_confidences = self._sanitize_confidence_scores(raw_confidences)

        event_payload = self._build_event_payload(
            component=AIComponent.PREDICTION_AI,
            model_name="fastra-predict",
            model_version=str(result.model_version).strip(),
            input_hash=result.input_hash(),
            output_hash=result.output_hash(),
            confidence_scores=sanitized_confidences,
        )

        event = AIEventLog(**event_payload)
        event_uuid = self._record_event_atomic(event)

        return {
            "result_uuid": result.result_uuid,
            "verification": verification.to_dict(),
            "event_uuid": event_uuid,
        }

    def record_human_review(
        self,
        event_uuid: str,
        approved: bool,
        modifications: List[str],
    ) -> bool:
        """
        Mencatatkan hasil evaluasi verifikasi manual manusia (Human-In-The-Loop Validation).
        Menolak mutasi memori langsung, wajib melintasi gerbang replikasi klon Pydantic murni.
        """
        if not isinstance(event_uuid, str) or not Identity.is_valid(event_uuid):
            logger.error("HUMAN_REVIEW_INVALID_EVENT_UUID: %r", event_uuid)
            raise ValueError(f"SECURITY_INTEGRITY_VIOLATION_INVALID_EVENT_UUID_STRUCTURE: {event_uuid}")

        if not isinstance(approved, bool):
            logger.error("HUMAN_REVIEW_APPROVED_MUST_BE_BOOL: %r", approved)
            raise TypeError("APPROVED_PARAMETER_MUST_BE_A_PURE_BOOLEAN")

        if not isinstance(modifications, list):
            logger.error("HUMAN_REVIEW_MODIFICATIONS_MUST_BE_LIST: %r", modifications)
            raise TypeError("MODIFICATIONS_MUST_BE_PROVIDED_IN_A_VALID_LIST")

        # Cari event target
        events_pool: List[AIEventLog] = []
        if hasattr(self.event_store, "get_event"):
            event = self.event_store.get_event(event_uuid)
            if event is not None:
                events_pool.append(event)
        else:
            events_pool = self.event_store.get_all()

        for current_event in events_pool:
            if current_event.event_uuid == event_uuid:
                # Sanitasi daftar modifikasi
                clean_modifications = [
                    str(m).strip() for m in modifications if m and str(m).strip()
                ]

                review_payload = {
                    "approved": bool(approved),
                    "modifications": clean_modifications,
                    "review_timestamp": datetime.now(timezone.utc).isoformat(),
                }

                # Replikasi klon Pydantic baru tanpa mutasi in-place
                event_dump = current_event.model_dump()
                event_dump["human_review"] = review_payload
                updated_event = AIEventLog(**event_dump)

                # Update store in-memory
                if hasattr(self.event_store, "update_event"):
                    self.event_store.update_event(updated_event)
                else:
                    # Jika store tidak mendukung update, gunakan record_event sebagai fallback
                    self.event_store.record_event(updated_event)

                # Sinkronisasi ke database
                if self.db is not None:
                    self.db.save_ai_event(updated_event)

                logger.info("Human review recorded for AI event %s", event_uuid)
                return True

        logger.warning("AI event not found for human review: %s", event_uuid)
        return False

    def get_audit_events(self) -> List[Dict[str, Any]]:
        """Mengembalikan seluruh log aktivitas AI yang tersimpan."""
        return [e.to_dict() for e in self.event_store.get_all()]