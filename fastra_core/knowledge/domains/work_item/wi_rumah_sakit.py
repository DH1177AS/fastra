# fastra_core\knowledge\domains\work_item\wi_rumah_sakit.py

from __future__ import annotations

import logging
from enum import Enum
from typing import Any, List, Dict, Tuple, Set

from pydantic import BaseModel, ConfigDict, Field, field_validator

logger = logging.getLogger("fastra.knowledge.work_item.rumah_sakit")


class WorkItemUnit(str, Enum):
    MTR_RUNNING = "m'"
    UNIT = "unit"
    MTR_SQUARE = "m²"


class WorkItemSpecification(str, Enum):
    STANDAR_KEMENKES = "Standar Kemenkes"
    STANDAR_BAPETEN = "Standar BAPETEN"


class WorkItemCategory(str, Enum):
    RUMAH_SAKIT = "RUMAH_SAKIT"


class WorkItemDTO(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        strict=False,
        frozen=True,
        allow_inf_nan=False,
    )

    id: str = Field(..., min_length=3, max_length=128, pattern=r"^wi_[a-z0-9_]+$")
    code: str = Field(..., min_length=5, max_length=32, pattern=r"^[A-Z]{2,4}\.[0-9]{3}$")
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


def load_wi_rumah_sakit(kg: Any) -> None:
    if kg is None:
        raise ValueError("KNOWLEDGE_GRAPH_INSTANCE_CANNOT_BE_NULL")

    if not hasattr(kg, "add_work_item") or not hasattr(kg, "remove_work_item"):
        raise AttributeError("KNOWLEDGE_GRAPH_MUST_HAVE_ADD_AND_REMOVE_WORK_ITEM_METHODS")

    from fastra_core.knowledge.nodes import WorkItemNode

    raw_items: List[Tuple[str, str, str, str, str, str]] = [
        ("wi_gas_medis_oksigen", "RS.001", "Instalasi Pipa Gas Medis (Oksigen Sentral) Tembaga Bebas Minyak", "m'", "Standar Kemenkes", "RUMAH_SAKIT"),
        ("wi_suction_central", "RS.002", "Instalasi Pipa Vakum Medis (Suction Central) Ruang Operasi", "m'", "Standar Kemenkes", "RUMAH_SAKIT"),
        ("wi_bed_head_unit", "RS.003", "Instalasi Outlet Gas Medis Bed Head Unit (OHU) Panel Ranjang", "unit", "Standar Kemenkes", "RUMAH_SAKIT"),
        ("wi_nurse_call", "RS.004", "Instalasi Nurse Call System (Tombol Panggil Perawat) Ruang Rawat", "unit", "Standar Kemenkes", "RUMAH_SAKIT"),
        ("wi_surgical_light", "RS.005", "Pemasangan Lampu Operasi (Surgical Light) Ceiling Mount", "unit", "Standar Kemenkes", "RUMAH_SAKIT"),
        ("wi_laminar_air_flow", "RS.006", "Pemasangan Panel Laminar Air Flow (LAF) HEPA Filter Kamar Operasi", "unit", "Standar Kemenkes", "RUMAH_SAKIT"),
        ("wi_hermetic_door", "RS.007", "Pemasangan Pintu Hermetic Otomatis Kamar Operasi Stainless Steel Sensor", "unit", "Standar Kemenkes", "RUMAH_SAKIT"),
        ("wi_gas_nitrogen_co2", "RS.008", "Instalasi Sistem Gas Nitrogen / CO2 Ruang Operasi Laparoskopi", "unit", "Standar Kemenkes", "RUMAH_SAKIT"),
        ("wi_holding_tank_infeksius", "RS.009", "Instalasi Pipa Pembuangan Air Limbah Infeksius (Holding Tank) Medis", "m'", "Standar Kemenkes", "RUMAH_SAKIT"),
        ("wi_ipal_medis", "RS.010", "Pembangunan Instalasi Pengolahan Air Limbah (IPAL) Medis Aerasi Klorinasi", "unit", "Standar Kemenkes", "RUMAH_SAKIT"),
        ("wi_incinerator", "RS.011", "Instalasi Incinerator / Mesin Pembakar Limbah Padat Medis (B3)", "unit", "Standar Kemenkes", "RUMAH_SAKIT"),
        ("wi_steam_cssd", "RS.012", "Instalasi Pipa Uap Panas (Steam) Sentral Sterilisasi (CSSD) Boiler", "m'", "Standar Kemenkes", "RUMAH_SAKIT"),
        ("wi_xray_shielding", "RS.013", "Pemasangan X-Ray Shielding (Timbal) Ruang Radiologi Timah Hitam", "m²", "Standar BAPETEN", "RUMAH_SAKIT"),
        ("wi_essential_power", "RS.014", "Instalasi Sistem Elektrikal Essential Power (Generator Medis) ICU/OK", "unit", "Standar Kemenkes", "RUMAH_SAKIT"),
        ("wi_tekanan_negatif", "RS.015", "Pemasangan Sistem Tata Udara Tekanan Negatif Ruang Isolasi HEPA Filter", "unit", "Standar Kemenkes", "RUMAH_SAKIT"),
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

    logger.info("Rumah Sakit: %d item pekerjaan dimuat", len(validated_domain_models))
