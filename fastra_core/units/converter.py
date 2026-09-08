# fastra_core\units\converter.py

from __future__ import annotations

import logging
import math
from typing import Any, Dict

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .validator import normalize_unit, are_units_compatible, get_quantity_type
from .exceptions import ConversionError

logger = logging.getLogger("fastra_core.units.converter")

# Matrix Konversi Global Immutable untuk Satuan Ukur Standar
LENGTH_TO_M: Dict[str, float] = {
    "m": 1.0,
    "mm": 0.001,
    "cm": 0.01,
    "km": 1000.0,
    "inch": 0.0254,
    "foot": 0.3048,
    "yard": 0.9144,
}
AREA_TO_M2: Dict[str, float] = {"m²": 1.0, "cm²": 1e-4, "ha": 10000.0}
VOLUME_TO_M3: Dict[str, float] = {"m³": 1.0, "cm³": 1e-6, "l": 0.001}
MASS_TO_KG: Dict[str, float] = {"kg": 1.0, "g": 0.001, "ton": 1000.0}
TIME_TO_S: Dict[str, float] = {"s": 1.0, "min": 60.0, "h": 3600.0, "day": 86400.0}


class UnitConversionGuard(BaseModel):
    """
    Engine Pengaman Validasi Konversi Satuan (Unit Conversion Guard Engine).
    Menjamin stabilitas matematis dari manipulasi data mengambang rusak.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        strict=True,
        frozen=True,
        allow_inf_nan=False,
    )

    value: float = Field(..., description="Besaran nilai kuantitas awal")
    from_unit: str = Field(..., min_length=1, max_length=32)
    to_unit: str = Field(..., min_length=1, max_length=32)

    @field_validator("value", mode="before")
    @classmethod
    def validate_numeric_no_coercion(cls, value: Any) -> float:
        if isinstance(value, bool):
            logger.error("CONVERSION_VALUE_BOOLEAN_REJECTED: %r", value)
            raise TypeError("DATA_TYPE_COERCION_FORBIDDEN_BOOLEAN_NOT_ALLOWED")
        if not isinstance(value, (int, float)):
            logger.error("CONVERSION_VALUE_NON_NUMERIC_REJECTED: %r", value)
            raise TypeError("QUANTITY_VALUE_MUST_BE_PURE_NUMERIC_TYPE")
        float_val = float(value)
        if math.isnan(float_val) or math.isinf(float_val):
            logger.error("CONVERSION_VALUE_NAN_OR_INF_REJECTED: %s", float_val)
            raise ValueError("NUMERIC_ANOMALY_DETECTED_VALUE_CANNOT_BE_NAN_OR_INFINITE")
        return float_val

    @field_validator("from_unit", "to_unit", mode="before")
    @classmethod
    def sanitize_strings(cls, value: Any) -> str:
        if not isinstance(value, str):
            logger.error("UNIT_TOKEN_COERCION_REJECTED: %r", value)
            raise TypeError("UNIT_TOKEN_MUST_BE_A_PURE_STRING")
        stripped = value.strip()
        if not stripped:
            logger.error("UNIT_TOKEN_EMPTY_OR_WHITESPACE_REJECTED")
            raise ValueError("UNIT_TOKEN_CANNOT_BE_EMPTY_OR_WHITESPACE")
        return stripped


def convert(value: Any, from_unit: str, to_unit: str) -> float:
    """
    Mengonversi nilai kuantitas fisis antar satuan ukur yang kompatibel secara aman.
    Menerapkan kebijakan strict fail-fast validation tanpa toleransi terhadap coercion hacks.
    """
    # Memaksa seluruh parameter masukan melintasi gerbang pelindung Pydantic v2
    guard = UnitConversionGuard(value=value, from_unit=from_unit, to_unit=to_unit)

    nf = normalize_unit(guard.from_unit)
    nt = normalize_unit(guard.to_unit)

    if nf == nt:
        logger.debug("UNIT_CONVERSION_SAME_UNIT: %s -> %s (no conversion needed)", nf, nt)
        return guard.value

    if not are_units_compatible(nf, nt):
        logger.error("INCOMPATIBLE_UNIT_CONVERSION_ATTEMPTED: %s -> %s", from_unit, to_unit)
        raise ConversionError(from_unit, to_unit, "tidak kompatibel")

    qtype = get_quantity_type(nf)

    # Menegakkan aturan batas fisis non-negatif pada besaran kuantitas fisik absolut (BOQ Constraints)
    if qtype in {"length", "area", "volume", "mass", "time"}:
        if guard.value < 0.0:
            logger.error(
                "PHYSICAL_CONSTRAINT_VIOLATION_QUANTITY_CANNOT_BE_NEGATIVE_FOR_TYPE_%s: %s",
                qtype.upper(),
                guard.value,
            )
            raise ValueError(
                f"PHYSICAL_CONSTRAINT_VIOLATION_QUANTITY_CANNOT_BE_NEGATIVE_FOR_TYPE_{qtype.upper()}: {guard.value}"
            )

    # Eksekusi pipeline jalur matematika penaksir berdasarkan jenis taksonomi besaran
    if qtype == "length":
        canonical = guard.value * LENGTH_TO_M[nf]
        result = canonical / LENGTH_TO_M[nt]
    elif qtype == "area":
        canonical = guard.value * AREA_TO_M2[nf]
        result = canonical / AREA_TO_M2[nt]
    elif qtype == "volume":
        canonical = guard.value * VOLUME_TO_M3[nf]
        result = canonical / VOLUME_TO_M3[nt]
    elif qtype == "mass":
        canonical = guard.value * MASS_TO_KG[nf]
        result = canonical / MASS_TO_KG[nt]
    elif qtype == "time":
        canonical = guard.value * TIME_TO_S[nf]
        result = canonical / TIME_TO_S[nt]
    elif qtype == "angle":
        # Proteksi divisi pembagi nol dan normalisasi periodik sudut lingkaran homogen
        rad = guard.value * (math.pi / 180.0) if nf == "deg" else guard.value
        result = rad if nt == "rad" else rad * (180.0 / math.pi)
    elif qtype == "temperature":
        # Mengunci pembatasan batas fisik terendah Termodinamika (Nol Mutlak / Absolute Zero)
        if nf in {"°c", "c"}:
            k = guard.value + 273.15
        elif nf in {"°f", "f"}:
            k = (guard.value - 32.0) * 5.0 / 9.0 + 273.15
        else:
            k = guard.value

        if k < 0.0:
            logger.error("THERMODYNAMIC_CONSTRAINT_VIOLATION_TEMPERATURE_BELOW_ABSOLUTE_ZERO: %s K", k)
            raise ValueError(f"THERMODYNAMIC_CONSTRAINT_VIOLATION_TEMPERATURE_BELOW_ABSOLUTE_ZERO: {k} K")

        if nt in {"°c", "c"}:
            result = k - 273.15
        elif nt in {"°f", "f"}:
            result = (k - 273.15) * 9.0 / 5.0 + 32.0
        else:
            result = k
    else:
        logger.error("UNSUPPORTED_QUANTITY_TYPE: %s", qtype)
        raise ConversionError(from_unit, to_unit, f"Tipe kuantitas '{qtype}' tidak didukung")

    if math.isnan(result) or math.isinf(result):
        logger.error("NUMERIC_ANOMALY_DETECTED_DURING_CONVERSION_OUTPUT_COMPUTATION")
        raise ValueError("NUMERIC_ANOMALY_DETECTED_DURING_CONVERSION_OUTPUT_COMPUTATION")

    logger.info("[UNIT CONVERSION] %s %s -> %s %s", guard.value, nf, result, nt)
    return float(result)