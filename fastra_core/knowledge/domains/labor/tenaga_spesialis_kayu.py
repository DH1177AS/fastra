"""
fastra_core/knowledge/domains/labor/tenaga_spesialis_kayu.py

Modul pemuatan data upah tenaga kerja spesialis kayu ke dalam Knowledge Graph.
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
class CarpenterLaborItemDTO(BaseModel):
    """DTO validasi ketat untuk mendaftar spesifikasi upah spesialis kayu."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, strict=True)

    id: str = Field(..., min_length=5, max_length=64, pattern=r"^lab_[a-z0-9_]+$")
    name: str = Field(..., min_length=2, max_length=256)
    role: NodeLaborRole = Field(default=NodeLaborRole.TUKANG)
    daily_rate: float = Field(..., ge=0.0, le=1e11, allow_inf_nan=False)
    region: str = Field(default="NASIONAL", max_length=64)


class CarpenterLaborBundleDTO(BaseModel):
    """Bundel manifes penampung sekumpulan daftar upah pengrajin kayu."""

    model_config = ConfigDict(extra="forbid", strict=True)

    items: List[CarpenterLaborItemDTO] = Field(..., max_length=50)


# ---------------------------------------------------------------------------
# Core Utilities & Automated Seeding Generator Layer
# ---------------------------------------------------------------------------
def load_tenaga_spesialis_kayu(kg: KnowledgeGraph) -> None:
    """
    Memuat dan menginjeksikan data spesialis tukang kayu, kusen, plafon, dan furniture (Orang Hari).
    ID menggunakan format lab_... (underscore) agar konsisten dengan sistem.
    """
    if not isinstance(kg, KnowledgeGraph):
        raise TypeError("Parameter masukan 'kg' wajib berupa instance orisinil dari kelas KnowledgeGraph.")

    # Rekam jejak tarif upah harian spesialis kayu (Standar AHSP PUPR)
    raw_bundle_payload: List[Dict[str, Any]] = [
        {"id": "lab_tukang_kayu", "name": "Tukang Kayu", "role": "TUKANG", "daily_rate": 165000.0, "region": "NASIONAL"},
        {"id": "lab_tukang_kusen", "name": "Tukang Kusen/Pintu", "role": "TUKANG", "daily_rate": 170000.0, "region": "NASIONAL"},
        {"id": "lab_tukang_plafon", "name": "Tukang Plafon/Partisi", "role": "TUKANG", "daily_rate": 155000.0, "region": "NASIONAL"},
        {"id": "lab_tukang_furniture", "name": "Tukang Furniture Custom", "role": "TUKANG", "daily_rate": 175000.0, "region": "NASIONAL"},
    ]

    # 1. GATEWAY SCHEMA VALIDATION
    try:
        validated_bundle = CarpenterLaborBundleDTO(items=raw_bundle_payload)
    except Exception as exc:
        logger.error("Gagal memuat repositori spesialis kayu: Kegagalan skema data: %s", exc)
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
        logger.debug("Labor spesialis kayu dimuat: %s (%s)", labor_instance.id, labor_instance.region)

    logger.info(
        "Daftar tenaga spesialis pekerjaan kayu berhasil dikunci ke repositori: %d entri Orang Hari aktif.",
        len(validated_bundle.items),
    )