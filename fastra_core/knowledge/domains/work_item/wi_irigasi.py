# fastra_core\knowledge\domains\work_item\wi_irigasi.py

from __future__ import annotations

import logging
from enum import Enum
from typing import Any, List, Dict, Tuple, Set

from pydantic import BaseModel, ConfigDict, Field, field_validator

logger = logging.getLogger("fastra.knowledge.work_item.irigasi")


class WorkItemUnit(str, Enum):
    MTR_RUNNING = "m'"
    MTR_CUBIC = "m³"
    MTR_SQUARE = "m²"
    BATANG = "batang"
    TITIK = "titik"
    UNIT = "unit"
    LUMP_SUM = "Ls"
    BUAH = "buah"


class WorkItemSpecification(str, Enum):
    SPESIFIKASI_IRIGASI = "Spesifikasi Irigasi"


class WorkItemCategory(str, Enum):
    IRIGASI = "IRIGASI"


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


def load_wi_irigasi(kg: Any) -> None:
    if kg is None:
        raise ValueError("KNOWLEDGE_GRAPH_INSTANCE_CANNOT_BE_NULL")

    if not hasattr(kg, "add_work_item") or not hasattr(kg, "remove_work_item"):
        raise AttributeError("KNOWLEDGE_GRAPH_MUST_HAVE_ADD_AND_REMOVE_WORK_ITEM_METHODS")

    from fastra_core.knowledge.nodes import WorkItemNode

    raw_items: List[Tuple[str, str, str, str, str, str]] = [
        ("wi_levelling_air", "IRG.001", "Survei Elevasi Kemiringan Aliran Air (Levelling Waterflow) Waterpas", "m'", "Spesifikasi Irigasi", "IRIGASI"),
        ("wi_galian_irigasi", "IRG.002", "Galian Tanah Jalur Saluran Irigasi Long Arm Excavator", "m³", "Spesifikasi Irigasi", "IRIGASI"),
        ("wi_rapian_galian_irigasi", "IRG.003", "Pekerjaan Perapian Dinding Galian Tanah Saluran Secara Manual", "m²", "Spesifikasi Irigasi", "IRIGASI"),
        ("wi_tanggul_irigasi", "IRG.004", "Pembuatan Struktur Tanggul Tanah Pembatas Saluran Irigasi", "m³", "Spesifikasi Irigasi", "IRIGASI"),
        ("wi_pasir_alas_irigasi", "IRG.005", "Urugan Pasir Alas Saluran Tebal 10 cm", "m³", "Spesifikasi Irigasi", "IRIGASI"),
        ("wi_lantai_kerja_b0_irigasi", "IRG.006", "Pemasangan Lapisan Lantai Kerja Beton Kurus B0 Dasar Saluran", "m²", "Spesifikasi Irigasi", "IRIGASI"),
        ("wi_cerucuk_bambu", "IRG.007", "Pemasangan Konstruksi Pondasi Cerucuk Bambu (Jika Tanah Saluran Lembek)", "batang", "Spesifikasi Irigasi", "IRIGASI"),
        ("wi_u_ditch_concrete", "IRG.008", "Pemasangan Saluran Beton Pracetak Bentuk U (U-Ditch Concrete) Truck Crane", "m'", "Spesifikasi Irigasi", "IRIGASI"),
        ("wi_nat_u_ditch", "IRG.009", "Pekerjaan Penyambungan Antar Nat U-Ditch Mortar Semen Warna", "m'", "Spesifikasi Irigasi", "IRIGASI"),
        ("wi_cover_u_ditch", "IRG.010", "Pemasangan Plat Beton Penutup Saluran U-Ditch (Cover U-Ditch Floor)", "m'", "Spesifikasi Irigasi", "IRIGASI"),
        ("wi_rcp_buis", "IRG.011", "Pemasangan Saluran Pipa Beton Bulat Pracetak (Buis Beton / RCP)", "m'", "Spesifikasi Irigasi", "IRIGASI"),
        ("wi_concrete_bedding", "IRG.012", "Pekerjaan Cor Beton Selimut Pembungkus Pipa Beton (Concrete Cradle)", "m³", "Spesifikasi Irigasi", "IRIGASI"),
        ("wi_pasangan_batu_kali_irigasi", "IRG.013", "Pemasangan Konstruksi Dinding Saluran Pasangan Batu Kali 1:4", "m³", "Spesifikasi Irigasi", "IRIGASI"),
        ("wi_siar_batu_kali", "IRG.014", "Pekerjaan Plesteran Siar Kepala Pasangan Batu Kali Saluran", "m²", "Spesifikasi Irigasi", "IRIGASI"),
        ("wi_weep_hole", "IRG.015", "Pekerjaan Pembuatan Lubang Sulingan Air Dinding Saluran (Weep Hole PVC)", "titik", "Spesifikasi Irigasi", "IRIGASI"),
        ("wi_geotextile_nonwoven", "IRG.016", "Pemasangan Lapisan Geotextile Non-Woven di Belakang Dinding Pasangan Batu", "m²", "Spesifikasi Irigasi", "IRIGASI"),
        ("wi_urugan_balik_irigasi", "IRG.017", "Urugan Tanah Sela Belakang Dinding Saluran Air Lalu Dipadatkan", "m³", "Spesifikasi Irigasi", "IRIGASI"),
        ("wi_manhole_drain", "IRG.018", "Pembuatan Konstruksi Bak Kontrol Pertemuan Saluran Air (Manhole Drain)", "unit", "Spesifikasi Irigasi", "IRIGASI"),
        ("wi_trash_rack", "IRG.019", "Pemasangan Grill Besi Saringan Sampah Tangkapan Bak Kontrol (Trash Rack)", "unit", "Spesifikasi Irigasi", "IRIGASI"),
        ("wi_sluice_gate", "IRG.020", "Pembuatan Pintu Air Irigasi Kontrol Sistem Angkat Manual (Sluice Gate Steel)", "unit", "Spesifikasi Irigasi", "IRIGASI"),
        ("wi_stilling_basin", "IRG.021", "Pembuatan Konstruksi Bak Pelepas Tekan Aliran Air (Stilling Basin)", "unit", "Spesifikasi Irigasi", "IRIGASI"),
        ("wi_division_box", "IRG.022", "Pembuatan Bangunan Pembagi Aliran Air Irigasi (Division Box Concrete)", "unit", "Spesifikasi Irigasi", "IRIGASI"),
        ("wi_acian_kedap_irigasi", "IRG.023", "Pekerjaan Plesteran Acian Kedap Air Dinding Dalam Bak Pembagi", "m²", "Spesifikasi Irigasi", "IRIGASI"),
        ("wi_cat_waterproofing_irigasi", "IRG.024", "Pelapisan Cat Waterproofing Khusus Kolam/Air pada Dinding Beton Irigasi", "m²", "Spesifikasi Irigasi", "IRIGASI"),
        ("wi_box_culvert", "IRG.025", "Pemasangan Pipa Gorong-Gorong Menembus Bawah Jalan (Box Culvert Precast)", "m'", "Spesifikasi Irigasi", "IRIGASI"),
        ("wi_wing_wall", "IRG.026", "Pengecoran Konstruksi Tembok Sayap Gorong-Gorong (Wing Wall Concrete)", "m³", "Spesifikasi Irigasi", "IRIGASI"),
        ("wi_sludge_dredging", "IRG.027", "Pekerjaan Pengerukan Endapan Lumpur Awal Saluran Eksisting (Sludge Dredging)", "m³", "Spesifikasi Irigasi", "IRIGASI"),
        ("wi_water_commissioning", "IRG.028", "Pengujian Pengaliran Air Sempurna Beban Maksimal Saluran (Water Commissioning)", "Ls", "Spesifikasi Irigasi", "IRIGASI"),
        ("wi_patok_sempadan", "IRG.029", "Pemasangan Patok Batas Tanah Sempadan Saluran Irigasi Pemerintah", "buah", "Spesifikasi Irigasi", "IRIGASI"),
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

    logger.info("Irigasi: %d item pekerjaan dimuat", len(validated_domain_models))
