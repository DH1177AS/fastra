"""
fastra_core/knowledge/domains/labor/tenaga_umum.py

Modul pemuatan data upah tenaga kerja umum ke dalam Knowledge Graph.
Seluruh ID menggunakan format lab_... (underscore) agar konsisten dengan
komponen labor lain di FASTRA.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from pydantic import BaseModel, ConfigDict, Field

from fastra_core.knowledge.graph import KnowledgeGraph
from fastra_core.knowledge.nodes import LaborNode, NodeLaborRole

logger = logging.getLogger("fastra.knowledge")


# ---------------------------------------------------------------------------
# Inbound DTOs – Pydantic Strict Gateway & Sanitization (Fail-Fast)
# ---------------------------------------------------------------------------
class GeneralLaborItemDTO(BaseModel):
    """DTO validasi ketat untuk mendaftar spesifikasi upah tenaga kerja umum."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, strict=True)

    id: str = Field(..., min_length=5, max_length=64, pattern=r"^lab_[a-z0-9_]+$")
    name: str = Field(..., min_length=2, max_length=256)
    role: NodeLaborRole = Field(..., description="Kualifikasi keahlian regulasi tenaga umum")
    daily_rate: float = Field(..., ge=0.0, le=1e11, allow_inf_nan=False)
    region: str = Field(default="NASIONAL", max_length=64)


class GeneralLaborBundleDTO(BaseModel):
    """Bundel manifes penampung sekumpulan daftar upah kru umum lapangan."""

    model_config = ConfigDict(extra="forbid", strict=True)

    items: List[GeneralLaborItemDTO] = Field(..., max_length=50)


# ---------------------------------------------------------------------------
# Core Utilities & Automated Seeding Generator Layer
# ---------------------------------------------------------------------------
def load_tenaga_umum(kg: KnowledgeGraph) -> None:
    """
    Memuat dan menginjeksikan data tenaga kerja umum, pengawas, dan operator logistik (Orang Hari).
    ID menggunakan format lab_... (underscore) agar konsisten dengan sistem.
    """
    if not isinstance(kg, KnowledgeGraph):
        raise TypeError("Parameter masukan 'kg' wajib berupa instance orisinil dari kelas KnowledgeGraph.")

    # Rekam jejak tarif upah harian kru umum dan pendukung operasional (Standar AHSP PUPR)
    raw_bundle_payload: List[Dict[str, Any]] = [
        {"id": "lab_kenek", "name": "Kenek / Pembantu Tukang", "role": "PEKERJA", "daily_rate": 95000.0, "region": "NASIONAL"},
        {"id": "lab_pekerja", "name": "Pekerja", "role": "PEKERJA", "daily_rate": 130000.0, "region": "NASIONAL"},
        {"id": "lab_mandor", "name": "Mandor Lapangan", "role": "MANDOR", "daily_rate": 200000.0, "region": "NASIONAL"},
        {"id": "lab_kepala_tukang", "name": "Kepala Tukang", "role": "KEPALA_TUKANG", "daily_rate": 180000.0, "region": "NASIONAL"},
        {"id": "lab_drafter", "name": "Drafter Lapangan", "role": "AHLI", "daily_rate": 175000.0, "region": "NASIONAL"},
        {"id": "lab_surveyor", "name": "Surveyor", "role": "AHLI", "daily_rate": 185000.0, "region": "NASIONAL"},
        {"id": "lab_operator_excavator", "name": "Operator Alat Berat/Excavator", "role": "AHLI", "daily_rate": 250000.0, "region": "NASIONAL"},
        {"id": "lab_sopir_truk", "name": "Sopir Truk/Dump Truck", "role": "PEKERJA", "daily_rate": 220000.0, "region": "NASIONAL"},
        {"id": "lab_operator_crane", "name": "Operator Crane Mobile", "role": "AHLI", "daily_rate": 280000.0, "region": "NASIONAL"},
        {"id": "lab_operator_paver", "name": "Operator Asphalt/Concrete Paver", "role": "AHLI", "daily_rate": 260000.0, "region": "NASIONAL"},
        {"id": "lab_operator_roller", "name": "Operator Tandem/Pneumatic Roller", "role": "AHLI", "daily_rate": 240000.0, "region": "NASIONAL"},
    ]

    # 1. GATEWAY SCHEMA VALIDATION
    try:
        validated_bundle = GeneralLaborBundleDTO(items=raw_bundle_payload)
    except Exception as exc:
        logger.error("Gagal memuat repositori tenaga umum: Kegagalan skema data: %s", exc)
        return

    # 2. IMMUTABLE DOMAIN INJECTION PIPELINE
    for item_dto in validated_bundle.items:
        labor_instance = LaborNode(
            id=item_dto.id,
            name=item_dto.name,
            role=item_dto.role,
            daily_rate=item_dto.daily_rate,
            region=item_dto.region,
        )
        kg.add_labor(labor_instance)
        logger.debug("Labor umum dimuat: %s (%s)", labor_instance.id, labor_instance.region)

    logger.info(
        "Daftar tenaga kerja umum berhasil dikunci ke repositori: %d entri Orang Hari aktif.",
        len(validated_bundle.items),
    )