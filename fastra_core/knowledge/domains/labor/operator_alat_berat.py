"""
fastra_core/knowledge/domains/labor/operator_alat_berat.py

Modul pemuatan data upah operator alat berat ke dalam Knowledge Graph.
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
class OperatorLaborItemDTO(BaseModel):
    """DTO validasi ketat untuk mendaftar spesifikasi upah operator mekanikal."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, strict=True)

    id: str = Field(..., min_length=5, max_length=64, pattern=r"^lab_[a-z0-9_]+$")
    name: str = Field(..., min_length=2, max_length=256)
    role: NodeLaborRole = Field(default=NodeLaborRole.AHLI)
    daily_rate: float = Field(..., ge=0.0, le=1e11, allow_inf_nan=False)
    region: str = Field(default="NASIONAL", max_length=64)


class OperatorLaborBundleDTO(BaseModel):
    """Bundel manifes penampung sekumpulan daftar upah operator alat berat."""

    model_config = ConfigDict(extra="forbid", strict=True)

    items: List[OperatorLaborItemDTO] = Field(..., max_length=100)


# ---------------------------------------------------------------------------
# Core Utilities & Automated Seeding Generator Layer
# ---------------------------------------------------------------------------
def load_operator_alat_berat(kg: KnowledgeGraph) -> None:
    """
    Memuat dan menginjeksikan data spesialis upah operator alat berat (Orang Hari).
    ID menggunakan format lab_... (underscore) agar konsisten dengan sistem.
    """
    if not isinstance(kg, KnowledgeGraph):
        raise TypeError("Parameter masukan 'kg' wajib berupa instance orisinil dari kelas KnowledgeGraph.")

    # Rekam jejak tarif upah harian operator alat khusus (Standar AHSP PUPR)
    raw_bundle_payload: List[Dict[str, Any]] = [
        {"id": "lab_operator_excavator", "name": "Operator Excavator", "role": "AHLI", "daily_rate": 250000.0, "region": "NASIONAL"},
        {"id": "lab_operator_bulldozer", "name": "Operator Bulldozer", "role": "AHLI", "daily_rate": 260000.0, "region": "NASIONAL"},
        {"id": "lab_operator_crane", "name": "Operator Crane Mobile 25Ton", "role": "AHLI", "daily_rate": 280000.0, "region": "NASIONAL"},
        {"id": "lab_operator_roller", "name": "Operator Tandem/Pneumatic Roller", "role": "AHLI", "daily_rate": 240000.0, "region": "NASIONAL"},
        {"id": "lab_operator_paver", "name": "Operator Asphalt/Concrete Paver", "role": "AHLI", "daily_rate": 260000.0, "region": "NASIONAL"},
        {"id": "lab_operator_grader", "name": "Operator Motor Grader", "role": "AHLI", "daily_rate": 255000.0, "region": "NASIONAL"},
        {"id": "lab_operator_borepile", "name": "Operator Mesin Bore Pile", "role": "AHLI", "daily_rate": 270000.0, "region": "NASIONAL"},
        {"id": "lab_operator_jackin", "name": "Operator Jack-In Pile Hidrolik", "role": "AHLI", "daily_rate": 265000.0, "region": "NASIONAL"},
        {"id": "lab_operator_forklift", "name": "Operator Forklift", "role": "AHLI", "daily_rate": 200000.0, "region": "NASIONAL"},
        {"id": "lab_operator_tbm", "name": "Operator TBM (Tunnel Boring Machine)", "role": "AHLI", "daily_rate": 350000.0, "region": "NASIONAL"},
    ]

    # 1. GATEWAY SCHEMA VALIDATION
    try:
        validated_bundle = OperatorLaborBundleDTO(items=raw_bundle_payload)
    except Exception as exc:
        logger.error("Gagal memuat repositori operator alat berat: Kegagalan skema data: %s", exc)
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
        logger.debug("Labor operator dimuat: %s (%s)", labor_instance.id, labor_instance.region)

    logger.info(
        "Daftar spesialis upah operator alat berat berhasil dikunci ke repositori: %d entri Orang Hari aktif.",
        len(validated_bundle.items),
    )