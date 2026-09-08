"""
fastra_core/knowledge/domains/work_item/wi_dermaga.py

Modul pemuatan data work item dermaga ke Knowledge Graph.
Seluruh ID menggunakan format wi_... (underscore) agar konsisten dengan sistem.
"""

from __future__ import annotations

import enum
import logging
from typing import Any, Dict, List

from pydantic import BaseModel, ConfigDict, Field

from fastra_core.knowledge.graph import KnowledgeGraph
from fastra_core.knowledge.nodes import WorkItemNode

logger = logging.getLogger("fastra.knowledge")


class MarineTaskCategory(str, enum.Enum):
    """Klasifikasi taksonomi formal untuk sub-divisi teknik kelautan, pelabuhan, dan dermaga."""

    DERMAGA = "DERMAGA"


# ---------------------------------------------------------------------------
# Inbound DTOs – Pydantic Strict Configuration Gate (Fail-Fast)
# ---------------------------------------------------------------------------
class InboundMarineTaskRowDTO(BaseModel):
    """DTO validasi untuk elemen task mentah di dalam paket dermaga."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, strict=False)

    id: str = Field(..., min_length=5, max_length=64, pattern=r"^wi_[a-z0-9_]+$")
    code: str = Field(..., min_length=2, max_length=32, pattern=r"^DER\.[0-9]{3}$")
    name: str = Field(..., min_length=5, max_length=512)
    unit: str = Field(..., min_length=1, max_length=16, pattern=r"^(m'|m³|unit)$")
    sni_ref: str = Field(..., min_length=2, max_length=128)
    category: MarineTaskCategory = Field(...)


class MarineTaskBundleDTO(BaseModel):
    """Master bundle schema yang memvalidasi seluruh koleksi work item dermaga."""

    model_config = ConfigDict(extra="forbid", strict=False)

    items: List[InboundMarineTaskRowDTO] = Field(..., max_length=200)


# ---------------------------------------------------------------------------
# Master Task Database Registry (Array Collection)
# ---------------------------------------------------------------------------
MARINE_TASK_REGISTRY_COLLECTION: List[Dict[str, Any]] = [
    {"id": "wi_pile_driving_dermaga", "code": "DER.001", "name": "Pemancangan Tiang Pancang Baja Dermaga (Marine Pile Driving)", "unit": "m'", "sni_ref": "Standar Pelabuhan", "category": "DERMAGA"},
    {"id": "wi_quay_deck_cor", "code": "DER.002", "name": "Pengecoran Beton Plat Lantai Dermaga (Quay Deck Concrete)", "unit": "m³", "sni_ref": "Standar Pelabuhan", "category": "DERMAGA"},
    {"id": "wi_marine_bollard", "code": "DER.003", "name": "Pemasangan Bollard / Penambat Kapal (Marine Bollard)", "unit": "unit", "sni_ref": "Standar Pelabuhan", "category": "DERMAGA"},
    {"id": "wi_rubber_fender", "code": "DER.004", "name": "Pemasangan Fender Karet Pelindung Dermaga (Rubber Dock Fender)", "unit": "unit", "sni_ref": "Standar Pelabuhan", "category": "DERMAGA"},
    {"id": "wi_gangway", "code": "DER.005", "name": "Pemasangan Tangga Turun Air / Gangway (Access Gangway)", "unit": "unit", "sni_ref": "Standar Pelabuhan", "category": "DERMAGA"},
    {"id": "wi_marine_water_supply", "code": "DER.006", "name": "Pemasangan Pipa Air Bersih Dermaga (Marine Water Supply)", "unit": "m'", "sni_ref": "Standar Pelabuhan", "category": "DERMAGA"},
]

# Extend dengan 6 definisi task dermaga tambahan
MARINE_TASK_REGISTRY_COLLECTION.extend([
    {"id": "wi_shore_power", "code": "DER.007", "name": "Pemasangan Panel Listrik Tepi Dermaga (Shore Power Panel)", "unit": "unit", "sni_ref": "Standar Pelabuhan", "category": "DERMAGA"},
    {"id": "wi_navigation_light", "code": "DER.008", "name": "Pemasangan Lampu Navigasi Tepi Dermaga (Marine Navigation Light)", "unit": "unit", "sni_ref": "Standar Pelabuhan", "category": "DERMAGA"},
    {"id": "wi_navigation_buoy", "code": "DER.009", "name": "Pemasangan Pelampung Batas Alur Pelabuhan (Navigation Buoy)", "unit": "unit", "sni_ref": "Standar Pelabuhan", "category": "DERMAGA"},
    {"id": "wi_safety_barrier", "code": "DER.010", "name": "Pemasangan Pagar Pengaman Tepi Dermaga (Safety Barrier)", "unit": "m'", "sni_ref": "Standar Pelabuhan", "category": "DERMAGA"},
    {"id": "wi_crane_rail_foundation", "code": "DER.011", "name": "Pengecoran Dudukan Crane Pelabuhan (Crane Rail Foundation)", "unit": "m³", "sni_ref": "Standar Pelabuhan", "category": "DERMAGA"},
    {"id": "wi_underground_drain", "code": "DER.012", "name": "Pemasangan Drainase Bawah Permukaan Dermaga (Underground Drain)", "unit": "m'", "sni_ref": "Standar Pelabuhan", "category": "DERMAGA"},
])


# ---------------------------------------------------------------------------
# Core Seeding Layer – Pure Domain Injection Pipeline (QS-Safe)
# ---------------------------------------------------------------------------
def load_wi_dermaga(kg: KnowledgeGraph) -> None:
    """
    Memvalidasi, menginstansiasi, dan menyuntikkan semua task dermaga ke KnowledgeGraph.
    Mencegah kesalahan argumen runtime dan korupsi struktural data dinamis.
    """
    if not isinstance(kg, KnowledgeGraph):
        raise TypeError("Parameter 'kg' harus berupa instance KnowledgeGraph.")

    # 1. GATEWAY SCHEMA VALIDATION
    try:
        validated_bundle = MarineTaskBundleDTO(items=MARINE_TASK_REGISTRY_COLLECTION)
    except Exception as exc:
        logger.error("Gagal seed dataset task dermaga. Pelanggaran skema: %s", exc)
        return

    # 2. IMMUTABLE OBJECT INJECTION PIPELINE
    for task_dto in validated_bundle.items:
        work_item_node_instance = WorkItemNode(
            id=task_dto.id,
            code=task_dto.code,
            name=task_dto.name,
            unit=task_dto.unit,
            sni_ref=task_dto.sni_ref,
            category=task_dto.category.value,
        )
        kg.add_work_item(work_item_node_instance)
        logger.debug("Work item dermaga dimuat: %s (%s)", work_item_node_instance.id, work_item_node_instance.code)

    logger.info(
        "Seeder task dermaga selesai: %d master work items terkunci.",
        len(validated_bundle.items),
    )
