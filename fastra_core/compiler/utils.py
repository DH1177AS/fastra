# fastra_core\compiler\utils.py

from __future__ import annotations

import copy
import dataclasses
import enum
from datetime import datetime, date, time
from decimal import Decimal
import logging
from typing import Any, Dict, List, Mapping

logger = logging.getLogger("fastra_core.compiler.utils")


def _normalize_value(value: Any) -> Any:
    
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    if isinstance(value, enum.Enum):
        return value.value
    if hasattr(value, "to_domain_state") or dataclasses.is_dataclass(value):
        return entity_to_dict(value)
    if isinstance(value, Mapping):
        return {str(k): _normalize_value(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [_normalize_value(item) for item in value]
    if hasattr(value, "__dict__") and not isinstance(value, type):
        return {str(k): _normalize_value(v) for k, v in vars(value).items()}
    return value


def entity_to_dict(entity: Any) -> Dict[str, Any]:
   
    if entity is None:
        return {}
    
    if hasattr(entity, "to_domain_state") and callable(getattr(entity, "to_domain_state", None)):
        try:
            state = entity.to_domain_state()
            if isinstance(state, dict):
                return {str(k): _normalize_value(v) for k, v in state.items()}
        except Exception as exc:
            logger.warning("entity_to_dict normalization failed: %s", exc)
            pass
    
    if dataclasses.is_dataclass(entity):
        try:
            return {str(k): _normalize_value(v) for k, v in dataclasses.asdict(entity).items()}
        except Exception as exc:
            logger.warning("entity_to_dict normalization failed: %s", exc)
            pass
    
    if isinstance(entity, dict):
        return {str(k): _normalize_value(v) for k, v in entity.items()}
    
    if hasattr(entity, "__dict__") and not isinstance(entity, type):
        try:
            return {str(k): _normalize_value(v) for k, v in vars(entity).items()}
        except Exception as exc:
            logger.warning("entity_to_dict normalization failed: %s", exc)
            pass
    
    return {"value": str(entity)}


def to_serializable(data: Any) -> Any:
    
    if data is None:
        return None
   
    return _normalize_value(copy.deepcopy(data))
