# fastra_core\digital_twin\serialization.py

from __future__ import annotations

import logging
import math
from enum import Enum
from typing import Any, Dict, List, Set, Tuple, Union

from pydantic import BaseModel

logger = logging.getLogger("fastra_core.digital_twin.serialization")


class StrictCCMSerializer:
    """
    Serializer Infrastruktur Digital Twin Deterministik.
    Melarang keras manipulasi string/objek longgar demi memotong risiko kerentanan
    penyelundupan data state hantu (Object Graph State Injection).
    """

    @classmethod
    def convert_value(cls, obj: Any, seen_ids: Set[int]) -> Any:
        """
        Mengonversi objek grafik menjadi struktur data primitif murni yang aman untuk JSON.
        Membentengi memori aplikasi dari ancaman Infinite Recursion via Cyclic Graph Check.
        """
        if obj is None:
            return None

        # Evaluasi Perlindungan Siklus Referensi Melingkar (Circular Loop Guard)
        if isinstance(obj, (dict, list, tuple, set, BaseModel)):
            obj_id = id(obj)
            if obj_id in seen_ids:
                logger.error("CYCLIC_GRAPH_REFERENCE_DETECTED_DURING_CCM_SERIALIZATION")
                raise ValueError("CYCLIC_GRAPH_REFERENCE_DETECTED_DURING_CCM_SERIALIZATION")
            seen_objects = set(seen_ids)
            seen_objects.add(obj_id)
        else:
            seen_objects = seen_ids

        # 1. Penanganan khusus instansiasi model data Pydantic v2 (Frozen Entities)
        if isinstance(obj, BaseModel):
            return cls.convert_value(obj.model_dump(mode="json"), seen_objects)

        # 2. Penanganan standardisasi Enums taksonomi hulu
        if isinstance(obj, Enum):
            return obj.value

        # 3. Penanganan kamus data
        if isinstance(obj, dict):
            clean_dict: Dict[str, Any] = {}
            for k, v in obj.items():
                if not isinstance(k, str):
                    logger.error("SERIALIZATION_ERROR_DICTIONARY_KEYS_MUST_BE_PURE_STRINGS: %r", k)
                    raise TypeError("SERIALIZATION_ERROR_DICTIONARY_KEYS_MUST_BE_PURE_STRINGS")
                clean_dict[k] = cls.convert_value(v, seen_objects)
            return clean_dict

        # 4. Penanganan koleksi berurutan (Iterable Arrays)
        if isinstance(obj, (list, tuple, set)):
            return [cls.convert_value(item, seen_objects) for item in obj]

        # 5. Penanganan tipe data skalar dasar (Primitif)
        if isinstance(obj, (int, float)):
            if isinstance(obj, bool):
                return obj
            # Menghancurkan anomali floating-point IEEE 754 sebelum lolos ke pipeline serialisasi
            if math.isnan(obj) or math.isinf(obj):
                logger.error("NUMERIC_ANOMALY_DETECTED_CANNOT_SERIALIZE_NAN_OR_INFINITE_VALUES: %s", obj)
                raise ValueError("NUMERIC_ANOMALY_DETECTED_CANNOT_SERIALIZE_NAN_OR_INFINITE_VALUES")
            return obj

        if isinstance(obj, str):
            return obj

        # Menghapus total fallback longgar hasattr(obj, "__dict__") atau str(obj) bawaan kode asli
        logger.error("UNSUPPORTED_DIGITAL_TWIN_SERIALIZATION_TYPE: %s", type(obj).__name__)
        raise TypeError(f"UNSUPPORTED_DIGITAL_TWIN_SERIALIZATION_TYPE: {type(obj).__name__}")


def to_serializable(obj: Any) -> Any:
    """
    Mengonversi graf objek apapun menjadi bentuk primitif yang siap diserialisasikan ke JSON.
    Menerapkan kebijakan strict fail-fast validation tanpa toleransi terhadap coercion hacks.
    """
    return StrictCCMSerializer.convert_value(obj, seen_ids=set())


def entity_to_dict(entity: Any) -> Dict[str, Any]:
    """
    Mengonversi entitas koridor utama CCM (UniversalObject/Pydantic Models) menjadi dictionary murni.
    Menghilangkan penggunaan modul lama dataclasses.asdict yang rapuh terhadap mutasi state.
    """
    if entity is None:
        logger.error("CANNOT_CONVERT_NULL_ENTITY_TO_DICTIONARY")
        raise ValueError("CANNOT_CONVERT_NULL_ENTITY_TO_DICTIONARY")

    # Memaksa seluruh entitas melewati filter interop taksonomi kanonikal pusat
    serialized_graph = StrictCCMSerializer.convert_value(entity, seen_ids=set())

    if not isinstance(serialized_graph, dict):
        logger.error(
            "SERIALIZATION_INTEGRITY_VIOLATION: Expected dict, got %s",
            type(serialized_graph).__name__,
        )
        raise TypeError(
            f"SERIALIZATION_INTEGRITY_VIOLATION: Expected entity structure conversion to yield "
            f"a valid dictionary, got '{type(serialized_graph).__name__}'."
        )

    return serialized_graph