"""
Helper serialisasi untuk entitas CCM dan struktur data Digital Twin.
"""
from __future__ import annotations

import dataclasses
import json
from enum import Enum
from typing import Any, Dict, List, Union


def _convert(obj: Any) -> Any:
    """Mengonversi objek menjadi tipe yang JSON-serializable."""
    if isinstance(obj, Enum):
        return obj.value
    if dataclasses.is_dataclass(obj):
        return {
            field.name: _convert(getattr(obj, field.name))
            for field in dataclasses.fields(obj)
            if field.repr
        }
    if isinstance(obj, dict):
        return {str(k): _convert(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [_convert(item) for item in obj]
    if isinstance(obj, (str, int, float, bool)) or obj is None:
        return obj
    # Fallback
    if hasattr(obj, "__dict__"):
        return _convert(obj.__dict__)
    return str(obj)


def to_serializable(obj: Any) -> Any:
    """Mengonversi objek apapun menjadi bentuk serializable."""
    return _convert(obj)


def entity_to_dict(entity: Any) -> Dict[str, Any]:
    """
    Mengonversi entitas CCM (UniversalObject) menjadi dictionary.
    Menggunakan dataclasses.asdict dengan konversi enum.
    """
    if hasattr(entity, "__dataclass_fields__"):
        data = {}
        for field in dataclasses.fields(entity):
            value = getattr(entity, field.name)
            data[field.name] = _convert(value)
        return data
    return _convert(entity)
