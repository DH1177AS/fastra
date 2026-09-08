# fastra_core\knowledge\domains\work_item\wi_gedung_pemerintah.py

from __future__ import annotations

import logging
from enum import Enum
from typing import Any, List, Dict, Tuple

from pydantic import BaseModel, ConfigDict, Field, field_validator

logger = logging.getLogger("fastra.knowledge.work_item.gedung_pemerintah")


class WorkItemUnit(str, Enum):
    UNIT = "unit"
    SET = "set"


class WorkItemSpecification(str, Enum):
    STANDAR_PEMERINTAH = "Standar Pemerintah"


class WorkItemCategory(str, Enum):
    GEDUNG_PEMERINTAH = "GEDUNG_PEMERINTAH"


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


def load_wi_gedung_pemerintah(kg: Any) -> None:
    if kg is None:
        raise ValueError("KNOWLEDGE_GRAPH_INSTANCE_CANNOT_BE_NULL")

    if not hasattr(kg, "add_work_item") or not hasattr(kg, "remove_work_item"):
        raise AttributeError("KNOWLEDGE_GRAPH_MUST_HAVE_ADD_AND_REMOVE_WORK_ITEM_METHODS")

    from fastra_core.knowledge.nodes import WorkItemNode

    raw_items: List[Tuple[str, str, str, str, str, str]] = [
        ("wi_data_center_pem", "PEM.001", "Pembangunan Ruang Server Data Center Pemerintah (Raised Floor, AC Presisi, Fire Suppression)", "unit", "Standar Pemerintah", "GEDUNG_PEMERINTAH"),
        ("wi_command_center", "PEM.002", "Pemasangan Sistem Command Center / Situation Room (Video Wall, Console, UPS N+1)", "unit", "Standar Pemerintah", "GEDUNG_PEMERINTAH"),
        ("wi_perimeter_security", "PEM.003", "Instalasi Sistem Pengamanan Perimeter Multi-Layer (CCTV Analytics, Barrier Gate, Bollard)", "unit", "Standar Pemerintah", "GEDUNG_PEMERINTAH"),
        ("wi_led_display_sign", "PEM.004", "Pemasangan Papan Informasi Elektronik / LED Display Sign Outdoor", "unit", "Standar Pemerintah", "GEDUNG_PEMERINTAH"),
        ("wi_queuing_system", "PEM.005", "Instalasi Antrian Elektronik Terpadu (Queuing System) Mesin Tiket + Display", "unit", "Standar Pemerintah", "GEDUNG_PEMERINTAH"),
        ("wi_detention_room", "PEM.006", "Pembangunan Ruang Tahanan Sementara / Detention Room (Dinding Beton, CCTV 24 Jam)", "unit", "Standar Pemerintah", "GEDUNG_PEMERINTAH"),
        ("wi_podium_ruang_rapat", "PEM.007", "Pemasangan Podium / Mimbar Ruang Rapat Besar (Tata Suara Terintegrasi)", "unit", "Standar Pemerintah", "GEDUNG_PEMERINTAH"),
        ("wi_video_conference", "PEM.008", "Pemasangan Sistem Teleconference Ruang Rapat (Layar, Kamera PTZ, Panel Sentuh)", "unit", "Standar Pemerintah", "GEDUNG_PEMERINTAH"),
        ("wi_lobby_penerimaan", "PEM.009", "Pembangunan Lobby Penerimaan Publik Skala Besar (Resepsionis, Backdrop, Ruang Tunggu)", "unit", "Standar Pemerintah", "GEDUNG_PEMERINTAH"),
        ("wi_flagpole_set", "PEM.010", "Pemasangan Flagpole Set (Tiang Bendera Dalam Ruangan + Bendera Merah Putih & Instansi)", "set", "Standar Pemerintah", "GEDUNG_PEMERINTAH"),
        ("wi_mobile_shelving", "PEM.011", "Instalasi Sistem Arsip Bergerak (Mobile Shelving / Roll O'Pack) Rel Lantai", "unit", "Standar Pemerintah", "GEDUNG_PEMERINTAH"),
        ("wi_double_gate_post", "PEM.012", "Pembangunan Pos Jaga Ganda (Double Gate Security Post) Palang Otomatis", "unit", "Standar Pemerintah", "GEDUNG_PEMERINTAH"),
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

    logger.info("Gedung Pemerintah: %d item pekerjaan dimuat", len(validated_domain_models))
