# fastra_core\units\validator.py

from __future__ import annotations

import logging
import re
from typing import Any, Dict, Optional, Set

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .exceptions import UnitMismatchError, MissingUnitError

logger = logging.getLogger("fastra_core.units.validator")

# Matrix Taksonomi Satuan Ukur Kompatibel (Global Immutable Constants)
COMPATIBLE_GROUPS: Dict[str, Set[str]] = {
    "length": {"m", "mm", "cm", "km", "inch", "foot", "feet", "yard"},
    "area": {"m²", "mm²", "cm²", "km²", "ha", "hektar"},
    "volume": {"m³", "cm³", "l", "liter"},
    "mass": {"kg", "g", "ton"},
    "angle": {"rad", "deg", "degree"},
    "time": {"s", "min", "h", "hour", "day", "week", "month"},
    "currency": {"idr", "usd", "eur"},
    "temperature": {"k", "°c", "°f", "c", "f"},
    "density": {"kg/m³", "g/cm³"},
}

# Resolusi Aliran Sinonim (Canonical Conversion Alias Mapping)
ALIASES: Dict[str, str] = {
    "feet": "foot",
    "ft": "foot",
    "hektar": "ha",
    "liter": "l",
    "degree": "deg",
    "hour": "h",
    "c": "°c",
    "f": "°f",
}


class UnitValidationGuard(BaseModel):
    """
    Model Guard Pydantic v2 untuk menguji keabsahan penanda parameter satuan ukur (Unit Parameter Guard).
    Menghalau penetrasi data kosong, token non-string, serta manipulasi coercion hantu.
    """
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        strict=True,
        frozen=True,
        allow_inf_nan=False,
    )

    unit_token: str = Field(..., min_length=1, max_length=32)

    @field_validator("unit_token", mode="before")
    @classmethod
    def validate_and_sanitize_unit_string(cls, value: Any) -> str:
        if not isinstance(value, str):
            logger.error("UNIT_PARAMETER_MUST_BE_A_PURE_STRING: %r", value)
            raise TypeError("UNIT_PARAMETER_MUST_BE_A_PURE_STRING_COERCION_FORBIDDEN")

        # Pembersihan paksa karakter whitespace, carriage return, dan line feed
        cleaned = re.sub(r"[\r\n\t]", " ", value).strip()
        if not cleaned:
            logger.error("UNIT_PARAMETER_CANNOT_BE_EMPTY_OR_WHITESPACE")
            raise ValueError("UNIT_PARAMETER_CANNOT_BE_EMPTY_OR_WHITESPACE")

        return cleaned


def normalize_unit(u: str) -> str:
    """
    Mentransformasikan token penunjuk ke dalam format kanonikal standardisasi huruf kecil murni.
    """
    if not isinstance(u, str) or not u.strip():
        logger.debug("normalize_unit received empty or non-string input: %r", u)
        return ""

    # Validasi fail-fast via gerbang pengaman Pydantic
    guard = UnitValidationGuard(unit_token=u)
    lowered = guard.unit_token.lower()

    if lowered in ALIASES:
        return ALIASES[lowered]
    return lowered


def get_quantity_type(unit: str) -> str:
    """
    Mengurai identitas jenis taksonomi besaran fisik/finansial (Quantity Dimension Mapping) bersumber dari kode satuan.
    """
    norm = normalize_unit(unit)
    if not norm:
        return "unknown"

    for qtype, units in COMPATIBLE_GROUPS.items():
        if norm in units:
            return qtype

    return "unknown"


def are_units_compatible(u1: str, u2: str) -> bool:
    """
    Memverifikasi kecocokan jenis dimensi biner spasial/finansial antara dua satuan ukur.
    """
    if not isinstance(u1, str) or not isinstance(u2, str) or not u1.strip() or not u2.strip():
        return False

    t1 = get_quantity_type(u1)
    t2 = get_quantity_type(u2)

    return t1 == t2 and t1 != "unknown"


def validate_compatibility(u1: str, u2: str, operation: str = "") -> bool:
    """
    Menegakkan interupsi pemutusan dini (fail-fast execution guard) jika mendeteksi kalkulasi lintas satuan ilegal.
    """
    if not are_units_compatible(u1, u2):
        logger.error("Unit compatibility validation failed: %s vs %s, operation=%s", u1, u2, operation)
        raise UnitMismatchError(unit1=u1, unit2=u2, operation=operation)
    return True


def validate_unit_presence(value: Any, unit: Optional[str]) -> None:
    """
    Memastikan kehadiran token penanda dimensi ukur pada setiap pemrosesan akuntansi finansial / spasial BOQ.
    """
    if unit is None or not isinstance(unit, str) or not unit.strip():
        logger.error("Missing required unit identifier for quantity representation: %r", value)
        raise MissingUnitError(
            message=f"Missing required unit identifier for quantity representation of: {value}"
        )


def validate_dimension(unit: str, expected_quantity_type: str) -> None:
    """
    Validasi penegasan bahwa unit fisis wajib memiliki korelasi dimensi kuantitas yang diekspektasikan.
    Contoh: validate_dimension("m²", "area") -> Lolos secara legal.
    """
    if not isinstance(unit, str) or not unit.strip():
        logger.error("Expected valid unit dimension representation, got empty identifier token")
        raise MissingUnitError(
            message="Expected valid unit dimension representation, got empty identifier token"
        )

    guard_expected = str(expected_quantity_type).strip().lower()
    qtype = get_quantity_type(unit)

    if qtype != guard_expected:
        logger.error(
            "Dimension mismatch: unit '%s' is type '%s', expected '%s'",
            unit,
            qtype,
            guard_expected,
        )
        raise UnitMismatchError(
            unit1=unit,
            unit2=guard_expected,
            operation=f"expected dimension type check: {guard_expected}",
        )


def validate_unit_not_unknown(unit: str) -> None:
    """
    Validasi ketat penolakan satuan liar di luar matriks taksonomi formal sistem (Unknown Unit Injection Block).
    """
    if not isinstance(unit, str) or not unit.strip():
        logger.error("Unit presence required, empty string token identified")
        raise MissingUnitError(
            message="Unit presence required, empty string token identified"
        )

    qtype = get_quantity_type(unit)
    if qtype == "unknown":
        logger.error("Unknown unit rejected: %s", unit)
        raise UnitMismatchError(
            unit1=unit,
            unit2="known system taxonomy configuration",
            operation="unit tidak dikenal",
        )