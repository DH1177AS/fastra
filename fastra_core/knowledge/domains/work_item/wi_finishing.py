"""
fastra_core/knowledge/domains/work_item/wi_finishing.py

Modul pemuatan data work item finishing ke Knowledge Graph.
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


class FinishingTaskCategory(str, enum.Enum):
    """Klasifikasi taksonomi formal untuk lantai, plafon, pengecatan, dan styling interior."""

    FINISHING = "FINISHING"
    LANTAI = "LANTAI"
    PLAFON = "PLAFON"
    CAT = "CAT"
    INTERIOR = "INTERIOR"


# ---------------------------------------------------------------------------
# Inbound DTOs – Pydantic Strict Configuration Gate (Fail-Fast)
# ---------------------------------------------------------------------------
class InboundFinishingTaskRowDTO(BaseModel):
    """DTO validasi untuk elemen task mentah di dalam paket finishing."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, strict=False)

    id: str = Field(..., min_length=5, max_length=64, pattern=r"^wi_[a-z0-9_]+$")
    code: str = Field(..., min_length=2, max_length=32, pattern=r"^FIN\.[0-9]{3}$")
    name: str = Field(..., min_length=5, max_length=512)
    unit: str = Field(..., min_length=1, max_length=16, pattern=r"^(m²|m'|titik)$")
    sni_ref: str = Field(..., min_length=2, max_length=128)
    category: FinishingTaskCategory = Field(...)


class FinishingTaskBundleDTO(BaseModel):
    """Master bundle schema yang memvalidasi seluruh koleksi work item finishing."""

    model_config = ConfigDict(extra="forbid", strict=False)

    items: List[InboundFinishingTaskRowDTO] = Field(..., max_length=200)


# ---------------------------------------------------------------------------
# Master Task Database Registry (Array Collection)
# ---------------------------------------------------------------------------
FINISHING_TASK_REGISTRY_COLLECTION: List[Dict[str, Any]] = [
    {"id": "wi_screeding_kt1", "code": "FIN.001", "name": "Pekerjaan Perataan Lantai Pasir Semen (Screeding) Kamar Tidur 1", "unit": "m²", "sni_ref": "AHSP PUPR", "category": "FINISHING"},
    {"id": "wi_screeding_rt", "code": "FIN.002", "name": "Pekerjaan Perataan Lantai Pasir Semen (Screeding) Ruang Tamu", "unit": "m²", "sni_ref": "AHSP PUPR", "category": "FINISHING"},
    {"id": "wi_screeding_kt2", "code": "FIN.003", "name": "Pekerjaan Perataan Lantai Pasir Semen (Screeding) Kamar Tidur 2", "unit": "m²", "sni_ref": "AHSP PUPR", "category": "FINISHING"},
    {"id": "wi_granit_rt", "code": "FIN.004", "name": "Pemasangan Lantai Granit Tile Ukuran 60x60 cm Ruang Tamu Utama", "unit": "m²", "sni_ref": "SNI 7395", "category": "LANTAI"},
    {"id": "wi_granit_kt1", "code": "FIN.005", "name": "Pemasangan Granit Tile Ukuran 60x60 cm Kamar Tidur Lantai 1", "unit": "m²", "sni_ref": "SNI 7395", "category": "LANTAI"},
    {"id": "wi_granit_keluarga_lt2", "code": "FIN.006", "name": "Pemasangan Granit Tile Ukuran 60x60 cm Ruang Keluarga Lantai 2", "unit": "m²", "sni_ref": "SNI 7395", "category": "LANTAI"},
    {"id": "wi_tile_adhesive", "code": "FIN.007", "name": "Penggunaan Semen Instan Pengikat Granit (Tile Adhesive Premium)", "unit": "m²", "sni_ref": "AHSP PUPR", "category": "LANTAI"},
    {"id": "wi_keramik_km1", "code": "FIN.008", "name": "Pemasangan Lantai Keramik Kasar Anti Slip 30x30 cm Kamar Mandi 1", "unit": "m²", "sni_ref": "SNI 7395", "category": "LANTAI"},
    {"id": "wi_keramik_km2", "code": "FIN.009", "name": "Pemasangan Lantai Keramik Kasar Anti Slip 30x30 cm Kamar Mandi 2", "unit": "m²", "sni_ref": "SNI 7395", "category": "LANTAI"},
    {"id": "wi_keramik_carport", "code": "FIN.010", "name": "Pemasangan Lantai Keramik Kasar 40x40 cm Area Carport Depan", "unit": "m²", "sni_ref": "SNI 7395", "category": "LANTAI"},
    {"id": "wi_step_nosing", "code": "FIN.011", "name": "Pemasangan Keramik Granit Tile Khusus Trap Anak Tangga (Step Nosing)", "unit": "m'", "sni_ref": "AHSP PUPR", "category": "LANTAI"},
    {"id": "wi_riser_keramik", "code": "FIN.012", "name": "Pemasangan Keramik Bagian Vertikal Anak Tangga (Riser)", "unit": "m'", "sni_ref": "AHSP PUPR", "category": "LANTAI"},
    {"id": "wi_bullnose", "code": "FIN.013", "name": "Pemotongan Pinggiran Granit Tile Metode Bullnose / Siku Tumpul", "unit": "m'", "sni_ref": "AHSP PUPR", "category": "LANTAI"},
    {"id": "wi_plin_granit", "code": "FIN.014", "name": "Pemasangan Plin Granit Tile Tinggi 10 cm Batas Bawah Dinding", "unit": "m'", "sni_ref": "AHSP PUPR", "category": "LANTAI"},
    {"id": "wi_epoxy_grout", "code": "FIN.015", "name": "Pekerjaan Pembersihan Sela Ubin & Pengisian Nat Granit Paku Epoxy Grout", "unit": "m²", "sni_ref": "AHSP PUPR", "category": "LANTAI"},
    {"id": "wi_vinyl_lantai", "code": "FIN.016", "name": "Pemasangan Lantai Kayu Vinyl Tebal 4mm Sistem Click Kamar Utama", "unit": "m²", "sni_ref": "AHSP PUPR", "category": "LANTAI"},
    {"id": "wi_foam_underlay", "code": "FIN.017", "name": "Pemasangan Lapisan Foam Underlayment Sebelum Pasang Lantai Vinyl", "unit": "m²", "sni_ref": "AHSP PUPR", "category": "LANTAI"},
    {"id": "wi_list_transisi", "code": "FIN.018", "name": "Pemasangan List Transisi Aluminium Batas Granit & Vinyl Lantai", "unit": "m'", "sni_ref": "AHSP PUPR", "category": "LANTAI"},
    {"id": "wi_rangka_plafon_2x4", "code": "FIN.019", "name": "Pemasangan Rangka Plafon Besi Hollow Galvalum 2x4 cm Ruang Tamu", "unit": "m²", "sni_ref": "AHSP PUPR", "category": "PLAFON"},
    {"id": "wi_rangka_plafon_4x4", "code": "FIN.020", "name": "Pemasangan Rangka Plafon Besi Hollow Galvalum 4x4 cm Rangka Induk", "unit": "m²", "sni_ref": "AHSP PUPR", "category": "PLAFON"},
    {"id": "wi_kawat_gantung_plafon", "code": "FIN.021", "name": "Pemasangan Kawat Penggantung Rangka Plafon Besi ke Plat Dak/Kaso", "unit": "titik", "sni_ref": "AHSP PUPR", "category": "PLAFON"},
    {"id": "wi_gypsum_9mm", "code": "FIN.022", "name": "Pemasangan Lembaran Papan Gipsum Tebal 9mm untuk Plafon Dalam", "unit": "m²", "sni_ref": "AHSP PUPR", "category": "PLAFON"},
    {"id": "wi_grc_plafon_km", "code": "FIN.023", "name": "Pemasangan Lembaran Papan GRC Board Tahan Lembab Plafon Kamar Mandi", "unit": "m²", "sni_ref": "AHSP PUPR", "category": "PLAFON"},
    {"id": "wi_grc_plafon_teras", "code": "FIN.024", "name": "Pemasangan Lembaran Papan GRC Board Plafon Area Teras Luar", "unit": "m²", "sni_ref": "AHSP PUPR", "category": "PLAFON"},
    {"id": "wi_drywall_screw", "code": "FIN.025", "name": "Pemasangan Sekrup Khusus Gipsum (Drywall Screw) Jarak Per 20 cm", "unit": "titik", "sni_ref": "AHSP PUPR", "category": "PLAFON"},
    {"id": "wi_fiber_tape", "code": "FIN.026", "name": "Pemasangan Kassa Kain Fiber (Fiber Tape) Sambungan Papan Gipsum", "unit": "m'", "sni_ref": "AHSP PUPR", "category": "PLAFON"},
    {"id": "wi_kompon_plafon", "code": "FIN.027", "name": "Pekerjaan Penutupan Sela Sambungan Gipsum Paku Bubuk Kompon Plafon", "unit": "m'", "sni_ref": "AHSP PUPR", "category": "PLAFON"},
]

# Perluas array koleksi registri dengan 28 definisi pekerjaan finishing tambahan
FINISHING_TASK_REGISTRY_COLLECTION.extend([
    {"id": "wi_amplas_kompon", "code": "FIN.028", "name": "Pekerjaan Pengampelasan Sambungan Kompon Plafon hingga Rata", "unit": "m'", "sni_ref": "AHSP PUPR", "category": "PLAFON"},
    {"id": "wi_drop_ceiling", "code": "FIN.029", "name": "Pembuatan Variasi Plafon Turun Tingkat (Drop Ceiling) Ruang Tamu", "unit": "m²", "sni_ref": "AHSP PUPR", "category": "PLAFON"},
    {"id": "wi_list_profil_gypsum", "code": "FIN.030", "name": "Pemasangan List Profil Gipsum Lebar 5 cm Keliling Tepi Plafon", "unit": "m'", "sni_ref": "AHSP PUPR", "category": "PLAFON"},
    {"id": "wi_plamir_dinding", "code": "FIN.031", "name": "Pekerjaan Plamir Dasar Dinding Interior Lapisan Pengisi Pori-Pori", "unit": "m²", "sni_ref": "SNI 2837", "category": "CAT"},
    {"id": "wi_amplas_plamir", "code": "FIN.032", "name": "Pekerjaan Pengampelasan Lapisan Plamir Dinding Interior", "unit": "m²", "sni_ref": "SNI 2837", "category": "CAT"},
    {"id": "wi_cat_dasar_interior", "code": "FIN.033", "name": "Pengecatan Cat Dasar Interior Tahan Alkali (Alkali Resisting Primer)", "unit": "m²", "sni_ref": "SNI 2837", "category": "CAT"},
    {"id": "wi_cat_interior_1", "code": "FIN.034", "name": "Pengecatan Cat Utama Interior Warna Pilihan Lapis 1", "unit": "m²", "sni_ref": "SNI 2837", "category": "CAT"},
    {"id": "wi_cat_interior_2", "code": "FIN.035", "name": "Pengecatan Cat Utama Interior Warna Pilihan Lapis 2 (Warna Solid)", "unit": "m²", "sni_ref": "SNI 2837", "category": "CAT"},
    {"id": "wi_cat_interior_3", "code": "FIN.036", "name": "Pengecatan Cat Utama Interior Warna Pilihan Lapis 3 (Finishing Akhir)", "unit": "m²", "sni_ref": "SNI 2837", "category": "CAT"},
    {"id": "wi_plamir_plafon", "code": "FIN.037", "name": "Pekerjaan Plamir & Pengampelasan Permukaan Plafon Gipsum", "unit": "m²", "sni_ref": "AHSP PUPR", "category": "CAT"},
    {"id": "wi_cat_plafon_1", "code": "FIN.038", "name": "Pengecatan Plafon Gipsum Dalam Warna Putih Matt Khusus Plafon Lapis 1", "unit": "m²", "sni_ref": "AHSP PUPR", "category": "CAT"},
    {"id": "wi_cat_plafon_2", "code": "FIN.039", "name": "Pengecatan Plafon Gipsum Dalam Warna Putih Matt Khusus Plafon Lapis 2", "unit": "m²", "sni_ref": "AHSP PUPR", "category": "CAT"},
    {"id": "wi_cat_dasar_luar", "code": "FIN.040", "name": "Pengecatan Dinding Luar Lapisan Cat Dasar Anti Karat/Zat Kapur", "unit": "m²", "sni_ref": "SNI 2837", "category": "CAT"},
    {"id": "wi_cat_eksterior_1", "code": "FIN.041", "name": "Pengecatan Dinding Luar Cat Utama Tahan Cuaca Ekstrem (Weathershield) Lapis 1", "unit": "m²", "sni_ref": "SNI 2837", "category": "CAT"},
    {"id": "wi_cat_eksterior_2", "code": "FIN.042", "name": "Pengecatan Dinding Luar Cat Utama Tahan Cuaca Ekstrem (Weathershield) Lapis 2", "unit": "m²", "sni_ref": "SNI 2837", "category": "CAT"},
    {"id": "wi_cat_anti_jamur", "code": "FIN.043", "name": "Pengecatan Lapisan Cat Anti Jamur/Lumut pada Samping Pagar Rumah", "unit": "m²", "sni_ref": "SNI 2837", "category": "CAT"},
    {"id": "wi_cat_duco_pintu", "code": "FIN.044", "name": "Finishing Cat Duco Warna Putih Semprot Daun Pintu Kamar", "unit": "m²", "sni_ref": "SNI 2837", "category": "CAT"},
    {"id": "wi_politur_pintu", "code": "FIN.045", "name": "Finishing Kuas Politur Kayu / Melamik Daun Pintu Utama Kayu Jati", "unit": "m²", "sni_ref": "SNI 2837", "category": "CAT"},
    {"id": "wi_wallpaper", "code": "FIN.046", "name": "Pemasangan Wallpaper Dinding Motif Minimalis Kamar Tidur Utama", "unit": "m²", "sni_ref": "AHSP PUPR", "category": "INTERIOR"},
    {"id": "wi_lem_wallpaper", "code": "FIN.047", "name": "Pengolesan Lem Khusus Wallpaper Premium pada Dinding Acian Mulus", "unit": "m²", "sni_ref": "AHSP PUPR", "category": "INTERIOR"},
    {"id": "wi_padded_wall", "code": "FIN.048", "name": "Pemasangan Panel Dinding Kain/Busa Empuk (Padded Wall Panel) Kepala Ranjang", "unit": "m²", "sni_ref": "AHSP PUPR", "category": "INTERIOR"},
    {"id": "wi_cermin_bevel", "code": "FIN.049", "name": "Pemasangan Kaca Cermin Besar Bevel Tempel Dinding Ruang Makan", "unit": "m²", "sni_ref": "AHSP PUPR", "category": "INTERIOR"},
    {"id": "wi_railing_tangga_besi", "code": "FIN.050", "name": "Pemasangan Railing Tangga Bahan Besi Hollow Minimalis Cat Hitam", "unit": "m'", "sni_ref": "AHSP PUPR", "category": "INTERIOR"},
    {"id": "wi_handrail_kayu", "code": "FIN.051", "name": "Pemasangan Pegangan Tangan Railing Tangga (Handrail) Bahan Kayu Kamper", "unit": "m'", "sni_ref": "AHSP PUPR", "category": "INTERIOR"},
    {"id": "wi_railing_balkon", "code": "FIN.052", "name": "Pemasangan Railing Pembatas Balkon Atas Bahan Besi & Kaca Tempered", "unit": "m'", "sni_ref": "AHSP PUPR", "category": "INTERIOR"},
    {"id": "wi_sekat_foyer", "code": "FIN.053", "name": "Pemasangan Kisi-Kisi Sekat Ruangan Pembatas Foyer & Ruang Tamu Bahan Kayu", "unit": "m²", "sni_ref": "AHSP PUPR", "category": "INTERIOR"},
    {"id": "wi_bata_terakota", "code": "FIN.054", "name": "Pemasangan Variasi Batu Bata Tempel Terakota Dinding Interior Belakang", "unit": "m²", "sni_ref": "AHSP PUPR", "category": "INTERIOR"},
    {"id": "wi_karpet_tile", "code": "FIN.055", "name": "Pemasangan Karpet Tile Lantai Ruang Kerja / Studio Interior Home Teater", "unit": "m²", "sni_ref": "AHSP PUPR", "category": "INTERIOR"},
])


# ---------------------------------------------------------------------------
# Core Seeding Layer – Pure Domain Injection Pipeline (QS-Safe)
# ---------------------------------------------------------------------------
def load_wi_finishing(kg: KnowledgeGraph) -> None:
    """
    Memvalidasi, menginstansiasi, dan menyuntikkan seluruh item pekerjaan finishing ke KnowledgeGraph.
    Mencegah pergeseran indeks susunan variabel memori RAM dengan pemetaan eksplisit bernama.
    """
    if not isinstance(kg, KnowledgeGraph):
        raise TypeError("Parameter 'kg' wajib berupa instance KnowledgeGraph.")

    # 1. GATEWAY SCHEMA VALIDATION
    try:
        validated_bundle = FinishingTaskBundleDTO(items=FINISHING_TASK_REGISTRY_COLLECTION)
    except Exception as exc:
        logger.error("Gagal memuat repositori pekerjaan finishing arsitektural. Pelanggaran skema data: %s", exc)
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
        logger.debug("Work item finishing dimuat: %s (%s)", work_item_node_instance.id, work_item_node_instance.code)

    logger.info(
        "Modul data master pekerjaan lantai, plafon, dan dekorasi interior sukses ditayangkan: %d master work items terkunci.",
        len(validated_bundle.items),
    )
