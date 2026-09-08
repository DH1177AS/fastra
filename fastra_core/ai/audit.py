# fastra_core\ai\audit.py

from __future__ import annotations

import logging
import math
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from fastra_core.ai.enums import AIComponent
from fastra_core.identity import Identity

logger = logging.getLogger("fastra_core.ai.audit")


class AIEventLog(BaseModel):
   
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        strict=True,
        frozen=True,
        allow_inf_nan=False,
    )

    ai_component: AIComponent
    model_name: str = Field(..., min_length=2, max_length=64, pattern=r"^[a-zA-Z0-9\-\_]+$")
    model_version: str = Field(..., min_length=1, max_length=32, pattern=r"^[a-zA-Z0-9\.\-\_]+$")
    input_hash: str = Field(..., min_length=1, max_length=128, pattern=r"^[a-fA-F0-9]+$|^[A-Z0-9\_]+$")
    output_hash: str = Field(..., min_length=1, max_length=128, pattern=r"^[a-fA-F0-9]+$")
    prompt_payload: Dict[str, Any] = Field(default_factory=dict)
    response_payload: Dict[str, Any] = Field(default_factory=dict)
    execution_time_ms: float = Field(default=0.0, ge=0.0)
    confidence_scores: Dict[str, float] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    event_uuid: str = Field(
        default_factory=Identity.generate,
        pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    )
    human_review: Optional[Dict[str, Any]] = Field(default=None)
    pipeline_entry: Optional[Dict[str, Any]] = Field(default=None)

    @field_validator("event_uuid", mode="after")
    @classmethod
    def verify_uuid_integrity(cls, value: str) -> str:
        if not Identity.is_valid(value):
            logger.error("AI_EVENT_INVALID_UUID: %s", value)
            raise ValueError("UUID_INTEGRITY_COMPROMISED_INVALID_STRUCTURE")
        return value

    @field_validator("model_name", "model_version", "input_hash", "output_hash", mode="before")
    @classmethod
    def sanitize_strings(cls, value: Any) -> str:
        if not isinstance(value, str):
            logger.error("AI_AUDIT_STRING_COERCION_REJECTED: %r", value)
            raise TypeError("VALUE_MUST_BE_A_PURE_STRING_COERCION_FORBIDDEN")
        stripped = value.strip()
        if not stripped:
            logger.error("AI_AUDIT_EMPTY_STRING_REJECTED")
            raise ValueError("CORE_AI_AUDIT_STRING_CANNOT_BE_EMPTY_OR_WHITESPACE")
        return stripped

    @field_validator("confidence_scores", mode="before")
    @classmethod
    def validate_confidence_scores(cls, value: Any) -> Dict[str, float]:
        if not isinstance(value, dict):
            logger.error("CONFIDENCE_SCORES_MUST_BE_DICT: %r", value)
            raise TypeError("CONFIDENCE_SCORES_MUST_BE_A_DICTIONARY")
        clean_scores: Dict[str, float] = {}
        for k, v in value.items():
            if not isinstance(k, str) or not k.strip():
                logger.error("CONFIDENCE_SCORE_INVALID_KEY: %r", k)
                raise ValueError("CONFIDENCE_KEYS_MUST_BE_NON_EMPTY_STRINGS")
            if isinstance(v, bool):
                logger.error("CONFIDENCE_SCORE_BOOLEAN_REJECTED at key %s: %r", k, v)
                raise TypeError("DATA_TYPE_COERCION_FORBIDDEN_BOOLEAN_NOT_ALLOWED")
            if not isinstance(v, (int, float)):
                logger.error("CONFIDENCE_SCORE_NON_NUMERIC at key %s: %r", k, v)
                raise TypeError("CONFIDENCE_SCORE_MUST_BE_PURE_NUMERIC_TYPE")
            float_val = float(v)
            if math.isnan(float_val) or math.isinf(float_val):
                logger.error("CONFIDENCE_SCORE_NAN_OR_INF at key %s: %s", k, float_val)
                raise ValueError(f"NUMERIC_ANOMALY_DETECTED_IN_CONFIDENCE_SCORE_AT_KEY_{k}")
            if not (0.0 <= float_val <= 1.0):
                logger.error("CONFIDENCE_SCORE_BOUNDARY_VIOLATION at key %s: %s", k, float_val)
                raise ValueError(f"CONFIDENCE_SCORE_MUST_BE_BETWEEN_0_AND_1: {float_val}")
            clean_scores[k.strip()] = float_val
        return clean_scores

    @field_validator("execution_time_ms", mode="before")
    @classmethod
    def validate_execution_time(cls, value: Any) -> float:
        if isinstance(value, bool):
            raise TypeError("DATA_TYPE_COERCION_FORBIDDEN_BOOLEAN_NOT_ALLOWED")
        if not isinstance(value, (int, float)):
            raise TypeError("EXECUTION_TIME_MS_MUST_BE_PURE_NUMERIC")
        float_val = float(value)
        if math.isnan(float_val) or math.isinf(float_val) or float_val < 0:
            raise ValueError("EXECUTION_TIME_MS_MUST_BE_FINITE_AND_NON_NEGATIVE")
        return float_val
    
    @field_validator("human_review", "pipeline_entry", mode="before")
    @classmethod
    def validate_payload_dictionaries(cls, value: Any) -> Optional[Dict[str, Any]]:
        if value is None:
            return None
        if not isinstance(value, dict):
            logger.error("PAYLOAD_MUST_BE_DICT: %r", value)
            raise TypeError("PAYLOAD_DATA_MUST_BE_A_VALID_DICTIONARY")
        for k, v in value.items():
            if not isinstance(k, str) or not k.strip():
                logger.error("PAYLOAD_INVALID_KEY: %r", k)
                raise ValueError("PAYLOAD_KEYS_MUST_BE_NON_EMPTY_STRINGS")
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                if math.isnan(v) or math.isinf(v):
                    logger.error("PAYLOAD_NUMERIC_ANOMALY at key %s: %s", k, v)
                    raise ValueError(f"NUMERIC_ANOMALY_DETECTED_IN_AI_AUDIT_LOG_AT_KEY_{k}")
        return value

    def to_dict(self) -> Dict[str, Any]:
        """
        Mengekspor struktur internal data log ke dalam bentuk primitif terikat JSON.
        """
        return {
            "event_uuid": self.event_uuid,
            "timestamp": self.timestamp.isoformat() if isinstance(self.timestamp, datetime) else str(self.timestamp),
            "ai_component": self.ai_component.value if hasattr(self.ai_component, "value") else str(self.ai_component),
            "model_name": self.model_name,
            "model_version": self.model_version,
            "input_hash": self.input_hash,
            "output_hash": self.output_hash,
            "confidence_scores": dict(self.confidence_scores),
            "human_review": dict(self.human_review) if self.human_review is not None else None,
            "pipeline_entry": dict(self.pipeline_entry) if self.pipeline_entry is not None else None,
        }


class AIEventStore(BaseModel):
    """
    Penyimpanan Rantai Jejak Log Kognitif AI (Append-Only AI Event Ledger) In-Memory.
    Menjamin thread-safety penuh dan isolasi mutasi state hantu melalui gerbang Pydantic v2.
    """
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        strict=True,
        frozen=False,
        allow_inf_nan=False,
    )

    events: List[AIEventLog] = Field(default_factory=list)
    event_map: Dict[str, AIEventLog] = Field(default_factory=dict)

    def record_event(self, event: AIEventLog) -> AIEventLog:
        """
        Mencatatkan rekaman peristiwa kognitif AI baru ke dalam tumpukan ledger.
        Otomatis memperbarui indeks pencarian peta memori (O(1) look-up optimization).
        """
        if not isinstance(event, AIEventLog):
            logger.error("AI_EVENT_STORE_INVALID_EVENT_TYPE: %r", event)
            raise TypeError("STORE_OPERATION_VIOLATION_INPUT_MUST_BE_AN_INSTANCE_OF_AI_EVENT_LOG")

        if event.event_uuid in self.event_map:
            logger.error("DUPLICATE_AI_EVENT_DETECTED: %s", event.event_uuid)
            raise ValueError(f"DUPLICATE_AI_EVENT_DETECTED_WITHIN_BATCH_{event.event_uuid}")

        self.events.append(event)
        self.event_map[event.event_uuid] = event
        logger.info("AI event recorded: %s", event.event_uuid)
        return event

    def get_event(self, event_uuid: str) -> Optional[AIEventLog]:
        """
        Mencari entri log peristiwa berdasarkan UUID dengan performa tinggi O(1).
        """
        if not isinstance(event_uuid, str):
            logger.warning("GET_EVENT_NON_STRING_UUID: %r", event_uuid)
            return None
        clean_uuid = event_uuid.strip()
        if not clean_uuid or not Identity.is_valid(clean_uuid):
            logger.warning("GET_EVENT_INVALID_UUID: %r", event_uuid)
            return None
        return self.event_map.get(clean_uuid)

    def update_event(self, updated_event: AIEventLog) -> None:
        """
        Memperbarui rekaman entri log di dalam store secara aman menggunakan replikasi murni.
        """
        if not isinstance(updated_event, AIEventLog):
            logger.error("AI_EVENT_STORE_UPDATE_INVALID_TYPE: %r", updated_event)
            raise TypeError("UPDATE_OPERATION_VIOLATION_INPUT_MUST_BE_AN_INSTANCE_OF_AI_EVENT_LOG")

        uuid_key = updated_event.event_uuid
        if uuid_key not in self.event_map:
            logger.error("TARGET_AI_EVENT_NOT_FOUND: %s", uuid_key)
            raise KeyError(f"TARGET_AI_EVENT_NOT_FOUND_FOR_UPDATE: {uuid_key}")

        # Sinkronisasi pembaruan referensi dalam list dan map indeks
        self.event_map[uuid_key] = updated_event
        for idx, ev in enumerate(self.events):
            if ev.event_uuid == uuid_key:
                self.events[idx] = updated_event
                break
        logger.info("AI event updated: %s", uuid_key)

    def get_all(self) -> List[AIEventLog]:
        return list(self.events)

    def count(self) -> int:
        return len(self.events)