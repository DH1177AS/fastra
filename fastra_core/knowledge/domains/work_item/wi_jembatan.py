# fastra_core\knowledge\domains\work_item\wi_jembatan.py

from __future__ import annotations

import logging
from enum import Enum
from typing import Any, List, Dict, Tuple, Set

from pydantic import BaseModel, ConfigDict, Field, field_validator

logger = logging.getLogger("fastra.knowledge.work_item.jembatan")


class WorkItemUnit(str, Enum):
    TITIK = "titik"
    MTR_RUNNING = "m'"
    MTR_SQUARE = "m²"
    UNIT = "unit"
    KG = "kg"
    MTR_CUBIC = "m³"
    BUAH = "buah"
    TON = "ton"
    LUMP_SUM = "Ls"


class WorkItemSpecification(str, Enum):
    SPESIFIKASI_JEMBATAN = "Spesifikasi Jembatan"


class WorkItemCategory(str, Enum):
    JEMBATAN = "JEMBATAN"


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


def load_wi_jembatan(kg: Any) -> None:
    if kg is None:
        raise ValueError("KNOWLEDGE_GRAPH_INSTANCE_CANNOT_BE_NULL")

    if not hasattr(kg, "add_work_item") or not hasattr(kg, "remove_work_item"):
        raise AttributeError("KNOWLEDGE_GRAPH_MUST_HAVE_ADD_AND_REMOVE_WORK_ITEM_METHODS")

    from fastra_core.knowledge.nodes import WorkItemNode

    raw_items: List[Tuple[str, str, str, str, str, str]] = [
        ("wi_titik_as_jembatan", "JEM.001", "Pekerjaan Penentuan Titik As Jembatan Pemancang (Abutment & Pier)", "titik", "Spesifikasi Jembatan", "JEMBATAN"),
        ("wi_detour_road", "JEM.002", "Pembuatan Jembatan Sementara / Jalur Alih Proyek (Detour Road)", "m'", "Spesifikasi Jembatan", "JEMBATAN"),
        ("wi_cofferdam", "JEM.003", "Pemasangan Dinding Pembatas Air Sungai Sementara (Cofferdam)", "m²", "Spesifikasi Jembatan", "JEMBATAN"),
        ("wi_dewatering_jembatan", "JEM.004", "Pemompaan Air Sungai Keluar Area Kerja Pondasi (Dewatering Jembatan)", "unit", "Spesifikasi Jembatan", "JEMBATAN"),
        ("wi_mobilisasi_borepile", "JEM.005", "Mobilisasi Alat Berat Bore Pile Machine", "unit", "Spesifikasi Jembatan", "JEMBATAN"),
        ("wi_borepile_drilling", "JEM.006", "Pengeboran Lubang Pondasi Dalam Jembatan (Bore Pile Drilling)", "m'", "Spesifikasi Jembatan", "JEMBATAN"),
        ("wi_bentonit", "JEM.007", "Pemasangan Cairan Bentonit Penahan Dinding Bor Pondasi", "m'", "Spesifikasi Jembatan", "JEMBATAN"),
        ("wi_rebar_cage_borepile", "JEM.008", "Pemasangan Anyaman Besi Silinder Tulangan Pondasi Bore Pile", "kg", "Spesifikasi Jembatan", "JEMBATAN"),
        ("wi_tremie_cor", "JEM.009", "Pengecoran Beton Pondasi Dalam Metode Pipa Tremi Bawah Air", "m³", "Spesifikasi Jembatan", "JEMBATAN"),
        ("wi_pile_chipping_jembatan", "JEM.010", "Pembobokan Kepala Beton Bore Pile (Pile Chipping)", "titik", "Spesifikasi Jembatan", "JEMBATAN"),
        ("wi_abutment_galian", "JEM.011", "Galian Tanah Struktur Kepala Jembatan (Abutment Excavation)", "m³", "Spesifikasi Jembatan", "JEMBATAN"),
        ("wi_pier_head_rebar", "JEM.012", "Pembesian Struktur Dudukan Tiang Jembatan (Pile Cap / Pier Head)", "kg", "Spesifikasi Jembatan", "JEMBATAN"),
        ("wi_pier_head_bekisting", "JEM.013", "Pemasangan Bekisting Baja Struktur Kepala Jembatan", "m²", "Spesifikasi Jembatan", "JEMBATAN"),
        ("wi_pier_head_cor", "JEM.014", "Pengecoran Beton Massal Struktur Kepala Jembatan Mutu K-350", "m³", "Spesifikasi Jembatan", "JEMBATAN"),
        ("wi_bearing_pad", "JEM.015", "Pemasangan Bantalan Karet Jembatan (Rubber Elastomeric Bearing Pad)", "buah", "Spesifikasi Jembatan", "JEMBATAN"),
        ("wi_angkur_bearing", "JEM.016", "Pemasangan Angkur Baja Penahan Geser Bantalan Jembatan", "buah", "Spesifikasi Jembatan", "JEMBATAN"),
        ("wi_mobilisasi_girder", "JEM.017", "Mobilisasi Balok Girder Beton Pracetak (PC-I Girder) Ke Lokasi", "buah", "Spesifikasi Jembatan", "JEMBATAN"),
        ("wi_launching_girder", "JEM.018", "Ereksi Peluncuran Balok Girder ke Atas Jembatan Launcher Crane", "buah", "Spesifikasi Jembatan", "JEMBATAN"),
        ("wi_post_tension", "JEM.019", "Pekerjaan Penarikan Kabel Baja Pasca-Tegang Girder Jembatan", "buah", "Spesifikasi Jembatan", "JEMBATAN"),
        ("wi_grouting_tendon", "JEM.020", "Penyuntikan Semen Grout ke Dalam Pipa Kabel Girder", "buah", "Spesifikasi Jembatan", "JEMBATAN"),
        ("wi_diaphragm_beam", "JEM.021", "Pemasangan Balok Pengikat Antar Girder (Diaphragm Beam Cast in Situ)", "m³", "Spesifikasi Jembatan", "JEMBATAN"),
        ("wi_precast_shuttering", "JEM.022", "Pemasangan Pelat Lantai Panel Pracetak Antar Girder", "m²", "Spesifikasi Jembatan", "JEMBATAN"),
        ("wi_rebar_lantai_jembatan", "JEM.023", "Perakitan Anyaman Besi Bertulang Pembesian Lantai Atas Jembatan", "kg", "Spesifikasi Jembatan", "JEMBATAN"),
        ("wi_scupper_pipe", "JEM.024", "Pemasangan Pipa Sparing Lubang Buang Air Jembatan (Scupper Pipe)", "titik", "Spesifikasi Jembatan", "JEMBATAN"),
        ("wi_cor_lantai_jembatan", "JEM.025", "Pengecoran Lapisan Lantai Beton Utama Jembatan Mutu K-400", "m³", "Spesifikasi Jembatan", "JEMBATAN"),
        ("wi_expansion_joint", "JEM.026", "Pemasangan Sambungan Siar Muai Baja Tepi Jembatan", "m'", "Spesifikasi Jembatan", "JEMBATAN"),
        ("wi_parapet_wall", "JEM.027", "Pemasangan Sandaran Pembatas Jembatan Beton (Parapet Wall Concrete)", "m'", "Spesifikasi Jembatan", "JEMBATAN"),
        ("wi_handrail_jembatan", "JEM.028", "Pemasangan Pipa Railing Sandaran Jembatan Besi Galvanis", "m'", "Spesifikasi Jembatan", "JEMBATAN"),
        ("wi_talud_batu_jembatan", "JEM.029", "Pekerjaan Pasangan Batu Talud Penahan Tanah Samping Jembatan", "m³", "Spesifikasi Jembatan", "JEMBATAN"),
        ("wi_gabion_jembatan", "JEM.030", "Pemasangan Lapisan Batu Bronjong Kawat Pencegah Erosi Air Sungai", "m³", "Spesifikasi Jembatan", "JEMBATAN"),
        ("wi_waterproofing_jembatan", "JEM.031", "Penyemprotan Lapisan Waterproofing Membran Atas Lantai Jembatan", "m²", "Spesifikasi Jembatan", "JEMBATAN"),
        ("wi_aspal_jembatan", "JEM.032", "Penghamparan Lapisan Aspal Hotmix di Atas Lantai Jembatan", "ton", "Spesifikasi Jembatan", "JEMBATAN"),
        ("wi_baby_roller_jembatan", "JEM.033", "Pemadatan Lapisan Aspal Atas Jembatan Menggunakan Baby Roller", "ton", "Spesifikasi Jembatan", "JEMBATAN"),
        ("wi_lampu_jembatan", "JEM.034", "Pemasangan Lampu Penerangan Jalan Jembatan Arsitektural", "unit", "Spesifikasi Jembatan", "JEMBATAN"),
        ("wi_kabel_lampu_jembatan", "JEM.035", "Instalasi Kabel Jalur Tiang Lampu Jembatan di Dalam Struktur Parapet", "m'", "Spesifikasi Jembatan", "JEMBATAN"),
        ("wi_penangkal_petir_jembatan", "JEM.036", "Instalasi Sistem Penangkal Petir Struktur Atas Jembatan", "unit", "Spesifikasi Jembatan", "JEMBATAN"),
        ("wi_static_load_test", "JEM.037", "Pengujian Beban Statis Jembatan Truk Berjejer (Static Load Test)", "unit", "Spesifikasi Jembatan", "JEMBATAN"),
        ("wi_dynamic_load_test", "JEM.038", "Pengujian Beban Dinamis Jembatan Truk Berjalan (Dynamic Load Test)", "unit", "Spesifikasi Jembatan", "JEMBATAN"),
        ("wi_akselerometer", "JEM.039", "Uji Keandalan Getaran Struktur Jembatan Sensor Akselerometer", "unit", "Spesifikasi Jembatan", "JEMBATAN"),
        ("wi_bersih_bawah_jembatan", "JEM.040", "Pembersihan Total Sisa Material Perancah Bawah Jembatan", "Ls", "Spesifikasi Jembatan", "JEMBATAN"),
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

    logger.info("Jembatan: %d item pekerjaan dimuat", len(validated_domain_models))
