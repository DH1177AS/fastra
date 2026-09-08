"""
fastra_core/knowledge/domains/material/atap_dan_genteng.py

Modul pemuatan data material penutup atap dan aksesoris arsitektural ke Knowledge Graph.
Seluruh ID menggunakan format mat_... (underscore) agar konsisten dengan komponen material lain di FASTRA.
"""

from __future__ import annotations

import enum
import logging
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from fastra_core.knowledge.graph import KnowledgeGraph
from fastra_core.knowledge.nodes import MaterialNode

logger = logging.getLogger("fastra.knowledge")


class RoofMaterialCategory(str, enum.Enum):
    """Klasifikasi taksonomi jenis komponen atap dan aksesoris arsitektural sipil."""

    GENTENG = "GENTENG"
    ATAP_LOGAM = "ATAP_LOGAM"
    ATAP_PLASTIK = "ATAP_PLASTIK"
    INSULASI = "INSULASI"
    TALANG = "TALANG"
    LISPLANK = "LISPLANK"


# ---------------------------------------------------------------------------
# Inbound DTOs – Pydantic Strict Gateway & Sanitization (Fail-Fast)
# ---------------------------------------------------------------------------
class RoofMaterialItemDTO(BaseModel):
    """DTO validasi ketat untuk mendaftar spesifikasi material penutup atap."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, strict=False)

    id: str = Field(..., min_length=5, max_length=64, pattern=r"^mat_[a-z0-9_\\.\\-]+$")
    name: str = Field(..., min_length=2, max_length=256)
    unit: str = Field(..., min_length=1, max_length=16, pattern=r"^[A-Za-z0-9²³\/()\s\u00B3']+$")
    category: RoofMaterialCategory = Field(...)
    specifications: Dict[str, Any] = Field(default_factory=dict, max_length=50)
    volatility_factor: float = Field(default=0.0, ge=0.0, le=1.0, allow_inf_nan=False)

    @field_validator("specifications", mode="after")
    @classmethod
    def validate_specifications_payload(cls, value: Dict[str, Any]) -> Dict[str, Any]:
        """Memastikan harga_patokan tersedia dan bernilai positif."""
        if "harga_patokan" not in value:
            raise ValueError("Skema metadata spesifikasi material cacat: Wajib melampirkan parameter 'harga_patokan'.")
        try:
            float_val = float(value["harga_patokan"])
            if float_val <= 0.0:
                raise ValueError()
        except (ValueError, TypeError):
            raise ValueError("Nilai nominal 'harga_patokan' di dalam spesifikasi wajib bertipe numerik positif.")
        return value


class RoofMaterialBundleDTO(BaseModel):
    """Bundel manifes penampung sekumpulan daftar komoditas atap dan genteng."""

    model_config = ConfigDict(extra="forbid", strict=False)

    items: List[RoofMaterialItemDTO] = Field(..., max_length=100)


# ---------------------------------------------------------------------------
# Core Seeding Layer – Pure Domain Injection Pipeline (QS-Safe)
# ---------------------------------------------------------------------------
def load_atap_genteng(kg: KnowledgeGraph) -> None:
    """
    Memuat dan menyuntikkan manifes master material atap dan genteng ke KnowledgeGraph.
    ID menggunakan format mat_... (underscore) agar konsisten dengan sistem.
    """
    if not isinstance(kg, KnowledgeGraph):
        raise TypeError("Parameter masukan 'kg' wajib berupa instance orisinil dari kelas KnowledgeGraph.")

    # Kumpulan raw data benih komoditas material atap sesuai spesifikasi teknis PUPR
    raw_bundle_payload: List[Dict[str, Any]] = [
        {"id": "mat_genteng_beton_flat", "name": "Genteng Beton Flat", "unit": "buah", "category": "GENTENG", "specifications": {"tipe": "Beton Flat", "harga_patokan": 6500.0}},
        {"id": "mat_genteng_keramik_kanmuri", "name": "Genteng Keramik Kanmuri", "unit": "buah", "category": "GENTENG", "specifications": {"tipe": "Keramik Kanmuri", "harga_patokan": 11500.0}},
        {"id": "mat_genteng_metal_berpasir", "name": "Genteng Metal Berpasir", "unit": "buah", "category": "GENTENG", "specifications": {"tipe": "Metal Berpasir", "harga_patokan": 8500.0}},
        {"id": "mat_genteng_aspal_bitumen", "name": "Genteng Aspal Bitumen", "unit": "buah", "category": "GENTENG", "specifications": {"tipe": "Aspal Bitumen", "harga_patokan": 45000.0}},
        {"id": "mat_spandek_025mm", "name": "Atap Spandek Galvalum 0.25mm", "unit": "m", "category": "ATAP_LOGAM", "specifications": {"tebal": "0.25mm", "harga_patokan": 45000.0}},
        {"id": "mat_spandek_030mm", "name": "Atap Spandek Galvalum 0.30mm", "unit": "m", "category": "ATAP_LOGAM", "specifications": {"tebal": "0.30mm", "harga_patokan": 55000.0}},
        {"id": "mat_spandek_035mm", "name": "Atap Spandek Galvalum 0.35mm", "unit": "m", "category": "ATAP_LOGAM", "specifications": {"tebal": "0.35mm", "harga_patokan": 65000.0}},
        {"id": "mat_spandek_040mm", "name": "Atap Spandek Galvalum 0.40mm", "unit": "m", "category": "ATAP_LOGAM", "specifications": {"tebal": "0.40mm", "harga_patokan": 78000.0}},
        {"id": "mat_zincalume_040mm", "name": "Atap Zincalume 0.40mm", "unit": "m²", "category": "ATAP_LOGAM", "specifications": {"tipe": "Zincalume", "tebal": "0.40mm", "harga_patokan": 65000.0}},
        {"id": "mat_genteng_nok", "name": "Genteng Nok/Bubungan", "unit": "buah", "category": "GENTENG", "specifications": {"tipe": "Nok", "harga_patokan": 12000.0}},
        {"id": "mat_aluminium_foil_single", "name": "Aluminium Foil Single Side", "unit": "m²", "category": "INSULASI", "specifications": {"tipe": "Single", "harga_patokan": 15000.0}},
        {"id": "mat_aluminium_foil_double", "name": "Aluminium Foil Double Side", "unit": "m²", "category": "INSULASI", "specifications": {"tipe": "Double", "harga_patokan": 25000.0}},
        {"id": "mat_glasswool", "name": "Glasswool Insulation", "unit": "m²", "category": "INSULASI", "specifications": {"bahan": "Glasswool", "harga_patokan": 35000.0}},
        {"id": "mat_rockwool", "name": "Rockwool Insulation", "unit": "m²", "category": "INSULASI", "specifications": {"bahan": "Rockwool", "harga_patokan": 45000.0}},
        {"id": "mat_polycarbonate", "name": "Atap Polycarbonate", "unit": "m²", "category": "ATAP_PLASTIK", "specifications": {"bahan": "Polycarbonate", "harga_patokan": 85000.0}},
        {"id": "mat_talang_pvc", "name": "Talang Horizontal PVC", "unit": "m'", "category": "TALANG", "specifications": {"bahan": "PVC", "harga_patokan": 45000.0}},
        {"id": "mat_talang_galvalum", "name": "Talang Horizontal Galvalum", "unit": "m'", "category": "TALANG", "specifications": {"bahan": "Galvalum", "harga_patokan": 65000.0}},
        {"id": "mat_lisplank_grc", "name": "Lisplank GRC", "unit": "m'", "category": "LISPLANK", "specifications": {"bahan": "GRC", "harga_patokan": 38000.0}},
        {"id": "mat_lisplank_kayu", "name": "Lisplank Kayu Kamper", "unit": "m'", "category": "LISPLANK", "specifications": {"bahan": "Kayu Kamper", "harga_patokan": 55000.0}},
    ]

    # 1. GATEWAY SCHEMA VALIDATION
    try:
        validated_bundle = RoofMaterialBundleDTO(items=raw_bundle_payload)
    except Exception as exc:
        logger.error("Gagal melakukan injeksi seeder atap dan genteng: Pelanggaran skema: %s", exc)
        return

    # 2. IMMUTABLE OBJECT INJECTION PIPELINE
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
        logger.debug("Material atap dimuat: %s", material_node_instance.id)

    logger.info(
        "Modul material penutup atap dan aksesoris arsitektural sukses dimuat: %d master nodes terkunci.",
        len(validated_bundle.items),
    )
