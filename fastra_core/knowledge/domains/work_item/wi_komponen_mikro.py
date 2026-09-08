# fastra_core\knowledge\domains\work_item\wi_komponen_mikro.py

from __future__ import annotations

import logging
from enum import Enum
from typing import Any, List, Dict, Tuple, Set

from pydantic import BaseModel, ConfigDict, Field, field_validator

logger = logging.getLogger("fastra.knowledge.work_item.komponen_mikro")


class WorkItemUnit(str, Enum):
    BUAH = "buah"
    MTR_RUNNING = "m'"
    SET = "set"
    TITIK = "titik"
    UNIT = "unit"
    KG = "kg"
    PAKET = "paket"
    MTR_SQUARE = "m²"


class WorkItemSpecification(str, Enum):
    AHSP_PUPR = "AHSP PUPR"
    SNI_PLUMBING = "SNI Plumbing"
    SNI_1729 = "SNI 1729"
    PUIL = "PUIL"


class WorkItemCategory(str, Enum):
    KOMPONEN_MIKRO = "KOMPONEN_MIKRO"


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


def load_wi_komponen_mikro(kg: Any) -> None:
    if kg is None:
        raise ValueError("KNOWLEDGE_GRAPH_INSTANCE_CANNOT_BE_NULL")

    if not hasattr(kg, "add_work_item") or not hasattr(kg, "remove_work_item"):
        raise AttributeError("KNOWLEDGE_GRAPH_MUST_HAVE_ADD_AND_REMOVE_WORK_ITEM_METHODS")

    from fastra_core.knowledge.nodes import WorkItemNode

    raw_items: List[Tuple[str, str, str, str, str, str]] = [
        ("wi_dynabolt_kusen", "MIK.001", "Pemasangan Dynabolt / Anchor Bolt Kusen (Angkur Besi Pengikat)", "buah", "AHSP PUPR", "KOMPONEN_MIKRO"),
        ("wi_silikon_sealant_kusen", "MIK.002", "Pekerjaan Silikon Sealant Kusen & Kaca (Lem Silikon Anti-Air)", "m'", "AHSP PUPR", "KOMPONEN_MIKRO"),
        ("wi_skrup_drywall", "MIK.003", "Pemasangan Skrup Drywall Plafon (Sekrup Khusus Anti-Karat Kepala Rata)", "buah", "AHSP PUPR", "KOMPONEN_MIKRO"),
        ("wi_fiber_tape", "MIK.004", "Pemasangan Kassa Plafon (Fiber Tape) Perekat Jaring Sambungan Gipsum", "m'", "AHSP PUPR", "KOMPONEN_MIKRO"),
        ("wi_drop_bolt", "MIK.005", "Pemasangan Drop Bolt Pintu (Slot Kunci Tanam Vertikal Pintu Ganda)", "set", "AHSP PUPR", "KOMPONEN_MIKRO"),
        ("wi_door_stop_magnet", "MIK.006", "Pemasangan Door Stop / Magnetic Catch (Penahan Pintu Magnetis)", "buah", "AHSP PUPR", "KOMPONEN_MIKRO"),
        ("wi_roofing_screw", "MIK.007", "Pemasangan Skrup Drilling Rangka Atap (Sekrup Baja Ringan Kepala Kunci)", "buah", "AHSP PUPR", "KOMPONEN_MIKRO"),
        ("wi_pipe_clamp", "MIK.008", "Pemasangan Klem Pipa Air (Pipe Clamp/Hanger) Dudukan Besi Gantung", "buah", "AHSP PUPR", "KOMPONEN_MIKRO"),
        ("wi_heat_fusion_ppr", "MIK.009", "Pekerjaan Penyambungan Pipa Metode Heat Fusion (PPR) Mesin Welding", "titik", "SNI Plumbing", "KOMPONEN_MIKRO"),
        ("wi_clean_out", "MIK.010", "Pemasangan Clean Out Pipa Air Kotor (Lubang Sumbat Berulir)", "unit", "SNI Plumbing", "KOMPONEN_MIKRO"),
        ("wi_roof_drain_castiron", "MIK.011", "Pemasangan Roof Drain Cast Iron (Saringan Dak Beton Besi Cor)", "unit", "AHSP PUPR", "KOMPONEN_MIKRO"),
        ("wi_kawat_las", "MIK.012", "Pemasangan Kawat Las (Welding Electrode) Struktur (Tipe E7018)", "kg", "SNI 1729", "KOMPONEN_MIKRO"),
        ("wi_lasdop", "MIK.013", "Pemasangan Wire Connector / Lasdop (Penutup Plastik Isolasi Kabel)", "buah", "PUIL", "KOMPONEN_MIKRO"),
        ("wi_fischer", "MIK.014", "Pemasangan Fischer Dinding (Selongsong Plastik Bor Dinding Cengkeram Sekrup)", "buah", "AHSP PUPR", "KOMPONEN_MIKRO"),
        ("wi_cable_lug", "MIK.015", "Pemasangan Kabel Skun (Cable Lug) Sepatu Kabel Tembaga Panel Utama", "buah", "PUIL", "KOMPONEN_MIKRO"),
        ("wi_gland_kabel", "MIK.016", "Pemasangan Gland Kabel Panel (Pengunci Lubang Kabel Kedap Debu)", "buah", "PUIL", "KOMPONEN_MIKRO"),
        ("wi_kabel_ties", "MIK.017", "Pemasangan Ties Wrap / Kabel Ties (Pengikat Plastik Jalur Kabel)", "paket", "PUIL", "KOMPONEN_MIKRO"),
        ("wi_flexible_conduit", "MIK.018", "Pemasangan Metal Conduit Flexibel (Pipa Besi Lentur Pembungkus Kabel)", "m'", "PUIL", "KOMPONEN_MIKRO"),
        ("wi_tile_adhesive_c2", "MIK.019", "Pemasangan Perekat Ubin Instan Tipe Premium (C2) Ubin Besar/Kolam", "m²", "AHSP PUPR", "KOMPONEN_MIKRO"),
        ("wi_zinc_chromate", "MIK.020", "Pekerjaan Pelapisan Primer Coated Baja (Zinc Chromate Anti-Karat)", "m²", "SNI 1729", "KOMPONEN_MIKRO"),
        ("wi_thermostat", "MIK.021", "Pemasangan Thermostat Kamar (Panel Pengatur Suhu Digital Dinding)", "unit", "AHSP PUPR", "KOMPONEN_MIKRO"),
        ("wi_acoustic_sealant", "MIK.022", "Pemasangan Acoustic Sealant (Lem Kedap Suara Sekeliling Partisi)", "m'", "AHSP PUPR", "KOMPONEN_MIKRO"),
        ("wi_seal_tape", "MIK.023", "Pemasangan Seal Tape Teflon (Lilitan Pita Putih Ulir Keran Anti Bocor)", "buah", "SNI Plumbing", "KOMPONEN_MIKRO"),
        ("wi_corner_bead", "MIK.024", "Pemasangan Corner Bead PVC/Aluminium (Profil Pelindung Sudut Acian)", "m'", "AHSP PUPR", "KOMPONEN_MIKRO"),
        ("wi_flexible_joint", "MIK.025", "Pemasangan Flexible Joint Pipa (Karet/Kawat Anyam Peredam Getaran Pompa)", "unit", "SNI Plumbing", "KOMPONEN_MIKRO"),
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

    logger.info("Komponen Mikro: %d item pekerjaan dimuat", len(validated_domain_models))
