# fastra_core\serialization\canonical_json.py

from __future__ import annotations

import json
import logging
import math
from datetime import date, datetime
from typing import Any, Dict, Set
from uuid import UUID

from pydantic import BaseModel

logger = logging.getLogger("fastra_core.serialization.canonical_json")


class CanonicalJSONEncoder:
    """
    Kanonikal JSON Encoder dengan proteksi fail-fast ketat dan deterministik penuh.
    Mematikan seluruh variasi spasi serta menjamin pengurutan kunci (sort_keys)
    konisten di level memori demi menghasilkan hash kriptografis yang valid.
    """

    @classmethod
    def serialize_value(cls, obj: Any, seen_objects: Set[int]) -> Any:
        """
        Membongkar graf objek secara aman tanpa rekursi tidak berbatas.
        Menerapkan deteksi siklus referensi melingkar (Circular Reference Guard).
        """
        if obj is None:
            return None

        if isinstance(obj, (dict, list, set, BaseModel)):
            obj_id = id(obj)
            if obj_id in seen_objects:
                logger.error("CANONICAL_JSON_CIRCULAR_REFERENCE_DETECTED: type=%s", type(obj).__name__)
                raise ValueError("CIRCULAR_REFERENCE_DETECTED_IN_JSON_OBJECT_GRAPH")
            seen_objects.add(obj_id)

        try:
            if isinstance(obj, BaseModel):
                return cls.serialize_value(obj.model_dump(mode="json"), seen_objects)

            if isinstance(obj, dict):
                clean_dict: Dict[str, Any] = {}
                for k, v in obj.items():
                    if not isinstance(k, str):
                        logger.error("CANONICAL_JSON_KEY_NOT_STRING: %r", k)
                        raise TypeError("CANONICAL_JSON_ERROR_KEYS_MUST_BE_PURE_STRINGS")
                    clean_dict[k] = cls.serialize_value(v, seen_objects)
                return clean_dict

            # PERBAIKAN: list/tuple mempertahankan urutan asli (urutan itu semantik),
            # TAPI set/frozenset TIDAK punya urutan yang bermakna -- urutan iterasinya
            # bergantung pada tata letak hash table internal, yang bisa BERBEDA untuk
            # dua objek set dengan isi identik jika dibangun lewat urutan insert yang
            # berbeda (mis. set asli vs set(list) hasil round-trip JSON). Ini AKAR
            # PENYEBAB ARCHIVE_CHECKSUM_MISMATCH: hash jadi tidak deterministik setiap
            # kali ada `set` di dalam data yang di-hash. Fix: urutkan dulu berdasarkan
            # representasi JSON kanonik masing-masing elemen sebelum dikembalikan.
            if isinstance(obj, (list, tuple)):
                return [cls.serialize_value(item, seen_objects) for item in obj]

            if isinstance(obj, set):
                serialized_items = [cls.serialize_value(item, seen_objects) for item in obj]
                serialized_items.sort(key=lambda v: json.dumps(v, sort_keys=True, separators=(",", ":")))
                return serialized_items

            if isinstance(obj, (datetime, date)):
                return obj.isoformat()

            if isinstance(obj, UUID):
                return str(obj)

            if isinstance(obj, bool):
                return obj

            if isinstance(obj, (int, float)):
                if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
                    logger.error("CANONICAL_JSON_NUMERIC_ANOMALY: %s", obj)
                    raise ValueError("NUMERIC_ANOMALY_DETECTED_CANNOT_SERIALIZE_NAN_OR_INFINITE")
                return obj

            if isinstance(obj, str):
                return obj

            logger.error("CANONICAL_JSON_UNSUPPORTED_TYPE: %s", type(obj).__name__)
            raise TypeError(f"UNSUPPORTED_CANONICAL_SERIALIZATION_TYPE: {type(obj).__name__}")

        finally:
            if isinstance(obj, (dict, list, set, BaseModel)):
                seen_objects.remove(obj_id)


def to_json(obj: Any) -> str:
    """
    Mengonversi objek menjadi representasi string Kanonikal JSON deterministik.
    Menjamin ketiadaan karakter whitespace sekunder (anti polusi spasi UI).
    """
    clean_primitive_graph = CanonicalJSONEncoder.serialize_value(obj, seen_objects=set())

    return json.dumps(
        clean_primitive_graph,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )


def from_json(s: Any) -> Any:
    """
    Membongkar string JSON mentah menjadi graf objek primitif Python secara aman.
    Menolak pengiriman data string kosong atau whitespace zombie hantu.
    """
    if not isinstance(s, str):
        logger.error("FROM_JSON_INPUT_NOT_STRING: %r", s)
        raise TypeError("INPUT_MUST_BE_A_PURE_STRING")

    clean_str = s.strip()
    if not clean_str:
        logger.error("FROM_JSON_INPUT_EMPTY_OR_WHITESPACE")
        raise ValueError("JSON_STRING_CANNOT_BE_EMPTY_OR_WHITESPACE")

    try:
        return json.loads(clean_str)
    except json.JSONDecodeError as exc:
        logger.error("FROM_JSON_DECODE_ERROR: %s", exc)
        raise ValueError("INVALID_JSON_FORMAT") from exc