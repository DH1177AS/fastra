# fastra_core\knowledge\domains\work_item\wi_pengujian_qc.py

from __future__ import annotations

import logging
from enum import Enum
from typing import Any, List, Dict, Tuple, Set

from pydantic import BaseModel, ConfigDict, Field, field_validator

logger = logging.getLogger("fastra.knowledge.work_item.pengujian_qc")


class WorkItemUnit(str, Enum):
    SAMPEL = "sampel"
    UNIT = "unit"
    SIRKUIT = "sirkuit"
    TITIK = "titik"
    MTR_SQUARE = "m²"


class WorkItemSpecification(str, Enum):
    SNI_1974 = "SNI 1974"
    SNI_2052 = "SNI 2052"
    AHSP_PUPR = "AHSP PUPR"
    PUIL = "PUIL"
    SNI_PLUMBING = "SNI Plumbing"
    SNI_LIFT = "SNI Lift"
    STANDAR_NFPA = "Standar NFPA"
    PERATURAN_PLN = "Peraturan PLN"
    STANDAR_KEMENKES = "Standar Kemenkes"
    SNI_CAT = "SNI Cat"
    SNI_KACA = "SNI Kaca"
    STANDAR_AKUSTIK = "Standar Akustik"


class WorkItemCategory(str, Enum):
    QAQC = "QAQC"


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


def load_wi_pengujian_qc(kg: Any) -> None:
    if kg is None:
        raise ValueError("KNOWLEDGE_GRAPH_INSTANCE_CANNOT_BE_NULL")

    if not hasattr(kg, "add_work_item") or not hasattr(kg, "remove_work_item"):
        raise AttributeError("KNOWLEDGE_GRAPH_MUST_HAVE_ADD_AND_REMOVE_WORK_ITEM_METHODS")

    from fastra_core.knowledge.nodes import WorkItemNode

    raw_items: List[Tuple[str, str, str, str, str, str]] = [
        ("wi_slump_test", "QC.001", "Pengujian Kuat Tekan Beton (Slump Test & Compression Test) Lab 28 Hari", "sampel", "SNI 1974", "QAQC"),
        ("wi_tensile_test", "QC.002", "Pengujian Tarik Besi Beton (Tensile Test) Lab", "sampel", "SNI 2052", "QAQC"),
        ("wi_flood_test", "QC.003", "Pengujian Kebocoran Atap (Flood Test Plafon/Dak) Genangan 5cm 2x24 Jam", "unit", "AHSP PUPR", "QAQC"),
        ("wi_megger_test", "QC.004", "Pengujian Tahanan Isolasi Kabel (Megger Test) Sirkuit Listrik", "sirkuit", "PUIL", "QAQC"),
        ("wi_earth_test", "QC.005", "Pengujian Tahanan Tanah (Earth Grounding Test) Earth Tester", "titik", "PUIL", "QAQC"),
        ("wi_nitrogen_test", "QC.006", "Pengujian Tekanan Udara Pipa AC (Nitrogen Leak Test) Deteksi Bocor", "unit", "AHSP PUPR", "QAQC"),
        ("wi_flow_test", "QC.007", "Pengujian Aliran Air Bersih (Flow Test) Debit Keran & Shower", "titik", "SNI Plumbing", "QAQC"),
        ("wi_load_test_lift", "QC.008", "Pengujian Beban Angkat Lift (Load Test Elevator) Beban Pasir/Besi", "unit", "SNI Lift", "QAQC"),
        ("wi_smoke_test", "QC.009", "Pengujian Fungsi Pemadam Kamar (Smoke & Heat Detector Test) Asap Buatan", "unit", "Standar NFPA", "QAQC"),
        ("wi_slo", "QC.010", "Sertifikasi Kelaikan Struktur Kelistrikan (SLO) Inspeksi LIT", "unit", "Peraturan PLN", "QAQC"),
        ("wi_bakteri_test", "QC.011", "Pengujian Bakteriologis Air Bersih (E.Coli Lab) Sampel Air", "sampel", "Standar Kemenkes", "QAQC"),
        ("wi_dft_test", "QC.012", "Pengujian Ketebalan Cat (Dry Film Thickness Test) Alat Ukur Digital", "titik", "SNI Cat", "QAQC"),
        ("wi_heat_soak_test", "QC.013", "Pengujian Kaca Tempered (Heat Soak Test) Minimalkan Pecah Spontan", "unit", "SNI Kaca", "QAQC"),
        ("wi_acoustic_test", "QC.014", "Pengujian Kebisingan Ruangan (Acoustic DB Test) Sound Level Meter", "unit", "Standar Akustik", "QAQC"),
        ("wi_floor_flatness", "QC.015", "Pemeriksaan Kerataan Lantai (Floor Flatness Test) Jidar Laser", "m²", "AHSP PUPR", "QAQC"),
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

    logger.info("Pengujian QA/QC: %d item pekerjaan dimuat", len(validated_domain_models))
