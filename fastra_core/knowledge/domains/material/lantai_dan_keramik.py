"""
fastra_core/knowledge/domains/material/lantai_dan_keramik.py

Modul pemuatan data material penutup lantai dan keramik ke Knowledge Graph.
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


class FlooringMaterialCategory(str, enum.Enum):
    """Klasifikasi taksonomi resmi kelompok material penutup lantai dan pelapis dinding."""

    KERAMIK = "KERAMIK"
    KERAMIK_DINDING = "KERAMIK_DINDING"
    GRANIT = "GRANIT"
    MARMER = "MARMER"
    HOMOGENEOUS = "HOMOGENEOUS"
    VINYL = "VINYL"
    KARPET = "KARPET"
    PARKET = "PARKET"
    SPC = "SPC"


# ---------------------------------------------------------------------------
# Inbound DTOs – Pydantic Strict Gateway & Sanitization (Fail-Fast)
# ---------------------------------------------------------------------------
class GeneratedFlooringItemDTO(BaseModel):
    """DTO validasi ketat untuk mendaftar spesifikasi produk penutup lantai arsitektural."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, strict=False)

    id: str = Field(..., min_length=5, max_length=128, pattern=r"^mat_[a-z0-9_\\.\\-]+$")
    name: str = Field(..., min_length=2, max_length=256)
    unit: str = Field(..., min_length=2, max_length=16, pattern=r"^(dus|m²)$")
    category: FlooringMaterialCategory = Field(...)
    specifications: Dict[str, Any] = Field(default_factory=dict, max_length=50)
    volatility_factor: float = Field(default=0.0, ge=0.0, le=1.0, allow_inf_nan=False)

    @field_validator("specifications", mode="after")
    @classmethod
    def validate_specifications_payload(cls, value: Dict[str, Any]) -> Dict[str, Any]:
        """Memastikan harga_patokan tersedia dan bernilai positif."""
        if "harga_patokan" not in value:
            raise ValueError("Skema metadata spesifikasi penutup lantai cacat: Wajib melampirkan parameter 'harga_patokan'.")
        try:
            float_val = float(value["harga_patokan"])
            if float_val <= 0.0:
                raise ValueError()
        except (ValueError, TypeError):
            raise ValueError("Nilai nominal 'harga_patokan' di dalam spesifikasi wajib bertipe numerik positif.")
        return value


class FlooringMaterialBundleDTO(BaseModel):
    """Bundel manifes penampung sekumpulan daftar komoditas produk keramik dan penutup lantai."""

    model_config = ConfigDict(extra="forbid", strict=False)

    items: List[GeneratedFlooringItemDTO] = Field(..., max_length=500)


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
# Core Seeding Layer – Pure Flooring Generation Pipeline (QS-Safe)
# ---------------------------------------------------------------------------
def load_lantai_keramik(kg: KnowledgeGraph) -> None:
    """
    Membuat, memvalidasi, dan menyuntikkan manifes master material lantai ke KnowledgeGraph.
    ID menggunakan format mat_... (underscore) agar konsisten dengan sistem.
    """
    if not isinstance(kg, KnowledgeGraph):
        raise TypeError("Parameter masukan 'kg' wajib berupa instance orisinil dari kelas KnowledgeGraph.")

    # Kumpulan raw data benih komoditas material penutup lantai sesuai spesifikasi teknis PUPR
    raw_bundle_payload: List[Dict[str, Any]] = [
        {
            "id": "mat_keramik_40x40_kw1",
            "name": "Keramik Lantai 40x40 KW1",
            "unit": "dus",
            "category": "KERAMIK",
            "specifications": {"ukuran": "40x40", "kw": "1", "harga_patokan": float(_to_decimal(62000, "patokan"))},
            "volatility_factor": 0.03,
        },
        {
            "id": "mat_keramik_50x50_kw1",
            "name": "Keramik Lantai 50x50 KW1",
            "unit": "dus",
            "category": "KERAMIK",
            "specifications": {"ukuran": "50x50", "kw": "1", "harga_patokan": float(_to_decimal(85000, "patokan"))},
            "volatility_factor": 0.03,
        },
        {
            "id": "mat_keramik_60x60_kw1",
            "name": "Keramik Lantai 60x60 KW1",
            "unit": "dus",
            "category": "KERAMIK",
            "specifications": {"ukuran": "60x60", "kw": "1", "harga_patokan": float(_to_decimal(120000, "patokan"))},
            "volatility_factor": 0.03,
        },
        {
            "id": "mat_keramik_dinding_25x40",
            "name": "Keramik Dinding 25x40cm",
            "unit": "dus",
            "category": "KERAMIK_DINDING",
            "specifications": {"ukuran": "25x40", "harga_patokan": float(_to_decimal(48000, "patokan"))},
            "volatility_factor": 0.03,
        },
        {
            "id": "mat_keramik_dinding_30x60",
            "name": "Keramik Dinding 30x60cm Motif Marmer",
            "unit": "dus",
            "category": "KERAMIK_DINDING",
            "specifications": {"ukuran": "30x60", "motif": "Marmer", "harga_patokan": float(_to_decimal(65000, "patokan"))},
            "volatility_factor": 0.03,
        },
        {
            "id": "mat_granit_60x60",
            "name": "Granit Tile 60x60cm",
            "unit": "dus",
            "category": "GRANIT",
            "specifications": {"ukuran": "60x60", "harga_patokan": float(_to_decimal(165000, "patokan"))},
            "volatility_factor": 0.04,
        },
        {
            "id": "mat_granit_80x80",
            "name": "Granit Tile 80x80cm",
            "unit": "dus",
            "category": "GRANIT",
            "specifications": {"ukuran": "80x80", "harga_patokan": float(_to_decimal(285000, "patokan"))},
            "volatility_factor": 0.04,
        },
        {
            "id": "mat_granit_100x100",
            "name": "Granit Tile 100x100cm",
            "unit": "dus",
            "category": "GRANIT",
            "specifications": {"ukuran": "100x100", "harga_patokan": float(_to_decimal(450000, "patokan"))},
            "volatility_factor": 0.04,
        },
        {
            "id": "mat_marmer_lokal_60x60",
            "name": "Marmer Lokal 60x60cm",
            "unit": "dus",
            "category": "MARMER",
            "specifications": {"ukuran": "60x60", "harga_patokan": float(_to_decimal(380000, "patokan"))},
            "volatility_factor": 0.05,
        },
        {
            "id": "mat_homogeneous_60x60",
            "name": "Homogeneous Tile 60x60 KW1",
            "unit": "dus",
            "category": "HOMOGENEOUS",
            "specifications": {"ukuran": "60x60", "harga_patokan": float(_to_decimal(145000, "patokan"))},
            "volatility_factor": 0.04,
        },
        {
            "id": "mat_vinyl_plank",
            "name": "Vinyl Plank Click System",
            "unit": "m²",
            "category": "VINYL",
            "specifications": {"tipe": "Click", "harga_patokan": float(_to_decimal(85000, "patokan"))},
            "volatility_factor": 0.03,
        },
        {
            "id": "mat_vinyl_sheet",
            "name": "Vinyl Sheet 2mm",
            "unit": "m²",
            "category": "VINYL",
            "specifications": {"tebal": "2mm", "harga_patokan": float(_to_decimal(55000, "patokan"))},
            "volatility_factor": 0.03,
        },
        {
            "id": "mat_karpet_tile",
            "name": "Karpet Tile 50x50cm",
            "unit": "m²",
            "category": "KARPET",
            "specifications": {"ukuran": "50x50", "harga_patokan": float(_to_decimal(95000, "patokan"))},
            "volatility_factor": 0.02,
        },
        {
            "id": "mat_parket_engineered",
            "name": "Parket Engineered Oak 15mm",
            "unit": "m²",
            "category": "PARKET",
            "specifications": {"kayu": "Oak", "tebal": "15mm", "harga_patokan": float(_to_decimal(285000, "patokan"))},
            "volatility_factor": 0.04,
        },
        {
            "id": "mat_lantai_spc",
            "name": "Lantai SPC (Stone Plastic Composite)",
            "unit": "m²",
            "category": "SPC",
            "specifications": {"harga_patokan": float(_to_decimal(125000, "patokan"))},
            "volatility_factor": 0.03,
        },
    ]

    # 1. GATEWAY SCHEMA VALIDATION
    try:
        validated_bundle = FlooringMaterialBundleDTO(items=raw_bundle_payload)
    except Exception as exc:
        logger.error("Gagal mengeksekusi otomatisasi seeder lantai keramik: Pelanggaran skema: %s", exc)
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
        logger.debug("Material lantai/keramik dimuat: %s", material_node_instance.id)

    logger.info(
        "Modul material penutup lantai ubin keramik dan lantai komposit kayu sukses ditayangkan: %d master nodes terkunci.",
        len(validated_bundle.items),
    )
