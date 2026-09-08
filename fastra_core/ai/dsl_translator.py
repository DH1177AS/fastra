# fastra_core\ai\dsl_translator.py

from __future__ import annotations

import logging
import math
import re
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, ConfigDict, Field, field_validator

from fastra_core.ai.safety import SafetyFilter

logger = logging.getLogger("fastra_core.ai.dsl_translator")


class DSLTranslationResult(BaseModel):
    """
    Model Value Object hasil translasi bahasa alami menuju Construction DSL.
    Menjamin keabsahan penampang data lewat imutabilitas murni (frozen=True).
    """
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        strict=True,
        frozen=True,
        allow_inf_nan=False,
    )

    source_text: str = Field(..., min_length=2, max_length=2048)
    dsl_text: str = Field(..., min_length=0)
    entities: Tuple[Dict[str, Any], ...] = Field(default_factory=tuple)
    needs_review: bool = Field(default=True)
    warnings: Tuple[str, ...] = Field(default_factory=tuple)

    @field_validator("source_text", "dsl_text", mode="before")
    @classmethod
    def sanitize_strings(cls, value: Any) -> str:
        if not isinstance(value, str):
            logger.error("DSL_RESULT_STRING_COERCION_REJECTED: %r", value)
            raise TypeError("VALUE_MUST_BE_A_PURE_STRING_COERCION_FORBIDDEN")
        stripped = value.strip()
        if not stripped and value:
            logger.error("DSL_RESULT_WHITESPACE_ONLY_STRING_REJECTED")
            raise ValueError("STRING_CANNOT_CONSIST_OF_WHITESPACE_ONLY")
        return stripped

    @field_validator("entities", mode="before")
    @classmethod
    def validate_entities_collection(cls, value: Any) -> Tuple[Dict[str, Any], ...]:
        if isinstance(value, bool):
            logger.error("DSL_ENTITIES_BOOLEAN_REJECTED: %r", value)
            raise TypeError("DATA_TYPE_COERCION_FORBIDDEN_BOOLEAN_NOT_ALLOWED")
        if not isinstance(value, (list, tuple)):
            logger.error("DSL_ENTITIES_MUST_BE_LIST_OR_TUPLE: %r", value)
            raise TypeError("ENTITIES_MUST_BE_A_LIST_OR_TUPLE")
        clean_entities: List[Dict[str, Any]] = []
        for idx, item in enumerate(value):
            if not isinstance(item, dict):
                logger.error("DSL_ENTITY_%d_NOT_DICT: %r", idx, item)
                raise TypeError(f"ENTITY_AT_INDEX_{idx}_MUST_BE_A_DICTIONARY")
            for k, v in item.items():
                if not isinstance(k, str) or not k.strip():
                    logger.error("DSL_ENTITY_%d_INVALID_KEY: %r", idx, k)
                    raise ValueError(f"ENTITY_KEYS_MUST_BE_NON_EMPTY_STRINGS_AT_INDEX_{idx}")
                if isinstance(v, (int, float)) and not isinstance(v, bool):
                    if math.isnan(v) or math.isinf(v):
                        logger.error("DSL_ENTITY_%d_NUMERIC_ANOMALY at key %s: %s", idx, k, v)
                        raise ValueError(f"NUMERIC_ANOMALY_DETECTED_IN_DSL_ENTITIES_AT_KEY_{k}")
            clean_entities.append(item)
        return tuple(clean_entities)

    @field_validator("warnings", mode="before")
    @classmethod
    def validate_warnings_collection(cls, value: Any) -> Tuple[str, ...]:
        if isinstance(value, bool):
            logger.error("DSL_WARNINGS_BOOLEAN_REJECTED: %r", value)
            raise TypeError("DATA_TYPE_COERCION_FORBIDDEN_BOOLEAN_NOT_ALLOWED")
        if not isinstance(value, (list, tuple)):
            logger.error("DSL_WARNINGS_MUST_BE_LIST_OR_TUPLE: %r", value)
            raise TypeError("WARNINGS_MUST_BE_A_LIST_OR_TUPLE")
        clean_warnings: List[str] = []
        for idx, item in enumerate(value):
            if not isinstance(item, str):
                logger.error("DSL_WARNING_%d_NOT_STRING: %r", idx, item)
                raise TypeError(f"WARNING_AT_INDEX_{idx}_MUST_BE_A_STRING")
            stripped = item.strip()
            if not stripped:
                logger.error("DSL_WARNING_%d_EMPTY: %r", idx, item)
                raise ValueError(f"WARNING_AT_INDEX_{idx}_CANNOT_BE_EMPTY_OR_WHITESPACE")
            clean_warnings.append(stripped)
        return tuple(clean_warnings)


class DSLTranslator(BaseModel):
    """
    Penerjemah Bahasa Alami ke Ruang Struktur Penilai Konstruksi (Construction DSL Translator).
    Mengevaluasi muatan payload teks secara adaptif dan terproteksi dari ancaman injeksi.
    """
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        extra="forbid",
        str_strip_whitespace=True,
        strict=True,
        frozen=True,
        allow_inf_nan=False,
    )

    safety: SafetyFilter = Field(default_factory=SafetyFilter)

    @field_validator("safety", mode="before")
    @classmethod
    def validate_safety_filter_instance(cls, value: Any) -> SafetyFilter:
        if not isinstance(value, SafetyFilter):
            logger.error("SAFETY_FILTER_INVALID_TYPE: %r", value)
            raise TypeError("SAFETY_FILTER_MUST_BE_AN_INSTANCE_OF_SAFETY_FILTER")
        return value

    def translate(self, text: str) -> DSLTranslationResult:
        """
        Menerjemahkan teks bahasa alami menjadi susunan kode token DSL legal.
        Setiap hasil dipaksa bertanda 'needs_review=True' demi kepatuhan kognitif ACES-700.
        """
        if not isinstance(text, str):
            logger.error("TRANSLATOR_INPUT_MUST_BE_STRING: %r", text)
            raise TypeError("TRANSLATOR_ERROR_INPUT_MUST_BE_A_PURE_STRING")

        clean_text = text.strip()
        if not clean_text:
            logger.error("TRANSLATOR_INPUT_EMPTY_OR_WHITESPACE")
            raise ValueError("INPUT_TEXT_CANNOT_BE_EMPTY_OR_WHITESPACE")
        if len(clean_text) < 2:
            logger.error("TRANSLATOR_INPUT_TOO_SHORT: %d chars", len(clean_text))
            raise ValueError("INPUT_TEXT_TOO_SHORT_TO_EXECUTE_DSL_TRANSLATION")
        if len(clean_text) > 2048:
            logger.error("TRANSLATOR_INPUT_TOO_LONG: %d chars", len(clean_text))
            raise ValueError("INPUT_TEXT_EXCEEDS_MAXIMUM_ALLOWED_LENGTH")

        # Gerbang Proteksi Keamanan Kognitif (Cognitive Injection Content Guard)
        safe, reason = self.safety.check(clean_text)
        if not safe:
            logger.error("COGNITIVE_SAFETY_VIOLATION: %s", reason)
            raise ValueError(f"COGNITIVE_SAFETY_VIOLATION_INPUT_TEXT_REJECTED: {reason}")

        dsl_lines: List[str] = []
        entities_list: List[Dict[str, Any]] = []
        warnings_list: List[str] = []

        lowered = clean_text.lower()

        # 1. Klasifikasi Segmentasi Tipe Penampang Bangunan
        building_type: Optional[str] = None
        if "rumah" in lowered:
            building_type = "HOUSE"
        elif "ruko" in lowered:
            building_type = "RUKO"
        elif "gedung" in lowered:
            building_type = "BUILDING"
        elif "gudang" in lowered:
            building_type = "WAREHOUSE"

        if building_type:
            dsl_lines.append(f"CREATE BUILDING TYPE {building_type}")
            entities_list.append({"type": "Building", "building_type": building_type})

        # 2. Segmentasi Jumlah Lantai (Storey Level Tracing)
        storey: Optional[int] = None
        if "1 lantai" in lowered or "satu lantai" in lowered:
            storey = 1
        elif "2 lantai" in lowered or "dua lantai" in lowered:
            storey = 2
        elif "3 lantai" in lowered or "tiga lantai" in lowered:
            storey = 3

        if storey is not None:
            dsl_lines.append(f"STOREY {storey}")
            if entities_list:
                entities_list[0]["storeys"] = storey
            else:
                entities_list.append({"type": "Building", "storeys": storey})

        # 3. Ekstraksi Dimensi Luasan (Area Token Regex Parsing Engine)
        area_match = re.search(r"(\d+)\s*(?:m2|m²|meter persegi|m persegi|square meter)", lowered)
        if area_match:
            try:
                area = int(area_match.group(1))
                if area <= 0:
                    raise ValueError("AREA_MUST_BE_GREATER_THAN_ZERO")
                if area > 1_000_000:  # Batas wajar area dalam m²
                    raise ValueError("AREA_EXCEEDS_REASONABLE_LIMIT")
                dsl_lines.append(f"AREA {area}")
                if entities_list:
                    entities_list[0]["area"] = area
                else:
                    entities_list.append({"type": "Building", "area": area})
            except (ValueError, OverflowError) as exc:
                logger.warning("AREA_PARSING_WARNING: %s", exc)
                warnings_list.append("FAIL_TO_PARSE_VALID_BOUNDED_AREA_NUMERIC_TOKEN")

        # 4. Filter Sinkronisasi Wilayah Regional Lokal (GIS Anchor Matching)
        known_locations = ["bandung", "jakarta", "surabaya", "yogyakarta", "medan", "semarang"]
        for loc in known_locations:
            if loc in lowered:
                dsl_lines.append(f"LOCATION {loc.upper()}")
                if entities_list:
                    entities_list[0]["location"] = loc.upper()
                break

        # 5. Klasifikasi Taksonomi Komoditas Material Dinding
        wall_material: Optional[str] = None
        if "hebel" in lowered or "bata ringan" in lowered or "aac" in lowered:
            wall_material = "AAC_BLOCK"
        elif "bata merah" in lowered:
            wall_material = "BATA_MERAH"

        if wall_material:
            dsl_lines.append(f"WALL MATERIAL {wall_material}")
            entities_list.append({"type": "Wall", "material": wall_material})

        # 6. Klasifikasi Taksonomi Rangka Atap Struktural
        roof_type: Optional[str] = None
        if "baja ringan" in lowered:
            roof_type = "LIGHT_STEEL"
        elif "kayu" in lowered:
            roof_type = "WOOD"

        if roof_type:
            dsl_lines.append(f"ROOF STRUCTURE {roof_type}")
            entities_list.append({"type": "Roof", "structure": roof_type})

        # Kompilasi penanganan jika masukan hampa komponen token
        if not dsl_lines:
            warnings_list.append("Tidak ada fitur dikenali, DSL kosong. Perlu input lebih detail.")

        logger.info("DSL translation completed: %d DSL lines, %d entities, %d warnings",
                    len(dsl_lines), len(entities_list), len(warnings_list))

        return DSLTranslationResult(
            source_text=clean_text,
            dsl_text="\n".join(dsl_lines),
            entities=tuple(entities_list),
            needs_review=True,
            warnings=tuple(warnings_list),
        )