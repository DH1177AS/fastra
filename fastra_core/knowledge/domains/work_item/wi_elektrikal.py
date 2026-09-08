"""
fastra_core/knowledge/domains/work_item/wi_elektrikal.py

Modul pemuatan data work item elektrikal ke Knowledge Graph.
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


class ElectricalTaskCategory(str, enum.Enum):
    """Klasifikasi taksonomi formal untuk sub-divisi elektrikal, tegangan rendah, penangkal petir, dan smart home."""

    ELEKTRIKAL = "ELEKTRIKAL"


# ---------------------------------------------------------------------------
# Inbound DTOs – Pydantic Strict Configuration Gate (Fail-Fast)
# ---------------------------------------------------------------------------
class InboundElecTaskRowDTO(BaseModel):
    """DTO validasi untuk elemen task mentah di dalam paket elektrikal."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, strict=False)

    id: str = Field(..., min_length=5, max_length=64, pattern=r"^wi_[a-z0-9_]+$")
    code: str = Field(..., min_length=2, max_length=32, pattern=r"^ELE\.[0-9]{3}$")
    name: str = Field(..., min_length=5, max_length=512)
    unit: str = Field(..., min_length=1, max_length=16, pattern=r"^(unit|m'|buah|titik|batang)$")
    sni_ref: str = Field(..., min_length=2, max_length=128)
    category: ElectricalTaskCategory = Field(...)


class ElecTaskBundleDTO(BaseModel):
    """Master bundle schema yang memvalidasi seluruh koleksi work item elektrikal."""

    model_config = ConfigDict(extra="forbid", strict=False)

    items: List[InboundElecTaskRowDTO] = Field(..., max_length=200)


# ---------------------------------------------------------------------------
# Master Task Database Registry (Array Collection)
# ---------------------------------------------------------------------------
ELECTRICAL_TASK_REGISTRY_COLLECTION: List[Dict[str, Any]] = [
    {"id": "wi_kwh_meter", "code": "ELE.001", "name": "Pemasangan KWH Meter Listrik Baru Khusus dari PLN Depan Rumah", "unit": "unit", "sni_ref": "PUIL", "category": "ELEKTRIKAL"},
    {"id": "wi_panel_listrik_utama", "code": "ELE.002", "name": "Pemasangan Kotak Panel Listrik Utama Master (Distribution Board) Dalam", "unit": "unit", "sni_ref": "PUIL", "category": "ELEKTRIKAL"},
    {"id": "wi_mcb_3phase", "code": "ELE.003", "name": "Pemasangan Unit Master MCB 3 Phase Pemutus Arus Utama Gedung", "unit": "unit", "sni_ref": "PUIL", "category": "ELEKTRIKAL"},
    {"id": "wi_mcb_pembagi", "code": "ELE.004", "name": "Pemasangan Unit MCB Pembagi Arus Tiap-Tiap Lantai & Kelompok Ruang", "unit": "unit", "sni_ref": "PUIL", "category": "ELEKTRIKAL"},
    {"id": "wi_bobokan_konduit", "code": "ELE.005", "name": "Bobokan Dinding Bata untuk Jalur Pipa Konduit Saklar & Stopkontak", "unit": "m'", "sni_ref": "AHSP PUPR", "category": "ELEKTRIKAL"},
    {"id": "wi_pipa_konduit_20mm", "code": "ELE.006", "name": "Pemasangan Pipa Pelindung Kabel Fleksibel Konduit PVC 20mm Dinding", "unit": "m'", "sni_ref": "PUIL", "category": "ELEKTRIKAL"},
    {"id": "wi_inbow_doos", "code": "ELE.007", "name": "Pemasangan Kotak Sambungan Kabel (Inbow Doos) Saklar Tanam Dinding", "unit": "buah", "sni_ref": "PUIL", "category": "ELEKTRIKAL"},
    {"id": "wi_kabel_feeder_lt2", "code": "ELE.008", "name": "Penarikan Kabel Induk NYM 3x4mm dari Panel Utama ke Sub-Panel Lantai 2", "unit": "m'", "sni_ref": "PUIL", "category": "ELEKTRIKAL"},
    {"id": "wi_kabel_stopkontak", "code": "ELE.009", "name": "Penarikan Kabel Jalur Stopkontak Standar Jenis NYM 3x2.5mm (SNI)", "unit": "m'", "sni_ref": "PUIL", "category": "ELEKTRIKAL"},
    {"id": "wi_kabel_lampu", "code": "ELE.010", "name": "Penarikan Kabel Jalur Lampu Penerangan Jenis NYM 2x1.5mm (SNI)", "unit": "m'", "sni_ref": "PUIL", "category": "ELEKTRIKAL"},
    {"id": "wi_kabel_grounding", "code": "ELE.011", "name": "Penarikan Kabel Khusus Grounding Arde Hijau-Kuning Menuju Pasak Tanah", "unit": "m'", "sni_ref": "PUIL", "category": "ELEKTRIKAL"},
    {"id": "wi_tdos_plafon", "code": "ELE.012", "name": "Pemasangan Kotak Percabangan Kabel (T-Dos / Cross-Dos) Plafon", "unit": "buah", "sni_ref": "PUIL", "category": "ELEKTRIKAL"},
    {"id": "wi_lasdop", "code": "ELE.013", "name": "Penyambungan Puntir Kabel Sambungan & Pembungkusan Isolasi Lasdop PVC", "unit": "titik", "sni_ref": "PUIL", "category": "ELEKTRIKAL"},
    {"id": "wi_saklar_tunggal", "code": "ELE.014", "name": "Pemasangan Unit Saklar Tunggal Tanam Merek Schneider/Panasonic", "unit": "buah", "sni_ref": "PUIL", "category": "ELEKTRIKAL"},
    {"id": "wi_saklar_ganda", "code": "ELE.015", "name": "Pemasangan Unit Saklar Ganda (Dua Tombol) Tanam Dinding", "unit": "buah", "sni_ref": "PUIL", "category": "ELEKTRIKAL"},
    {"id": "wi_saklar_tukar", "code": "ELE.016", "name": "Pemasangan Unit Saklar Hotel (Saklar Tukar Tangga Lantai 1 & 2)", "unit": "buah", "sni_ref": "PUIL", "category": "ELEKTRIKAL"},
    {"id": "wi_stopkontak_standar", "code": "ELE.017", "name": "Pemasangan Unit Stopkontak Standar Lengkap Pin Grounding Keselamatan", "unit": "buah", "sni_ref": "PUIL", "category": "ELEKTRIKAL"},
    {"id": "wi_stopkontak_ac", "code": "ELE.018", "name": "Pemasangan Unit Stopkontak Khusus AC Daya Tinggi Lengkap Saklar On/Off", "unit": "buah", "sni_ref": "PUIL", "category": "ELEKTRIKAL"},
    {"id": "wi_floor_socket", "code": "ELE.019", "name": "Pemasangan Unit Stopkontak Tanam Lantai Bahan Kuningan (Floor Socket)", "unit": "buah", "sni_ref": "PUIL", "category": "ELEKTRIKAL"},
    {"id": "wi_kabel_lan", "code": "ELE.020", "name": "Penarikan Jalur Kabel Data Internet LAN Cat6 dari Posisi Hub ke Kamar", "unit": "m'", "sni_ref": "AHSP PUPR", "category": "ELEKTRIKAL"},
    {"id": "wi_kabel_tv", "code": "ELE.021", "name": "Penarikan Jalur Kabel Antena Koaksial TV ke Titik Ruang Keluarga", "unit": "m'", "sni_ref": "AHSP PUPR", "category": "ELEKTRIKAL"},
    {"id": "wi_terminal_rj45", "code": "ELE.022", "name": "Pemasangan Unit Terminal Stopkontak Data RJ45 & Terminal TV Dinding", "unit": "buah", "sni_ref": "AHSP PUPR", "category": "ELEKTRIKAL"},
    {"id": "wi_downlight_3in", "code": "ELE.023", "name": "Pemasangan Rumah Lampu Tanam Plafon (Downlight Fixture) Diameter 3 Inci", "unit": "buah", "sni_ref": "PUIL", "category": "ELEKTRIKAL"},
    {"id": "wi_lampu_smart_9w", "code": "ELE.024", "name": "Pemasangan Lampu LED Bulb Smart Home 9 Watt (Bisa Atur Warna Via Wifi)", "unit": "buah", "sni_ref": "PUIL", "category": "ELEKTRIKAL"},
    {"id": "wi_double_head_gimbals", "code": "ELE.025", "name": "Pemasangan Rumah Lampu Tanam Plafon Kotak (Double Head Gimbals)", "unit": "buah", "sni_ref": "PUIL", "category": "ELEKTRIKAL"},
    {"id": "wi_spotlight_lukisan", "code": "ELE.026", "name": "Pemasangan Lampu Sorot LED (Spotlight) Menyorot Lukisan Dinding", "unit": "buah", "sni_ref": "PUIL", "category": "ELEKTRIKAL"},
    {"id": "wi_led_strip_plafon", "code": "ELE.027", "name": "Pemasangan Jalur Lampu Sembunyi Plafon (LED Strip Semak) Drop Ceiling", "unit": "m'", "sni_ref": "PUIL", "category": "ELEKTRIKAL"},
    {"id": "wi_driver_led", "code": "ELE.028", "name": "Pemasangan Unit Transformator / Driver LED Strip Plafon Atas", "unit": "unit", "sni_ref": "PUIL", "category": "ELEKTRIKAL"},
]

# Extend dengan 28 definisi task elektrikal tambahan
ELECTRICAL_TASK_REGISTRY_COLLECTION.extend([
    {"id": "wi_lampu_gantung_kristal", "code": "ELE.029", "name": "Pemasangan Lampu Gantung Hias Kristal Besar Tengah Ruang Tamu", "unit": "unit", "sni_ref": "PUIL", "category": "ELEKTRIKAL"},
    {"id": "wi_lampu_dinding_outdoor", "code": "ELE.030", "name": "Pemasangan Lampu Dinding Outdoor Tahan Air Teras Depan Rumah", "unit": "buah", "sni_ref": "PUIL", "category": "ELEKTRIKAL"},
    {"id": "wi_spike_led", "code": "ELE.031", "name": "Pemasangan Lampu Sorot Taman Kedap Air (Spike LED Spotlight IP65)", "unit": "buah", "sni_ref": "PUIL", "category": "ELEKTRIKAL"},
    {"id": "wi_in_ground_uplight", "code": "ELE.032", "name": "Pemasangan Lampu Tanam Lantai Carport (In-ground Uplight IP67)", "unit": "buah", "sni_ref": "PUIL", "category": "ELEKTRIKAL"},
    {"id": "wi_pir_sensor", "code": "ELE.033", "name": "Pemasangan Sistem Saklar Otomatis Sensor Gerak (PIR Sensor) Toilet", "unit": "unit", "sni_ref": "PUIL", "category": "ELEKTRIKAL"},
    {"id": "wi_smart_home_gateway", "code": "ELE.034", "name": "Pemasangan Hub Sentral Smart Home Gateway Pusat Kontrol Nirkabel", "unit": "unit", "sni_ref": "AHSP PUPR", "category": "ELEKTRIKAL"},
    {"id": "wi_smart_switch", "code": "ELE.035", "name": "Pemasangan Modul Saklar Pintar Smart Switch Terkoneksi Asisten Suara", "unit": "unit", "sni_ref": "AHSP PUPR", "category": "ELEKTRIKAL"},
    {"id": "wi_cctv_dome", "code": "ELE.036", "name": "Pemasangan Kamera Pengawas CCTV Jenis Dome Indoor Kamar Anak", "unit": "unit", "sni_ref": "AHSP PUPR", "category": "ELEKTRIKAL"},
    {"id": "wi_cctv_bullet", "code": "ELE.037", "name": "Pemasangan Kamera Pengawas CCTV Jenis Bullet Outdoor Tahan Air Sudut Luar", "unit": "unit", "sni_ref": "AHSP PUPR", "category": "ELEKTRIKAL"},
    {"id": "wi_kabel_poe", "code": "ELE.038", "name": "Penarikan Kabel LAN PoE (Power over Ethernet) Khusus Jaringan CCTV", "unit": "m'", "sni_ref": "AHSP PUPR", "category": "ELEKTRIKAL"},
    {"id": "wi_nvr_cctv", "code": "ELE.039", "name": "Pemasangan Unit Perekam Video CCTV (NVR - Network Video Recorder)", "unit": "unit", "sni_ref": "AHSP PUPR", "category": "ELEKTRIKAL"},
    {"id": "wi_hdd_cctv", "code": "ELE.040", "name": "Pemasangan Harddisk Khusus CCTV Survailance 4 Terabyte dalam NVR", "unit": "unit", "sni_ref": "AHSP PUPR", "category": "ELEKTRIKAL"},
    {"id": "wi_monitor_cctv", "code": "ELE.041", "name": "Pemasangan Monitor Kontrol Layar LED CCTV di Dalam Kamar Utama", "unit": "unit", "sni_ref": "AHSP PUPR", "category": "ELEKTRIKAL"},
    {"id": "wi_smart_door_lock", "code": "ELE.042", "name": "Pemasangan Kunci Pintu Pintar (Smart Door Lock Fingerprint/Card) Pintu Utama", "unit": "unit", "sni_ref": "AHSP PUPR", "category": "ELEKTRIKAL"},
    {"id": "wi_kabel_interkom", "code": "ELE.043", "name": "Penarikan Kabel Bel Rumah Utama Video Interkom dari Pagar ke Foyer", "unit": "m'", "sni_ref": "AHSP PUPR", "category": "ELEKTRIKAL"},
    {"id": "wi_monitor_interkom", "code": "ELE.044", "name": "Pemasangan Unit Layar Video Interkom Monitor Dinding Dalam Foyer", "unit": "unit", "sni_ref": "AHSP PUPR", "category": "ELEKTRIKAL"},
    {"id": "wi_kamera_bell", "code": "ELE.045", "name": "Pemasangan Unit Kamera Tombol Bel Pintu Tahan Cuaca Depan Pagar", "unit": "unit", "sni_ref": "AHSP PUPR", "category": "ELEKTRIKAL"},
    {"id": "wi_grounding_petir", "code": "ELE.046", "name": "Penarikan Jalur Kabel Penangkal Petir Tembaga BC Menembus Tanah", "unit": "m'", "sni_ref": "SNI 03-7015", "category": "ELEKTRIKAL"},
    {"id": "wi_bor_grounding", "code": "ELE.047", "name": "Pengeboran Tanah Kedalaman 6 Meter untuk Pasak Grounding Penangkal Petir", "unit": "titik", "sni_ref": "SNI 03-7015", "category": "ELEKTRIKAL"},
    {"id": "wi_grounding_rod", "code": "ELE.048", "name": "Pemasangan Pasak Tembaga Padat (Grounding Rod) Diameter 5/8 Inci", "unit": "batang", "sni_ref": "SNI 03-7015", "category": "ELEKTRIKAL"},
    {"id": "wi_bak_grounding", "code": "ELE.049", "name": "Pemasangan Bak Kontrol Khusus Titik Sambungan Grounding Penangkal Petir", "unit": "unit", "sni_ref": "SNI 03-7015", "category": "ELEKTRIKAL"},
    {"id": "wi_elcb", "code": "ELE.050", "name": "Pemasangan Sistem Pengaman Kebocoran Arus Listrik (ELCB / RCCB) di Panel", "unit": "unit", "sni_ref": "PUIL", "category": "ELEKTRIKAL"},
    {"id": "wi_exhaust_fan_km1", "code": "ELE.051", "name": "Pemasangan Unit Exhaust Fan Plafon Kamar Mandi 1 Sambungan Konduit Udara", "unit": "unit", "sni_ref": "AHSP PUPR", "category": "ELEKTRIKAL"},
    {"id": "wi_exhaust_fan_km2", "code": "ELE.052", "name": "Pemasangan Unit Exhaust Fan Plafon Kamar Mandi 2 Sambungan Konduit Udara", "unit": "unit", "sni_ref": "AHSP PUPR", "category": "ELEKTRIKAL"},
    {"id": "wi_kabel_water_heater", "code": "ELE.053", "name": "Penarikan Kabel Power untuk Unit Mesin Pemanas Air Kamar Mandi", "unit": "m'", "sni_ref": "PUIL", "category": "ELEKTRIKAL"},
    {"id": "wi_kabel_kompor_induksi", "code": "ELE.054", "name": "Pemasangan Kabel Power Induk untuk Kompor Induksi Daya Besar Dapur", "unit": "m'", "sni_ref": "PUIL", "category": "ELEKTRIKAL"},
    {"id": "wi_emergency_light", "code": "ELE.055", "name": "Pemasangan Lampu Darurat Otomatis (Emergency Wall Light) Area Tangga", "unit": "unit", "sni_ref": "PUIL", "category": "ELEKTRIKAL"},
    {"id": "wi_sparing_speaker", "code": "ELE.056", "name": "Pemasangan Jalur Pipa Sparing Kabel Speaker Langit-Langit (Ceiling Speaker)", "unit": "m'", "sni_ref": "AHSP PUPR", "category": "ELEKTRIKAL"},
])


# ---------------------------------------------------------------------------
# Core Seeding Layer – Pure Domain Injection Pipeline (QS-Safe)
# ---------------------------------------------------------------------------
def load_wi_elektrikal(kg: KnowledgeGraph) -> None:
    """
    Memvalidasi, menginstansiasi, dan menyuntikkan semua task elektrikal dan smart systems ke KnowledgeGraph.
    Mencegah kesalahan argumen runtime dan korupsi struktural data dinamis.
    """
    if not isinstance(kg, KnowledgeGraph):
        raise TypeError("Parameter 'kg' harus berupa instance KnowledgeGraph.")

    # 1. GATEWAY SCHEMA VALIDATION
    try:
        validated_bundle = ElecTaskBundleDTO(items=ELECTRICAL_TASK_REGISTRY_COLLECTION)
    except Exception as exc:
        logger.error("Gagal seed dataset task elektrikal. Pelanggaran skema: %s", exc)
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
        logger.debug("Work item elektrikal dimuat: %s (%s)", work_item_node_instance.id, work_item_node_instance.code)

    logger.info(
        "Seeder task elektrikal selesai: %d master work items terkunci.",
        len(validated_bundle.items),
    )
