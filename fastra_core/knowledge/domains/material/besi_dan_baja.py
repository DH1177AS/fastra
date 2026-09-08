"""
fastra_core/knowledge/domains/material/besi_dan_baja.py

Modul pemuatan data material besi dan baja ke Knowledge Graph.
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


class SteelMaterialCategory(str, enum.Enum):
    """Klasifikasi taksonomi resmi kelompok besi baja struktural bangunan."""

    BESI_POLOS = "BESI_POLOS"
    BESI_ULIR = "BESI_ULIR"
    BAJA_RINGAN = "BAJA_RINGAN"
    WIREMESH = "WIREMESH"


# ---------------------------------------------------------------------------
# Inbound DTOs – Pydantic Strict Gateway & Sanitization (Fail-Fast)
# ---------------------------------------------------------------------------
class GeneratedSteelItemDTO(BaseModel):
    """DTO validasi ketat untuk mendaftar spesifikasi variasi produk besi baja buatan engine."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, strict=False)

    id: str = Field(
        ...,
        min_length=5,
        max_length=128,
        pattern=r"^mat_(besi_polos|besi_ulir|baja_ringan|wiremesh)_[a-z0-9_]+$",
    )
    name: str = Field(..., min_length=2, max_length=256)
    unit: str = Field(..., min_length=2, max_length=16, pattern=r"^(batang|lembar|m²)$")
    category: str = Field(..., min_length=1, max_length=64)
    specifications: Dict[str, Any] = Field(default_factory=dict, max_length=50)
    volatility_factor: float = Field(default=0.0, ge=0.0, le=1.0, allow_inf_nan=False)

    @field_validator("specifications", mode="after")
    @classmethod
    def validate_specifications_payload(cls, value: Dict[str, Any]) -> Dict[str, Any]:
        """Memastikan harga_patokan tersedia dan bernilai positif."""
        if "harga_patokan" not in value:
            raise ValueError("Skema metadata spesifikasi besi baja cacat: Wajib melampirkan parameter 'harga_patokan'.")
        try:
            float_val = float(value["harga_patokan"])
            if float_val <= 0.0:
                raise ValueError()
        except (ValueError, TypeError):
            raise ValueError("Nilai nominal 'harga_patokan' di dalam spesifikasi wajib bertipe numerik positif.")
        return value


class SteelMaterialBundleDTO(BaseModel):
    """Bundel manifes penampung sekumpulan daftar komoditas besi tulangan dan baja."""

    model_config = ConfigDict(extra="forbid", strict=False)

    items: List[GeneratedSteelItemDTO] = Field(..., max_length=1000)


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
# Core Seeding Layer – Pure Domain Generation Pipeline (QS-Safe)
# ---------------------------------------------------------------------------
def load_besi_baja(kg: KnowledgeGraph) -> None:
    """
    Membuat, memvalidasi, dan menyuntikkan manifes master material besi dan baja ke KnowledgeGraph.
    ID menggunakan format mat_... (underscore) agar konsisten dengan sistem.
    """
    if not isinstance(kg, KnowledgeGraph):
        raise TypeError("Parameter masukan 'kg' wajib berupa instance orisinil dari kelas KnowledgeGraph.")

    raw_bundle_payload: List[Dict[str, Any]] = []

    brands: List[Tuple[str, str]] = [
        ("Krakatau Steel", "PT Krakatau Steel"),
        ("Master Steel", "PT Master Steel Indonesia"),
        ("Gunung Garuda", "PT Gunung Garuda Steel"),
        ("Hanil Jaya", "PT Hanil Jaya Steel"),
    ]

    diameters: List[int] = [6, 8, 10, 12, 13, 16, 19, 22, 25]

    # Harga patokan per batang (12m) standar nasional
    harga_patokan: Dict[int, int] = {
        6: 32000, 8: 46000, 10: 69000, 12: 98000,
        13: 118000, 16: 178000, 19: 252000, 22: 335000, 25: 430000
    }

    # 1. Varian Besi Polos (BJTP 280)
    for brand, manufacturer in brands:
        brand_slug = brand.lower().replace(' ', '_')
        for d in diameters:
            base_price = harga_patokan.get(d, 0)
            raw_bundle_payload.append({
                "id": f"mat_besi_polos_d{d}_{brand_slug}",
                "name": f"Besi Beton Polos D{d}mm — {brand}",
                "unit": "batang",
                "category": "BESI_POLOS",
                "specifications": {
                    "merek": brand,
                    "produsen": manufacturer,
                    "tipe": "Polos (BJTP 280)",
                    "diameter_mm": d,
                    "panjang": "12m",
                    "harga_patokan": float(base_price),
                    "standar": "SNI 2052:2017"
                },
                "volatility_factor": 0.12
            })

    # 2. Varian Besi Ulir (BJTS 420) dengan Premium Margin 8%
    for brand, manufacturer in brands:
        brand_slug = brand.lower().replace(' ', '_')
        for d in diameters:
            base_price_dec = _to_decimal(harga_patokan.get(d, 0), f"base_price_d{d}")
            premium_price_dec = (base_price_dec * _to_decimal(1.08, "premium_factor")).quantize(Decimal("1"))

            raw_bundle_payload.append({
                "id": f"mat_besi_ulir_d{d}_{brand_slug}",
                "name": f"Besi Beton Ulir D{d}mm — {brand}",
                "unit": "batang",
                "category": "BESI_ULIR",
                "specifications": {
                    "merek": brand,
                    "produsen": manufacturer,
                    "tipe": "Ulir (BJTS 420)",
                    "diameter_mm": d,
                    "panjang": "12m",
                    "harga_patokan": float(premium_price_dec),
                    "standar": "SNI 2052:2017"
                },
                "volatility_factor": 0.12
            })

    # 3. Komponen Baja Ringan Atap
    baja_ringan_presets: List[Tuple[str, str, float]] = [
        ("Kanal C75 0.75mm", "batang", 85000.0),
        ("Kanal C75 1.0mm", "batang", 105000.0),
        ("Reng R30 0.45mm", "batang", 42000.0),
        ("Reng R32 0.5mm", "batang", 48000.0),
    ]
    for name, unit, harga in baja_ringan_presets:
        name_slug = name.lower().replace(' ', '_').replace('.', '')
        raw_bundle_payload.append({
            "id": f"mat_baja_ringan_{name_slug}",
            "name": f"Baja Ringan {name}",
            "unit": unit,
            "category": "BAJA_RINGAN",
            "specifications": {
                "nama": name,
                "harga_patokan": harga,
                "standar": "SNI 8393:2017"
            },
            "volatility_factor": 0.08
        })

    # 4. Komponen Plat Slab Wiremesh Tulangan Lantai
    wiremesh_presets: List[Tuple[str, str, float]] = [
        ("M4 (2.1m x 5.4m)", "lembar", 185000.0),
        ("M5 (2.1m x 5.4m)", "lembar", 225000.0),
        ("M6 (2.1m x 5.4m)", "lembar", 320000.0),
        ("M8 (2.1m x 5.4m)", "lembar", 485000.0),
    ]
    for name, unit, harga in wiremesh_presets:
        name_slug = name.lower().replace(' ', '_').replace('.', '').replace('(', '').replace(')', '')
        raw_bundle_payload.append({
            "id": f"mat_wiremesh_{name_slug}",
            "name": f"Wiremesh {name}",
            "unit": unit,
            "category": "WIREMESH",
            "specifications": {
                "nama": name,
                "harga_patokan": harga,
                "standar": "SNI 07-0663-2002"
            },
            "volatility_factor": 0.10
        })

    # 5. Validasi skema
    try:
        validated_bundle = SteelMaterialBundleDTO(items=raw_bundle_payload)
    except Exception as exc:
        logger.error("Gagal mengeksekusi kompilasi otomatis seeder besi baja: Pelanggaran skema: %s", exc)
        return

    # 6. Injeksi ke KnowledgeGraph
    for item_dto in validated_bundle.items:
        material_node_instance = MaterialNode(
            id=item_dto.id,
            name=item_dto.name,
            unit=item_dto.unit,
            category=item_dto.category,
            specifications=item_dto.specifications,
            volatility_factor=item_dto.volatility_factor,
        )
        kg.add_material(material_node_instance)
        logger.debug("Material besi/baja dimuat: %s", material_node_instance.id)

    logger.info(
        "Modul material besi tulangan dan komponen struktur baja sukses ditayangkan: %d master nodes terkunci.",
        len(validated_bundle.items),
    )
