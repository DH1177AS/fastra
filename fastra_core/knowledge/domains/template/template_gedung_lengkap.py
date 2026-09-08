"""
fastra_core/knowledge/domains/template/template_gedung_lengkap.py

Modul template klasifikasi pekerjaan gedung lengkap (10 divisi ACES-300).
Menyediakan peta klasifikasi work item per divisi dan sub-divisi untuk
keperluan standarisasi penamaan dan pengelompokan pekerjaan.

Prinsip:
- Registry klasifikasi bersifat immutable (tidak dapat dimutasi dari luar).
- Validasi struktur menggunakan Pydantic DTO (fail-fast).
- Tidak ada efek samping pada KnowledgeGraph; hanya mengembalikan salinan data.
"""

from __future__ import annotations

import enum
import logging
from types import MappingProxyType
from typing import Any, Dict, List

from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger("fastra.knowledge")


class ACES300DivisionCode(str, enum.Enum):
    """Token divisi alfanumerik formal berdasarkan Spesifikasi ACES-300 Seksi 7.2."""

    PREP = "PREP"
    TNH = "TNH"
    FND = "FND"
    STR = "STR"
    DIN = "DIN"
    LNT = "LNT"
    PLF = "PLF"
    ATP = "ATP"
    KUS = "KUS"
    MEP = "MEP"


# ---------------------------------------------------------------------------
# Outbound Integrity DTOs – Pydantic Strict Configuration Gate (Fail-Fast)
# ---------------------------------------------------------------------------
class DivisionDefinitionDTO(BaseModel):
    """Skema definisi struktural untuk satu divisi ACES-300."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, strict=True)

    code: ACES300DivisionCode = Field(...)
    sub_divisi: Dict[str, List[str]] = Field(..., max_length=50)


class BuildingClassificationTemplateDTO(BaseModel):
    """Skema bundel konfigurasi root yang memvalidasi seluruh manifes 10 divisi."""

    model_config = ConfigDict(extra="forbid", strict=True)

    divisions: Dict[str, DivisionDefinitionDTO] = Field(..., max_length=10)


# ---------------------------------------------------------------------------
# Master Classification Data Dictionary Registry
# ---------------------------------------------------------------------------
_MASTER_CLASSIFICATION_REGISTRY_RAW: Dict[str, Dict[str, Any]] = {
    "DIV-01 Pekerjaan Persiapan": {
        "code": ACES300DivisionCode.PREP,
        "sub_divisi": {
            "1.1 Pembersihan Lahan": ["wi_pembersihan_lahan", "wi_clearing"],
            "1.2 Bouwplank": ["wi_bouwplank"],
            "1.3 Mobilisasi/Demobilisasi": ["wi_mobilisasi", "wi_demobilisasi"],
            "1.4 Pengukuran": ["wi_pengukuran", "wi_survey"],
        },
    },
    "DIV-02 Pekerjaan Tanah": {
        "code": ACES300DivisionCode.TNH,
        "sub_divisi": {
            "2.1 Galian Tanah Biasa": ["wi_galian_tanah", "wi_galian_pondasi_spesifik"],
            "2.2 Galian Tanah Keras": ["wi_galian_tanah_keras"],
            "2.3 Urugan Tanah Kembali": ["wi_urugan_tanah"],
            "2.4 Pemadatan Tanah": ["wi_pemadatan"],
            "2.5 Urugan Pasir": ["wi_urugan_pasir", "wi_pasir_alas_pondasi"],
        },
    },
    "DIV-03 Pekerjaan Pondasi": {
        "code": ACES300DivisionCode.FND,
        "sub_divisi": {
            "3.1 Pondasi Batu Kali": ["wi_pondasi_batu", "wi_pasangan_batu_kali_irigasi"],
            "3.2 Pondasi Footplate": ["wi_pondasi_footplate"],
            "3.3 Pondasi Bore Pile": ["wi_bore_pile_jembatan", "wi_bore_pile"],
            "3.4 Pondasi Sumuran": ["wi_sumuran"],
            "3.5 Pondasi Raft": ["wi_raft_foundation"],
            "3.6 Pondasi Talud": ["wi_talud_batu"],
        },
    },
    "DIV-04 Pekerjaan Struktur Beton": {
        "code": ACES300DivisionCode.STR,
        "sub_divisi": {
            "4.1 Bekisting": ["wi_bekisting_kolom", "wi_bekisting_balok", "wi_bekisting_plat_lt2", "wi_sloof_bekisting"],
            "4.2 Pembesian": ["wi_besi_polos", "wi_besi_ulir", "wi_kolom_lt1_rebar_fab", "wi_kolom_lt1_sengkang"],
            "4.3 Pengecoran": ["wi_beton_k225", "wi_beton_k250", "wi_beton_k300", "wi_beton_k350", "wi_beton_k400"],
            "4.4 Beton Precast": ["wi_precast_column", "wi_precast_beam"],
            "4.5 Struktur Baja": ["wi_baja_profil", "wi_baja_wf"],
        },
    },
    "DIV-05 Pekerjaan Dinding": {
        "code": ACES300DivisionCode.DIN,
        "sub_divisi": {
            "5.1 Pasangan Bata Merah": ["wi_pas_bata", "wi_bata_merah_taman"],
            "5.2 Pasangan Bata Ringan (Hebel)": ["wi_hebel_lt1", "wi_hebel_lt2", "wi_pas_bata_ringan"],
            "5.3 Plesteran": ["wi_plesteran", "wi_plester_dalam", "wi_plester_luar", "wi_plester_kasar_km"],
            "5.4 Acian": ["wi_acian", "wi_acian_dalam", "wi_acian_luar"],
            "5.5 Pengecatan": ["wi_cat_tembok", "wi_cat_dinding"],
            "5.6 Waterproofing": ["wi_waterproofing_pu", "wi_waterproofing"],
        },
    },
    "DIV-06 Pekerjaan Lantai": {
        "code": ACES300DivisionCode.LNT,
        "sub_divisi": {
            "6.1 Keramik Lantai": ["wi_keramik_lantai", "wi_keramik_dinding"],
            "6.2 Granit Lantai": ["wi_granit_lantai"],
            "6.3 Plint Lantai": ["wi_plint_lantai"],
            "6.4 Screed Lantai": ["wi_screed_lantai"],
            "6.5 Lantai Beton": ["wi_lantai_kerja_b0", "wi_rigid_pavement"],
        },
    },
    "DIV-07 Pekerjaan Plafon": {
        "code": ACES300DivisionCode.PLF,
        "sub_divisi": {
            "7.1 Rangka Plafon": ["wi_rangka_plafon_4x4", "wi_plafon_gypsum"],
            "7.2 Penutup Plafon Gypsum": ["wi_plafon_gypsum"],
            "7.3 Plafon Tripleks": ["wi_plafon_tripleks"],
        },
    },
    "DIV-08 Pekerjaan Atap": {
        "code": ACES300DivisionCode.ATP,
        "sub_divisi": {
            "8.1 Rangka Atap Baja Ringan": ["wi_atap_baja_ringan", "wi_kudakuda_fab", "wi_kudakuda_assembly"],
            "8.2 Rangka Atap Kayu": ["wi_rangka_atap_kayu"],
            "8.3 Penutup Genteng": ["wi_genteng_beton", "wi_genteng_metal", "wi_genteng_utama"],
            "8.4 Penutup Metal": ["wi_spandek", "wi_genteng_metal_berpasir"],
        },
    },
    "DIV-09 Pekerjaan Kusen, Pintu, Jendela": {
        "code": ACES300DivisionCode.KUS,
        "sub_divisi": {
            "9.1 Kusen Kayu": ["wi_kusen_kayu"],
            "9.2 Kusen Aluminium": ["wi_kusen_jendela_aluminium", "wi_kusen_pintu_kamar"],
            "9.3 Daun Pintu": ["wi_pintu_panel", "wi_daun_pintu_utama"],
            "9.4 Daun Jendela": ["wi_jendela_kayu", "wi_jendela_casement", "wi_jendela_sliding"],
        },
    },
    "DIV-10 Pekerjaan MEP": {
        "code": ACES300DivisionCode.MEP,
        "sub_divisi": {
            "10.1 Instalasi Listrik": ["wi_instalasi_titik_lampu", "wi_instalasi_stop_kontak", "wi_instalasi_panel"],
            "10.2 Instalasi Plumbing": ["wi_pipa_air_bersih_1_2", "wi_pipa_air_kotor_4", "wi_pasang_kloset", "wi_pasang_wastafel"],
            "10.3 Instalasi AC": ["wi_ac_wc", "wi_instalasi_ac"],
        },
    },
}

# Jadikan registry tidak dapat diubah dari luar
MASTER_CLASSIFICATION_REGISTRY = MappingProxyType(_MASTER_CLASSIFICATION_REGISTRY_RAW)


# ---------------------------------------------------------------------------
# Core Seeding Layer – Pure Semantic Transformation Pipeline (QS-Safe)
# ---------------------------------------------------------------------------
def load_workitem_classification() -> Dict[str, Any]:
    """
    Memvalidasi dan mengekstrak peta klasifikasi work item 10 divisi.
    Menjamin kepatuhan struktur hilir terhadap efek samping runtime dinamis.
    """
    # 1. GATEWAY SCHEMA VALIDATION
    try:
        validated_manifest = BuildingClassificationTemplateDTO(
            divisions=MASTER_CLASSIFICATION_REGISTRY
        )
    except Exception as exc:
        logger.critical("Pelanggaran struktural pada template klasifikasi master: %s", exc)
        raise RuntimeError(
            f"Fatal: Violasi struktural terdeteksi pada dictionary template klasifikasi master: {exc}"
        ) from exc

    # 2. Kembalikan salinan mendalam untuk mencegah mutasi eksternal
    return validated_manifest.model_dump()


__all__ = [
    "ACES300DivisionCode",
    "MASTER_CLASSIFICATION_REGISTRY",
    "load_workitem_classification",
]