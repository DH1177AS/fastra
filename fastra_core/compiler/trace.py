# fastra_core\compiler\trace.py

from __future__ import annotations

import enum
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class TraceStageType(str, enum.Enum):
   
    GEOMETRY_BUILDER = "GEOMETRY_BUILDER"
    QUANTITY_GENERATOR = "QUANTITY_GENERATOR"
    BOQ_GENERATOR = "BOQ_GENERATOR"
    SMKK_ENGINE = "SMKK_ENGINE"
    COST_ENGINE = "COST_ENGINE"

class TraceStepDTO(BaseModel):
   
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, strict=True)

    stage: TraceStageType = Field(...)
    operation: str = Field(..., min_length=2, max_length=128, pattern=r"^[A-Za-z0-9_\-\s\(\)\&\.\,]+$")
    output_value: str = Field(..., min_length=1, max_length=256)
    operation_detail: Optional[str] = Field(default=None, max_length=1024)
    mapped_to: Optional[str] = Field(default=None, max_length=64, pattern=r"^[A-Za-z0-9_\-\.]+$")
    input_entity: Optional[List[str]] = Field(default=None, max_length=500)


class TraceLog:
   
    def __init__(self, generated_at: Optional[str] = None) -> None:
        self._generated_at = generated_at or datetime.now(timezone.utc).isoformat()
        self._steps: List[Dict[str, Any]] = []

    def finalize(self) -> str:
        import hashlib
        import json

        payload = self.to_dict() if hasattr(self, "to_dict") else {
            "generated_at": getattr(self, "_generated_at", ""),
            "steps": getattr(self, "_steps", []),
        }
        serialized = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    @property
    def generated_at(self) -> str:
        return self._generated_at

    def add_step(
        self,
        stage: str,
        operation: str,
        output_value: str,
        operation_detail: Optional[str] = None,
        mapped_to: Optional[str] = None,
        input_entity: Optional[List[str]] = None
    ) -> None:
       
        sanitized_input: Optional[List[str]] = None
        if input_entity is not None:
            if isinstance(input_entity, list):
                sanitized_input = [str(e).strip() for e in input_entity if str(e).strip()]
            else:
                sanitized_input = [str(input_entity).strip()]

        step_payload = {
            "stage": TraceStageType(str(stage).strip().upper()),
            "operation": str(operation).strip(),
            "output_value": str(output_value).strip(),
            "operation_detail": str(operation_detail).strip() if operation_detail is not None else None,
            "mapped_to": str(mapped_to).strip() if mapped_to is not None else None,
            "input_entity": sanitized_input
        }
               
        validated_step = TraceStepDTO.model_validate(step_payload)
        
        self._steps.append(validated_step.model_dump(exclude_none=True))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "generated_at": self._generated_at,
            "computation_steps": list(self._steps),
        }
