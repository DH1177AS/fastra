# fastra_core\knowledge\domains\work_item\wi_serah_terima.py

from __future__ import annotations

import logging
from enum import Enum
from typing import Any, List, Dict, Tuple, Set

from pydantic import BaseModel, ConfigDict, Field, field_validator

logger = logging.getLogger("fastra.knowledge.work_item.serah_terima")


class WorkItemUnit(str, Enum):
    LUMP_SUM = "Ls"
    UNIT = "unit"


class WorkItemSpecification(str, Enum):
    UU_JASA_KONSTRUKSI = "UU Jasa Konstruksi"
    KONTRAK_KERJA = "Kontrak Kerja"
    PERATURAN_DAMKAR = "Peraturan Damkar"
    UU_BANGUNAN_GEDUNG = "UU Bangunan Gedung"
    PERATURAN_PLN_PDAM = "Peraturan PLN/PDAM"
    AHSP_PUPR = "AHSP PUPR"


class WorkItemCategory(str, Enum):
    SERAH_TERIMA = "SERAH_TERIMA"


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


def load_wi_serah_terima(kg: Any) -> None:
    if kg is None:
        raise ValueError("KNOWLEDGE_GRAPH_INSTANCE_CANNOT_BE_NULL")

    if not hasattr(kg, "add_work_item") or not hasattr(kg, "remove_work_item"):
        raise AttributeError("KNOWLEDGE_GRAPH_MUST_HAVE_ADD_AND_REMOVE_WORK_ITEM_METHODS")

    from fastra_core.knowledge.nodes import WorkItemNode

    raw_items: List[Tuple[str, str, str, str, str, str]] = [
        ("wi_as_built_drawing", "ST.001", "Pembuatan Gambar Akhir Terpasang (As-Built Drawing) Rekaman Lapangan", "Ls", "UU Jasa Konstruksi", "SERAH_TERIMA"),
        ("wi_om_manual", "ST.002", "Penyusunan Buku Manual Dokumen MEP (Operation & Maintenance Manual)", "Ls", "UU Jasa Konstruksi", "SERAH_TERIMA"),
        ("wi_punch_list", "ST.003", "Pekerjaan Inspeksi Cacat Bersama (Punch List / Defect List) Arsitek-Kontraktor", "Ls", "Kontrak Kerja", "SERAH_TERIMA"),
        ("wi_perbaikan_punch", "ST.004", "Perbaikan Item Punch List (Cat Kurang Rata, Ubin Pecah, Pintu Seret)", "Ls", "Kontrak Kerja", "SERAH_TERIMA"),
        ("wi_fire_clearance", "ST.005", "Inspeksi Dinas Kebakaran (Fire Clearance Approval) Sertifikat Kelaikan", "unit", "Peraturan Damkar", "SERAH_TERIMA"),
        ("wi_slf", "ST.006", "Pengurusan Sertifikat Laik Fungsi (SLF) Pemerintah Daerah", "unit", "UU Bangunan Gedung", "SERAH_TERIMA"),
        ("wi_bast1", "ST.007", "Serah Terima Kunci Pertama (First Handover - BAST 1) Penandatanganan Berita Acara", "unit", "Kontrak Kerja", "SERAH_TERIMA"),
        ("wi_meter_awal", "ST.008", "Pencatatan Angka KWH Meter Pertama (Listrik PLN & Air PDAM) Awal", "unit", "Peraturan PLN/PDAM", "SERAH_TERIMA"),
        ("wi_maintenance_period", "ST.009", "Fase Masa Pemeliharaan (Maintenance Period / Retention) 3-6 Bulan", "Ls", "Kontrak Kerja", "SERAH_TERIMA"),
        ("wi_demobilisasi_total", "ST.010", "Pengosongan Area Proyek (Demobilisasi Total) Bongkar Barak & Pagar", "Ls", "AHSP PUPR", "SERAH_TERIMA"),
        ("wi_bersih_fasum", "ST.011", "Pembersihan Fasilitas Umum Sekitar (Lumpur Jalan & Selokan Warga)", "Ls", "AHSP PUPR", "SERAH_TERIMA"),
        ("wi_turun_papan_proyek", "ST.012", "Pelepasan Papan Nama Proyek & PBG (Tanda Proyek Resmi Ditutup)", "unit", "UU Jasa Konstruksi", "SERAH_TERIMA"),
        ("wi_garansi_material", "ST.013", "Penyerahan Garansi Material Resmi (AC, Pompa, Waterproofing, Genset, Atap)", "Ls", "Kontrak Kerja", "SERAH_TERIMA"),
        ("wi_bast2", "ST.014", "Serah Terima Akhir (Final Handover - BAST 2) Pencairan Retensi 5%", "unit", "Kontrak Kerja", "SERAH_TERIMA"),
        ("wi_audit_akhir", "ST.015", "Audit Finansial Proyek Akhir (Rekonsiliasi RAB + Addendum + Nota)", "Ls", "Kontrak Kerja", "SERAH_TERIMA"),
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

    logger.info("Serah Terima: %d item pekerjaan dimuat", len(validated_domain_models))
