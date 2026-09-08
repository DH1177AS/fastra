# fastra_core\knowledge\domains\work_item\wi_tambahan_relasi.py

from __future__ import annotations

import logging
from enum import Enum
from typing import Any, List, Dict, Tuple, Set

from pydantic import BaseModel, ConfigDict, Field, field_validator

logger = logging.getLogger("fastra.knowledge.work_item.tambahan_relasi")


class WorkItemUnit(str, Enum):
    MTR_SQUARE = "m²"
    MTR_RUNNING = "m'"
    TITIK = "titik"
    KG = "kg"
    UNIT = "unit"
    SET = "set"


class WorkItemSpecification(str, Enum):
    AHSP_PUPR = "AHSP PUPR"
    SNI_2835_2008 = "SNI 2835:2008"
    SNI_2847_2013 = "SNI 2847:2013"
    SNI_7394_2008 = "SNI 7394:2008"


class WorkItemCategory(str, Enum):
    DINDING = "DINDING"
    TANAH = "TANAH"
    INTERIOR = "INTERIOR"
    RENOVASI = "RENOVASI"
    STRUKTUR = "STRUKTUR"


class WorkItemDTO(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        strict=False,
        frozen=True,
        allow_inf_nan=False,
    )

    id: str = Field(..., min_length=3, max_length=128, pattern=r"^wi_[a-z0-9_]+$")
    code: str = Field(..., min_length=5, max_length=32, pattern=r"^[A-Z]{3,4}\.[0-9]{3}(:[0-9]{4})?$")
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


def load_wi_tambahan_relasi(kg: Any) -> None:
    if kg is None:
        raise ValueError("KNOWLEDGE_GRAPH_INSTANCE_CANNOT_BE_NULL")

    if not hasattr(kg, "add_work_item") or not hasattr(kg, "remove_work_item"):
        raise AttributeError("KNOWLEDGE_GRAPH_MUST_HAVE_ADD_AND_REMOVE_WORK_ITEM_METHODS")

    from fastra_core.knowledge.nodes import WorkItemNode

    raw_items: List[Tuple[str, str, str, str, str, str]] = [
        ("wi_pasang_partisi_gypsum_double", "DIN.009", "Pasangan Partisi Gypsum Double", "m²", "AHSP PUPR", "DINDING"),
        ("wi_pemadatan", "TAN.005", "Pemadatan Tanah", "m²", "SNI 2835:2008", "TANAH"),
        ("wi_pasang_gorden_blackout", "INT.017", "Pemasangan Gorden Blackout", "m²", "AHSP PUPR", "INTERIOR"),
        ("wi_pasang_railing_tangga_stainless", "INT.018", "Pemasangan Railing Tangga Stainless", "m'", "AHSP PUPR", "INTERIOR"),
        ("wi_carbon_frp", "REN.004", "Perkuatan Carbon FRP", "m²", "SNI 2847:2013", "RENOVASI"),
        ("wi_pasang_karpet_roll", "INT.019", "Pemasangan Karpet Roll", "m²", "AHSP PUPR", "INTERIOR"),
        ("wi_perbaikan_instalasi_air", "REN.016", "Perbaikan Instalasi Air Bocor", "titik", "AHSP PUPR", "RENOVASI"),
        ("wi_besi_polos", "STR.003", "Pembesian dengan Besi Polos", "kg", "SNI 7394:2008", "STRUKTUR"),
        ("wi_pasang_partisi_kantor", "INT.020", "Pemasangan Partisi Kantor", "m²", "AHSP PUPR", "INTERIOR"),
        ("wi_pasang_lantai_vinyl_sheet", "INT.021", "Pemasangan Lantai Vinyl Sheet", "m²", "AHSP PUPR", "INTERIOR"),
        ("wi_pasang_cermin_bevel", "INT.022", "Pemasangan Cermin Bevel", "m²", "AHSP PUPR", "INTERIOR"),
        ("wi_pasang_roller_blind", "INT.023", "Pemasangan Roller Blind", "m²", "AHSP PUPR", "INTERIOR"),
        ("wi_pasang_panel_wpc", "INT.024", "Pemasangan Panel Dinding WPC", "m²", "AHSP PUPR", "INTERIOR"),
        ("wi_pasang_wall_moulding", "INT.025", "Pemasangan Wall Moulding", "m²", "AHSP PUPR", "INTERIOR"),
        ("wi_pasang_fluted_panel", "INT.026", "Pemasangan Fluted Panel", "m²", "AHSP PUPR", "INTERIOR"),
        ("wi_pasang_top_table_kuarsa", "INT.027", "Pemasangan Top Table Kuarsa", "m'", "AHSP PUPR", "INTERIOR"),
        ("wi_pasang_siku_pinggul", "INT.028", "Pemasangan Siku Pinggul Granit", "m'", "AHSP PUPR", "INTERIOR"),
        ("wi_pasang_led_strip_lemari", "INT.029", "Pemasangan LED Strip Lemari", "unit", "AHSP PUPR", "INTERIOR"),
        ("wi_pasang_led_kolong_kabinet", "INT.030", "Pemasangan LED Kolong Kabinet", "m'", "AHSP PUPR", "INTERIOR"),
        ("wi_pasang_rel_laci_undermount", "INT.031", "Pemasangan Rel Laci Undermount", "set", "AHSP PUPR", "INTERIOR"),
        ("wi_pasang_engsel_softclose", "INT.032", "Pemasangan Engsel Soft-Close", "set", "AHSP PUPR", "INTERIOR"),
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

    logger.info("Tambahan Relasi: %d item pekerjaan dimuat", len(validated_domain_models))
