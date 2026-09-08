# fastra_core\knowledge\domains\work_item\wi_pra_konstruksi.py

from __future__ import annotations

import logging
from enum import Enum
from typing import Any, List, Dict, Tuple, Set

from pydantic import BaseModel, ConfigDict, Field, field_validator

logger = logging.getLogger("fastra.knowledge.work_item.pra_konstruksi")


class WorkItemUnit(str, Enum):
    LUMP_SUM = "Ls"
    TITIK = "titik"
    UNIT = "unit"
    MTR_SQUARE = "m²"
    POHON = "pohon"
    MTR_CUBIC = "m³"
    MTR_RUNNING = "m'"
    SET = "set"


class WorkItemSpecification(str, Enum):
    UU_JASA_KONSTRUKSI = "UU Jasa Konstruksi"
    UU_LLAJ = "UU LLAJ"
    UU_LH = "UU LH"
    PERATURAN_PLN = "Peraturan PLN"
    PERATURAN_PDAM = "Peraturan PDAM"
    STANDAR_GAMBAR = "Standar Gambar"
    SNI_2847 = "SNI 2847"
    STANDAR_MEP = "Standar MEP"
    STANDAR_GEOMATIK = "Standar Geomatik"
    AHSP_PUPR = "AHSP PUPR"
    PUIL = "PUIL"
    STANDAR_KONSTRUKSI = "Standar Konstruksi"
    PP_K3 = "PP K3"


class WorkItemCategory(str, Enum):
    PRA_KONSTRUKSI = "PRA_KONSTRUKSI"


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


def load_wi_pra_konstruksi(kg: Any) -> None:
    if kg is None:
        raise ValueError("KNOWLEDGE_GRAPH_INSTANCE_CANNOT_BE_NULL")

    if not hasattr(kg, "add_work_item") or not hasattr(kg, "remove_work_item"):
        raise AttributeError("KNOWLEDGE_GRAPH_MUST_HAVE_ADD_AND_REMOVE_WORK_ITEM_METHODS")

    from fastra_core.knowledge.nodes import WorkItemNode

    raw_items: List[Tuple[str, str, str, str, str, str]] = [
        ("wi_pbg", "PRA.001", "Pengurusan Persetujuan Bangunan Gedung (PBG / Eks IMB)", "Ls", "UU Jasa Konstruksi", "PRA_KONSTRUKSI"),
        ("wi_andalalin", "PRA.002", "Pengurusan Andalalin (Analisis Dampak Lalu Lintas)", "Ls", "UU LLAJ", "PRA_KONSTRUKSI"),
        ("wi_uklupl", "PRA.003", "Pengurusan Dokumen UKL-UPL / Amdal Lingkungan", "Ls", "UU LH", "PRA_KONSTRUKSI"),
        ("wi_slo_listrik", "PRA.004", "Pengurusan Izin Penyambungan Baru Daya PLN", "Ls", "Peraturan PLN", "PRA_KONSTRUKSI"),
        ("wi_slo_pdam", "PRA.005", "Pengurusan Izin Sambungan Baru Air Bersih PDAM", "Ls", "Peraturan PDAM", "PRA_KONSTRUKSI"),
        ("wi_shopdraw_arsitek", "PRA.006", "Penyusunan Gambar Kerja Arsitektur (Shop Drawings)", "Ls", "Standar Gambar", "PRA_KONSTRUKSI"),
        ("wi_shopdraw_struktur", "PRA.007", "Penyusunan Gambar Struktur & Perhitungan Pembebanan", "Ls", "SNI 2847", "PRA_KONSTRUKSI"),
        ("wi_shopdraw_mep", "PRA.008", "Penyusunan Gambar Instalasi MEP", "Ls", "Standar MEP", "PRA_KONSTRUKSI"),
        ("wi_survei_batas", "PRA.009", "Pengukuran Batas Lahan dengan GPS / Total Station", "Ls", "Standar Geomatik", "PRA_KONSTRUKSI"),
        ("wi_benchmark", "PRA.010", "Pembuatan Titik Benchmark (BM) Utama Elevasi Proyek", "titik", "Standar Geomatik", "PRA_KONSTRUKSI"),
        ("wi_papan_proyek", "PRA.011", "Pemasangan Papan Nama Legalitas Proyek", "unit", "UU Jasa Konstruksi", "PRA_KONSTRUKSI"),
        ("wi_land_clearing", "PRA.012", "Pembersihan Lahan Tahap Awal (Land Clearing) dari Semak", "m²", "AHSP PUPR", "PRA_KONSTRUKSI"),
        ("wi_tebang_pohon", "PRA.013", "Penebangan Pohon Eksisting & Pembongkaran Akar Tanam", "pohon", "AHSP PUPR", "PRA_KONSTRUKSI"),
        ("wi_stripping_topsoil", "PRA.014", "Pengupasan Lapisan Tanah Subur Atas (Stripping Top Soil) 20 cm", "m³", "AHSP PUPR", "PRA_KONSTRUKSI"),
        ("wi_buang_topsoil", "PRA.015", "Pembuangan Tanah Kupasan Keluar Area Site Proyek", "m³", "AHSP PUPR", "PRA_KONSTRUKSI"),
        ("wi_pagar_keliling", "PRA.016", "Pemasangan Pagar Keliling Proyek Bahan Spandek Tinggi 2m", "m'", "AHSP PUPR", "PRA_KONSTRUKSI"),
        ("wi_pintu_gerbang", "PRA.017", "Pembuatan Pintu Gerbang Utama Akses Truk Proyek", "unit", "AHSP PUPR", "PRA_KONSTRUKSI"),
        ("wi_direksikit", "PRA.018", "Pembangunan Kantor Sementara Pengawas (Direksikit)", "m²", "AHSP PUPR", "PRA_KONSTRUKSI"),
        ("wi_barak_pekerja", "PRA.019", "Pembangunan Barak Tempat Tinggal Sementara Pekerja", "m²", "AHSP PUPR", "PRA_KONSTRUKSI"),
        ("wi_gudang_tertutup", "PRA.020", "Pembangunan Gudang Tertutup Khusus Semen & Alat Presisi", "m²", "AHSP PUPR", "PRA_KONSTRUKSI"),
        ("wi_gudang_terbuka", "PRA.021", "Pembangunan Gudang Terbuka Khusus Besi & Material Berat", "m²", "AHSP PUPR", "PRA_KONSTRUKSI"),
        ("wi_bedeng_toilet", "PRA.022", "Pembuatan Bedeng Toilet Sementara & Septic Tank Pekerja", "unit", "AHSP PUPR", "PRA_KONSTRUKSI"),
        ("wi_sumur_bor_sementara", "PRA.023", "Pembuatan Sumur Bor Sementara untuk Air Kerja Proyek", "unit", "AHSP PUPR", "PRA_KONSTRUKSI"),
        ("wi_jetpump_sementara", "PRA.024", "Pemasangan Pompa Air Jetpump Sementara untuk Air Kerja", "unit", "AHSP PUPR", "PRA_KONSTRUKSI"),
        ("wi_genset_proyek", "PRA.025", "Penyewaan Genset Utama Proyek Kapasitas Besar (Silenced)", "unit", "AHSP PUPR", "PRA_KONSTRUKSI"),
        ("wi_kabel_induk_genset", "PRA.026", "Penarikan Kabel Induk dari Genset ke Panel Distribusi Kerja", "m'", "PUIL", "PRA_KONSTRUKSI"),
        ("wi_bak_air_kerja", "PRA.027", "Pembuatan Bak Penampung Air Kerja Kapasitas 2000 Liter", "unit", "AHSP PUPR", "PRA_KONSTRUKSI"),
        ("wi_bouwplank", "PRA.028", "Pemasangan Papan Pengukur Koordinat Dinding (Bouwplank)", "m'", "Standar Konstruksi", "PRA_KONSTRUKSI"),
        ("wi_benang_as", "PRA.029", "Pemasangan Paku As Bangunan & Penarikan Benang Levelling", "m'", "Standar Konstruksi", "PRA_KONSTRUKSI"),
        ("wi_mobilisasi_excavator", "PRA.030", "Mobilisasi Ekskavator PC200 ke Lokasi Proyek", "unit", "AHSP PUPR", "PRA_KONSTRUKSI"),
        ("wi_mobilisasi_dumptruck", "PRA.031", "Mobilisasi Truk Jungkit (Dump Truck) 8 Kubik", "unit", "AHSP PUPR", "PRA_KONSTRUKSI"),
        ("wi_mobilisasi_stamper", "PRA.032", "Mobilisasi Mesin Stamper Kodok & Stamper Kuda", "unit", "AHSP PUPR", "PRA_KONSTRUKSI"),
        ("wi_apd_k3", "PRA.033", "Penyediaan Alat Pelindung Diri (APD) K3 untuk Pekerja", "set", "PP K3", "PRA_KONSTRUKSI"),
        ("wi_rambu_k3", "PRA.034", "Pemasangan Rambu Bahaya & Spanduk K3 Keliling Proyek", "unit", "PP K3", "PRA_KONSTRUKSI"),
        ("wi_drainase_sementara", "PRA.035", "Pembuatan Saluran Air Pembuangan Sementara Area Proyek", "m'", "AHSP PUPR", "PRA_KONSTRUKSI"),
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

    logger.info("Pra-Konstruksi: %d item pekerjaan dimuat", len(validated_domain_models))
