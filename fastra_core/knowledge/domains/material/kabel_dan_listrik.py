"""
fastra_core/knowledge/domains/material/kabel_dan_listrik.py

Modul pemuatan data material kabel dan perlengkapan listrik ke Knowledge Graph.
Seluruh ID menggunakan format mat_... (underscore) agar konsisten dengan sistem.
"""

from __future__ import annotations

import enum
import logging
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from fastra_core.knowledge.graph import KnowledgeGraph
from fastra_core.knowledge.nodes import MaterialNode

logger = logging.getLogger("fastra.knowledge")


class ElectricalMaterialCategory(str, enum.Enum):
    """Klasifikasi taksonomi komponen kelistrikan."""

    KABEL = "KABEL"
    MCB = "MCB"
    SAKLAR = "SAKLAR"
    STOP_KONTAK = "STOP_KONTAK"
    KONDUIT = "KONDUIT"
    BOX_SEKRING = "BOX_SEKRING"
    PANEL = "PANEL"
    LAMPU = "LAMPU"
    KABEL_DATA = "KABEL_DATA"


# ---------------------------------------------------------------------------
# Inbound DTOs – Pydantic Strict Gateway & Sanitization (Fail-Fast)
# ---------------------------------------------------------------------------
class ElectricalMaterialItemDTO(BaseModel):
    """DTO validasi ketat untuk mendaftar spesifikasi produk kabel dan listrik."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, strict=False)

    id: str = Field(..., min_length=5, max_length=128, pattern=r"^mat_[a-z0-9_\\.\\-]+$")
    name: str = Field(..., min_length=2, max_length=256)
    unit: str = Field(..., min_length=1, max_length=16, pattern=r"^(m|buah|batang|unit)$")
    category: ElectricalMaterialCategory = Field(...)
    specifications: Dict[str, Any] = Field(default_factory=dict, max_length=50)
    volatility_factor: float = Field(default=0.0, ge=0.0, le=1.0, allow_inf_nan=False)

    @field_validator("specifications", mode="after")
    @classmethod
    def validate_specifications_payload(cls, value: Dict[str, Any]) -> Dict[str, Any]:
        """Memastikan harga_patokan tersedia dan bernilai positif."""
        if "harga_patokan" not in value:
            raise ValueError("Skema metadata spesifikasi material listrik cacat: Wajib melampirkan parameter 'harga_patokan'.")
        try:
            float_val = float(value["harga_patokan"])
            if float_val <= 0.0:
                raise ValueError()
        except (ValueError, TypeError):
            raise ValueError("Nilai nominal 'harga_patokan' di dalam spesifikasi wajib bertipe numerik positif.")
        return value


class ElectricalMaterialBundleDTO(BaseModel):
    """Bundel manifes penampung sekumpulan daftar komoditas kabel dan listrik."""

    model_config = ConfigDict(extra="forbid", strict=False)

    items: List[ElectricalMaterialItemDTO] = Field(..., max_length=100)


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
# Core Seeding Layer – Pure Electrical Generation Pipeline (QS-Safe)
# ---------------------------------------------------------------------------
def load_kabel_listrik(kg: KnowledgeGraph) -> None:
    """
    Membuat, memvalidasi, dan menyuntikkan manifes master material kabel dan listrik.
    ID menggunakan format mat_... (underscore) agar konsisten dengan sistem.
    """
    if not isinstance(kg, KnowledgeGraph):
        raise TypeError("Parameter masukan 'kg' wajib berupa instance orisinil dari kelas KnowledgeGraph.")

    # Kumpulan raw data benih komoditas material kelistrikan sesuai spesifikasi teknis PUPR
    raw_bundle_payload: List[Dict[str, Any]] = [
        {
            "id": "mat_kabel_nym_2x1_5",
            "name": "Kabel NYM 2x1.5mm²",
            "unit": "m",
            "category": "KABEL",
            "specifications": {"tipe": "NYM 2x1.5", "harga_patokan": float(_to_decimal(12000, "patokan"))},
            "volatility_factor": 0.05,
        },
        {
            "id": "mat_kabel_nym_2x2_5",
            "name": "Kabel NYM 2x2.5mm²",
            "unit": "m",
            "category": "KABEL",
            "specifications": {"tipe": "NYM 2x2.5", "harga_patokan": float(_to_decimal(18000, "patokan"))},
            "volatility_factor": 0.05,
        },
        {
            "id": "mat_kabel_nym_3x2_5",
            "name": "Kabel NYM 3x2.5mm²",
            "unit": "m",
            "category": "KABEL",
            "specifications": {"tipe": "NYM 3x2.5", "harga_patokan": float(_to_decimal(25000, "patokan"))},
            "volatility_factor": 0.05,
        },
        {
            "id": "mat_kabel_nym_4x4",
            "name": "Kabel NYM 4x4mm²",
            "unit": "m",
            "category": "KABEL",
            "specifications": {"tipe": "NYM 4x4", "harga_patokan": float(_to_decimal(42000, "patokan"))},
            "volatility_factor": 0.05,
        },
        {
            "id": "mat_kabel_nyy_4x10",
            "name": "Kabel NYY 4x10mm²",
            "unit": "m",
            "category": "KABEL",
            "specifications": {"tipe": "NYY 4x10", "harga_patokan": float(_to_decimal(85000, "patokan"))},
            "volatility_factor": 0.05,
        },
        {
            "id": "mat_kabel_nyy_4x16",
            "name": "Kabel NYY 4x16mm²",
            "unit": "m",
            "category": "KABEL",
            "specifications": {"tipe": "NYY 4x16", "harga_patokan": float(_to_decimal(125000, "patokan"))},
            "volatility_factor": 0.05,
        },
        {
            "id": "mat_mcb_6a",
            "name": "MCB 6A Schneider",
            "unit": "buah",
            "category": "MCB",
            "specifications": {"ampere": "6A", "merek": "Schneider", "harga_patokan": float(_to_decimal(58000, "patokan"))},
            "volatility_factor": 0.03,
        },
        {
            "id": "mat_mcb_10a",
            "name": "MCB 10A Schneider",
            "unit": "buah",
            "category": "MCB",
            "specifications": {"ampere": "10A", "merek": "Schneider", "harga_patokan": float(_to_decimal(68000, "patokan"))},
            "volatility_factor": 0.03,
        },
        {
            "id": "mat_mcb_16a",
            "name": "MCB 16A Schneider",
            "unit": "buah",
            "category": "MCB",
            "specifications": {"ampere": "16A", "merek": "Schneider", "harga_patokan": float(_to_decimal(72000, "patokan"))},
            "volatility_factor": 0.03,
        },
        {
            "id": "mat_mcb_20a",
            "name": "MCB 20A Schneider",
            "unit": "buah",
            "category": "MCB",
            "specifications": {"ampere": "20A", "merek": "Schneider", "harga_patokan": float(_to_decimal(76000, "patokan"))},
            "volatility_factor": 0.03,
        },
        {
            "id": "mat_saklar_tunggal",
            "name": "Saklar Tunggal Panasonic",
            "unit": "buah",
            "category": "SAKLAR",
            "specifications": {"tipe": "Tunggal", "merek": "Panasonic", "harga_patokan": float(_to_decimal(22000, "patokan"))},
            "volatility_factor": 0.02,
        },
        {
            "id": "mat_saklar_ganda",
            "name": "Saklar Ganda Panasonic",
            "unit": "buah",
            "category": "SAKLAR",
            "specifications": {"tipe": "Ganda", "merek": "Panasonic", "harga_patokan": float(_to_decimal(29000, "patokan"))},
            "volatility_factor": 0.02,
        },
        {
            "id": "mat_stop_kontak",
            "name": "Stop Kontak Panasonic",
            "unit": "buah",
            "category": "STOP_KONTAK",
            "specifications": {"merek": "Panasonic", "harga_patokan": float(_to_decimal(26000, "patokan"))},
            "volatility_factor": 0.02,
        },
        {
            "id": "mat_pipa_konduit_20mm",
            "name": "Pipa Konduit PVC 20mm",
            "unit": "batang",
            "category": "KONDUIT",
            "specifications": {"diameter": "20mm", "harga_patokan": float(_to_decimal(12000, "patokan"))},
            "volatility_factor": 0.03,
        },
        {
            "id": "mat_box_sekring",
            "name": "Box Sekring 4 Group",
            "unit": "unit",
            "category": "BOX_SEKRING",
            "specifications": {"group": 4, "harga_patokan": float(_to_decimal(185000, "patokan"))},
            "volatility_factor": 0.03,
        },
        {
            "id": "mat_panel_lvmdp",
            "name": "Panel LVMDP 100A",
            "unit": "unit",
            "category": "PANEL",
            "specifications": {"kapasitas": "100A", "harga_patokan": float(_to_decimal(2500000, "patokan"))},
            "volatility_factor": 0.04,
        },
        {
            "id": "mat_lampu_led_9w",
            "name": "Lampu LED Bulb 9W",
            "unit": "buah",
            "category": "LAMPU",
            "specifications": {"daya": "9W", "harga_patokan": float(_to_decimal(45000, "patokan"))},
            "volatility_factor": 0.03,
        },
        {
            "id": "mat_lampu_led_18w",
            "name": "Lampu LED Bulb 18W",
            "unit": "buah",
            "category": "LAMPU",
            "specifications": {"daya": "18W", "harga_patokan": float(_to_decimal(95000, "patokan"))},
            "volatility_factor": 0.03,
        },
        {
            "id": "mat_downlight_6w",
            "name": "Downlight LED 6W",
            "unit": "buah",
            "category": "LAMPU",
            "specifications": {"tipe": "Downlight", "daya": "6W", "harga_patokan": float(_to_decimal(55000, "patokan"))},
            "volatility_factor": 0.03,
        },
        {
            "id": "mat_kabel_lan_cat6",
            "name": "Kabel LAN Cat6",
            "unit": "m",
            "category": "KABEL_DATA",
            "specifications": {"tipe": "Cat6", "harga_patokan": float(_to_decimal(8500, "patokan"))},
            "volatility_factor": 0.03,
        },
    ]

    # 1. GATEWAY SCHEMA VALIDATION
    try:
        validated_bundle = ElectricalMaterialBundleDTO(items=raw_bundle_payload)
    except Exception as exc:
        logger.error("Gagal mengeksekusi otomatisasi seeder kabel listrik: Pelanggaran skema: %s", exc)
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
        logger.debug("Material kabel/listrik dimuat: %s", material_node_instance.id)

    logger.info(
        "Modul material kabel dan perlengkapan listrik sukses ditayangkan: %d master nodes terkunci.",
        len(validated_bundle.items),
    )
