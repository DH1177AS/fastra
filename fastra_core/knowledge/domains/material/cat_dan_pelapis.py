"""
fastra_core/knowledge/domains/material/cat_dan_pelapis.py

Modul pemuatan data material cat dan pelapis ke Knowledge Graph.
Seluruh ID menggunakan format mat_... (underscore) agar konsisten dengan sistem.
"""

from __future__ import annotations

import enum
import logging
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, ConfigDict, Field, field_validator

from fastra_core.knowledge.graph import KnowledgeGraph
from fastra_core.knowledge.nodes import MaterialNode

logger = logging.getLogger("fastra.knowledge")


class CoatingMaterialCategory(str, enum.Enum):
    """Klasifikasi taksonomi resmi kelompok cat, pelapis pelindung, dan bahan finishing."""

    CAT_INTERIOR = "CAT_INTERIOR"
    CAT_EKSTERIOR = "CAT_EKSTERIOR"
    CAT_KAYU = "CAT_KAYU"
    CAT_BESI = "CAT_BESI"
    CAT_FIRE = "CAT_FIRE"
    PLAMIR = "PLAMIR"
    DEMPUL = "DEMPUL"
    THINNER = "THINNER"


# ---------------------------------------------------------------------------
# Inbound DTOs – Pydantic Strict Gateway & Sanitization (Fail-Fast)
# ---------------------------------------------------------------------------
class GeneratedCoatingItemDTO(BaseModel):
    """DTO validasi ketat untuk mendaftar spesifikasi produk cat dan pelapis."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, strict=False)

    id: str = Field(..., min_length=5, max_length=128, pattern=r"^mat_[a-z0-9_\\.\\-]+$")
    name: str = Field(..., min_length=2, max_length=256)
    unit: str = Field(..., min_length=2, max_length=16, pattern=r"^(pail|kg|m²|liter)$")
    category: CoatingMaterialCategory = Field(...)
    specifications: Dict[str, Any] = Field(default_factory=dict, max_length=50)
    volatility_factor: float = Field(default=0.0, ge=0.0, le=1.0, allow_inf_nan=False)

    @field_validator("specifications", mode="after")
    @classmethod
    def validate_specifications_payload(cls, value: Dict[str, Any]) -> Dict[str, Any]:
        """Memastikan harga_patokan tersedia dan bernilai positif."""
        if "harga_patokan" not in value:
            raise ValueError("Skema metadata spesifikasi cat/pelapis cacat: Wajib melampirkan parameter 'harga_patokan'.")
        try:
            float_val = float(value["harga_patokan"])
            if float_val <= 0.0:
                raise ValueError()
        except (ValueError, TypeError):
            raise ValueError("Nilai nominal 'harga_patokan' di dalam spesifikasi wajib bertipe numerik positif.")
        return value


class CoatingMaterialBundleDTO(BaseModel):
    """Bundel manifes penampung sekumpulan daftar komoditas produk cat dan pelapis finishing."""

    model_config = ConfigDict(extra="forbid", strict=False)

    items: List[GeneratedCoatingItemDTO] = Field(..., max_length=500)


# ---------------------------------------------------------------------------
# Core Utilities – Jaminan Keamanan Type Casting
# ---------------------------------------------------------------------------
def _to_decimal(value: float | int | Decimal, field_name: str) -> Decimal:
    """Konversi eksak ke Decimal dengan validasi tipe."""
    if isinstance(value, Decimal):
        return value
    if not isinstance(value, (int, float)):
        raise TypeError(f"Field '{field_name}' wajib bertipe numerik dasar (int/float/Decimal).")
    try:
        return Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError(f"Field '{field_name}' gagal dikonversi ke representasi Decimal imutabel.") from exc


# ---------------------------------------------------------------------------
# Core Seeding Layer – Pure Coating Generation Pipeline (QS-Safe)
# ---------------------------------------------------------------------------
def load_cat_pelapis(kg: KnowledgeGraph) -> None:
    """
    Membuat, memvalidasi, dan menyuntikkan manifes master material cat ke KnowledgeGraph.
    ID menggunakan format mat_... (underscore) agar konsisten dengan sistem.
    """
    if not isinstance(kg, KnowledgeGraph):
        raise TypeError("Parameter masukan 'kg' wajib berupa instance orisinil dari kelas KnowledgeGraph.")

    # Kumpulan raw data benih komoditas material pelapis sesuai spesifikasi teknis PUPR
    raw_bundle_payload: List[Dict[str, Any]] = [
        {
            "id": "mat_cat_interior_dulux_25kg",
            "name": "Cat Interior Dulux Pentalite 25kg",
            "unit": "pail",
            "category": "CAT_INTERIOR",
            "specifications": {"merek": "Dulux", "kemasan": "25kg", "harga_patokan": float(_to_decimal(340000, "patokan"))},
            "volatility_factor": 0.04,
        },
        {
            "id": "mat_cat_interior_nippon_25kg",
            "name": "Cat Interior Nippon Vinilex 25kg",
            "unit": "pail",
            "category": "CAT_INTERIOR",
            "specifications": {"merek": "Nippon", "kemasan": "25kg", "harga_patokan": float(_to_decimal(155000, "patokan"))},
            "volatility_factor": 0.04,
        },
        {
            "id": "mat_cat_interior_avian_25kg",
            "name": "Cat Interior Avian 25kg",
            "unit": "pail",
            "category": "CAT_INTERIOR",
            "specifications": {"merek": "Avian", "kemasan": "25kg", "harga_patokan": float(_to_decimal(130000, "patokan"))},
            "volatility_factor": 0.04,
        },
        {
            "id": "mat_cat_interior_mowilex_25kg",
            "name": "Cat Interior Mowilex Emulsion 25kg",
            "unit": "pail",
            "category": "CAT_INTERIOR",
            "specifications": {"merek": "Mowilex", "kemasan": "25kg", "harga_patokan": float(_to_decimal(310000, "patokan"))},
            "volatility_factor": 0.04,
        },
        {
            "id": "mat_cat_eksterior_dulux_25kg",
            "name": "Cat Eksterior Dulux Weathershield 25kg",
            "unit": "pail",
            "category": "CAT_EKSTERIOR",
            "specifications": {"merek": "Dulux", "kemasan": "25kg", "harga_patokan": float(_to_decimal(480000, "patokan"))},
            "volatility_factor": 0.05,
        },
        {
            "id": "mat_cat_eksterior_nippon_25kg",
            "name": "Cat Eksterior Nippon Weatherbond 25kg",
            "unit": "pail",
            "category": "CAT_EKSTERIOR",
            "specifications": {"merek": "Nippon", "kemasan": "25kg", "harga_patokan": float(_to_decimal(420000, "patokan"))},
            "volatility_factor": 0.05,
        },
        {
            "id": "mat_cat_kayu_melamik",
            "name": "Cat Melamik Kayu",
            "unit": "kg",
            "category": "CAT_KAYU",
            "specifications": {"harga_patokan": float(_to_decimal(42000, "patokan"))},
            "volatility_factor": 0.03,
        },
        {
            "id": "mat_cat_besi_anti_karat",
            "name": "Cat Anti Karat Zinc Chromate",
            "unit": "kg",
            "category": "CAT_BESI",
            "specifications": {"harga_patokan": float(_to_decimal(38000, "patokan"))},
            "volatility_factor": 0.03,
        },
        {
            "id": "mat_cat_intumescent",
            "name": "Cat Fireproofing Intumescent",
            "unit": "m²",
            "category": "CAT_FIRE",
            "specifications": {"fungsi": "Anti Api", "harga_patokan": float(_to_decimal(185000, "patokan"))},
            "volatility_factor": 0.06,
        },
        {
            "id": "mat_plamir",
            "name": "Plamir Dinding",
            "unit": "kg",
            "category": "PLAMIR",
            "specifications": {"harga_patokan": float(_to_decimal(18000, "patokan"))},
            "volatility_factor": 0.02,
        },
        {
            "id": "mat_dempul_kayu",
            "name": "Dempul Kayu",
            "unit": "kg",
            "category": "DEMPUL",
            "specifications": {"harga_patokan": float(_to_decimal(25000, "patokan"))},
            "volatility_factor": 0.02,
        },
        {
            "id": "mat_thinner",
            "name": "Thinner",
            "unit": "liter",
            "category": "THINNER",
            "specifications": {"harga_patokan": float(_to_decimal(22000, "patokan"))},
            "volatility_factor": 0.05,
        },
    ]

    # 1. GATEWAY SCHEMA VALIDATION
    try:
        validated_bundle = CoatingMaterialBundleDTO(items=raw_bundle_payload)
    except Exception as exc:
        logger.error("Gagal mengeksekusi otomatisasi seeder cat pelapis: Pelanggaran skema: %s", exc)
        return

    # 2. IMMUTABLE DOMAIN INJECTION PIPELINE
    for item_dto in validated_bundle.items:
        material_node_instance = MaterialNode(
            id=item_dto.id,
            name=item_dto.name,
            unit=item_dto.unit,
            category=item_dto.category.value,
            specifications=item_dto.specifications,
            volatility_factor=item_dto.volatility_factor,
        )
        kg.add_material(material_node_instance)
        logger.debug("Material cat/pelapis dimuat: %s", material_node_instance.id)

    logger.info(
        "Modul material cat dinding arsitektural dan pelapis proteksi sukses ditayangkan: %d master nodes terkunci.",
        len(validated_bundle.items),
    )
