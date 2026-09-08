"""
fastra_core/knowledge/domains/work_item/wi_atap.py

Modul pemuatan data work item pekerjaan atap ke Knowledge Graph.
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


class RoofTaskCategory(str, enum.Enum):
    """Klasifikasi taksonomi formal untuk sub-divisi atap dan penutup struktur."""

    ATAP = "ATAP"


# ---------------------------------------------------------------------------
# Inbound DTOs – Pydantic Strict Configuration Gate (Fail-Fast)
# ---------------------------------------------------------------------------
class InboundRoofTaskRowDTO(BaseModel):
    """DTO validasi untuk elemen task mentah di dalam paket atap."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, strict=False)

    id: str = Field(..., min_length=5, max_length=64, pattern=r"^wi_[a-z0-9_]+$")
    code: str = Field(..., min_length=2, max_length=32, pattern=r"^ATP\.[0-9]{3}$")
    name: str = Field(..., min_length=5, max_length=512)
    unit: str = Field(..., min_length=1, max_length=16, pattern=r"^(titik|unit|m²|m'|buah)$")
    sni_ref: str = Field(..., min_length=2, max_length=128)
    category: RoofTaskCategory = Field(...)


class RoofTaskBundleDTO(BaseModel):
    """Bundel master schema yang memvalidasi seluruh koleksi work item atap."""

    model_config = ConfigDict(extra="forbid", strict=False)

    items: List[InboundRoofTaskRowDTO] = Field(..., max_length=200)


# ---------------------------------------------------------------------------
# Master Task Database Registry (Array Collection)
# ---------------------------------------------------------------------------
ROOF_TASK_REGISTRY_COLLECTION: List[Dict[str, Any]] = [
    {"id": "wi_angkur_baja_atap", "code": "ATP.001", "name": "Pemasangan Baut Angkur Baja (Anchor Bolt) di Atas Ring Balk", "unit": "titik", "sni_ref": "AHSP PUPR", "category": "ATAP"},
    {"id": "wi_baseplate_atap", "code": "ATP.002", "name": "Pengelasan Pelat Dudukan Baja Kuda-Kuda Atas Ring Balk", "unit": "unit", "sni_ref": "SNI 1729", "category": "ATAP"},
    {"id": "wi_kudakuda_fab", "code": "ATP.003", "name": "Fabrikasi Kuda-Kuda Atap Baja Ringan Kanal C Tinggi Standar", "unit": "m²", "sni_ref": "SNI 7973", "category": "ATAP"},
    {"id": "wi_kudakuda_assembly", "code": "ATP.004", "name": "Perakitan Kuda-Kuda Atap Baja Ringan di Area Bawah Lapangan", "unit": "m²", "sni_ref": "SNI 7973", "category": "ATAP"},
    {"id": "wi_kudakuda_erection", "code": "ATP.005", "name": "Pengangkatan Kuda-Kuda Baja Ringan ke Atas Ring Balk Manual", "unit": "m²", "sni_ref": "AHSP PUPR", "category": "ATAP"},
    {"id": "wi_bracing_atap", "code": "ATP.006", "name": "Pemasangan Batang Pengikat Antar Kuda-Kuda (Bracing)", "unit": "m'", "sni_ref": "SNI 7973", "category": "ATAP"},
    {"id": "wi_reng_atap", "code": "ATP.007", "name": "Pemasangan Batang Horisontal Penyangga Genteng (Reng) Baja Ringan", "unit": "m'", "sni_ref": "SNI 7973", "category": "ATAP"},
    {"id": "wi_jarak_reng", "code": "ATP.008", "name": "Pengukuran Jarak Antar Reng Sesuai Spesifikasi Panjang Genteng", "unit": "m²", "sni_ref": "AHSP PUPR", "category": "ATAP"},
    {"id": "wi_jurai_dalam", "code": "ATP.009", "name": "Pemasangan Batang Jurai Dalam / Jurai Luar Baja Ringan", "unit": "m'", "sni_ref": "SNI 7973", "category": "ATAP"},
    {"id": "wi_foil_single", "code": "ATP.010", "name": "Pemasangan Lapisan Aluminium Foil Single Sided Penahan Panas", "unit": "m²", "sni_ref": "AHSP PUPR", "category": "ATAP"},
    {"id": "wi_wiremesh_foil", "code": "ATP.011", "name": "Pemasangan Jaring Kawat Penyangga Aluminium Foil (Wire Mesh Net)", "unit": "m²", "sni_ref": "AHSP PUPR", "category": "ATAP"},
    {"id": "wi_glasswool_atap", "code": "ATP.012", "name": "Pemasangan Lapisan Peredam Suara Hujan Lembaran Glasswool", "unit": "m²", "sni_ref": "AHSP PUPR", "category": "ATAP"},
    {"id": "wi_genteng_utama", "code": "ATP.013", "name": "Pemasangan Genteng Utama (Genteng Keramik Berglazur)", "unit": "m²", "sni_ref": "SNI 0096", "category": "ATAP"},
    {"id": "wi_genteng_skrup", "code": "ATP.014", "name": "Penguncian Genteng Utama Paku Skrup Galvalum pada Batang Reng", "unit": "titik", "sni_ref": "AHSP PUPR", "category": "ATAP"},
    {"id": "wi_genteng_nok", "code": "ATP.015", "name": "Pemasangan Genteng Nok / Bubungan Atas Pertemuan Atap", "unit": "m'", "sni_ref": "SNI 0096", "category": "ATAP"},
]

# Extend dengan 15 definisi task atap tambahan
ROOF_TASK_REGISTRY_COLLECTION.extend([
    {"id": "wi_adukan_nok", "code": "ATP.016", "name": "Pasangan Adukan Semen Warna untuk Pengikat Genteng Nok", "unit": "m'", "sni_ref": "AHSP PUPR", "category": "ATAP"},
    {"id": "wi_flashing_atap", "code": "ATP.017", "name": "Pemasangan Flashing Seng/Aluminium Pembatas Atap & Dinding Tetangga", "unit": "m'", "sni_ref": "AHSP PUPR", "category": "ATAP"},
    {"id": "wi_talang_gantung", "code": "ATP.018", "name": "Pemasangan Talang Air Horisontal Bahan Fiberglass Gantung", "unit": "m'", "sni_ref": "AHSP PUPR", "category": "ATAP"},
    {"id": "wi_braket_talang", "code": "ATP.019", "name": "Pemasangan Braket Besi Penyangga Talang Gantung Tiap Jarak 1m", "unit": "buah", "sni_ref": "AHSP PUPR", "category": "ATAP"},
    {"id": "wi_corong_talang", "code": "ATP.020", "name": "Pemasangan Corong Output Jalur Talang Gantung menuju Pipa Turun", "unit": "titik", "sni_ref": "AHSP PUPR", "category": "ATAP"},
    {"id": "wi_skylight", "code": "ATP.021", "name": "Pemasangan Atap Kaca Transparan (Skylight) Rangka Besi Kotak", "unit": "m²", "sni_ref": "AHSP PUPR", "category": "ATAP"},
    {"id": "wi_silikon_skylight", "code": "ATP.022", "name": "Pemasangan Lapisan Karet Silikon Sealant Sambungan Atap Skylight", "unit": "m'", "sni_ref": "AHSP PUPR", "category": "ATAP"},
    {"id": "wi_kanopi_polycarbonate", "code": "ATP.023", "name": "Pemasangan Penutup Atap Kanopi Belakang Bahan Polycarbonate", "unit": "m²", "sni_ref": "AHSP PUPR", "category": "ATAP"},
    {"id": "wi_skrup_polycarbonate", "code": "ATP.024", "name": "Pemasangan Skrup Atap Polycarbonate Lengkap dengan Karet Ring", "unit": "titik", "sni_ref": "AHSP PUPR", "category": "ATAP"},
    {"id": "wi_lisplang_grc", "code": "ATP.025", "name": "Pemasangan Lisplang Papan Fiber Semen (GRC) Pinggiran Atap", "unit": "m'", "sni_ref": "AHSP PUPR", "category": "ATAP"},
    {"id": "wi_cat_lisplang", "code": "ATP.026", "name": "Pengecatan Lembaran Lisplang GRC Paku Cat Minyak Eksterior", "unit": "m'", "sni_ref": "AHSP PUPR", "category": "ATAP"},
    {"id": "wi_ventilasi_atap", "code": "ATP.027", "name": "Pemasangan Ventilasi Atap Bahan Aluminium Louver Kisi-Kisi", "unit": "unit", "sni_ref": "AHSP PUPR", "category": "ATAP"},
    {"id": "wi_kawat_nyamuk_atap", "code": "ATP.028", "name": "Pemasangan Kawat Nyamuk Baja pada Kisi-Kisi Ventilasi Atap", "unit": "unit", "sni_ref": "AHSP PUPR", "category": "ATAP"},
    {"id": "wi_terminal_petir", "code": "ATP.029", "name": "Pemasangan Pemutus Arus Petir Terminal Udara (Tombak Tembaga) Atap", "unit": "unit", "sni_ref": "SNI 03-7015", "category": "ATAP"},
    {"id": "wi_kabel_petir_turun", "code": "ATP.030", "name": "Penarikan Kabel Tembaga BC 50mm dari Atap Turun ke Tanah", "unit": "m'", "sni_ref": "SNI 03-7015", "category": "ATAP"},
])


# ---------------------------------------------------------------------------
# Core Seeding Layer – Pure Domain Injection Pipeline (QS-Safe)
# ---------------------------------------------------------------------------
def load_wi_atap(kg: KnowledgeGraph) -> None:
    """
    Memvalidasi, menginstansiasi, dan menyuntikkan semua task atap ke KnowledgeGraph.
    Mencegah kesalahan argumen runtime dan korupsi struktural data dinamis.
    """
    if not isinstance(kg, KnowledgeGraph):
        raise TypeError("Parameter 'kg' harus berupa instance KnowledgeGraph.")

    # 1. GATEWAY SCHEMA VALIDATION
    try:
        validated_bundle = RoofTaskBundleDTO(items=ROOF_TASK_REGISTRY_COLLECTION)
    except Exception as exc:
        logger.error("Gagal seed dataset task atap. Pelanggaran skema: %s", exc)
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
        logger.debug("Work item atap dimuat: %s (%s)", work_item_node_instance.id, work_item_node_instance.code)

    logger.info(
        "Seeder task atap selesai: %d master work items terkunci.",
        len(validated_bundle.items),
    )
