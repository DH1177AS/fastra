"""
fastra_core/knowledge/domains/labor/tenaga_profesional.py

Modul pemuatan data upah tenaga profesional/ahli ke dalam Knowledge Graph.
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
class ProfessionalLaborItemDTO(BaseModel):
    """DTO validasi ketat untuk mendaftar spesifikasi upah tenaga profesional/tenaga ahli."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, strict=True)

    id: str = Field(..., min_length=5, max_length=64, pattern=r"^lab_[a-z0-9_]+$")
    name: str = Field(..., min_length=2, max_length=256)
    role: NodeLaborRole = Field(default=NodeLaborRole.AHLI)
    daily_rate: float = Field(..., ge=0.0, le=1e11, allow_inf_nan=False)
    region: str = Field(default="NASIONAL", max_length=64)


class ProfessionalLaborBundleDTO(BaseModel):
    """Bundel manifes penampung sekumpulan daftar upah staf profesional teknik."""

    model_config = ConfigDict(extra="forbid", strict=True)

    items: List[ProfessionalLaborItemDTO] = Field(..., max_length=100)


# ---------------------------------------------------------------------------
# Core Utilities & Automated Seeding Generator Layer
# ---------------------------------------------------------------------------
def load_tenaga_profesional(kg: KnowledgeGraph) -> None:
    """
    Memuat dan menginjeksikan data spesialis staf profesional teknik sipil dan arsitektur.
    ID menggunakan format lab_... (underscore) agar konsisten dengan sistem.
    """
    if not isinstance(kg, KnowledgeGraph):
        raise TypeError("Parameter masukan 'kg' wajib berupa instance orisinil dari kelas KnowledgeGraph.")

    # Rekam jejak tarif upah harian staf ahli manajemen proyek (Standar INKINDO / PUPR)
    raw_bundle_payload: List[Dict[str, Any]] = [
        {"id": "lab_engineer_sipil", "name": "Civil/Structural Engineer", "role": "AHLI", "daily_rate": 350000.0, "region": "NASIONAL"},
        {"id": "lab_engineer_mep", "name": "MEP Engineer", "role": "AHLI", "daily_rate": 350000.0, "region": "NASIONAL"},
        {"id": "lab_arsitek", "name": "Architect/Arsitek", "role": "AHLI", "daily_rate": 350000.0, "region": "NASIONAL"},
        {"id": "lab_qs_estimator", "name": "Quantity Surveyor/Estimator", "role": "AHLI", "daily_rate": 350000.0, "region": "NASIONAL"},
        {"id": "lab_drafter", "name": "Drafter CAD/BIM", "role": "AHLI", "daily_rate": 200000.0, "region": "NASIONAL"},
        {"id": "lab_supervisor", "name": "Supervisor Lapangan", "role": "AHLI", "daily_rate": 250000.0, "region": "NASIONAL"},
        {"id": "lab_safety_officer", "name": "Safety Officer/K3", "role": "AHLI", "daily_rate": 225000.0, "region": "NASIONAL"},
        {"id": "lab_surveyor", "name": "Surveyor/Geomatik", "role": "AHLI", "daily_rate": 200000.0, "region": "NASIONAL"},
    ]

    # 1. GATEWAY SCHEMA VALIDATION
    try:
        validated_bundle = ProfessionalLaborBundleDTO(items=raw_bundle_payload)
    except Exception as exc:
        logger.error("Gagal memuat repositori staf profesional: Kegagalan skema data: %s", exc)
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
        logger.debug("Labor profesional dimuat: %s (%s)", labor_instance.id, labor_instance.region)

    logger.info(
        "Daftar staf profesional teknik berhasil dikunci ke repositori: %d entri Orang Hari aktif.",
        len(validated_bundle.items),
    )