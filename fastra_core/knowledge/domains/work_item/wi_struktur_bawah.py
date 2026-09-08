# fastra_core\knowledge\domains\work_item\wi_struktur_bawah.py

from __future__ import annotations

import logging
from enum import Enum
from typing import Any, List, Dict, Tuple, Set

from pydantic import BaseModel, ConfigDict, Field, field_validator

logger = logging.getLogger("fastra.knowledge.work_item.struktur_bawah")


class WorkItemUnit(str, Enum):
    MTR_CUBIC = "m³"
    MTR_SQUARE = "m²"
    UNIT = "unit"
    MTR_RUNNING = "m'"
    TITIK = "titik"
    KG = "kg"


class WorkItemSpecification(str, Enum):
    SNI_2835_2008 = "SNI 2835:2008"
    AHSP_PUPR = "AHSP PUPR"
    SNI_8460_2017 = "SNI 8460:2017"
    ASTM_D5882 = "ASTM D5882"
    ASTM_D1143 = "ASTM D1143"
    SNI_2836_2008 = "SNI 2836:2008"
    SNI_2847_2019 = "SNI 2847:2019"


class WorkItemCategory(str, Enum):
    STRUKTUR_BAWAH = "STRUKTUR_BAWAH"


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


def load_wi_struktur_bawah(kg: Any) -> None:
    if kg is None:
        raise ValueError("KNOWLEDGE_GRAPH_INSTANCE_CANNOT_BE_NULL")

    if not hasattr(kg, "add_work_item") or not hasattr(kg, "remove_work_item"):
        raise AttributeError("KNOWLEDGE_GRAPH_MUST_HAVE_ADD_AND_REMOVE_WORK_ITEM_METHODS")

    from fastra_core.knowledge.nodes import WorkItemNode

    raw_items: List[Tuple[str, str, str, str, str, str]] = [
        ("wi_galian_pondasi_spesifik", "SUB.001", "Galian Tanah Pondasi Spesifik (Manual Presisi)", "m³", "SNI 2835:2008", "STRUKTUR_BAWAH"),
        ("wi_sheet_pile", "SUB.002", "Pemasangan Dinding Penahan Tanah (Sheet Pile)", "m²", "AHSP PUPR", "STRUKTUR_BAWAH"),
        ("wi_dewatering_pump", "SUB.003", "Instalasi Sistem Pengeringan (Dewatering Pump)", "unit", "AHSP PUPR", "STRUKTUR_BAWAH"),
        ("wi_soil_improvement", "SUB.004", "Pekerjaan Perbaikan Tanah (Soil Improvement)", "m³", "AHSP PUPR", "STRUKTUR_BAWAH"),
        ("wi_pemancangan_spun_pile", "SUB.005", "Pemancangan Tiang Pancang (Mini Pile / Spun Pile)", "m'", "SNI 8460:2017", "STRUKTUR_BAWAH"),
        ("wi_welding_joint_pile", "SUB.006", "Penyambungan Tiang Pancang (Welding Joints)", "titik", "SNI 8460:2017", "STRUKTUR_BAWAH"),
        ("wi_bored_pile_drilling", "SUB.007", "Pengeboran Pondasi Bored Pile", "m'", "SNI 8460:2017", "STRUKTUR_BAWAH"),
        ("wi_slurry_cleaning", "SUB.008", "Pembersihan Lumpur Bore Pile (Slurry Cleaning)", "titik", "SNI 8460:2017", "STRUKTUR_BAWAH"),
        ("wi_bore_pile_rebar_cage", "SUB.009", "Fabrikasi & Penurunan Keranjang Besi Bore Pile", "kg", "SNI 8460:2017", "STRUKTUR_BAWAH"),
        ("wi_bore_pile_tremie", "SUB.010", "Pengecoran Beton Bore Pile Sistem Pipa Tremie", "m³", "SNI 8460:2017", "STRUKTUR_BAWAH"),
        ("wi_pit_test", "SUB.011", "Pengujian Integritas Tiang Pancang (Pile Integrity Test - PIT)", "titik", "ASTM D5882", "STRUKTUR_BAWAH"),
        ("wi_static_load_test", "SUB.012", "Pengujian Beban Statis (Static Load Test)", "titik", "ASTM D1143", "STRUKTUR_BAWAH"),
        ("wi_pile_chipping", "SUB.013", "Pemotongan Kepala Tiang (Pile Chipping)", "titik", "AHSP PUPR", "STRUKTUR_BAWAH"),
        ("wi_pasir_alas_pondasi", "SUB.014", "Penghamparan Pasir Alas Pondasi (10 cm)", "m³", "AHSP PUPR", "STRUKTUR_BAWAH"),
        ("wi_lean_concrete", "SUB.015", "Pembuatan Lantai Kerja (Lean Concrete K-100)", "m³", "AHSP PUPR", "STRUKTUR_BAWAH"),
        ("wi_aanstanding", "SUB.016", "Pemasangan Pondasi Batu Kosong (Aanstanding)", "m³", "AHSP PUPR", "STRUKTUR_BAWAH"),
        ("wi_pondasi_batu_kali", "SUB.017", "Pemasangan Pondasi Batu Kali Belah 1:4", "m³", "SNI 2836:2008", "STRUKTUR_BAWAH"),
        ("wi_pile_cap_rebar", "SUB.018", "Fabrikasi Tulangan Besi Pile Cap / Footplat", "kg", "SNI 2847:2019", "STRUKTUR_BAWAH"),
        ("wi_pile_cap_bekisting", "SUB.019", "Pemasangan Bekisting Pile Cap / Footplat", "m²", "AHSP PUPR", "STRUKTUR_BAWAH"),
        ("wi_pile_cap_cor", "SUB.020", "Pengecoran Beton Struktur Pondasi (Ready Mix K-250/K-300)", "m³", "SNI 2847:2019", "STRUKTUR_BAWAH"),
        ("wi_bekisting_bongkar_pondasi", "SUB.021", "Pembongkaran Bekisting Pondasi (Setelah 24 Jam)", "m²", "AHSP PUPR", "STRUKTUR_BAWAH"),
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

    logger.info("Struktur Bawah: %d item pekerjaan dimuat", len(validated_domain_models))
