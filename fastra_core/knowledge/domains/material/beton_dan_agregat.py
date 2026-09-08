"""
fastra_core/knowledge/domains/material/beton_dan_agregat.py

Modul pemuatan data material beton ready mix dan agregat ke Knowledge Graph.
Seluruh ID menggunakan format mat_... (underscore) agar konsisten dengan sistem.
"""

from __future__ import annotations

import enum
import logging
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Tuple

from pydantic import BaseModel, ConfigDict, Field, field_validator

from fastra_core.knowledge.graph import KnowledgeGraph
from fastra_core.knowledge.nodes import MaterialNode

logger = logging.getLogger("fastra.knowledge")


class ConcreteMaterialCategory(str, enum.Enum):
    """Klasifikasi taksonomi resmi kelompok beton ready mix dan batuan agregat."""

    BETON_READY_MIX = "BETON_READY_MIX"
    AGREGAT = "AGREGAT"


# ---------------------------------------------------------------------------
# Inbound DTOs – Pydantic Strict Gateway & Sanitization (Fail-Fast)
# ---------------------------------------------------------------------------
class GeneratedConcreteItemDTO(BaseModel):
    """DTO validasi ketat untuk mendaftar spesifikasi produk beton dan batuan."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, strict=False)

    id: str = Field(
        ...,
        min_length=5,
        max_length=128,
        pattern=r"^mat_[a-z0-9_\\.\\-]+$",
    )
    name: str = Field(..., min_length=2, max_length=256)
    unit: str = Field(..., min_length=2, max_length=16, pattern=r"^m³$")
    category: ConcreteMaterialCategory = Field(...)
    specifications: Dict[str, Any] = Field(default_factory=dict, max_length=50)
    volatility_factor: float = Field(default=0.0, ge=0.0, le=1.0, allow_inf_nan=False)

    @field_validator("specifications", mode="after")
    @classmethod
    def validate_specifications_payload(cls, value: Dict[str, Any]) -> Dict[str, Any]:
        """Memastikan harga_patokan tersedia dan bernilai positif."""
        if "harga_patokan" not in value:
            raise ValueError("Skema metadata spesifikasi beton/agregat cacat: Wajib melampirkan parameter 'harga_patokan'.")
        try:
            float_val = float(value["harga_patokan"])
            if float_val <= 0.0:
                raise ValueError()
        except (ValueError, TypeError):
            raise ValueError("Nilai nominal 'harga_patokan' di dalam spesifikasi wajib bertipe numerik positif.")
        return value


class ConcreteMaterialBundleDTO(BaseModel):
    """Bundel manifes penampung sekumpulan daftar komoditas beton dan batuan agregat."""

    model_config = ConfigDict(extra="forbid", strict=False)

    items: List[GeneratedConcreteItemDTO] = Field(..., max_length=500)


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
# Core Seeding Layer – Pure Concrete Generation Pipeline (QS-Safe)
# ---------------------------------------------------------------------------
def load_beton_agregat(kg: KnowledgeGraph) -> None:
    """
    Membuat, memvalidasi, dan menyuntikkan manifes master material beton ready-mix ke KnowledgeGraph.
    ID menggunakan format mat_... (underscore) agar konsisten dengan sistem.
    """
    if not isinstance(kg, KnowledgeGraph):
        raise TypeError("Parameter masukan 'kg' wajib berupa instance orisinil dari kelas KnowledgeGraph.")

    raw_bundle_payload: List[Dict[str, Any]] = []

    # Daftar produsen / vendor ready-mix berskala nasional
    suppliers: List[str] = ["Holcim", "SCG", "Adhimix", "Pionir Beton"]

    # Matriks mutu beton karakteristik, kuat tekan ekuivalen (MPa), dan harga dasar
    mutu_list: List[Tuple[str, str, float]] = [
        ("K-175", "14.5 MPa", 820000.0),
        ("K-225", "18.6 MPa", 890000.0),
        ("K-250", "20.7 MPa", 930000.0),
        ("K-275", "22.6 MPa", 960000.0),
        ("K-300", "24.9 MPa", 990000.0),
        ("K-350", "29.0 MPa", 1080000.0),
    ]

    # 1. Kombinasi Mutu Beton dan Produsen Vendor
    for supplier in suppliers:
        supplier_slug = supplier.lower().replace(' ', '_')
        for mutu, fc, harga in mutu_list:
            mutu_slug = mutu.lower()
            harga_dec = _to_decimal(harga, f"beton_{mutu_slug}_{supplier_slug}")

            raw_bundle_payload.append({
                "id": f"mat_beton_{mutu_slug}_{supplier_slug}",
                "name": f"Beton Ready Mix {mutu} (fc' {fc}) — {supplier}",
                "unit": "m³",
                "category": "BETON_READY_MIX",
                "specifications": {
                    "supplier": supplier,
                    "mutu": mutu,
                    "fc": fc,
                    "slump": "10-12 cm",
                    "harga_patokan": float(harga_dec),
                    "standar": "SNI 2847:2019",
                },
                "volatility_factor": 0.05,
            })

    # 2. Kelompok Batuan Agregat Kasar dan Halus (Bahan Pengisi)
    agregat_presets: List[Tuple[str, str, float]] = [
        ("Pasir Beton", "m³", 280000.0),
        ("Pasir Pasang", "m³", 240000.0),
        ("Pasir Urug", "m³", 180000.0),
        ("Batu Split 1-2 cm", "m³", 320000.0),
        ("Batu Split 2-3 cm", "m³", 290000.0),
        ("Screening", "m³", 210000.0),
        ("Sirtu", "m³", 195000.0),
    ]

    for name, unit, harga in agregat_presets:
        name_slug = name.lower().replace(' ', '_').replace('-', '_')
        harga_dec = _to_decimal(harga, f"agregat_{name_slug}")

        raw_bundle_payload.append({
            "id": f"mat_{name_slug}",
            "name": name,
            "unit": unit,
            "category": "AGREGAT",
            "specifications": {
                "nama": name,
                "harga_patokan": float(harga_dec),
            },
            "volatility_factor": 0.04,
        })

    # 3. Validasi skema
    try:
        validated_bundle = ConcreteMaterialBundleDTO(items=raw_bundle_payload)
    except Exception as exc:
        logger.error("Gagal melakukan otomatisasi generasi seeder beton agregat: Pelanggaran skema: %s", exc)
        return

    # 4. Injeksi ke KnowledgeGraph
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
        logger.debug("Material beton/agregat dimuat: %s", material_node_instance.id)

    logger.info(
        "Modul repositori material ready-mix cor dan komponen pasir agregat sukses ditayangkan: %d master nodes terkunci.",
        len(validated_bundle.items),
    )
