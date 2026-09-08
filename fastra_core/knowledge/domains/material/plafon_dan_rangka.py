"""
fastra_core/knowledge/domains/material/plafon_dan_rangka.py

Modul pemuatan data material plafon dan rangka ke Knowledge Graph.
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


class CeilingMaterialCategory(str, enum.Enum):
    """Klasifikasi taksonomi resmi kelompok material plafon dan aksesoris rangka penggantung."""

    GYPSUM = "GYPSUM"
    GRC = "GRC"
    KALSIBOARD = "KALSIBOARD"
    PLAFON_PVC = "PLAFON_PVC"
    PLAFON_AKUSTIK = "PLAFON_AKUSTIK"
    RANGKA_HOLLOW = "RANGKA_HOLLOW"
    LIST_PLAFON = "LIST_PLAFON"


# ---------------------------------------------------------------------------
# Inbound DTOs – Pydantic Strict Gateway & Sanitization (Fail-Fast)
# ---------------------------------------------------------------------------
class GeneratedCeilingItemDTO(BaseModel):
    """DTO validasi ketat untuk mendaftar spesifikasi produk plafon dan penutup langit-langit."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, strict=False)

    id: str = Field(..., min_length=5, max_length=128, pattern=r"^mat_[a-z0-9_\\.\\-]+$")
    name: str = Field(..., min_length=2, max_length=256)
    unit: str = Field(..., min_length=1, max_length=16, pattern=r"^(lembar|m²|batang|m')$")
    category: CeilingMaterialCategory = Field(...)
    specifications: Dict[str, Any] = Field(default_factory=dict, max_length=50)
    volatility_factor: float = Field(default=0.0, ge=0.0, le=1.0, allow_inf_nan=False)

    @field_validator("specifications", mode="after")
    @classmethod
    def validate_specifications_payload(cls, value: Dict[str, Any]) -> Dict[str, Any]:
        """Memastikan harga_patokan tersedia dan bernilai positif."""
        if "harga_patokan" not in value:
            raise ValueError("Skema metadata spesifikasi plafon/rangka cacat: Wajib melampirkan parameter 'harga_patokan'.")
        try:
            float_val = float(value["harga_patokan"])
            if float_val <= 0.0:
                raise ValueError()
        except (ValueError, TypeError):
            raise ValueError("Nilai nominal 'harga_patokan' di dalam spesifikasi wajib bertipe numerik positif.")
        return value


class CeilingMaterialBundleDTO(BaseModel):
    """Bundel manifes penampung sekumpulan daftar komoditas produk gipsum, kalsiboard, dan hollow."""

    model_config = ConfigDict(extra="forbid", strict=False)

    items: List[GeneratedCeilingItemDTO] = Field(..., max_length=500)


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
# Core Seeding Layer – Pure Ceiling Generation Pipeline (QS-Safe)
# ---------------------------------------------------------------------------
def load_plafon_rangka(kg: KnowledgeGraph) -> None:
    """
    Membuat, memvalidasi, dan menyuntikkan manifes master material plafon ke KnowledgeGraph.
    ID menggunakan format mat_... (underscore) agar konsisten dengan sistem.
    """
    if not isinstance(kg, KnowledgeGraph):
        raise TypeError("Parameter masukan 'kg' wajib berupa instance orisinil dari kelas KnowledgeGraph.")

    # Kumpulan raw data benih komoditas material langit-langit sesuai spesifikasi teknis PUPR
    raw_bundle_payload: List[Dict[str, Any]] = [
        {
            "id": "mat_gypsum_9mm",
            "name": "Papan Gypsum 9mm",
            "unit": "lembar",
            "category": "GYPSUM",
            "specifications": {"tebal": "9mm", "harga_patokan": float(_to_decimal(65000, "patokan"))},
            "volatility_factor": 0.04,
        },
        {
            "id": "mat_gypsum_12mm",
            "name": "Papan Gypsum 12mm",
            "unit": "lembar",
            "category": "GYPSUM",
            "specifications": {"tebal": "12mm", "harga_patokan": float(_to_decimal(85000, "patokan"))},
            "volatility_factor": 0.04,
        },
        {
            "id": "mat_grc_board",
            "name": "Papan GRC Board",
            "unit": "lembar",
            "category": "GRC",
            "specifications": {"harga_patokan": float(_to_decimal(75000, "patokan"))},
            "volatility_factor": 0.03,
        },
        {
            "id": "mat_kalsiboard",
            "name": "Papan Kalsiboard",
            "unit": "lembar",
            "category": "KALSIBOARD",
            "specifications": {"harga_patokan": float(_to_decimal(55000, "patokan"))},
            "volatility_factor": 0.03,
        },
        {
            "id": "mat_plafon_pvc",
            "name": "Plafon PVC Panel",
            "unit": "m²",
            "category": "PLAFON_PVC",
            "specifications": {"harga_patokan": float(_to_decimal(45000, "patokan"))},
            "volatility_factor": 0.04,
        },
        {
            "id": "mat_plafon_akustik",
            "name": "Plafon Akustik Tile 60x60cm",
            "unit": "m²",
            "category": "PLAFON_AKUSTIK",
            "specifications": {"ukuran": "60x60", "harga_patokan": float(_to_decimal(95000, "patokan"))},
            "volatility_factor": 0.05,
        },
        {
            "id": "mat_hollow_2x4",
            "name": "Rangka Hollow Galvalum 2x4cm",
            "unit": "batang",
            "category": "RANGKA_HOLLOW",
            "specifications": {"ukuran": "2x4cm", "harga_patokan": float(_to_decimal(21500, "patokan"))},
            "volatility_factor": 0.05,
        },
        {
            "id": "mat_hollow_4x4",
            "name": "Rangka Hollow Galvalum 4x4cm",
            "unit": "batang",
            "category": "RANGKA_HOLLOW",
            "specifications": {"ukuran": "4x4cm", "harga_patokan": float(_to_decimal(38000, "patokan"))},
            "volatility_factor": 0.05,
        },
        {
            "id": "mat_list_gypsum",
            "name": "List Profil Gypsum 5cm",
            "unit": "m'",
            "category": "LIST_PLAFON",
            "specifications": {"lebar": "5cm", "harga_patokan": float(_to_decimal(8500, "patokan"))},
            "volatility_factor": 0.02,
        },
        {
            "id": "mat_list_gypsum_10cm",
            "name": "List Profil Gypsum 10cm",
            "unit": "m'",
            "category": "LIST_PLAFON",
            "specifications": {"lebar": "10cm", "harga_patokan": float(_to_decimal(12500, "patokan"))},
            "volatility_factor": 0.02,
        },
    ]

    # 1. GATEWAY SCHEMA VALIDATION
    try:
        validated_bundle = CeilingMaterialBundleDTO(items=raw_bundle_payload)
    except Exception as exc:
        logger.error("Gagal mengeksekusi otomatisasi seeder plafon rangka: Pelanggaran skema: %s", exc)
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
        logger.debug("Material plafon/rangka dimuat: %s", material_node_instance.id)

    logger.info(
        "Modul material penutup langit-langit gipsum arsitektural dan profil besi hollow sukses ditayangkan: %d master nodes terkunci.",
        len(validated_bundle.items),
    )
