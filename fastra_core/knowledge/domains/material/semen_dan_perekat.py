"""
fastra_core/knowledge/domains/material/semen_dan_perekat.py

Modul pemuatan data material semen dan perekat ke Knowledge Graph.
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


class CementMaterialCategory(str, enum.Enum):
    """Klasifikasi taksonomi resmi kelompok material semen, semen putih, dan mortar instan."""

    SEMEN = "SEMEN"
    SEMEN_PUTIH = "SEMEN_PUTIH"
    MORTAR = "MORTAR"


# ---------------------------------------------------------------------------
# Inbound DTOs – Pydantic Strict Gateway & Sanitization (Fail-Fast)
# ---------------------------------------------------------------------------
class GeneratedCementItemDTO(BaseModel):
    """DTO validasi ketat untuk mendaftar spesifikasi produk semen dan mortar instan."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, strict=False)

    id: str = Field(..., min_length=5, max_length=128, pattern=r"^mat_[a-z0-9_\\.\\-]+$")
    name: str = Field(..., min_length=2, max_length=256)
    unit: str = Field(default="sak", min_length=3, max_length=16, pattern=r"^sak$")
    category: str = Field(..., min_length=1, max_length=64)
    specifications: Dict[str, Any] = Field(default_factory=dict, max_length=50)
    volatility_factor: float = Field(default=0.0, ge=0.0, le=1.0, allow_inf_nan=False)

    @field_validator("specifications", mode="after")
    @classmethod
    def validate_specifications_payload(cls, value: Dict[str, Any]) -> Dict[str, Any]:
        """Memastikan harga_patokan tersedia dan bernilai positif."""
        if "harga_patokan" not in value:
            raise ValueError("Skema metadata spesifikasi semen/mortar cacat: Wajib melampirkan parameter 'harga_patokan'.")
        try:
            float_val = float(value["harga_patokan"])
            if float_val <= 0.0:
                raise ValueError()
        except (ValueError, TypeError):
            raise ValueError("Nilai nominal 'harga_patokan' di dalam spesifikasi wajib bertipe numerik positif.")
        return value


class CementMaterialBundleDTO(BaseModel):
    """Bundel manifes penampung sekumpulan daftar komoditas produk semen dan mortar."""

    model_config = ConfigDict(extra="forbid", strict=False)

    items: List[GeneratedCementItemDTO] = Field(..., max_length=500)


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


def _slugify_underscore(text: str) -> str:
    """Mengubah string menjadi slug dengan underscore."""
    return text.lower().replace(' ', '_').replace('-', '_').replace('(', '').replace(')', '')


# ---------------------------------------------------------------------------
# Core Seeding Layer – Pure Cement Generation Pipeline (QS-Safe)
# ---------------------------------------------------------------------------
def load_semen(kg: KnowledgeGraph) -> None:
    """
    Membuat, memvalidasi, dan menyuntikkan manifes master material semen ke KnowledgeGraph.
    ID menggunakan format mat_... (underscore) agar konsisten dengan sistem.
    """
    if not isinstance(kg, KnowledgeGraph):
        raise TypeError("Parameter masukan 'kg' wajib berupa instance orisinil dari kelas KnowledgeGraph.")

    raw_bundle_payload: List[Dict[str, Any]] = []

    # Semen Portland - 6 merek × 2 varian kemasan = 12 nodes otomatis
    brands: List[Tuple[str, str, float, float]] = [
        ("Semen Tiga Roda", "PT Indocement Tunggal Prakarsa", 68000.0, 55760.0),
        ("Semen Gresik", "PT Semen Gresik", 66000.0, 54120.0),
        ("Semen Holcim", "PT Holcim Indonesia", 67000.0, 54940.0),
        ("Semen Dynamix", "PT Solusi Bangun Indonesia", 67000.0, 54940.0),
        ("Semen Padang", "PT Semen Padang", 65000.0, 53300.0),
        ("Semen Merah Putih", "PT Cemindo Gemilang", 64000.0, 52480.0),
    ]

    # 1. Kombinasi Jenis Merek dan Varian Berat Sak
    for brand, manufacturer, harga_50, harga_40 in brands:
        brand_slug = _slugify_underscore(brand)
        for variant, harga in [("50kg", harga_50), ("40kg", harga_40)]:
            harga_dec = _to_decimal(harga, f"semen_{brand_slug}_{variant}")

            raw_bundle_payload.append({
                "id": f"mat_semen_{brand_slug}_{variant}",
                "name": f"{brand} Portland Type I ({variant})",
                "unit": "sak",
                "category": "SEMEN",
                "specifications": {
                    "merek": brand,
                    "produsen": manufacturer,
                    "tipe": "Portland Type I",
                    "berat": variant,
                    "harga_patokan": float(harga_dec),
                    "standar": "SNI 15-2049-2004",
                },
                "volatility_factor": 0.05,
            })

    # 2. Semen Putih Arsitektural
    semen_putih_presets: List[Tuple[str, float]] = [
        ("Semen Tiga Roda Putih", 95000.0),
        ("Semen Gresik Putih", 92000.0),
    ]
    for brand, harga in semen_putih_presets:
        brand_slug = _slugify_underscore(brand)
        harga_dec = _to_decimal(harga, f"semen_putih_{brand_slug}")

        raw_bundle_payload.append({
            "id": f"mat_semen_putih_{brand_slug}",
            "name": f"{brand} (40kg)",
            "unit": "sak",
            "category": "SEMEN_PUTIH",
            "specifications": {
                "merek": brand,
                "warna": "putih",
                "berat": "40kg",
                "harga_patokan": float(harga_dec),
                "standar": "SNI 15-0129-2004",
            },
            "volatility_factor": 0.04,
        })

    # 3. Mortar Instan / Perekat Instan AAC
    mortar_brands: List[Tuple[str, str]] = [
        ("Mortar Utama (MU)", "PT Cipta Mortar Utama"),
        ("Drymix", "PT Drymix Indonesia"),
        ("SikaGrout", "PT Sika Indonesia"),
    ]
    for brand, manufacturer in mortar_brands:
        brand_slug = _slugify_underscore(brand)
        harga_dec = _to_decimal(75000.0, f"mortar_{brand_slug}")

        raw_bundle_payload.append({
            "id": f"mat_mortar_{brand_slug}",
            "name": f"Mortar Instan {brand} (25kg)",
            "unit": "sak",
            "category": "MORTAR",
            "specifications": {
                "merek": brand,
                "produsen": manufacturer,
                "berat": "25kg",
                "harga_patokan": float(harga_dec),
                "standar": "SNI 6882:2014",
            },
            "volatility_factor": 0.03,
        })

    # 4. GATEWAY SCHEMA VALIDATION
    try:
        validated_bundle = CementMaterialBundleDTO(items=raw_bundle_payload)
    except Exception as exc:
        logger.error("Gagal mengeksekusi otomatisasi seeder semen perekat: Pelanggaran skema: %s", exc)
        return

    # 5. IMMUTABLE DOMAIN INJECTION PIPELINE
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
        logger.debug("Material semen/mortar dimuat: %s", material_node_instance.id)

    logger.info(
        "Modul material pengikat semen portland dan mortar instan perekat sukses ditayangkan: %d master nodes terkunci.",
        len(validated_bundle.items),
    )
