"""
fastra_core/knowledge/domains/material/dinding_dan_partisi.py

Modul pemuatan data material dinding dan partisi ke Knowledge Graph.
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


class WallMaterialCategory(str, enum.Enum):
    """Klasifikasi taksonomi resmi kelompok material dinding, sekat, dan partisi arsitektural."""

    BATA = "BATA"
    BATA_RINGAN = "BATA_RINGAN"
    BATAKO = "BATAKO"
    GLASS_BLOCK = "GLASS_BLOCK"
    PARTISI = "PARTISI"
    PANEL_DINDING = "PANEL_DINDING"
    BATU_ALAM = "BATU_ALAM"


# ---------------------------------------------------------------------------
# Inbound DTOs – Pydantic Strict Gateway & Sanitization (Fail-Fast)
# ---------------------------------------------------------------------------
class GeneratedWallItemDTO(BaseModel):
    """DTO validasi ketat untuk mendaftar spesifikasi produk dinding dan partisi."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, strict=False)

    id: str = Field(..., min_length=5, max_length=128, pattern=r"^mat_[a-z0-9_\\.\\-]+$")
    name: str = Field(..., min_length=2, max_length=256)
    unit: str = Field(..., min_length=1, max_length=16, pattern=r"^(buah|m³|m²)$")
    category: WallMaterialCategory = Field(...)
    specifications: Dict[str, Any] = Field(default_factory=dict, max_length=50)
    volatility_factor: float = Field(default=0.0, ge=0.0, le=1.0, allow_inf_nan=False)

    @field_validator("specifications", mode="after")
    @classmethod
    def validate_specifications_payload(cls, value: Dict[str, Any]) -> Dict[str, Any]:
        """Memastikan harga_patokan tersedia dan bernilai positif."""
        if "harga_patokan" not in value:
            raise ValueError("Skema metadata spesifikasi dinding/partisi cacat: Wajib melampirkan parameter 'harga_patokan'.")
        try:
            float_val = float(value["harga_patokan"])
            if float_val <= 0.0:
                raise ValueError()
        except (ValueError, TypeError):
            raise ValueError("Nilai nominal 'harga_patokan' di dalam spesifikasi wajib bertipe numerik positif.")
        return value


class WallMaterialBundleDTO(BaseModel):
    """Bundel manifes penampung sekumpulan daftar komoditas produk dinding, bata, dan partisi."""

    model_config = ConfigDict(extra="forbid", strict=False)

    items: List[GeneratedWallItemDTO] = Field(..., max_length=500)


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
# Core Seeding Layer – Pure Wall Generation Pipeline (QS-Safe)
# ---------------------------------------------------------------------------
def load_dinding_partisi(kg: KnowledgeGraph) -> None:
    """
    Membuat, memvalidasi, dan menyuntikkan manifes master material dinding ke KnowledgeGraph.
    ID menggunakan format mat_... (underscore) agar konsisten dengan sistem.
    """
    if not isinstance(kg, KnowledgeGraph):
        raise TypeError("Parameter masukan 'kg' wajib berupa instance orisinil dari kelas KnowledgeGraph.")

    # Kumpulan raw data benih komoditas material sekat dinding sesuai spesifikasi teknis PUPR
    raw_bundle_payload: List[Dict[str, Any]] = [
        {
            "id": "mat_bata_merah",
            "name": "Bata Merah Oven",
            "unit": "buah",
            "category": "BATA",
            "specifications": {"ukuran": "5x11x22cm", "harga_patokan": float(_to_decimal(900, "patokan"))},
            "volatility_factor": 0.03,
        },
        {
            "id": "mat_bata_ringan_10cm",
            "name": "Bata Ringan AAC 10cm",
            "unit": "m³",
            "category": "BATA_RINGAN",
            "specifications": {"tebal": "10cm", "harga_patokan": float(_to_decimal(650000, "patokan"))},
            "volatility_factor": 0.05,
        },
        {
            "id": "mat_bata_ringan_7cm",
            "name": "Bata Ringan AAC 7.5cm",
            "unit": "m³",
            "category": "BATA_RINGAN",
            "specifications": {"tebal": "7.5cm", "harga_patokan": float(_to_decimal(620000, "patokan"))},
            "volatility_factor": 0.05,
        },
        {
            "id": "mat_batako",
            "name": "Batako Semen",
            "unit": "buah",
            "category": "BATAKO",
            "specifications": {"ukuran": "10x20x40cm", "harga_patokan": float(_to_decimal(3500, "patokan"))},
            "volatility_factor": 0.04,
        },
        {
            "id": "mat_glass_block",
            "name": "Glass Block 20x20cm",
            "unit": "buah",
            "category": "GLASS_BLOCK",
            "specifications": {"ukuran": "20x20cm", "harga_patokan": float(_to_decimal(25000, "patokan"))},
            "volatility_factor": 0.03,
        },
        {
            "id": "mat_partisi_gypsum",
            "name": "Partisi Gypsum 9mm Double",
            "unit": "m²",
            "category": "PARTISI",
            "specifications": {"tebal": "9mm", "tipe": "Double", "harga_patokan": float(_to_decimal(65000, "patokan"))},
            "volatility_factor": 0.04,
        },
        {
            "id": "mat_partisi_aluminium",
            "name": "Partisi Aluminium + Kaca",
            "unit": "m²",
            "category": "PARTISI",
            "specifications": {"bahan": "Aluminium+Kaca", "harga_patokan": float(_to_decimal(450000, "patokan"))},
            "volatility_factor": 0.06,
        },
        {
            "id": "mat_panel_wpc",
            "name": "Panel Dinding WPC",
            "unit": "m²",
            "category": "PANEL_DINDING",
            "specifications": {"bahan": "WPC", "harga_patokan": float(_to_decimal(165000, "patokan"))},
            "volatility_factor": 0.04,
        },
        {
            "id": "mat_batu_alam_andesit",
            "name": "Batu Alam Andesit Bakar",
            "unit": "m²",
            "category": "BATU_ALAM",
            "specifications": {"jenis": "Andesit", "finish": "Bakar", "harga_patokan": float(_to_decimal(350000, "patokan"))},
            "volatility_factor": 0.05,
        },
        {
            "id": "mat_batu_alam_palimanan",
            "name": "Batu Alam Palimanan",
            "unit": "m²",
            "category": "BATU_ALAM",
            "specifications": {"jenis": "Palimanan", "harga_patokan": float(_to_decimal(280000, "patokan"))},
            "volatility_factor": 0.05,
        },
        {
            "id": "mat_batu_alam_candi",
            "name": "Batu Alam Candi",
            "unit": "m²",
            "category": "BATU_ALAM",
            "specifications": {"jenis": "Candi", "harga_patokan": float(_to_decimal(320000, "patokan"))},
            "volatility_factor": 0.05,
        },
    ]

    # 1. GATEWAY SCHEMA VALIDATION
    try:
        validated_bundle = WallMaterialBundleDTO(items=raw_bundle_payload)
    except Exception as exc:
        logger.error("Gagal mengeksekusi otomatisasi seeder dinding partisi: Pelanggaran skema: %s", exc)
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
        logger.debug("Material dinding/partisi dimuat: %s", material_node_instance.id)

    logger.info(
        "Modul material pasangan batu dinding arsitektural dan sekat partisi sukses ditayangkan: %d master nodes terkunci.",
        len(validated_bundle.items),
    )
