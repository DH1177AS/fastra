import json
import uuid
from datetime import datetime
from typing import Any, Dict

def to_json(obj: Any) -> str:
    return json.dumps(obj, default=_serializer, sort_keys=True, separators=(",",":"))

def from_json(s: str) -> Any:
    return json.loads(s)

def _serializer(o):
    if isinstance(o, uuid.UUID):
        return str(o)
    if isinstance(o, datetime):
        return o.isoformat()
    if hasattr(o, "__dict__"):
        return o.__dict__
    raise TypeError(f"Object of type {type(o).__name__} is not JSON serializable")
