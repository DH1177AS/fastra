# fastra_core\knowledge\domains\work_item\wi_jalan.py

from __future__ import annotations

import logging
from enum import Enum
from typing import Any, List, Dict, Tuple, Set

from pydantic import BaseModel, ConfigDict, Field, field_validator

logger = logging.getLogger("fastra.knowledge.work_item.jalan")


class WorkItemUnit(str, Enum):
    LUMP_SUM = "Ls"
    MTR_CUBIC = "m³"
    MTR_SQUARE = "m²"
    TITIK = "titik"
    LITER = "liter"
    TON = "ton"
    KG = "kg"
    MTR_RUNNING = "m'"
    BUAH = "buah"


class WorkItemSpecification(str, Enum):
    SPESIFIKASI_BINA_MARGA = "Spesifikasi Bina Marga"


class WorkItemCategory(str, Enum):
    JALAN = "JALAN"


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


def load_wi_jalan(kg: Any) -> None:
    if kg is None:
        raise ValueError("KNOWLEDGE_GRAPH_INSTANCE_CANNOT_BE_NULL")

    if not hasattr(kg, "add_work_item") or not hasattr(kg, "remove_work_item"):
        raise AttributeError("KNOWLEDGE_GRAPH_MUST_HAVE_ADD_AND_REMOVE_WORK_ITEM_METHODS")

    from fastra_core.knowledge.nodes import WorkItemNode

    raw_items: List[Tuple[str, str, str, str, str, str]] = [
        ("wi_survei_trase", "JAL.001", "Pekerjaan Survei Trase dan Rekayasa Geometrik Jalan", "Ls", "Spesifikasi Bina Marga", "JALAN"),
        ("wi_stripping_jalan", "JAL.002", "Pengupasan Tanah Lapisan Atas (Stripping/Scarifying)", "m³", "Spesifikasi Bina Marga", "JALAN"),
        ("wi_galian_jalan", "JAL.003", "Galian Tanah Lunak Semenjana untuk Badan Jalan", "m³", "Spesifikasi Bina Marga", "JALAN"),
        ("wi_buang_tanah_jalan", "JAL.004", "Pembuangan Tanah Sisa Galian Jalur Jalan Keluar Site", "m³", "Spesifikasi Bina Marga", "JALAN"),
        ("wi_timbunan_pilihan", "JAL.005", "Pekerjaan Timbunan Tanah Pilihan Peninggi Elevasi Jalan", "m³", "Spesifikasi Bina Marga", "JALAN"),
        ("wi_subgrade_roller", "JAL.006", "Pemadatan Tanah Dasar (Subgrade) Menggunakan Vibratory Roller", "m²", "Spesifikasi Bina Marga", "JALAN"),
        ("wi_sandcone_jalan", "JAL.007", "Pengujian Kepadatan Tanah Lapangan (Sand Cone Test) per Lapisan", "titik", "Spesifikasi Bina Marga", "JALAN"),
        ("wi_geotextile_woven", "JAL.008", "Pemasangan Lapisan Geotextile Woven Penstabil Tanah Dasar", "m²", "Spesifikasi Bina Marga", "JALAN"),
        ("wi_lpa_b", "JAL.009", "Penghamparan Batu Belah Fondasi Bawah (LPA Kelas B)", "m³", "Spesifikasi Bina Marga", "JALAN"),
        ("wi_pemadatan_lpa_b", "JAL.010", "Pemadatan dan Penyiraman Air Agregat Kelas B", "m³", "Spesifikasi Bina Marga", "JALAN"),
        ("wi_lpa_a", "JAL.011", "Penghamparan Batu Pecah Fondasi Atas (LPA Kelas A)", "m³", "Spesifikasi Bina Marga", "JALAN"),
        ("wi_pemadatan_lpa_a", "JAL.012", "Pemadatan Maksimal Agregat Kelas A (Pneumatic Tire Roller)", "m³", "Spesifikasi Bina Marga", "JALAN"),
        ("wi_cbr_test", "JAL.013", "Pengujian Kepadatan Agregat (CBR Lapangan / DCP Test)", "titik", "Spesifikasi Bina Marga", "JALAN"),
        ("wi_bersih_debu_agregat", "JAL.014", "Pembersihan Debu Agregat Menggunakan Air Compressor", "m²", "Spesifikasi Bina Marga", "JALAN"),
        ("wi_prime_coat", "JAL.015", "Penyemprotan Aspal Cair Perekat Pengikat Dasar (Prime Coat)", "liter", "Spesifikasi Bina Marga", "JALAN"),
        ("wi_tack_coat", "JAL.016", "Penyemprotan Aspal Cair Perekat Antar Lapisan (Tack Coat)", "liter", "Spesifikasi Bina Marga", "JALAN"),
        ("wi_ac_base", "JAL.017", "Penghamparan Aspal Kasar Lapisan Pondasi (AC-Base)", "ton", "Spesifikasi Bina Marga", "JALAN"),
        ("wi_pemadatan_ac_base", "JAL.018", "Pemadatan Awal Aspal AC-Base Menggunakan Tandem Roller", "ton", "Spesifikasi Bina Marga", "JALAN"),
        ("wi_ac_bc", "JAL.019", "Penghamparan Aspal Pengikat Tengah (AC-BC)", "ton", "Spesifikasi Bina Marga", "JALAN"),
        ("wi_ac_wc", "JAL.020", "Penghamparan Aspal Halus Lapis Aus Atas (AC-WC)", "ton", "Spesifikasi Bina Marga", "JALAN"),
        ("wi_pemadatan_ptr", "JAL.021", "Pemadatan Akhir Aspal Jalan Menggunakan Pneumatic Tire Roller", "ton", "Spesifikasi Bina Marga", "JALAN"),
        ("wi_core_drill", "JAL.022", "Pengujian Ketebalan & Kepadatan Aspal Laboratorium (Core Drill Test)", "titik", "Spesifikasi Bina Marga", "JALAN"),
        ("wi_dowel_tie_bar", "JAL.023", "Pemasangan Rangka Besi Dudukan Jalan Beton (Dowel & Tie Bar)", "kg", "Spesifikasi Bina Marga", "JALAN"),
        ("wi_bekisting_jalan_beton", "JAL.024", "Pemasangan Bekisting Samping Cor Beton Jalan (Besi Plat)", "m'", "Spesifikasi Bina Marga", "JALAN"),
        ("wi_plastik_alas_cor", "JAL.025", "Penghamparan Plastik Alas Cor Jalan Beton", "m²", "Spesifikasi Bina Marga", "JALAN"),
        ("wi_rigid_pavement", "JAL.026", "Pengecoran Jalan Beton Mutu Tinggi (FS 45 / K-350) Pakai Paver Machine", "m³", "Spesifikasi Bina Marga", "JALAN"),
        ("wi_grooving_jalan", "JAL.027", "Pekerjaan Pembuatan Tekstur Gores Kain Rami / Alur Ban Jalan", "m²", "Spesifikasi Bina Marga", "JALAN"),
        ("wi_curing_compound", "JAL.028", "Penyemprotan Cairan Perawatan Beton (Curing Compound) Jalan", "m²", "Spesifikasi Bina Marga", "JALAN"),
        ("wi_joint_cutter", "JAL.029", "Pemotongan Celah Sambungan Beton Jalan (Concrete Cutting)", "m'", "Spesifikasi Bina Marga", "JALAN"),
        ("wi_asphalt_sealant", "JAL.030", "Pengisian Celah Potongan Jalan Beton Menggunakan Asphalt Sealant", "m'", "Spesifikasi Bina Marga", "JALAN"),
        ("wi_kanstin_beton", "JAL.031", "Pemasangan Batu Kanstin Beton Pembatas Pinggir Jalan (Kanstin)", "m'", "Spesifikasi Bina Marga", "JALAN"),
        ("wi_backing_kanstin", "JAL.032", "Pengecoran Cor Beton Pengunci Belakang Kanstin (Backing Concrete)", "m'", "Spesifikasi Bina Marga", "JALAN"),
        ("wi_marka_thermoplastic", "JAL.033", "Pengecatan Marka Jalan Garis Putih/Kuning (Thermoplastic Paint Resin)", "m²", "Spesifikasi Bina Marga", "JALAN"),
        ("wi_road_stud", "JAL.034", "Pemasangan Marka Jalan Timbul Paku Bumi Reflektor (Glass Road Stud)", "buah", "Spesifikasi Bina Marga", "JALAN"),
        ("wi_rambu_jalan", "JAL.035", "Pemasangan Rambu Lalu Lintas dan Petunjuk Arah Jalan", "buah", "Spesifikasi Bina Marga", "JALAN"),
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

    logger.info("Jalan: %d item pekerjaan dimuat", len(validated_domain_models))
