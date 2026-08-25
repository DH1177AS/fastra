"""
ACES-700 AI Audit & Logging
Menyimpan setiap output AI untuk keperluan audit dan monitoring.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastra_core.ai.enums import AIComponent


@dataclass
class AIEventLog:
    ai_component: AIComponent
    model_name: str
    model_version: str
    input_hash: str
    output_hash: str
    confidence_scores: Dict[str, float]
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    event_uuid: str = field(default_factory=lambda: str(uuid4()))
    human_review: Optional[Dict[str, Any]] = None
    pipeline_entry: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_uuid": self.event_uuid,
            "timestamp": self.timestamp,
            "ai_component": self.ai_component.value,
            "model_name": self.model_name,
            "model_version": self.model_version,
            "input_hash": self.input_hash,
            "output_hash": self.output_hash,
            "confidence_scores": self.confidence_scores,
            "human_review": self.human_review,
            "pipeline_entry": self.pipeline_entry,
        }


class AIEventStore:
    def __init__(self) -> None:
        self._events: List[AIEventLog] = []

    def record_event(self, event: AIEventLog) -> AIEventLog:
        self._events.append(event)
        return event

    def get_all(self) -> List[AIEventLog]:
        return list(self._events)

    def count(self) -> int:
        return len(self._events)
