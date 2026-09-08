"""
fastra_core/knowledge/domains/material/sanitair_dan_plumbing.py

Modul pemuatan data material sanitair dan plumbing ke Knowledge Graph.
Seluruh ID menggunakan format mat_... (underscore) agar konsisten dengan sistem.
"""

from __future__ import annotations

import enum
import logging
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List

from pydantic import BaseModel, ConfigDict, Field, field_validator

from fastra_core.knowledge.graph import KnowledgeGraph
from fastra_core.knowledge.nodes import MaterialNode

logger = logging.getLogger("fastra.knowledge")


class SanitaryMaterialCategory(str, enum.Enum):
    """Klasifikasi taksonomi resmi kelompok material saniter dan utilitas air penunjang arsitektur."""

    SANITAIR = "SANITAIR"
    KRAN = "KRAN"
    FLOOR_DRAIN = "FLOOR_DRAIN"
    POMPA_AIR = "POMPA_AIR"
    TANDON = "TANDON"
    WATER_HEATER = "WATER_HEATER"
    SEPTIC = "SEPTIC"


# ---------------------------------------------------------------------------
# Inbound DTOs – Pydantic Strict Gateway & Sanitization (Fail-Fast)
# ---------------------------------------------------------------------------
class GeneratedSanitaryItemDTO(BaseModel):
    """DTO validasi ketat untuk mendaftar spesifikasi produk perlengkapan saniter mekanikal."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, strict=False)

    id: str = Field(..., min_length=5, max_length=128, pattern=r"^mat_[a-z0-9_\\.\\-]+$")
    name: str = Field(..., min_length=2, max_length=256)
    unit: str = Field(..., min_length=1, max_length=16, pattern=r"^(unit|buah)$")
    category: SanitaryMaterialCategory = Field(...)
    specifications: Dict[str, Any] = Field(default_factory=dict, max_length=50)
    volatility_factor: float = Field(default=0.0, ge=0.0, le=1.0, allow_inf_nan=False)

    @field_validator("specifications", mode="after")
    @classmethod
    def validate_specifications_payload(cls, value: Dict[str, Any]) -> Dict[str, Any]:
        """Memastikan harga_patokan tersedia dan bernilai positif."""
        if "harga_patokan" not in value:
            raise ValueError("Skema metadata spesifikasi saniter/plumbing cacat: Wajib melampirkan parameter 'harga_patokan'.")
        try:
            float_val = float(value["harga_patokan"])
            if float_val <= 0.0:
                raise ValueError()
        except (ValueError, TypeError):
            raise ValueError("Nilai nominal 'harga_patokan' di dalam spesifikasi wajib bertipe numerik positif.")
        return value


class SanitaryMaterialBundleDTO(BaseModel):
    """Bundel manifes penampung sekumpulan daftar komoditas produk saniter dan tandon air."""

    model_config = ConfigDict(extra="forbid", strict=False)

    items: List[GeneratedSanitaryItemDTO] = Field(..., max_length=500)


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
# Core Seeding Layer – Pure Sanitary Generation Pipeline (QS-Safe)
# ---------------------------------------------------------------------------
def load_sanitair_plumbing(kg: KnowledgeGraph) -> None:
    """
    Membuat, memvalidasi, dan menyuntikkan manifes master material sanitair ke KnowledgeGraph.
    ID menggunakan format mat_... (underscore) agar konsisten dengan sistem.
    """
    if not isinstance(kg, KnowledgeGraph):
        raise TypeError("Parameter masukan 'kg' wajib berupa instance orisinil dari kelas KnowledgeGraph.")

    # Kumpulan raw data benih komoditas material sanitair sesuai spesifikasi teknis PUPR
    raw_bundle_payload: List[Dict[str, Any]] = [
        {
            "id": "mat_kloset_duduk",
            "name": "Kloset Duduk Toto",
            "unit": "unit",
            "category": "SANITAIR",
            "specifications": {"tipe": "Duduk", "merek": "Toto", "harga_patokan": float(_to_decimal(2100000, "patokan"))},
            "volatility_factor": 0.05,
        },
        {
            "id": "mat_kloset_jongkok",
            "name": "Kloset Jongkok INA",
            "unit": "unit",
            "category": "SANITAIR",
            "specifications": {"tipe": "Jongkok", "merek": "INA", "harga_patokan": float(_to_decimal(450000, "patokan"))},
            "volatility_factor": 0.03,
        },
        {
            "id": "mat_wastafel",
            "name": "Wastafel Toto",
            "unit": "unit",
            "category": "SANITAIR",
            "specifications": {"merek": "Toto", "harga_patokan": float(_to_decimal(1150000, "patokan"))},
            "volatility_factor": 0.05,
        },
        {
            "id": "mat_kran_tembok",
            "name": "Kran Tembok Standar",
            "unit": "buah",
            "category": "KRAN",
            "specifications": {"tipe": "Tembok", "harga_patokan": float(_to_decimal(85000, "patokan"))},
            "volatility_factor": 0.03,
        },
        {
            "id": "mat_kran_angsa",
            "name": "Kran Angsa Wastafel",
            "unit": "buah",
            "category": "KRAN",
            "specifications": {"tipe": "Angsa", "harga_patokan": float(_to_decimal(150000, "patokan"))},
            "volatility_factor": 0.03,
        },
        {
            "id": "mat_shower_set",
            "name": "Kran Shower Set",
            "unit": "buah",
            "category": "KRAN",
            "specifications": {"tipe": "Shower Set", "harga_patokan": float(_to_decimal(350000, "patokan"))},
            "volatility_factor": 0.04,
        },
        {
            "id": "mat_floor_drain",
            "name": "Floor Drain Stainless",
            "unit": "buah",
            "category": "FLOOR_DRAIN",
            "specifications": {"bahan": "Stainless", "harga_patokan": float(_to_decimal(55000, "patokan"))},
            "volatility_factor": 0.02,
        },
        {
            "id": "mat_jet_pump",
            "name": "Pompa Air Jet Pump",
            "unit": "unit",
            "category": "POMPA_AIR",
            "specifications": {"tipe": "Jet Pump", "harga_patokan": float(_to_decimal(2250000, "patokan"))},
            "volatility_factor": 0.06,
        },
        {
            "id": "mat_submersible_pump",
            "name": "Pompa Submersible/Sumur Dalam",
            "unit": "unit",
            "category": "POMPA_AIR",
            "specifications": {"tipe": "Submersible", "harga_patokan": float(_to_decimal(3500000, "patokan"))},
            "volatility_factor": 0.06,
        },
        {
            "id": "mat_booster_pump",
            "name": "Pompa Dorong Booster Pump",
            "unit": "unit",
            "category": "POMPA_AIR",
            "specifications": {"tipe": "Booster", "harga_patokan": float(_to_decimal(1800000, "patokan"))},
            "volatility_factor": 0.05,
        },
        {
            "id": "mat_tandon_1000l",
            "name": "Tandon Air 1000L HDPE",
            "unit": "unit",
            "category": "TANDON",
            "specifications": {"kapasitas": "1000L", "bahan": "HDPE", "harga_patokan": float(_to_decimal(1800000, "patokan"))},
            "volatility_factor": 0.04,
        },
        {
            "id": "mat_tandon_500l",
            "name": "Tandon Air 500L HDPE",
            "unit": "unit",
            "category": "TANDON",
            "specifications": {"kapasitas": "500L", "bahan": "HDPE", "harga_patokan": float(_to_decimal(950000, "patokan"))},
            "volatility_factor": 0.04,
        },
        {
            "id": "mat_water_heater_listrik",
            "name": "Water Heater Listrik 30L",
            "unit": "unit",
            "category": "WATER_HEATER",
            "specifications": {"tipe": "Listrik", "kapasitas": "30L", "harga_patokan": float(_to_decimal(2500000, "patokan"))},
            "volatility_factor": 0.06,
        },
        {
            "id": "mat_septic_biotank",
            "name": "Bio Septic Tank 2m³",
            "unit": "unit",
            "category": "SEPTIC",
            "specifications": {"tipe": "Biotank", "kapasitas": "2m³", "harga_patokan": float(_to_decimal(4500000, "patokan"))},
            "volatility_factor": 0.04,
        },
    ]

    # 1. GATEWAY SCHEMA VALIDATION
    try:
        validated_bundle = SanitaryMaterialBundleDTO(items=raw_bundle_payload)
    except Exception as exc:
        logger.error("Gagal mengeksekusi otomatisasi seeder sanitair plumbing: Pelanggaran skema: %s", exc)
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
        logger.debug("Material sanitair/plumbing dimuat: %s", material_node_instance.id)

    logger.info(
        "Modul material sanitair dan plumbing mekanikal sukses ditayangkan: %d master nodes terkunci.",
        len(validated_bundle.items),
    )
