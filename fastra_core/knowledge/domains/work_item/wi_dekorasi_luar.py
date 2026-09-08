"""
fastra_core/knowledge/domains/work_item/wi_dekorasi_luar.py

Modul pemuatan data work item dekorasi luar ke Knowledge Graph.
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


class ExteriorTaskCategory(str, enum.Enum):
    """Klasifikasi taksonomi formal untuk sub-divisi dekorasi luar dan penunjang eksterior."""

    DEKORASI_LUAR = "DEKORASI_LUAR"


# ---------------------------------------------------------------------------
# Inbound DTOs – Pydantic Strict Configuration Gate (Fail-Fast)
# ---------------------------------------------------------------------------
class InboundExteriorTaskRowDTO(BaseModel):
    """DTO validasi untuk elemen task mentah di dalam paket dekorasi luar."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, strict=False)

    id: str = Field(..., min_length=5, max_length=64, pattern=r"^wi_[a-z0-9_]+$")
    code: str = Field(..., min_length=2, max_length=32, pattern=r"^DL\.[0-9]{3}$")
    name: str = Field(..., min_length=5, max_length=512)
    unit: str = Field(..., min_length=1, max_length=16, pattern=r"^(m²|set|unit|m'|set)$")
    sni_ref: str = Field(..., min_length=2, max_length=128)
    category: ExteriorTaskCategory = Field(...)


class ExteriorTaskBundleDTO(BaseModel):
    """Master bundle schema yang memvalidasi seluruh koleksi work item dekorasi luar."""

    model_config = ConfigDict(extra="forbid", strict=False)

    items: List[InboundExteriorTaskRowDTO] = Field(..., max_length=200)


# ---------------------------------------------------------------------------
# Master Task Database Registry (Array Collection)
# ---------------------------------------------------------------------------
EXTERIOR_TASK_REGISTRY_COLLECTION: List[Dict[str, Any]] = [
    {"id": "wi_deck_bengkirai", "code": "DL.001", "name": "Pembuatan Lantai Kayu Dek Luar Kolam (Wood Decking / Bengkirai)", "unit": "m²", "sni_ref": "AHSP PUPR", "category": "DEKORASI_LUAR"},
    {"id": "wi_rangka_deck", "code": "DL.002", "name": "Pemasangan Rangka Dudukan Deck Kayu Besi Hollow Galvanis", "unit": "m²", "sni_ref": "AHSP PUPR", "category": "DEKORASI_LUAR"},
    {"id": "wi_cat_deck", "code": "DL.003", "name": "Finishing Deck Kayu dengan Cat Ultran Lasur (Anti Matahari & Air)", "unit": "m²", "sni_ref": "AHSP PUPR", "category": "DEKORASI_LUAR"},
    {"id": "wi_payung_taman", "code": "DL.004", "name": "Pemasangan Payung Taman Besar & Kursi Tidur Kolam (Sun Lounger)", "unit": "set", "sni_ref": "AHSP PUPR", "category": "DEKORASI_LUAR"},
    {"id": "wi_shower_bilas", "code": "DL.005", "name": "Pemasangan Shower Bilas Luar Ruangan (Outdoor Pool Shower Column)", "unit": "unit", "sni_ref": "AHSP PUPR", "category": "DEKORASI_LUAR"},
    {"id": "wi_spout_wall", "code": "DL.006", "name": "Pembuatan Dinding Fitur Pancuran Air (Spout Wall Feature)", "unit": "unit", "sni_ref": "AHSP PUPR", "category": "DEKORASI_LUAR"},
    {"id": "wi_patung_pancuran", "code": "DL.007", "name": "Pemasangan Patung Pancuran Air Kolam (Bahan GRC/Batu Alam)", "unit": "unit", "sni_ref": "AHSP PUPR", "category": "DEKORASI_LUAR"},
    {"id": "wi_fire_pit", "code": "DL.008", "name": "Pembuatan Area Bak Api Unggun Duduk Santai (Sunken Seating Area / Fire Pit)", "unit": "unit", "sni_ref": "AHSP PUPR", "category": "DEKORASI_LUAR"},
    {"id": "wi_pipa_gas_firepit", "code": "DL.009", "name": "Instalasi Pipa Gas & Tungku Fire Pit Outdoor", "unit": "unit", "sni_ref": "AHSP PUPR", "category": "DEKORASI_LUAR"},
    {"id": "wi_neon_flex_taman", "code": "DL.010", "name": "Pemasangan Lampu LED Neon Flex Dekorasi Taman", "unit": "m'", "sni_ref": "AHSP PUPR", "category": "DEKORASI_LUAR"},
    {"id": "wi_jembatan_kayu_kolam", "code": "DL.011", "name": "Pembuatan Jembatan Kayu Penyeberangan Kolam (Footbridge)", "unit": "unit", "sni_ref": "AHSP PUPR", "category": "DEKORASI_LUAR"},
    {"id": "wi_pool_safety_net", "code": "DL.012", "name": "Pemasangan Jaring Pengaman Kolam Anak (Pool Safety Net / Fence)", "unit": "m'", "sni_ref": "AHSP PUPR", "category": "DEKORASI_LUAR"},
    {"id": "wi_gazebo_bambu", "code": "DL.013", "name": "Pembangunan Gazebo Bambu / Kayu Kelapa (Beratap Jerami/Genteng)", "unit": "unit", "sni_ref": "AHSP PUPR", "category": "DEKORASI_LUAR"},
    {"id": "wi_wet_bar", "code": "DL.014", "name": "Pembuatan Bar Basah Tepi Kolam (Poolside Wet Bar) Cor Keramik", "unit": "unit", "sni_ref": "AHSP PUPR", "category": "DEKORASI_LUAR"},
    {"id": "wi_submerged_stools", "code": "DL.015", "name": "Pemasangan Kursi Duduk Dalam Air Kolam (Submerged Pool Bar Stools)", "unit": "unit", "sni_ref": "AHSP PUPR", "category": "DEKORASI_LUAR"},
]

# Extend dengan 20 definisi task dekorasi luar tambahan
EXTERIOR_TASK_REGISTRY_COLLECTION.extend([
    {"id": "wi_tebing_riam", "code": "DL.016", "name": "Pemasangan Ornaments Batu Lapis Dinding Air Terjun (Efek Gemericik)", "unit": "unit", "sni_ref": "AHSP PUPR", "category": "DEKORASI_LUAR"},
    {"id": "wi_pool_storage", "code": "DL.017", "name": "Pembuatan Tempat Penyimpanan Alat Pembersih Kolam (Pool Equipment Storage Box)", "unit": "unit", "sni_ref": "AHSP PUPR", "category": "DEKORASI_LUAR"},
    {"id": "wi_mosquito_trap", "code": "DL.018", "name": "Pemasangan Alat Pengusir Nyamuk Taman Elektrik (Mosquito Trap Outdoor IPX4)", "unit": "unit", "sni_ref": "AHSP PUPR", "category": "DEKORASI_LUAR"},
    {"id": "wi_rock_speaker", "code": "DL.019", "name": "Pemasangan Sistem Musik Luar Ruangan Tahan Cuaca (Outdoor Rock Speakers)", "unit": "unit", "sni_ref": "AHSP PUPR", "category": "DEKORASI_LUAR"},
    {"id": "wi_kabel_speaker_taman", "code": "DL.020", "name": "Instalasi Kabel Jalur Utama Sound System Taman (Bawah Tanah + Konduit)", "unit": "m'", "sni_ref": "AHSP PUPR", "category": "DEKORASI_LUAR"},
    {"id": "wi_misting_system", "code": "DL.021", "name": "Pemasangan Sistem Kabut Taman (Outdoor Misting/Fogging System) Nozzle Mikro", "unit": "set", "sni_ref": "AHSP PUPR", "category": "DEKORASI_LUAR"},
    {"id": "wi_pompa_kabut", "code": "DL.022", "name": "Instalasi Pompa Booster Tekanan Tinggi Sistem Kabut (Minimal 100 Bar)", "unit": "unit", "sni_ref": "AHSP PUPR", "category": "DEKORASI_LUAR"},
    {"id": "wi_hammock_catwalk", "code": "DL.023", "name": "Pembuatan Tempat Berjemur Jaring Gantung Atas Kolam (Over-pool Hammock Catwalk)", "unit": "unit", "sni_ref": "AHSP PUPR", "category": "DEKORASI_LUAR"},
    {"id": "wi_retractable_awning", "code": "DL.024", "name": "Pemasangan Payung Kanopi Lipat Otomatis (Retractable Awning Motorized)", "unit": "unit", "sni_ref": "AHSP PUPR", "category": "DEKORASI_LUAR"},
    {"id": "wi_living_fence", "code": "DL.025", "name": "Pemasangan Pagar Tanaman Hidup (Living Green Fence/Topiary) Pucuk Merah", "unit": "m'", "sni_ref": "AHSP PUPR", "category": "DEKORASI_LUAR"},
    {"id": "wi_topiary_art", "code": "DL.026", "name": "Pekerjaan Pemangkasan Bentuk Seni Pohon (Topiary Art Pruning) Bulat/Spiral", "unit": "unit", "sni_ref": "AHSP PUPR", "category": "DEKORASI_LUAR"},
    {"id": "wi_rumput_sintetis_balkon", "code": "DL.027", "name": "Pemasangan Karpet Rumput Sintetis Lapisan Drainase (Drainage Cell Layer)", "unit": "m²", "sni_ref": "AHSP PUPR", "category": "DEKORASI_LUAR"},
    {"id": "wi_glass_balustrade", "code": "DL.028", "name": "Pemasangan Kaca Pembatas Balkon Taman Atas (Frameless Glass Balustrade)", "unit": "m'", "sni_ref": "AHSP PUPR", "category": "DEKORASI_LUAR"},
    {"id": "wi_geocell", "code": "DL.029", "name": "Pekerjaan Pembuatan Tanah Lereng Penahan Erosi (Geocell Grid System)", "unit": "m²", "sni_ref": "AHSP PUPR", "category": "DEKORASI_LUAR"},
    {"id": "wi_wall_washer_rgb", "code": "DL.030", "name": "Pemasangan Lampu Sorot Fasad Kolam Variasi Warna (Wall Washer RGB Lamp)", "unit": "unit", "sni_ref": "AHSP PUPR", "category": "DEKORASI_LUAR"},
    {"id": "wi_waterproofing_dak_taman", "code": "DL.031", "name": "Pekerjaan Waterproofing Dak Beton Taman Atas (Roof Garden Water Barrier)", "unit": "m²", "sni_ref": "AHSP PUPR", "category": "DEKORASI_LUAR"},
    {"id": "wi_root_barrier", "code": "DL.032", "name": "Pemasangan Lapisan Penahan Akar Tanaman (Root Barrier Sheet) Taman Dak", "unit": "m²", "sni_ref": "AHSP PUPR", "category": "DEKORASI_LUAR"},
    {"id": "wi_rainwater_harvesting", "code": "DL.033", "name": "Instalasi Sistem Penangkap Air Hujan (Rainwater Harvesting Tank) Siram Taman", "unit": "unit", "sni_ref": "AHSP PUPR", "category": "DEKORASI_LUAR"},
    {"id": "wi_bersih_kerak_batu", "code": "DL.034", "name": "Pekerjaan Pembersihan Kerak Batu Alam Berkala Proyek (Cairan Asam Ringan)", "unit": "m²", "sni_ref": "AHSP PUPR", "category": "DEKORASI_LUAR"},
    {"id": "wi_coating_batu_luar", "code": "DL.035", "name": "Pekerjaan Akhir Pelapisan Anti Air Batu Alam (Coating Gloss/Doft)", "unit": "m²", "sni_ref": "AHSP PUPR", "category": "DEKORASI_LUAR"},
])


# ---------------------------------------------------------------------------
# Core Seeding Layer – Pure Domain Injection Pipeline (QS-Safe)
# ---------------------------------------------------------------------------
def load_wi_dekorasi_luar(kg: KnowledgeGraph) -> None:
    """
    Memvalidasi, menginstansiasi, dan menyuntikkan semua task dekorasi luar ke KnowledgeGraph.
    Mencegah kesalahan argumen runtime dan korupsi struktural data dinamis.
    """
    if not isinstance(kg, KnowledgeGraph):
        raise TypeError("Parameter 'kg' harus berupa instance KnowledgeGraph.")

    # 1. GATEWAY SCHEMA VALIDATION
    try:
        validated_bundle = ExteriorTaskBundleDTO(items=EXTERIOR_TASK_REGISTRY_COLLECTION)
    except Exception as exc:
        logger.error("Gagal seed dataset task dekorasi luar. Pelanggaran skema: %s", exc)
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
        logger.debug("Work item dekorasi luar dimuat: %s (%s)", work_item_node_instance.id, work_item_node_instance.code)

    logger.info(
        "Seeder task dekorasi luar selesai: %d master work items terkunci.",
        len(validated_bundle.items),
    )
