# fastra_core\knowledge\domains\work_item\wi_pertanian.py

from __future__ import annotations

import logging
from enum import Enum
from typing import Any, List, Dict, Tuple, Set

from pydantic import BaseModel, ConfigDict, Field, field_validator

logger = logging.getLogger("fastra.knowledge.work_item.pertanian")


class WorkItemUnit(str, Enum):
    MTR_SQUARE = "m²"
    UNIT = "unit"
    SET = "set"


class WorkItemSpecification(str, Enum):
    STANDAR_PETERNAKAN = "Standar Peternakan"
    STANDAR_PERIKANAN = "Standar Perikanan"
    STANDAR_PERTANIAN = "Standar Pertanian"


class WorkItemCategory(str, Enum):
    PERTANIAN = "PERTANIAN"


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


def load_wi_pertanian(kg: Any) -> None:
    if kg is None:
        raise ValueError("KNOWLEDGE_GRAPH_INSTANCE_CANNOT_BE_NULL")

    if not hasattr(kg, "add_work_item") or not hasattr(kg, "remove_work_item"):
        raise AttributeError("KNOWLEDGE_GRAPH_MUST_HAVE_ADD_AND_REMOVE_WORK_ITEM_METHODS")

    from fastra_core.knowledge.nodes import WorkItemNode

    raw_items: List[Tuple[str, str, str, str, str, str]] = [
        ("wi_closed_house", "TAN.001", "Pembangunan Kandang Ternak Baja Ringan Sistem Closed House", "m²", "Standar Peternakan", "PERTANIAN"),
        ("wi_slatted_floor", "TAN.002", "Pemasangan Lantai Slat Beton Kandang (Slatted Floor)", "m²", "Standar Peternakan", "PERTANIAN"),
        ("wi_cooling_pad", "TAN.003", "Pemasangan Sistem Ventilasi Kandang (Exhaust Fan + Cooling Pad)", "unit", "Standar Peternakan", "PERTANIAN"),
        ("wi_steel_silo", "TAN.004", "Pemasangan Silo Penyimpanan Pakan Ternak (Steel Silo)", "unit", "Standar Peternakan", "PERTANIAN"),
        ("wi_auto_feeder", "TAN.005", "Pemasangan Tempat Pakan & Minum Otomatis Ternak", "set", "Standar Peternakan", "PERTANIAN"),
        ("wi_bioflok_kolam", "TAN.006", "Pembangunan Kolam Terpal / Beton Bioflok Lele (Intensive Fish Pond)", "m²", "Standar Perikanan", "PERTANIAN"),
        ("wi_paddle_wheel", "TAN.007", "Pemasangan Aerator Kincir Air Kolam Ikan (Paddle Wheel Aerator)", "unit", "Standar Perikanan", "PERTANIAN"),
        ("wi_greenhouse", "TAN.008", "Pembangunan Rumah Kaca / Greenhouse Baja Ringan + UV Plastic", "m²", "Standar Pertanian", "PERTANIAN"),
        ("wi_drip_irrigation", "TAN.009", "Pemasangan Jaringan Irigasi Tetes Greenhouse (Drip Irrigation System)", "m²", "Standar Pertanian", "PERTANIAN"),
        ("wi_cold_storage", "TAN.010", "Pembangunan Ruang Pendingin & Penyimpanan Hasil Panen (Cold Storage)", "unit", "Standar Pertanian", "PERTANIAN"),
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

    logger.info("Pertanian: %d item pekerjaan dimuat", len(validated_domain_models))
