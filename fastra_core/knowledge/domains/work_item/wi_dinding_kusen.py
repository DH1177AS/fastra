"""
fastra_core/knowledge/domains/work_item/wi_dinding_kusen.py

Modul pemuatan data work item dinding, kusen, dan fasad ke Knowledge Graph.
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


class ArchitecturalTaskCategory(str, enum.Enum):
    """Klasifikasi taksonomi formal untuk dinding, partisi, bukaan, dan kulit fasad."""

    DINDING = "DINDING"
    KUSEN = "KUSEN"
    FASAD = "FASAD"


# ---------------------------------------------------------------------------
# Inbound DTOs – Pydantic Strict Configuration Gate (Fail-Fast)
# ---------------------------------------------------------------------------
class InboundArchTaskRowDTO(BaseModel):
    """DTO validasi untuk elemen task mentah di dalam paket arsitektural."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, strict=False)

    id: str = Field(..., min_length=5, max_length=64, pattern=r"^wi_[a-z0-9_]+$")
    code: str = Field(..., min_length=2, max_length=32, pattern=r"^DIN\.[0-9]{3}$")
    name: str = Field(..., min_length=5, max_length=512)
    unit: str = Field(..., min_length=1, max_length=16, pattern=r"^(m²|m'|unit|titik|set|buah)$")
    sni_ref: str = Field(..., min_length=2, max_length=128)
    category: ArchitecturalTaskCategory = Field(...)


class ArchTaskBundleDTO(BaseModel):
    """Master bundle schema yang memvalidasi seluruh koleksi work item arsitektural."""

    model_config = ConfigDict(extra="forbid", strict=False)

    items: List[InboundArchTaskRowDTO] = Field(..., max_length=200)


# ---------------------------------------------------------------------------
# Master Task Database Registry (Array Collection)
# ---------------------------------------------------------------------------
ARCH_TASK_REGISTRY_COLLECTION: List[Dict[str, Any]] = [
    {"id": "wi_hebel_lt1", "code": "DIN.001", "name": "Pemasangan Dinding Bata Ringan (Hebel) Tebal 10 cm Lantai 1", "unit": "m²", "sni_ref": "AHSP PUPR", "category": "DINDING"},
    {"id": "wi_thinbed_hebel", "code": "DIN.002", "name": "Penggunaan Semen Mortar Perekat Bata Ringan (Thinbed)", "unit": "m²", "sni_ref": "AHSP PUPR", "category": "DINDING"},
    {"id": "wi_hebel_trasram", "code": "DIN.003", "name": "Pemasangan Dinding Hebel Transram (Kedap Air) Area Kamar Mandi", "unit": "m²", "sni_ref": "AHSP PUPR", "category": "DINDING"},
    {"id": "wi_hebel_lt2", "code": "DIN.004", "name": "Pemasangan Dinding Bata Ringan (Hebel) Tebal 10 cm Lantai 2", "unit": "m²", "sni_ref": "AHSP PUPR", "category": "DINDING"},
    {"id": "wi_bata_merah_taman", "code": "DIN.005", "name": "Pemasangan Pasangan Bata Merah untuk Area Bak Kontrol/Taman", "unit": "m²", "sni_ref": "AHSP PUPR", "category": "DINDING"},
    {"id": "wi_kepalaan_plester", "code": "DIN.006", "name": "Pembuatan Lajur Panduan Tebal Plesteran Dinding (Kepalaan Plester)", "unit": "m²", "sni_ref": "AHSP PUPR", "category": "DINDING"},
    {"id": "wi_kawat_ayam", "code": "DIN.007", "name": "Pemasangan Kawat Ayam Perlindungan Retak Pertemuan Hebel-Beton", "unit": "m'", "sni_ref": "AHSP PUPR", "category": "DINDING"},
    {"id": "wi_plester_dalam", "code": "DIN.008", "name": "Pekerjaan Plesteran Dinding Hebel Dalam Ruangan Campuran Mortar", "unit": "m²", "sni_ref": "SNI 6897", "category": "DINDING"},
    {"id": "wi_plester_luar", "code": "DIN.009", "name": "Pekerjaan Plesteran Dinding Hebel Luar Ruangan (Tahan Cuaca)", "unit": "m²", "sni_ref": "SNI 6897", "category": "DINDING"},
    {"id": "wi_plester_kasar_km", "code": "DIN.010", "name": "Pekerjaan Plesteran Kamar Mandi Kasar sebagai Dudukan Keramik", "unit": "m²", "sni_ref": "AHSP PUPR", "category": "DINDING"},
    {"id": "wi_acian_dalam", "code": "DIN.011", "name": "Pekerjaan Acian Halus Dinding Plesteran Dalam Ruangan", "unit": "m²", "sni_ref": "SNI 6897", "category": "DINDING"},
    {"id": "wi_acian_luar", "code": "DIN.012", "name": "Pekerjaan Acian Halus Dinding Plesteran Luar Ruangan", "unit": "m²", "sni_ref": "SNI 6897", "category": "DINDING"},
    {"id": "wi_amplas_acian", "code": "DIN.013", "name": "Pekerjaan Pengampelasan Permukaan Dinding Acian hingga Mulus", "unit": "m²", "sni_ref": "AHSP PUPR", "category": "DINDING"},
    {"id": "wi_tali_air", "code": "DIN.014", "name": "Pembuatan Detail Garis Celah Dekoratif Luar (Tali Air Minimalis)", "unit": "m'", "sni_ref": "AHSP PUPR", "category": "DINDING"},
    {"id": "wi_corner_bead", "code": "DIN.015", "name": "Pemasangan Profil Sudut PVC (Corner Bead) pada Siku Dinding", "unit": "m'", "sni_ref": "AHSP PUPR", "category": "DINDING"},
    {"id": "wi_kusen_pintu_utama", "code": "DIN.016", "name": "Pemasangan Kusen Pintu Utama Bahan Kayu Jati Oven Finishing Melamik", "unit": "unit", "sni_ref": "SNI 3434", "category": "KUSEN"},
    {"id": "wi_kusen_jendela_aluminium", "code": "DIN.017", "name": "Pemasangan Kusen Jendela Rangka Aluminium 4 Inci Powder Coating White", "unit": "unit", "sni_ref": "AHSP PUPR", "category": "KUSEN"},
    {"id": "wi_kusen_pintu_kamar", "code": "DIN.018", "name": "Pemasangan Kusen Pintu Kamar Tidur Rangka Aluminium 3 Inci", "unit": "unit", "sni_ref": "AHSP PUPR", "category": "KUSEN"},
    {"id": "wi_dynabolt_kusen", "code": "DIN.019", "name": "Pemasangan Sekrup Dynabolt Pengikat Kusen Aluminium ke Dinding", "unit": "titik", "sni_ref": "AHSP PUPR", "category": "KUSEN"},
    {"id": "wi_foam_kusen", "code": "DIN.020", "name": "Penyemprotan Cairan Polyurethane Foam Sela Kusen & Dinding", "unit": "unit", "sni_ref": "AHSP PUPR", "category": "KUSEN"},
    {"id": "wi_daun_pintu_utama", "code": "DIN.021", "name": "Pemasangan Daun Pintu Utama Bahan Kayu Jati Solid Custom", "unit": "unit", "sni_ref": "SNI 3434", "category": "KUSEN"},
    {"id": "wi_daun_pintu_kamar", "code": "DIN.022", "name": "Pemasangan Daun Pintu Kamar Tidur Bahan Engineered Wood (HDF)", "unit": "unit", "sni_ref": "SNI 3434", "category": "KUSEN"},
    {"id": "wi_jendela_casement", "code": "DIN.023", "name": "Pemasangan Daun Jendela Aluminium Model Ayun (Casement)", "unit": "unit", "sni_ref": "AHSP PUPR", "category": "KUSEN"},
    {"id": "wi_jendela_sliding", "code": "DIN.024", "name": "Pemasangan Daun Jendela Aluminium Model Geser (Sliding)", "unit": "unit", "sni_ref": "AHSP PUPR", "category": "KUSEN"},
    {"id": "wi_kaca_polos_5mm", "code": "DIN.025", "name": "Pemasangan Kaca Polos Tebal 5mm pada Daun Jendela Kamar", "unit": "m²", "sni_ref": "SNI 15-0047", "category": "KUSEN"},
    {"id": "wi_kaca_sanblast", "code": "DIN.026", "name": "Pemasangan Kaca Sanblast Buram Tebal 5mm Kamar Mandi", "unit": "m²", "sni_ref": "SNI 15-0047", "category": "KUSEN"},
    {"id": "wi_karet_sealant_kaca", "code": "DIN.027", "name": "Pemasangan Karet Sealant Kaca pada Rangka Daun Jendela", "unit": "m'", "sni_ref": "AHSP PUPR", "category": "KUSEN"},
    {"id": "wi_engsel_pintu", "code": "DIN.028", "name": "Pemasangan Engsel Kupu-Kupu Stainless Steel 4 Inci Pintu Utama", "unit": "set", "sni_ref": "SNI 3434", "category": "KUSEN"},
]

# Perluas array koleksi registri dengan 27 definisi pekerjaan arsitektural kulit luar
ARCH_TASK_REGISTRY_COLLECTION.extend([
    {"id": "wi_engsel_jendela", "code": "DIN.029", "name": "Pemasangan Engsel Jendela Aluminium Model Friction Stay", "unit": "set", "sni_ref": "AHSP PUPR", "category": "KUSEN"},
    {"id": "wi_mortise_lock", "code": "DIN.030", "name": "Pemasangan Rumah Kunci Pintu Utama Sistem Mortise Lock Heavy Duty", "unit": "set", "sni_ref": "SNI 3434", "category": "KUSEN"},
    {"id": "wi_handle_pintu", "code": "DIN.031", "name": "Pemasangan Gagang Pintu (Handle) Stainless Steel Pintu Utama", "unit": "buah", "sni_ref": "SNI 3434", "category": "KUSEN"},
    {"id": "wi_kunci_km", "code": "DIN.032", "name": "Pemasangan Kunci Bulat Kamar Mandi Bahan Kuningan Anti Karat", "unit": "buah", "sni_ref": "AHSP PUPR", "category": "KUSEN"},
    {"id": "wi_flush_bolt", "code": "DIN.033", "name": "Pemasangan Grendel Tanam (Flush Bolt) pada Daun Pintu Ganda", "unit": "buah", "sni_ref": "AHSP PUPR", "category": "KUSEN"},
    {"id": "wi_door_closer", "code": "DIN.034", "name": "Pemasangan Alat Penutup Pintu Otomatis (Door Closer) Hidrolik", "unit": "unit", "sni_ref": "AHSP PUPR", "category": "KUSEN"},
    {"id": "wi_door_stop", "code": "DIN.035", "name": "Pemasangan Penahan Pintu Magnetis (Door Stop) Tanam Lantai", "unit": "buah", "sni_ref": "AHSP PUPR", "category": "KUSEN"},
    {"id": "wi_waterproofing_km1", "code": "DIN.036", "name": "Pelapisan Semen Anti Bocor (Waterproofing Slurry) Lantai Kamar Mandi 1", "unit": "m²", "sni_ref": "AHSP PUPR", "category": "DINDING"},
    {"id": "wi_waterproofing_km2", "code": "DIN.037", "name": "Pelapisan Semen Anti Bocor (Waterproofing Slurry) Lantai Kamar Mandi 2", "unit": "m²", "sni_ref": "AHSP PUPR", "category": "DINDING"},
    {"id": "wi_waterproofing_balkon", "code": "DIN.038", "name": "Pelapisan Semen Anti Bocor (Waterproofing Membran) Area Balkon Atas", "unit": "m²", "sni_ref": "AHSP PUPR", "category": "DINDING"},
    {"id": "wi_batu_alam_fasad", "code": "DIN.039", "name": "Pemasangan Dinding Fasad Luar Bahan Batu Alam Andesit Bakar", "unit": "m²", "sni_ref": "AHSP PUPR", "category": "FASAD"},
    {"id": "wi_batu_alam_sirih", "code": "DIN.040", "name": "Pemasangan Batu Alam Tempel Pola Susun Sirih Dinding Depan", "unit": "m²", "sni_ref": "AHSP PUPR", "category": "FASAD"},
    {"id": "wi_coating_batu_alam", "code": "DIN.041", "name": "Pengolesan Cairan Pelindung Batu Alam (Coating Matte/Glossy)", "unit": "m²", "sni_ref": "AHSP PUPR", "category": "FASAD"},
    {"id": "wi_acp_panel", "code": "DIN.042", "name": "Pemasangan Dinding Fasad Bahan ACP (Aluminium Composite Panel)", "unit": "m²", "sni_ref": "AHSP PUPR", "category": "FASAD"},
    {"id": "wi_rangka_acp", "code": "DIN.043", "name": "Pembuatan Rangka Besi Kotak Hollow Penyangga Lembaran ACP", "unit": "m²", "sni_ref": "AHSP PUPR", "category": "FASAD"},
    {"id": "wi_acp_sekrup", "code": "DIN.044", "name": "Pemasangan Lembaran ACP Pengunci Sekrup Drilling Tanam", "unit": "m²", "sni_ref": "AHSP PUPR", "category": "FASAD"},
    {"id": "wi_nat_acp", "code": "DIN.045", "name": "Pengisian Nat Lembaran ACP Paku Silikon Sealant Eksterior", "unit": "m'", "sni_ref": "AHSP PUPR", "category": "FASAD"},
    {"id": "wi_kaca_mati_8mm", "code": "DIN.046", "name": "Pemasangan Jendela Kaca Mati Ukuran Besar Fasad Depan (Tebal 8mm)", "unit": "m²", "sni_ref": "AHSP PUPR", "category": "FASAD"},
    {"id": "wi_wpc_dinding_luar", "code": "DIN.047", "name": "Pemasangan Ornamen Kisi-Kisi Kayu Sintetis (WPC) Dinding Luar", "unit": "m²", "sni_ref": "AHSP PUPR", "category": "FASAD"},
    {"id": "wi_keramik_dinding_km", "code": "DIN.048", "name": "Pemasangan Dinding Kamar Mandi Bahan Keramik 30x60 cm Motif Marmer", "unit": "m²", "sni_ref": "SNI 7395", "category": "DINDING"},
    {"id": "wi_grouting_nat_keramik", "code": "DIN.049", "name": "Pengisian Nat Keramik Dinding Kamar Mandi Paku Semen Warna Grout", "unit": "m²", "sni_ref": "AHSP PUPR", "category": "DINDING"},
    {"id": "wi_batako_pagar", "code": "DIN.050", "name": "Pasangan Batako untuk Konstruksi Pagar Keliling Samping Rumah", "unit": "m²", "sni_ref": "AHSP PUPR", "category": "DINDING"},
    {"id": "wi_plester_pagar", "code": "DIN.051", "name": "Pekerjaan Plesteran & Acian Halus Pagar Keliling Samping", "unit": "m²", "sni_ref": "AHSP PUPR", "category": "DINDING"},
    {"id": "wi_topi_beton", "code": "DIN.052", "name": "Pembuatan Topi-Topi Beton Pelindung Jendela dari Air Hujan", "unit": "m'", "sni_ref": "AHSP PUPR", "category": "DINDING"},
    {"id": "wi_glass_block", "code": "DIN.053", "name": "Pemasangan Ornamen Glass Block Tebal pada Dinding Tangga", "unit": "m²", "sni_ref": "AHSP PUPR", "category": "DINDING"},
    {"id": "wi_kamprot_ekspos", "code": "DIN.054", "name": "Pekerjaan Pembentukan Tekstur Kamprot Semen Semi-Kasar Dinding Luar", "unit": "m²", "sni_ref": "AHSP PUPR", "category": "DINDING"},
    {"id": "wi_acian_ekspos_clear", "code": "DIN.055", "name": "Pekerjaan Finishing Acian Semen Ekspos Halus Proteksi Clear Coating", "unit": "m²", "sni_ref": "AHSP PUPR", "category": "DINDING"},
])


# ---------------------------------------------------------------------------
# Core Seeding Layer – Pure Domain Injection Pipeline (QS-Safe)
# ---------------------------------------------------------------------------
def load_wi_dinding_kusen(kg: KnowledgeGraph) -> None:
    """
    Memvalidasi, menginstansiasi, dan menyuntikkan seluruh item pekerjaan arsitektur ke KnowledgeGraph.
    Mencegah pergeseran indeks susunan variabel memori RAM dengan pemetaan eksplisit bernama.
    """
    if not isinstance(kg, KnowledgeGraph):
        raise TypeError("Parameter 'kg' wajib berupa instance KnowledgeGraph.")

    # 1. GATEWAY SCHEMA VALIDATION
    try:
        validated_bundle = ArchTaskBundleDTO(items=ARCH_TASK_REGISTRY_COLLECTION)
    except Exception as exc:
        logger.error("Gagal memuat repositori pekerjaan dinding kusen. Pelanggaran skema data: %s", exc)
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
        logger.debug("Work item dinding/kusen dimuat: %s (%s)", work_item_node_instance.id, work_item_node_instance.code)

    logger.info(
        "Modul data master pekerjaan dinding, kusen, dan fasad arsitektural sukses ditayangkan: %d master work items terkunci.",
        len(validated_bundle.items),
    )
