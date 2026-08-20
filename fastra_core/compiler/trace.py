
"""
TraceLog deterministik untuk ACES-400, sesuai §13.4.
"""
import hashlib
import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

class TraceLog:
    def __init__(self, trace_uuid: Optional[str] = None, generated_at: Optional[str] = None):
        self.trace_uuid = trace_uuid
        self.generated_at = generated_at or datetime.now(timezone.utc).isoformat()
        self.steps: List[Dict[str, Any]] = []

    def add_step(self, stage: str, operation: str, input_entity: str = None,
                 input_value: Any = None, operation_detail: str = None,
                 output_value: Any = None, mapped_to: str = None):
        step = {
            "step": len(self.steps) + 1,
            "stage": stage,
            "operation": operation,
            "timestamp": self.generated_at,  # deterministik
        }
        if input_entity is not None:
            step["input_entity"] = input_entity
        if input_value is not None:
            step["input_value"] = input_value
        if operation_detail is not None:
            step["operation_detail"] = operation_detail
        if output_value is not None:
            step["output_value"] = output_value
        if mapped_to is not None:
            step["mapped_to"] = mapped_to
        self.steps.append(step)

    def finalize(self) -> str:
        if not self.trace_uuid:
            self.trace_uuid = hashlib.sha256(
                json.dumps(self.steps, sort_keys=True, default=str).encode()
            ).hexdigest()
        return hashlib.sha256(
            json.dumps(self.steps, sort_keys=True, default=str).encode()
        ).hexdigest()

    def to_dict(self) -> Dict:
        return {
            "trace_uuid": self.trace_uuid or self.finalize(),
            "computation_steps": self.steps,
            "audit_hash": self.finalize(),
            "generated_at": self.generated_at
        }
