# fastra_core\knowledge\domains\work_item\wi_gondola.py

from __future__ import annotations

import logging
from enum import Enum
from typing import Any, List, Dict, Tuple

from pydantic import BaseModel, ConfigDict, Field, field_validator

logger = logging.getLogger("fastra.knowledge.work_item.gondola")


class WorkItemUnit(str, Enum):
    MTR_RUNNING = "m'"
    UNIT = "unit"


class WorkItemSpecification(str, Enum):
    SNI_03_3985 = "SNI 03-3985"


class WorkItemCategory(str, Enum):
    GONDOLA = "GONDOLA"


class WorkItemDTO(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        strict=False,
        frozen=True,
        allow_inf_nan=False,
    )

    id: str = Field(..., min_length=1, max_length=128, pattern=r"^wi_[a-z0-9_]+$")
    code: str = Field(..., min_length=1, max_length=32, pattern=r"^[A-Z]{3}\.[0-9]{3}$")
    name: str = Field(..., min_length=1, max_length=512)
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


def load_wi_gondola(kg: Any) -> None:
    if kg is None:
        raise ValueError("KNOWLEDGE_GRAPH_INSTANCE_CANNOT_BE_NULL")

    if not hasattr(kg, "add_work_item") or not hasattr(kg, "remove_work_item"):
        raise AttributeError("KNOWLEDGE_GRAPH_MUST_HAVE_ADD_AND_REMOVE_WORK_ITEM_METHODS")

    from fastra_core.knowledge.nodes import WorkItemNode

    raw_items: List[Tuple[str, str, str, str, str, str]] = [
        ("wi_rel_gondola_atap", "GON.001", "Pemasangan Rel Gondola Atap Gedung (Permanent Davit Arm System)", "m'", "SNI 03-3985", "GONDOLA"),
        ("wi_mesin_gondola", "GON.002", "Pemasangan Mesin Gondola Elektrik (Traction Hoist)", "unit", "SNI 03-3985", "GONDOLA"),
        ("wi_bracket_gondola", "GON.003", "Pemasangan Bracket Penyangga Gondola Fasad Kaca", "unit", "SNI 03-3985", "GONDOLA"),
        ("wi_keranjang_gondola", "GON.004", "Pemasangan Keranjang Gondola (Suspended Cradle Platform)", "unit", "SNI 03-3985", "GONDOLA"),
        ("wi_safety_rope_gondola", "GON.005", "Pemasangan Sistem Pengaman Gondola Independent Safety Rope", "unit", "SNI 03-3985", "GONDOLA"),
    ]

    validated_domain_models: List[WorkItemDomainModel] = []

    for item in raw_items:
        if not isinstance(item, tuple) or len(item) != 6:
            raise ValueError("INVALID_RAW_DATA_STRUCTURE")

        payload: Dict[str, Any] = {
            "id": item[0],
            "code": item[1],
            "name": item[2],
            "unit": item[3],
            "specification": item[4],
            "category": item[5],
        }

        try:
            dto = WorkItemDTO(**payload)
        except Exception as pydantic_exception:
            logger.error("STRICT_FAIL_FAST_VALIDATION_FAILED for payload %s: %s", payload, pydantic_exception)
            raise ValueError(f"STRICT_FAIL_FAST_VALIDATION_FAILED: {str(pydantic_exception)}") from pydantic_exception

        domain_model = WorkItemDomainModel(
            id=dto.id,
            code=dto.code,
            name=dto.name,
            unit=dto.unit,
            specification=dto.specification,
            category=dto.category,
        )
        validated_domain_models.append(domain_model)

    rollback_list: List[Any] = []
    try:
        for model in validated_domain_models:
            node_args = model.to_node_arguments()
            node_instance = WorkItemNode(*node_args)

            kg.add_work_item(node_instance)
            rollback_list.append(node_instance)

    except Exception as execution_exception:
        logger.error("TRANSACTION_SAFE_UPSERT_FAILED, rolling back %d items: %s", len(rollback_list), execution_exception)
        for failing_node in reversed(rollback_list):
            try:
                kg.remove_work_item(failing_node.id)
            except Exception as rollback_exception:
                logger.error("ROLLBACK_FAILED for node id %s: %s", failing_node.id, rollback_exception)
        raise RuntimeError(f"TRANSACTION_SAFE_UPSERT_FAILED_ROLLBACK_EXECUTED: {str(execution_exception)}") from execution_exception

    logger.info("Gondola: %d item pekerjaan dimuat", len(validated_domain_models))
