"""
fastra_core/knowledge/domains/material/kayu_dan_plywood.py

Modul pemuatan data material kayu dan plywood ke Knowledge Graph.
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


class TimberMaterialCategory(str, enum.Enum):
    """Klasifikasi taksonomi resmi kelompok material kayu gelondongan/olahan dan papan lapis."""

    KAYU = "KAYU"
    PLYWOOD = "PLYWOOD"


# ---------------------------------------------------------------------------
# Inbound DTOs – Pydantic Strict Gateway & Sanitization (Fail-Fast)
# ---------------------------------------------------------------------------
class GeneratedTimberItemDTO(BaseModel):
    """DTO validasi ketat untuk mendaftar spesifikasi produk perkayuan dan tripleks."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, strict=False)

    id: str = Field(..., min_length=5, max_length=128, pattern=r"^mat_[a-z0-9_\\.\\-]+$")
    name: str = Field(..., min_length=2, max_length=256)
    unit: str = Field(..., min_length=2, max_length=16, pattern=r"^(m³|lembar)$")
    category: TimberMaterialCategory = Field(...)
    specifications: Dict[str, Any] = Field(default_factory=dict, max_length=50)
    volatility_factor: float = Field(default=0.0, ge=0.0, le=1.0, allow_inf_nan=False)

    @field_validator("specifications", mode="after")
    @classmethod
    def validate_specifications_payload(cls, value: Dict[str, Any]) -> Dict[str, Any]:
        """Memastikan harga_patokan tersedia dan bernilai positif."""
        if "harga_patokan" not in value:
            raise ValueError("Skema metadata spesifikasi perkayuan cacat: Wajib melampirkan parameter 'harga_patokan'.")
        try:
            float_val = float(value["harga_patokan"])
            if float_val <= 0.0:
                raise ValueError()
        except (ValueError, TypeError):
            raise ValueError("Nilai nominal 'harga_patokan' di dalam spesifikasi wajib bertipe numerik positif.")
        return value


class TimberMaterialBundleDTO(BaseModel):
    """Bundel manifes penampung sekumpulan daftar komoditas produk kayu dan tripleks bekisting."""

    model_config = ConfigDict(extra="forbid", strict=False)

    items: List[GeneratedTimberItemDTO] = Field(..., max_length=500)


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
# Core Seeding Layer – Pure Timber Generation Pipeline (QS-Safe)
# ---------------------------------------------------------------------------
def load_kayu_plywood(kg: KnowledgeGraph) -> None:
    """
    Membuat, memvalidasi, dan menyuntikkan manifes master material kayu ke KnowledgeGraph.
    ID menggunakan format mat_... (underscore) agar konsisten dengan sistem.
    """
    if not isinstance(kg, KnowledgeGraph):
        raise TypeError("Parameter masukan 'kg' wajib berupa instance orisinil dari kelas KnowledgeGraph.")

    # Kumpulan raw data benih komoditas material perkayuan sesuai spesifikasi teknis PUPR
    raw_bundle_payload: List[Dict[str, Any]] = [
        {
            "id": "mat_kayu_meranti_balok",
            "name": "Kayu Meranti Balok",
            "unit": "m³",
            "category": "KAYU",
            "specifications": {"jenis": "Meranti", "bentuk": "Balok", "kelas": "II", "harga_patokan": float(_to_decimal(3200000, "patokan"))},
            "volatility_factor": 0.06,
        },
        {
            "id": "mat_kayu_meranti_papan",
            "name": "Kayu Meranti Papan",
            "unit": "m³",
            "category": "KAYU",
            "specifications": {"jenis": "Meranti", "bentuk": "Papan", "kelas": "II", "harga_patokan": float(_to_decimal(3360000, "patokan"))},
            "volatility_factor": 0.06,
        },
        {
            "id": "mat_kayu_kamper_balok",
            "name": "Kayu Kamper Balok",
            "unit": "m³",
            "category": "KAYU",
            "specifications": {"jenis": "Kamper", "bentuk": "Balok", "kelas": "II", "harga_patokan": float(_to_decimal(4500000, "patokan"))},
            "volatility_factor": 0.05,
        },
        {
            "id": "mat_kayu_kamper_papan",
            "name": "Kayu Kamper Papan",
            "unit": "m³",
            "category": "KAYU",
            "specifications": {"jenis": "Kamper", "bentuk": "Papan", "kelas": "II", "harga_patokan": float(_to_decimal(4725000, "patokan"))},
            "volatility_factor": 0.05,
        },
        {
            "id": "mat_kayu_jati_balok",
            "name": "Kayu Jati Balok",
            "unit": "m³",
            "category": "KAYU",
            "specifications": {"jenis": "Jati", "bentuk": "Balok", "kelas": "I", "harga_patokan": float(_to_decimal(12500000, "patokan"))},
            "volatility_factor": 0.04,
        },
        {
            "id": "mat_kayu_jati_papan",
            "name": "Kayu Jati Papan",
            "unit": "m³",
            "category": "KAYU",
            "specifications": {"jenis": "Jati", "bentuk": "Papan", "kelas": "I", "harga_patokan": float(_to_decimal(13125000, "patokan"))},
            "volatility_factor": 0.04,
        },
        {
            "id": "mat_kayu_borneo_balok",
            "name": "Kayu Borneo Balok",
            "unit": "m³",
            "category": "KAYU",
            "specifications": {"jenis": "Borneo", "bentuk": "Balok", "kelas": "III", "harga_patokan": float(_to_decimal(2600000, "patokan"))},
            "volatility_factor": 0.08,
        },
        {
            "id": "mat_kayu_borneo_papan",
            "name": "Kayu Borneo Papan",
            "unit": "m³",
            "category": "KAYU",
            "specifications": {"jenis": "Borneo", "bentuk": "Papan", "kelas": "III", "harga_patokan": float(_to_decimal(2730000, "patokan"))},
            "volatility_factor": 0.08,
        },
        {
            "id": "mat_kayu_bengkirai_balok",
            "name": "Kayu Bengkirai Balok",
            "unit": "m³",
            "category": "KAYU",
            "specifications": {"jenis": "Bengkirai", "bentuk": "Balok", "kelas": "I", "harga_patokan": float(_to_decimal(5800000, "patokan"))},
            "volatility_factor": 0.05,
        },
        {
            "id": "mat_plywood_4mm",
            "name": "Plywood 4mm",
            "unit": "lembar",
            "category": "PLYWOOD",
            "specifications": {"tebal": "4mm", "harga_patokan": float(_to_decimal(65000, "patokan"))},
            "volatility_factor": 0.04,
        },
        {
            "id": "mat_plywood_6mm",
            "name": "Plywood 6mm",
            "unit": "lembar",
            "category": "PLYWOOD",
            "specifications": {"tebal": "6mm", "harga_patokan": float(_to_decimal(85000, "patokan"))},
            "volatility_factor": 0.04,
        },
        {
            "id": "mat_plywood_9mm",
            "name": "Plywood 9mm",
            "unit": "lembar",
            "category": "PLYWOOD",
            "specifications": {"tebal": "9mm", "harga_patokan": float(_to_decimal(125000, "patokan"))},
            "volatility_factor": 0.04,
        },
        {
            "id": "mat_plywood_12mm",
            "name": "Plywood 12mm",
            "unit": "lembar",
            "category": "PLYWOOD",
            "specifications": {"tebal": "12mm", "harga_patokan": float(_to_decimal(165000, "patokan"))},
            "volatility_factor": 0.04,
        },
        {
            "id": "mat_plywood_15mm",
            "name": "Plywood 15mm",
            "unit": "lembar",
            "category": "PLYWOOD",
            "specifications": {"tebal": "15mm", "harga_patokan": float(_to_decimal(205000, "patokan"))},
            "volatility_factor": 0.04,
        },
        {
            "id": "mat_plywood_18mm",
            "name": "Plywood 18mm",
            "unit": "lembar",
            "category": "PLYWOOD",
            "specifications": {"tebal": "18mm", "harga_patokan": float(_to_decimal(245000, "patokan"))},
            "volatility_factor": 0.04,
        },
    ]

    # 1. GATEWAY SCHEMA VALIDATION
    try:
        validated_bundle = TimberMaterialBundleDTO(items=raw_bundle_payload)
    except Exception as exc:
        logger.error("Gagal mengeksekusi otomatisasi seeder kayu plywood: Pelanggaran skema: %s", exc)
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
        logger.debug("Material kayu/plywood dimuat: %s", material_node_instance.id)

    logger.info(
        "Modul material perkayuan dan papan tripleks bekisting cetakan sukses ditayangkan: %d master nodes terkunci.",
        len(validated_bundle.items),
    )
