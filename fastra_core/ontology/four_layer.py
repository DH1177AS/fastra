# fastra_core\ontology\four_layer.py

from __future__ import annotations

import logging
from datetime import date
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from fastra_core.primitives.area import Area
from fastra_core.primitives.currency import Currency
from fastra_core.primitives.volume import Volume

logger = logging.getLogger("fastra.ontology.four_layer")


class PhysicalReality(BaseModel):
    """
    Model representasi domain untuk validasi ketat status fisik di lapangan.
    Mengunci integritas tanggal inspeksi menggunakan tipe temporal terikat.
    """
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        strict=True,
        frozen=True,
        allow_inf_nan=False,
    )

    exists_in_field: bool = Field(default=False)
    last_inspection_date: Optional[date] = Field(default=None)
    condition: Optional[str] = Field(default=None, min_length=2, max_length=64)

    @field_validator("condition", mode="before")
    @classmethod
    def validate_condition_string(cls, value: Any) -> Optional[str]:
        if value is None:
            return None
        if not isinstance(value, str):
            logger.error("PHYSICAL_CONDITION_REJECTED_NON_STRING: %r", value)
            raise TypeError("PHYSICAL_CONDITION_MUST_BE_A_PURE_STRING")
        stripped = value.strip()
        if not stripped:
            logger.error("PHYSICAL_CONDITION_REJECTED_EMPTY_OR_WHITESPACE")
            raise ValueError("PHYSICAL_CONDITION_CANNOT_BE_AN_EMPTY_STRING")
        return stripped


class GeometricReality(BaseModel):
    """
    Model representasi domain geometri spasial teknik sipil.
    Melarang penggunaan tipe Any dan menjamin validitas dimensional objek.
    """
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        strict=True,
        frozen=True,
        allow_inf_nan=False,
    )

    has_geometry: bool = Field(default=False)
    bounding_box: Optional[Dict[str, float]] = Field(default=None)
    volume: Optional[Volume] = Field(default=None)
    area: Optional[Area] = Field(default=None)

    @field_validator("bounding_box", mode="before")
    @classmethod
    def validate_bounding_box_structure(cls, value: Any) -> Optional[Dict[str, float]]:
        if value is None:
            return None
        if not isinstance(value, dict):
            logger.error("BOUNDING_BOX_REJECTED_NON_DICT: %r", value)
            raise TypeError("BOUNDING_BOX_MUST_BE_A_DICTIONARY")

        required_keys = {"min_x", "min_y", "min_z", "max_x", "max_y", "max_z"}
        if not required_keys.issubset(value.keys()):
            logger.error("BOUNDING_BOX_MISSING_KEYS: %s", value.keys())
            raise ValueError("BOUNDING_BOX_MISSING_REQUIRED_DIMENSIONAL_KEYS")

        for k, v in value.items():
            if not isinstance(v, (int, float)) or isinstance(v, bool):
                logger.error("BOUNDING_BOX_INVALID_COORDINATE_TYPE at key %s: %r", k, v)
                raise TypeError(f"BOUNDING_BOX_COORDINATE_VALUE_MUST_BE_NUMERIC_AT_KEY_{k}")
        return value


class SemanticReality(BaseModel):
    """
    Model representasi klasifikasi taksonomi konstruksi berdasarkan standardisasi QS.
    Menghilangkan celah hantu penulisan kosong (whitespace zombie string).
    """
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        strict=True,
        frozen=True,
        allow_inf_nan=False,
    )

    entity_class: Optional[str] = Field(default=None, min_length=2, max_length=128)
    structural_type: Optional[str] = Field(default=None, min_length=2, max_length=128)
    material_type: Optional[str] = Field(default=None, min_length=2, max_length=128)
    function: Optional[str] = Field(default=None, min_length=2, max_length=256)

    @field_validator("entity_class", "structural_type", "material_type", "function", mode="before")
    @classmethod
    def validate_semantic_strings(cls, value: Any) -> Optional[str]:
        if value is None:
            return None
        if not isinstance(value, str):
            logger.error("SEMANTIC_VALUE_REJECTED_NON_STRING: %r", value)
            raise TypeError("SEMANTIC_VALUE_MUST_BE_A_PURE_STRING")
        stripped = value.strip()
        if not stripped:
            logger.error("SEMANTIC_VALUE_REJECTED_EMPTY_OR_WHITESPACE")
            raise ValueError("SEMANTIC_VALUE_CANNOT_BE_EMPTY_OR_WHITESPACE")
        return stripped


class EconomicReality(BaseModel):
    """
    Model perhitungan estimasi biaya (QS Cost Estimation Model).
    Menjamin validasi faktor risiko agar tidak melanggar batas margin kelayakan proyek.
    """
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        strict=True,
        frozen=True,
        allow_inf_nan=False,
    )

    material_cost: Optional[Currency] = Field(default=None)
    labor_cost: Optional[Currency] = Field(default=None)
    equipment_cost: Optional[Currency] = Field(default=None)
    total_cost: Optional[Currency] = Field(default=None)
    risk_factor: float = Field(default=0.0, ge=0.0, le=1.0)

    @field_validator("risk_factor", mode="before")
    @classmethod
    def validate_risk_factor_numeric(cls, value: Any) -> float:
        if isinstance(value, bool):
            logger.error("RISK_FACTOR_REJECTED_BOOLEAN: %r", value)
            raise TypeError("RISK_FACTOR_COERCION_HACK_DETECTED_BOOLEAN_NOT_ALLOWED")
        if not isinstance(value, (int, float)):
            logger.error("RISK_FACTOR_REJECTED_NON_NUMERIC: %r", value)
            raise TypeError("RISK_FACTOR_MUST_BE_A_PURE_NUMERIC_TYPE")
        float_val = float(value)
        if not (0.0 <= float_val <= 1.0):
            logger.error("RISK_FACTOR_OUT_OF_RANGE: %s", float_val)
            raise ValueError("RISK_FACTOR_MUST_BE_BETWEEN_0_AND_1")
        return float_val


class FourLayerReality(BaseModel):
    """
    Orchestrator utama pembungkus model data realitas 4-lapisan ontologi konstruksi.
    Objek dijamin Immutable (frozen=True) demi keamanan sirkulasi memori hulu-ke-hilir.
    """
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        strict=True,
        frozen=True,
        allow_inf_nan=False,
    )

    physical: PhysicalReality = Field(default_factory=PhysicalReality)
    geometric: GeometricReality = Field(default_factory=GeometricReality)
    semantic: SemanticReality = Field(default_factory=SemanticReality)
    economic: EconomicReality = Field(default_factory=EconomicReality)

    def is_complete(self) -> bool:
        """
        Logika bisnis penentuan pemenuhan kelayakan integritas data empat dimensi (Four-Layer).
        Mengecek kelengkapan komit properti inti secara fail-fast dan akurat.
        """
        return (
            self.physical.exists_in_field is True and
            self.geometric.has_geometry is True and
            self.semantic.entity_class is not None and
            self.economic.total_cost is not None
        )