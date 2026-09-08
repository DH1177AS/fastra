"""
fastra_core/knowledge/domains/material/pipa_dan_fitting.py

Modul pemuatan data material pipa dan fitting ke Knowledge Graph.
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


class PipingMaterialCategory(str, enum.Enum):
    """Klasifikasi taksonomi resmi kelompok material pipa utilitas dan aksesoris penyambung."""

    PIPA_PVC = "PIPA_PVC"
    PIPA_PPR = "PIPA_PPR"
    FITTING = "FITTING"
    LEM_PIPA = "LEM_PIPA"
    SEAL_TAPE = "SEAL_TAPE"


# ---------------------------------------------------------------------------
# Inbound DTOs – Pydantic Strict Gateway & Sanitization (Fail-Fast)
# ---------------------------------------------------------------------------
class GeneratedPipingItemDTO(BaseModel):
    """DTO validasi ketat untuk mendaftar spesifikasi produk perpipaan mekanikal."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, strict=False)

    id: str = Field(..., min_length=5, max_length=128, pattern=r"^mat_[a-z0-9_\\.\\-]+$")
    name: str = Field(..., min_length=2, max_length=256)
    unit: str = Field(..., min_length=2, max_length=16, pattern=r"^(batang|buah|kaleng|roll)$")
    category: PipingMaterialCategory = Field(...)
    specifications: Dict[str, Any] = Field(default_factory=dict, max_length=50)
    volatility_factor: float = Field(default=0.0, ge=0.0, le=1.0, allow_inf_nan=False)

    @field_validator("specifications", mode="after")
    @classmethod
    def validate_specifications_payload(cls, value: Dict[str, Any]) -> Dict[str, Any]:
        """Memastikan harga_patokan tersedia dan bernilai positif."""
        if "harga_patokan" not in value:
            raise ValueError("Skema metadata spesifikasi perpipaan cacat: Wajib melampirkan parameter 'harga_patokan'.")
        try:
            float_val = float(value["harga_patokan"])
            if float_val <= 0.0:
                raise ValueError()
        except (ValueError, TypeError):
            raise ValueError("Nilai nominal 'harga_patokan' di dalam spesifikasi wajib bertipe numerik positif.")
        return value


class PipingMaterialBundleDTO(BaseModel):
    """Bundel manifes penampung sekumpulan daftar komoditas produk pipa dan fiting penunjang."""

    model_config = ConfigDict(extra="forbid", strict=False)

    items: List[GeneratedPipingItemDTO] = Field(..., max_length=1000)


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
    return text.lower().replace('"', '').replace('/', '_').replace('-', '_').replace(' ', '_')


# ---------------------------------------------------------------------------
# Core Seeding Layer – Pure Piping Generation Pipeline (QS-Safe)
# ---------------------------------------------------------------------------
def load_pipa_fitting(kg: KnowledgeGraph) -> None:
    """
    Membuat, memvalidasi, dan menyuntikkan manifes master material pipa dan fitting ke KnowledgeGraph.
    ID menggunakan format mat_... (underscore) agar konsisten dengan sistem.
    """
    if not isinstance(kg, KnowledgeGraph):
        raise TypeError("Parameter masukan 'kg' wajib berupa instance orisinil dari kelas KnowledgeGraph.")

    raw_bundle_payload: List[Dict[str, Any]] = []

    brands: List[str] = ["Rucika", "Wavin", "Maspion", "Vinilon"]
    sizes: List[str] = ['1/2"', '3/4"', '1"', '1.5"', '2"', '3"', '4"']

    # 1. Varian Pipa PVC AW
    for brand in brands:
        brand_slug = _slugify_underscore(brand)
        for size in sizes:
            size_id = _slugify_underscore(size)  # e.g. 1_2, 3_4, 1, 1_5, 2, 3, 4
            harga_dec = _to_decimal(50000.0, f"pvc_{size_id}_{brand_slug}")

            raw_bundle_payload.append({
                "id": f"mat_pipa_pvc_aw_{size_id}_{brand_slug}",
                "name": f"Pipa PVC AW {size} {brand}",
                "unit": "batang",
                "category": "PIPA_PVC",
                "specifications": {
                    "merek": brand,
                    "tipe": "AW",
                    "ukuran": size,
                    "harga_patokan": float(harga_dec),
                },
                "volatility_factor": 0.04,
            })

    # 2. Varian Pipa PPR PN-10
    for size in sizes:
        size_id = _slugify_underscore(size)
        harga_dec = _to_decimal(65000.0, f"ppr_{size_id}")

        raw_bundle_payload.append({
            "id": f"mat_pipa_ppr_{size_id}",
            "name": f"Pipa PPR PN-10 {size}",
            "unit": "batang",
            "category": "PIPA_PPR",
            "specifications": {
                "tipe": "PN-10",
                "ukuran": size,
                "harga_patokan": float(harga_dec),
            },
            "volatility_factor": 0.05,
        })

    # 3. Fitting dan aksesoris
    fittings_presets: List[Tuple[str, str, str, str, Dict[str, Any], float]] = [
        ("mat_fitting_elbow_90", "Fitting Elbow 90° PVC", "buah", "FITTING", {"tipe": "Elbow 90°", "harga_patokan": 4500.0}, 0.03),
        ("mat_fitting_tee", "Fitting Tee PVC", "buah", "FITTING", {"tipe": "Tee", "harga_patokan": 4500.0}, 0.03),
        ("mat_fitting_sock", "Fitting Sock PVC", "buah", "FITTING", {"tipe": "Sock", "harga_patokan": 3500.0}, 0.03),
        ("mat_fitting_dop", "Fitting Dop/Cap PVC", "buah", "FITTING", {"tipe": "Dop", "harga_patokan": 3500.0}, 0.03),
        ("mat_lem_pipa", "Lem Pipa PVC", "kaleng", "LEM_PIPA", {"harga_patokan": 25000.0}, 0.03),
        ("mat_seal_tape", "Seal Tape Teflon", "roll", "SEAL_TAPE", {"harga_patokan": 5000.0}, 0.03),
    ]

    for fid, fname, funit, fcat, fspecs, fvol in fittings_presets:
        harga_dec = _to_decimal(fspecs["harga_patokan"], f"fitting_price_{fid}")
        fspecs["harga_patokan"] = float(harga_dec)

        raw_bundle_payload.append({
            "id": fid,
            "name": fname,
            "unit": funit,
            "category": fcat,
            "specifications": fspecs,
            "volatility_factor": fvol,
        })

    # 4. Validasi skema
    try:
        validated_bundle = PipingMaterialBundleDTO(items=raw_bundle_payload)
    except Exception as exc:
        logger.error("Gagal mengeksekusi otomatisasi seeder pipa fitting: Pelanggaran skema: %s", exc)
        return

    # 5. Injeksi ke KnowledgeGraph
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
        logger.debug("Material pipa/fitting dimuat: %s", material_node_instance.id)

    logger.info(
        "Modul material pipa distribusi utilitas dan fiting komponen sambungan sukses ditayangkan: %d master nodes terkunci.",
        len(validated_bundle.items),
    )
