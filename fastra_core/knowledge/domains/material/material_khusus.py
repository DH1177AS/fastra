"""
fastra_core/knowledge/domains/material/material_khusus.py

Modul pemuatan data material khusus (aluminium, kaca, HVAC, fasad) ke Knowledge Graph.
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


class SpecialMaterialCategory(str, enum.Enum):
    """Klasifikasi taksonomi resmi kelompok material aluminium, kaca, dan komponen utilitas MEP."""

    KUSEN_ALUMINIUM = "KUSEN_ALUMINIUM"
    PINTU_ALUMINIUM = "PINTU_ALUMINIUM"
    JENDELA_ALUMINIUM = "JENDELA_ALUMINIUM"
    KACA = "KACA"
    AC = "AC"
    VENTILASI = "VENTILASI"
    FASAD = "FASAD"


# ---------------------------------------------------------------------------
# Inbound DTOs – Pydantic Strict Gateway & Sanitization (Fail-Fast)
# ---------------------------------------------------------------------------
class GeneratedSpecialItemDTO(BaseModel):
    """DTO validasi ketat untuk mendaftar spesifikasi produk komponen khusus fasad dan HVAC."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, strict=False)

    id: str = Field(..., min_length=5, max_length=128, pattern=r"^mat_[a-z0-9_\\.\\-]+$")
    name: str = Field(..., min_length=2, max_length=256)
    unit: str = Field(..., min_length=1, max_length=16, pattern=r"^(m'|unit|m²)$")
    category: SpecialMaterialCategory = Field(...)
    specifications: Dict[str, Any] = Field(default_factory=dict, max_length=50)
    volatility_factor: float = Field(default=0.0, ge=0.0, le=1.0, allow_inf_nan=False)

    @field_validator("specifications", mode="after")
    @classmethod
    def validate_specifications_payload(cls, value: Dict[str, Any]) -> Dict[str, Any]:
        """Memastikan harga_patokan tersedia dan bernilai positif."""
        if "harga_patokan" not in value:
            raise ValueError("Skema metadata spesifikasi komponen khusus cacat: Wajib melampirkan parameter 'harga_patokan'.")
        try:
            float_val = float(value["harga_patokan"])
            if float_val <= 0.0:
                raise ValueError()
        except (ValueError, TypeError):
            raise ValueError("Nilai nominal 'harga_patokan' di dalam spesifikasi wajib bertipe numerik positif.")
        return value


class SpecialMaterialBundleDTO(BaseModel):
    """Bundel manifes penampung sekumpulan daftar komoditas produk aluminium, kaca, dan pendingin udara."""

    model_config = ConfigDict(extra="forbid", strict=False)

    items: List[GeneratedSpecialItemDTO] = Field(..., max_length=500)


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
# Core Seeding Layer – Pure Special Material Generation Pipeline (QS-Safe)
# ---------------------------------------------------------------------------
def load_material_khusus(kg: KnowledgeGraph) -> None:
    """
    Membuat, memvalidasi, dan menyuntikkan manifes master material khusus ke KnowledgeGraph.
    ID menggunakan format mat_... (underscore) agar konsisten dengan sistem.
    """
    if not isinstance(kg, KnowledgeGraph):
        raise TypeError("Parameter masukan 'kg' wajib berupa instance orisinil dari kelas KnowledgeGraph.")

    # Kumpulan raw data benih komoditas material khusus sesuai spesifikasi teknis PUPR
    raw_bundle_payload: List[Dict[str, Any]] = [
        {
            "id": "mat_kusen_aluminium_4in",
            "name": "Kusen Aluminium 4 inch Powder Coating",
            "unit": "m'",
            "category": "KUSEN_ALUMINIUM",
            "specifications": {"ukuran": '4"', "finish": "Powder Coating", "harga_patokan": float(_to_decimal(185000, "patokan"))},
            "volatility_factor": 0.05,
        },
        {
            "id": "mat_kusen_aluminium_3in",
            "name": "Kusen Aluminium 3 inch",
            "unit": "m'",
            "category": "KUSEN_ALUMINIUM",
            "specifications": {"ukuran": '3"', "harga_patokan": float(_to_decimal(145000, "patokan"))},
            "volatility_factor": 0.05,
        },
        {
            "id": "mat_pintu_aluminium",
            "name": "Pintu Aluminium + Kaca",
            "unit": "unit",
            "category": "PINTU_ALUMINIUM",
            "specifications": {"harga_patokan": float(_to_decimal(2200000, "patokan"))},
            "volatility_factor": 0.06,
        },
        {
            "id": "mat_jendela_aluminium",
            "name": "Jendela Aluminium + Kaca",
            "unit": "unit",
            "category": "JENDELA_ALUMINIUM",
            "specifications": {"harga_patokan": float(_to_decimal(1500000, "patokan"))},
            "volatility_factor": 0.06,
        },
        {
            "id": "mat_kaca_polos_5mm",
            "name": "Kaca Polos 5mm",
            "unit": "m²",
            "category": "KACA",
            "specifications": {"tebal": "5mm", "tipe": "Polos", "harga_patokan": float(_to_decimal(185000, "patokan"))},
            "volatility_factor": 0.04,
        },
        {
            "id": "mat_kaca_polos_8mm",
            "name": "Kaca Polos 8mm",
            "unit": "m²",
            "category": "KACA",
            "specifications": {"tebal": "8mm", "tipe": "Polos", "harga_patokan": float(_to_decimal(285000, "patokan"))},
            "volatility_factor": 0.04,
        },
        {
            "id": "mat_kaca_tempered_10mm",
            "name": "Kaca Tempered 10mm",
            "unit": "m²",
            "category": "KACA",
            "specifications": {"tebal": "10mm", "tipe": "Tempered", "harga_patokan": float(_to_decimal(450000, "patokan"))},
            "volatility_factor": 0.05,
        },
        {
            "id": "mat_kaca_tempered_12mm",
            "name": "Kaca Tempered 12mm",
            "unit": "m²",
            "category": "KACA",
            "specifications": {"tebal": "12mm", "tipe": "Tempered", "harga_patokan": float(_to_decimal(550000, "patokan"))},
            "volatility_factor": 0.05,
        },
        {
            "id": "mat_ac_split_1pk",
            "name": "AC Split 1 PK Daikin",
            "unit": "unit",
            "category": "AC",
            "specifications": {"tipe": "Split", "pk": "1", "merek": "Daikin", "harga_patokan": float(_to_decimal(4830000, "patokan"))},
            "volatility_factor": 0.08,
        },
        {
            "id": "mat_ac_split_2pk",
            "name": "AC Split 2 PK Daikin",
            "unit": "unit",
            "category": "AC",
            "specifications": {"tipe": "Split", "pk": "2", "merek": "Daikin", "harga_patokan": float(_to_decimal(8280000, "patokan"))},
            "volatility_factor": 0.08,
        },
        {
            "id": "mat_ac_cassette_3pk",
            "name": "AC Cassette 3 PK",
            "unit": "unit",
            "category": "AC",
            "specifications": {"tipe": "Cassette", "pk": "3", "harga_patokan": float(_to_decimal(12500000, "patokan"))},
            "volatility_factor": 0.08,
        },
        {
            "id": "mat_exhaust_fan_10in",
            "name": "Exhaust Fan 10 inch",
            "unit": "unit",
            "category": "VENTILASI",
            "specifications": {"ukuran": '10"', "harga_patokan": float(_to_decimal(350000, "patokan"))},
            "volatility_factor": 0.04,
        },
        {
            "id": "mat_exhaust_fan_12in",
            "name": "Exhaust Fan 12 inch",
            "unit": "unit",
            "category": "VENTILASI",
            "specifications": {"ukuran": '12"', "harga_patokan": float(_to_decimal(450000, "patokan"))},
            "volatility_factor": 0.04,
        },
        {
            "id": "mat_acp_panel",
            "name": "ACP (Aluminium Composite Panel)",
            "unit": "m²",
            "category": "FASAD",
            "specifications": {"bahan": "ACP", "harga_patokan": float(_to_decimal(285000, "patokan"))},
            "volatility_factor": 0.07,
        },
        {
            "id": "mat_curtain_wall",
            "name": "Curtain Wall Aluminium + Kaca",
            "unit": "m²",
            "category": "FASAD",
            "specifications": {"bahan": "Aluminium+Kaca", "harga_patokan": float(_to_decimal(850000, "patokan"))},
            "volatility_factor": 0.08,
        },
    ]

    # 1. GATEWAY SCHEMA VALIDATION
    try:
        validated_bundle = SpecialMaterialBundleDTO(items=raw_bundle_payload)
    except Exception as exc:
        logger.error("Gagal mengeksekusi otomatisasi seeder material khusus: Pelanggaran skema: %s", exc)
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
        logger.debug("Material khusus dimuat: %s", material_node_instance.id)

    logger.info(
        "Modul material spesifik penampang fasad aluminium, kaca, dan utilitas HVAC sukses ditayangkan: %d master nodes terkunci.",
        len(validated_bundle.items),
    )
