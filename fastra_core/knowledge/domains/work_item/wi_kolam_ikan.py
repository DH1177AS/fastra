# fastra_core\knowledge\domains\work_item\wi_kolam_ikan.py

from __future__ import annotations

import logging
from enum import Enum
from typing import Any, List, Dict, Tuple, Set

from pydantic import BaseModel, ConfigDict, Field, field_validator

logger = logging.getLogger("fastra.knowledge.work_item.kolam_ikan")


class WorkItemUnit(str, Enum):
    MTR_CUBIC = "m³"
    KG = "kg"
    TITIK = "titik"
    UNIT = "unit"
    MTR_SQUARE = "m²"
    SET = "set"


class WorkItemSpecification(str, Enum):
    AHSP_PUPR = "AHSP PUPR"
    SNI_2847 = "SNI 2847"
    STANDAR_KOI = "Standar Koi"


class WorkItemCategory(str, Enum):
    KOLAM_IKAN = "KOLAM_IKAN"


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


def load_wi_kolam_ikan(kg: Any) -> None:
    if kg is None:
        raise ValueError("KNOWLEDGE_GRAPH_INSTANCE_CANNOT_BE_NULL")

    if not hasattr(kg, "add_work_item") or not hasattr(kg, "remove_work_item"):
        raise AttributeError("KNOWLEDGE_GRAPH_MUST_HAVE_ADD_AND_REMOVE_WORK_ITEM_METHODS")

    from fastra_core.knowledge.nodes import WorkItemNode

    raw_items: List[Tuple[str, str, str, str, str, str]] = [
        ("wi_galian_kolam_ikan", "KOL.036", "Galian Tanah Kolam Ikan (Kedalaman 1-1.5m)", "m³", "AHSP PUPR", "KOLAM_IKAN"),
        ("wi_tulangan_kolam_ikan", "KOL.037", "Pemasangan Tulangan Besi Anyam Ganda Kolam Ikan", "kg", "SNI 2847", "KOLAM_IKAN"),
        ("wi_bottom_drain", "KOL.038", "Pemasangan Pipa Saluran Bawah Kolam (Bottom Drain) PVC 3 inci", "titik", "Standar Koi", "KOLAM_IKAN"),
        ("wi_surface_skimmer", "KOL.039", "Pemasangan Pipa Penyedot Permukaan (Surface Skimmer) Kolam", "titik", "Standar Koi", "KOLAM_IKAN"),
        ("wi_multi_chamber", "KOL.040", "Pembuatan Kamar Filter Multi-Chamber (3-4 Sekat) Beton", "unit", "Standar Koi", "KOLAM_IKAN"),
        ("wi_overflow_pipe", "KOL.041", "Pemasangan Pipa Penghubung Antar Chamber (Underflow/Overflow)", "titik", "Standar Koi", "KOLAM_IKAN"),
        ("wi_cor_kolam_ikan", "KOL.042", "Pengecoran Beton Mutu Tinggi Kolam Ikan (Waterproof Admixture)", "m³", "SNI 2847", "KOLAM_IKAN"),
        ("wi_waterproofing_kolam_ikan", "KOL.043", "Pekerjaan Waterproofing Kolam Tipe Cementitious Premium (Aman Ikan)", "m²", "AHSP PUPR", "KOLAM_IKAN"),
        ("wi_plester_kolam_ikan", "KOL.044", "Pekerjaan Plesteran Halus Dinding Dalam Kolam (Corner Rounded)", "m²", "AHSP PUPR", "KOLAM_IKAN"),
        ("wi_waterfall_lip", "KOL.045", "Pembuatan Saluran Air Terjun Dekoratif (Waterfall Lip Stainless)", "unit", "Standar Koi", "KOLAM_IKAN"),
        ("wi_venturi_jet", "KOL.046", "Pemasangan Pipa Pancuran Udara (Venturi Jet System) Bawah Air", "unit", "Standar Koi", "KOLAM_IKAN"),
        ("wi_backwash_drain", "KOL.047", "Instalasi Pipa Pembuangan Lumpur Chamber (Backwash Drain System)", "titik", "Standar Koi", "KOLAM_IKAN"),
        ("wi_brush_filter", "KOL.048", "Pemasangan Media Filter Mekanis (Jaring Nelayan/Brush) Chamber 1", "set", "Standar Koi", "KOLAM_IKAN"),
        ("wi_mat_jepang", "KOL.049", "Pemasangan Media Filter Biologis (Mat Jepang / Batu Gombong) Chamber 2", "set", "Standar Koi", "KOLAM_IKAN"),
        ("wi_zeolit", "KOL.050", "Pemasangan Media Kimiawi (Batu Zeolit / Karbon Aktif) Chamber 3", "set", "Standar Koi", "KOLAM_IKAN"),
        ("wi_uv_sterilizer", "KOL.051", "Instalasi Rumah Lampu UV (Ultraviolet Sterilizer) Chamber Terakhir", "unit", "Standar Koi", "KOLAM_IKAN"),
        ("wi_eco_pump", "KOL.052", "Pemasangan Pompa Celup Sirkulasi Kolam (Submersible Eco Pump)", "unit", "Standar Koi", "KOLAM_IKAN"),
        ("wi_hi_blow_aerator", "KOL.053", "Instalasi Mesin Gelembung Udara (Hi-Blow Aerator Pump) Luar", "unit", "Standar Koi", "KOLAM_IKAN"),
        ("wi_rubber_diffuser", "KOL.054", "Pemasangan Pipa Piringan Aerasi (Rubber Air Diffuser Diaphragm) Dasar Kolam", "unit", "Standar Koi", "KOLAM_IKAN"),
        ("wi_batu_alam_kolam_ikan", "KOL.055", "Pemasangan Batu Alam Pelapis Dinding Kolam (Andesit/Candi) Atas Air", "m²", "AHSP PUPR", "KOLAM_IKAN"),
        ("wi_cat_kolam_ikan", "KOL.056", "Pengecatan Dinding Dalam Kolam Warna Hitam/Hijau Tua (Kontras Ikan)", "m²", "Standar Koi", "KOLAM_IKAN"),
        ("wi_kaca_intip", "KOL.057", "Pemasangan Kaca Intip Samping Kolam (Glass Viewing Window) Tempered 15mm", "unit", "Standar Koi", "KOLAM_IKAN"),
        ("wi_auto_refill", "KOL.058", "Pemasangan Pipa Air Otomatis (Auto Refill Float Valve) Filter", "unit", "Standar Koi", "KOLAM_IKAN"),
        ("wi_rendam_test_ikan", "KOL.059", "Pengujian Kebocoran Kolam 7 Hari (Rendam Penuh)", "unit", "AHSP PUPR", "KOLAM_IKAN"),
        ("wi_netralisasi_kolam_ikan", "KOL.060", "Pekerjaan Netralisasi Semen Beton Kolam (Curing Water Treatment)", "unit", "Standar Koi", "KOLAM_IKAN"),
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

    logger.info("Kolam Ikan Koi: %d item pekerjaan dimuat", len(validated_domain_models))
