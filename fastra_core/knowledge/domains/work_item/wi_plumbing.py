# fastra_core\knowledge\domains\work_item\wi_plumbing.py

from __future__ import annotations

import logging
from enum import Enum
from typing import Any, List, Dict, Tuple, Set

from pydantic import BaseModel, ConfigDict, Field, field_validator

logger = logging.getLogger("fastra.knowledge.work_item.plumbing")


class WorkItemUnit(str, Enum):
    UNIT = "unit"
    MTR_RUNNING = "m'"
    TITIK = "titik"
    MTR_CUBIC = "m³"
    BUAH = "buah"
    SET = "set"
    MTR_SQUARE = "m²"


class WorkItemSpecification(str, Enum):
    AHSP_PUPR = "AHSP PUPR"
    SNI_PLUMBING = "SNI Plumbing"
    SNI_2847 = "SNI 2847"


class WorkItemCategory(str, Enum):
    PLUMBING = "PLUMBING"


class WorkItemDTO(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        strict=False,
        frozen=True,
        allow_inf_nan=False,
    )

    id: str = Field(..., min_length=3, max_length=128, pattern=r"^wi_[a-z0-9_]+$")
    code: str = Field(..., min_length=5, max_length=32, pattern=r"^[A-Z]{3,4}\.[0-9]{3}$")
    name: str = Field(..., min_length=5, max_length=512)
    unit: WorkItemUnit
    specification: WorkItemSpecification
    category: WorkItemCategory

    @field_validator("id", "code", "name", mode="before")
    @classmethod
    def validate_strings_no_coercion(cls, value: Any) -> str:
        if not isinstance(value, str):
            raise ValueError("VALUE_MUST_BE_A_STRING")
        stripped = value.strip()
        if not stripped:
            raise ValueError("VALUE_CANNOT_BE_EMPTY_OR_WHITESPACE")
        return stripped


class WorkItemDomainModel:
    def __init__(
        self,
        id: str,
        code: str,
        name: str,
        unit: WorkItemUnit,
        specification: WorkItemSpecification,
        category: WorkItemCategory,
    ) -> None:
        self.__id: str = id
        self.__code: str = code
        self.__name: str = name
        self.__unit: WorkItemUnit = unit
        self.__specification: WorkItemSpecification = specification
        self.__category: WorkItemCategory = category

    @property
    def id(self) -> str:
        return self.__id

    @property
    def code(self) -> str:
        return self.__code

    @property
    def name(self) -> str:
        return self.__name

    @property
    def unit(self) -> WorkItemUnit:
        return self.__unit

    @property
    def specification(self) -> WorkItemSpecification:
        return self.__specification

    @property
    def category(self) -> WorkItemCategory:
        return self.__category

    def to_node_arguments(self) -> Tuple[str, str, str, str, str, str]:
        return (
            self.__id,
            self.__code,
            self.__name,
            self.__unit.value,
            self.__specification.value,
            self.__category.value,
        )


def load_wi_plumbing(kg: Any) -> None:
    if kg is None:
        raise ValueError("KNOWLEDGE_GRAPH_INSTANCE_CANNOT_BE_NULL")

    if not hasattr(kg, "add_work_item") or not hasattr(kg, "remove_work_item"):
        raise AttributeError("KNOWLEDGE_GRAPH_MUST_HAVE_ADD_AND_REMOVE_WORK_ITEM_METHODS")

    from fastra_core.knowledge.nodes import WorkItemNode

    raw_items: List[Tuple[str, str, str, str, str, str]] = [
        ("wi_submersible_pump", "PLU.001", "Pemasangan Mesin Pompa Air Tanah Sumur Dalam (Submersible Pump)", "unit", "AHSP PUPR", "PLUMBING"),
        ("wi_pipa_isap_1in", "PLU.002", "Penarikan Pipa Isap PVC AW 1 Inci Turun ke Dalam Sumur Bor", "m'", "SNI Plumbing", "PLUMBING"),
        ("wi_kabel_submersible", "PLU.003", "Pemasangan Kabel Power Waterproof Motor Submersible Pump ke Atas", "m'", "SNI Plumbing", "PLUMBING"),
        ("wi_pressure_switch", "PLU.004", "Pemasangan Alat Otomatis Pompa Tekanan Air (Pressure Switch / Radar)", "unit", "SNI Plumbing", "PLUMBING"),
        ("wi_filter_tabung_1054", "PLU.005", "Pemasangan Tabung Filter Air Tabung Serat Fiber Tinggi Tipe 1054 Depan", "unit", "AHSP PUPR", "PLUMBING"),
        ("wi_media_filter", "PLU.006", "Pengisian Media Filter Pasir Silika & Karbon Aktif Dalam Tabung Filter", "unit", "AHSP PUPR", "PLUMBING"),
        ("wi_pipa_ppr_lt1", "PLU.007", "Pemasangan Pipa Distribusi Air Bersih Utama Pipa PPR PN-10 Lantai 1", "m'", "SNI Plumbing", "PLUMBING"),
        ("wi_pipa_ppr_lt2", "PLU.008", "Pemasangan Pipa Distribusi Air Bersih Utama Pipa PPR PN-10 Lantai 2", "m'", "SNI Plumbing", "PLUMBING"),
        ("wi_pipa_air_panas", "PLU.009", "Pemasangan Pipa Air Panas Khusus Tebal PPR PN-20 Jalur Kamar Mandi", "m'", "SNI Plumbing", "PLUMBING"),
        ("wi_bobokan_pipa", "PLU.010", "Bobokan Dinding Bata untuk Penanaman Jalur Pipa PPR Air Bersih", "m'", "AHSP PUPR", "PLUMBING"),
        ("wi_polyfusion_las", "PLU.011", "Penyambungan Pipa PPR Metode Las Panas Paku Mesin PPR Polyfusion", "titik", "SNI Plumbing", "PLUMBING"),
        ("wi_gate_valve", "PLU.012", "Pemasangan Kran Stop Utama (Gate Valve) Kuningan Tiap Lantai", "unit", "SNI Plumbing", "PLUMBING"),
        ("wi_menara_toren", "PLU.013", "Pemasangan Menara Besi Siku / Dudukan Dak Beton Tempat Toren Air Atas", "unit", "AHSP PUPR", "PLUMBING"),
        ("wi_toren_1000l", "PLU.014", "Pemasangan Tangki Air Atas (Toren) Bahan Plastik HDPE Kapasitas 1000L", "unit", "AHSP PUPR", "PLUMBING"),
        ("wi_radar_toren", "PLU.015", "Pemasangan Unit Kran Pelampung Otomatis (Radar Toren) Dalam Tangki Air", "unit", "AHSP PUPR", "PLUMBING"),
        ("wi_booster_pump", "PLU.016", "Pemasangan Pompa Air Pendorong Tekanan (Booster Pump Inverter) Setelah Toren", "unit", "AHSP PUPR", "PLUMBING"),
        ("wi_pipa_kotor_4in", "PLU.017", "Pemasangan Pipa Pembuangan Air Kotor Kloset Pipa PVC Kelas AW 4 Inci", "m'", "SNI Plumbing", "PLUMBING"),
        ("wi_pipa_bekas_3in", "PLU.018", "Pemasangan Pipa Pembuangan Air Bekas Mandi/Wastafel Pipa PVC AW 3 Inci", "m'", "SNI Plumbing", "PLUMBING"),
        ("wi_pipa_hujan_3in", "PLU.019", "Pemasangan Pipa Pembuangan Air Hujan Atas Pipa PVC Kelas AW 3 Inci", "m'", "SNI Plumbing", "PLUMBING"),
        ("wi_elbow_pvc", "PLU.020", "Pemasangan Sambungan Siku Pipa (Elbow) PVC AW Tebal Tiap Belokan Jalur", "buah", "SNI Plumbing", "PLUMBING"),
        ("wi_y_branch", "PLU.021", "Pemasangan Sambungan Huruf Y (Y-Branch) Pipa Pembuangan Air Kotor", "buah", "SNI Plumbing", "PLUMBING"),
        ("wi_lem_pipa_pvc", "PLU.022", "Pengolesan Lem Pipa PVC Mutu Tinggi Sambungan Rapat Anti Bocor", "titik", "SNI Plumbing", "PLUMBING"),
        ("wi_galian_septic", "PLU.023", "Galian Tanah Kompleks untuk Kamar Tangki Septic Tank Pabrikan (Biotank)", "m³", "AHSP PUPR", "PLUMBING"),
        ("wi_plat_dasar_biotank", "PLU.024", "Pengecoran Plat Beton Dasar Dudukan Tangki Biotank Bawah Tanah", "m³", "AHSP PUPR", "PLUMBING"),
        ("wi_penurunan_biotank", "PLU.025", "Penurunan Unit Tangki Biotank Kapasitas Volume Rumah Tangga 5 Orang", "unit", "AHSP PUPR", "PLUMBING"),
        ("wi_pengisian_air_biotank", "PLU.026", "Pengisian Air Bersih Tangki Biotank & Uji Kebocoran Awal", "unit", "AHSP PUPR", "PLUMBING"),
        ("wi_pipa_vent_plumbing", "PLU.027", "Instalasi Pipa Udara Venting Plambing 1.5 Inci Naik ke Atas Atap", "m'", "SNI Plumbing", "PLUMBING"),
        ("wi_bak_kontrol_plumbing", "PLU.028", "Pembuatan Bak Kontrol Saluran Plambing Beton Mini + Tutup Besi", "unit", "AHSP PUPR", "PLUMBING"),
        ("wi_kloset_duduk", "PLU.029", "Pemasangan Kloset Duduk Porselen + Baut Silet Dynabolt + Wax Ring", "unit", "AHSP PUPR", "PLUMBING"),
        ("wi_wastafel_gantung", "PLU.030", "Pemasangan Wastafel Cuci Muka Gantung Dinding + Kran Pencampur", "unit", "AHSP PUPR", "PLUMBING"),
        ("wi_shower_mandi", "PLU.031", "Pemasangan Tiang Pancuran Shower Mandi + Mixer Panas Dingin", "unit", "AHSP PUPR", "PLUMBING"),
        ("wi_aksesoris_km", "PLU.032", "Pemasangan Aksesoris Gantung Kamar Mandi (Handuk, Sabun, Tisu, Floor Drain)", "set", "AHSP PUPR", "PLUMBING"),
        ("wi_kitchen_sink", "PLU.033", "Pemasangan Bak Cuci Piring Dapur (Kitchen Sink) Stainless + Kran", "unit", "AHSP PUPR", "PLUMBING"),
        ("wi_hydrotest", "PLU.034", "Uji Tekan Jaringan Pipa Air (Hydrostatic Test) 8-10 Bar Selama 24 Jam", "unit", "SNI Plumbing", "PLUMBING"),
        ("wi_pompa_sumur_dangkal", "PLU.035", "Pemasangan Mesin Pompa Sumur Dangkal / Jetpump", "unit", "AHSP PUPR", "PLUMBING"),
        ("wi_ground_tank", "PLU.036", "Pembuatan Bak Tampung Air Bawah Tanah (Ground Tank) Beton", "m³", "SNI 2847", "PLUMBING"),
        ("wi_waterproofing_gt", "PLU.037", "Pemasangan Lapisan Waterproofing Semen Base Dalam Ground Tank", "m²", "AHSP PUPR", "PLUMBING"),
        ("wi_sparing_gt", "PLU.038", "Pemasangan Pipa Sparing Inlet/Outlet Tembus Dinding Ground Tank", "titik", "AHSP PUPR", "PLUMBING"),
        ("wi_manhole_gt", "PLU.039", "Pemasangan Manhole Cover Besi Cor untuk Penutup Ground Tank", "unit", "AHSP PUPR", "PLUMBING"),
        ("wi_water_heater_listrik", "PLU.040", "Instalasi Unit Pemanas Air Listrik (Storage Heater) 30L", "unit", "AHSP PUPR", "PLUMBING"),
        ("wi_water_heater_gas", "PLU.041", "Instalasi Unit Pemanas Air Gas Instan Kamar Mandi", "unit", "AHSP PUPR", "PLUMBING"),
        ("wi_solar_water_heater", "PLU.042", "Pemasangan Solar Water Heater + Kolektor Panel di Atap", "unit", "AHSP PUPR", "PLUMBING"),
        ("wi_pipa_tembaga_ac", "PLU.043", "Pemasangan Pipa Tembaga AC + Isolasi Pendingin", "m'", "AHSP PUPR", "PLUMBING"),
        ("wi_drainase_bawah_tanah", "PLU.044", "Pemasangan Pipa Sub-Drain Lapisan Bawah (Pipa Berlubang Bungkus Ijuk)", "m'", "AHSP PUPR", "PLUMBING"),
        ("wi_sumur_resapan_hujan", "PLU.045", "Pembuatan Sumur Resapan Air Hujan Lapangan (Konservasi Air)", "unit", "AHSP PUPR", "PLUMBING"),
        ("wi_pipa_gas_dapur", "PLU.046", "Instalasi Pipa Gas Sentral Dapur (Pipa Tembaga Tebal Khusus)", "m'", "SNI Plumbing", "PLUMBING"),
        ("wi_gas_detector", "PLU.047", "Pemasangan Detektor Kebocoran Gas & Solenoid Valve Otomatis Dapur", "unit", "SNI Plumbing", "PLUMBING"),
        ("wi_toren_500l", "PLU.048", "Pemasangan Tangki Air Atas (Toren) Bahan Plastik HDPE Kapasitas 500L", "unit", "AHSP PUPR", "PLUMBING"),
        ("wi_pompa_booster_inverter", "PLU.049", "Pemasangan Pompa Dorong Tekanan Konstan (Inverter Pump) Hemat Listrik", "unit", "AHSP PUPR", "PLUMBING"),
        ("wi_filter_sentral", "PLU.050", "Instalasi Sistem Penyaring Air Utama (Water Filter Central) Pasir + Karbon", "unit", "AHSP PUPR", "PLUMBING"),
        ("wi_roof_drain_castiron", "PLU.051", "Pemasangan Roof Drain Cast Iron Saringan Dak Beton Atas", "unit", "AHSP PUPR", "PLUMBING"),
        ("wi_pipa_air_kotor_2in", "PLU.052", "Pemasangan Pipa Pembuangan Air Kotor 2 Inci untuk Wastafel", "m'", "SNI Plumbing", "PLUMBING"),
        ("wi_pipe_clamp", "PLU.053", "Pemasangan Klem Pipa Air (Pipe Clamp/Hanger) Dudukan Besi Gantung", "buah", "SNI Plumbing", "PLUMBING"),
        ("wi_flexible_joint", "PLU.054", "Pemasangan Flexible Joint Pipa (Karet/Kawat Anyam) Peredam Getaran Pompa", "unit", "SNI Plumbing", "PLUMBING"),
        ("wi_clean_out", "PLU.055", "Pemasangan Clean Out Pipa Air Kotor (Lubang Sumbat Berulir) Akses Bersih", "unit", "SNI Plumbing", "PLUMBING"),
    ]

    validated_domain_models: List[WorkItemDomainModel] = []
    seen_ids: Set[str] = set()

    for idx, item in enumerate(raw_items):
        if not isinstance(item, tuple) or len(item) != 6:
            raise ValueError(f"STRUCTURE_INTEGRITY_VIOLATION_AT_INDEX_{idx}")

        payload: Dict[str, Any] = {
            "id": item[0],
            "code": item[1],
            "name": item[2],
            "unit": item[3],
            "specification": item[4],
            "category": item[5],
        }

        if payload["id"] in seen_ids:
            raise ValueError(f"DUPLICATE_RAW_ID_DETECTED_WITHIN_BATCH_{payload['id']}")
        seen_ids.add(payload["id"])

        try:
            dto = WorkItemDTO(**payload)
        except Exception as pydantic_exception:
            logger.error("STRICT_FAIL_FAST_VALIDATION_FAILED for id %s: %s", payload["id"], pydantic_exception)
            raise ValueError(f"STRICT_FAIL_FAST_VALIDATION_FAILED_AT_ID_{payload['id']}: {str(pydantic_exception)}") from pydantic_exception

        domain_model = WorkItemDomainModel(
            id=dto.id,
            code=dto.code,
            name=dto.name,
            unit=dto.unit,
            specification=dto.specification,
            category=dto.category,
        )
        validated_domain_models.append(domain_model)

    rollback_list: List[str] = []
    try:
        for model in validated_domain_models:
            node_args = model.to_node_arguments()
            node_instance = WorkItemNode(*node_args)

            kg.add_work_item(node_instance)
            rollback_list.append(model.id)

    except Exception as execution_exception:
        logger.error("TRANSACTION_SAFE_UPSERT_FAILED, rolling back %d items: %s", len(rollback_list), execution_exception)
        for failing_id in reversed(rollback_list):
            try:
                kg.remove_work_item(failing_id)
            except Exception as rollback_exception:
                logger.error("ROLLBACK_FAILED for node id %s: %s", failing_id, rollback_exception)
        raise RuntimeError(f"TRANSACTION_SAFE_UPSERT_FAILED_ROLLBACK_EXECUTED: {str(execution_exception)}") from execution_exception

    logger.info("Plumbing: %d item pekerjaan dimuat", len(validated_domain_models))
