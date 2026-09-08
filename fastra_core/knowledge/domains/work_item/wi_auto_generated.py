# fastra_core\knowledge\domains\work_item\wi_auto_generated.py

from __future__ import annotations

import logging
from enum import Enum
from typing import Any, List, Dict, Tuple, Set

from pydantic import BaseModel, ConfigDict, Field, field_validator

logger = logging.getLogger("fastra.knowledge.work_item.auto_generated")


class WorkItemUnit(str, Enum):
    UNIT = "unit"


class WorkItemSpecification(str, Enum):
    AHSP_PUPR = "AHSP PUPR"


class WorkItemCategory(str, Enum):
    TAMBAHAN = "TAMBAHAN"


class WorkItemDTO(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        strict=False,
        frozen=True,
        allow_inf_nan=False,
    )

    id: str = Field(..., min_length=3, max_length=128, pattern=r"^wi_[a-z0-9_]+$")
    code: str = Field(..., min_length=2, max_length=32, pattern=r"^[A-Z0-9\.]+$")
    name: str = Field(..., min_length=2, max_length=512)
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


def load_wi_auto_generated(kg: Any) -> None:
    if kg is None:
        raise ValueError("KNOWLEDGE_GRAPH_INSTANCE_CANNOT_BE_NULL")

    if not hasattr(kg, "add_work_item") or not hasattr(kg, "remove_work_item"):
        raise AttributeError("KNOWLEDGE_GRAPH_MUST_HAVE_ADD_AND_REMOVE_WORK_ITEM_METHODS")

    from fastra_core.knowledge.nodes import WorkItemNode

    raw_items: List[Tuple[str, str, str, str, str, str]] = [
        ("wi_acian", "WI.ACIAN", "Acian", "unit", "AHSP PUPR", "TAMBAHAN"),
        ("wi_atap_baja_ringan", "WI.ATAP.BA", "Atap Baja Ringan", "unit", "AHSP PUPR", "TAMBAHAN"),
        ("wi_bak_kontrol", "WI.BAK.KON", "Bak Kontrol", "unit", "AHSP PUPR", "TAMBAHAN"),
        ("wi_batu_belah_1_5", "WI.BATU.BE", "Batu Belah 1 5", "unit", "AHSP PUPR", "TAMBAHAN"),
        ("wi_batu_koral", "WI.BATU.KO", "Batu Koral", "unit", "AHSP PUPR", "TAMBAHAN"),
        ("wi_bekisting_balok", "WI.BEKISTI", "Bekisting Balok", "unit", "AHSP PUPR", "TAMBAHAN"),
        ("wi_bekisting_kolom", "WI.BEKISTI", "Bekisting Kolom", "unit", "AHSP PUPR", "TAMBAHAN"),
        ("wi_besi_ulir", "WI.BESI.UL", "Besi Ulir", "unit", "AHSP PUPR", "TAMBAHAN"),
        ("wi_beton_abutment", "WI.BETON.A", "Beton Abutment", "unit", "AHSP PUPR", "TAMBAHAN"),
        ("wi_beton_k225", "WI.BETON.K", "Beton K225", "unit", "AHSP PUPR", "TAMBAHAN"),
        ("wi_beton_k250", "WI.BETON.K", "Beton K250", "unit", "AHSP PUPR", "TAMBAHAN"),
        ("wi_bore_pile_jembatan", "WI.BORE.PI", "Bore Pile Jembatan", "unit", "AHSP PUPR", "TAMBAHAN"),
        ("wi_bronjong", "WI.BRONJON", "Bronjong", "unit", "AHSP PUPR", "TAMBAHAN"),
        ("wi_bronjong_kawat", "WI.BRONJON", "Bronjong Kawat", "unit", "AHSP PUPR", "TAMBAHAN"),
        ("wi_cat_anti_karat", "WI.CAT.ANT", "Cat Anti Karat", "unit", "AHSP PUPR", "TAMBAHAN"),
        ("wi_cat_besi", "WI.CAT.BES", "Cat Besi", "unit", "AHSP PUPR", "TAMBAHAN"),
        ("wi_cat_eksterior", "WI.CAT.EKS", "Cat Eksterior", "unit", "AHSP PUPR", "TAMBAHAN"),
        ("wi_cat_kayu", "WI.CAT.KAY", "Cat Kayu", "unit", "AHSP PUPR", "TAMBAHAN"),
        ("wi_cat_tembok", "WI.CAT.TEM", "Cat Tembok", "unit", "AHSP PUPR", "TAMBAHAN"),
        ("wi_diffuser_ac", "WI.DIFFUSE", "Diffuser Ac", "unit", "AHSP PUPR", "TAMBAHAN"),
        ("wi_elastomeric_bearing", "WI.ELASTOM", "Elastomeric Bearing", "unit", "AHSP PUPR", "TAMBAHAN"),
        ("wi_exhaust_fan_10in", "WI.EXHAUST", "Exhaust Fan 10In", "unit", "AHSP PUPR", "TAMBAHAN"),
        ("wi_galian_tanah", "WI.GALIAN.", "Galian Tanah", "unit", "AHSP PUPR", "TAMBAHAN"),
        ("wi_ganti_keramik", "WI.GANTI.K", "Ganti Keramik", "unit", "AHSP PUPR", "TAMBAHAN"),
        ("wi_genteng_beton", "WI.GENTENG", "Genteng Beton", "unit", "AHSP PUPR", "TAMBAHAN"),
        ("wi_genteng_metal", "WI.GENTENG", "Genteng Metal", "unit", "AHSP PUPR", "TAMBAHAN"),
        ("wi_gorong_gorong", "WI.GORONG.", "Gorong Gorong", "unit", "AHSP PUPR", "TAMBAHAN"),
        ("wi_granit_lantai", "WI.GRANIT.", "Granit Lantai", "unit", "AHSP PUPR", "TAMBAHAN"),
        ("wi_grouting_beton", "WI.GROUTIN", "Grouting Beton", "unit", "AHSP PUPR", "TAMBAHAN"),
        ("wi_guardrail", "WI.GUARDRA", "Guardrail", "unit", "AHSP PUPR", "TAMBAHAN"),
        ("wi_instalasi_access_point", "WI.INSTALA", "Instalasi Access Point", "unit", "AHSP PUPR", "TAMBAHAN"),
        ("wi_instalasi_alarm", "WI.INSTALA", "Instalasi Alarm", "unit", "AHSP PUPR", "TAMBAHAN"),
        ("wi_instalasi_cctv", "WI.INSTALA", "Instalasi Cctv", "unit", "AHSP PUPR", "TAMBAHAN"),
        ("wi_instalasi_detector", "WI.INSTALA", "Instalasi Detector", "unit", "AHSP PUPR", "TAMBAHAN"),
        ("wi_instalasi_emergency_light", "WI.INSTALA", "Instalasi Emergency Light", "unit", "AHSP PUPR", "TAMBAHAN"),
        ("wi_instalasi_hydrant", "WI.INSTALA", "Instalasi Hydrant", "unit", "AHSP PUPR", "TAMBAHAN"),
        ("wi_instalasi_nvr", "WI.INSTALA", "Instalasi Nvr", "unit", "AHSP PUPR", "TAMBAHAN"),
        ("wi_instalasi_panel", "WI.INSTALA", "Instalasi Panel", "unit", "AHSP PUPR", "TAMBAHAN"),
        ("wi_instalasi_sensor_gas", "WI.INSTALA", "Instalasi Sensor Gas", "unit", "AHSP PUPR", "TAMBAHAN"),
        ("wi_instalasi_sprinkler", "WI.INSTALA", "Instalasi Sprinkler", "unit", "AHSP PUPR", "TAMBAHAN"),
        ("wi_instalasi_stop_kontak", "WI.INSTALA", "Instalasi Stop Kontak", "unit", "AHSP PUPR", "TAMBAHAN"),
        ("wi_instalasi_titik_lampu", "WI.INSTALA", "Instalasi Titik Lampu", "unit", "AHSP PUPR", "TAMBAHAN"),
        ("wi_jacketing_kolom", "WI.JACKETI", "Jacketing Kolom", "unit", "AHSP PUPR", "TAMBAHAN"),
        ("wi_jendela_kayu", "WI.JENDELA", "Jendela Kayu", "unit", "AHSP PUPR", "TAMBAHAN"),
        ("wi_kanopi", "WI.KANOPI", "Kanopi", "unit", "AHSP PUPR", "TAMBAHAN"),
        ("wi_keramik_dinding", "WI.KERAMIK", "Keramik Dinding", "unit", "AHSP PUPR", "TAMBAHAN"),
        ("wi_keramik_lantai", "WI.KERAMIK", "Keramik Lantai", "unit", "AHSP PUPR", "TAMBAHAN"),
        ("wi_kusen_kayu", "WI.KUSEN.K", "Kusen Kayu", "unit", "AHSP PUPR", "TAMBAHAN"),
        ("wi_lantai_spc", "WI.LANTAI.", "Lantai Spc", "unit", "AHSP PUPR", "TAMBAHAN"),
        ("wi_nok_genteng", "WI.NOK.GEN", "Nok Genteng", "unit", "AHSP PUPR", "TAMBAHAN"),
        ("wi_pagar_besi", "WI.PAGAR.B", "Pagar Besi", "unit", "AHSP PUPR", "TAMBAHAN"),
        ("wi_pagar_brc", "WI.PAGAR.B", "Pagar Brc", "unit", "AHSP PUPR", "TAMBAHAN"),
        ("wi_pas_bata", "WI.PAS.BAT", "Pas Bata", "unit", "AHSP PUPR", "TAMBAHAN"),
        ("wi_pas_bata_ringan", "WI.PAS.BAT", "Pas Bata Ringan", "unit", "AHSP PUPR", "TAMBAHAN"),
        ("wi_pasang_ac_1pk", "WI.PASANG.", "Pasang Ac 1Pk", "unit", "AHSP PUPR", "TAMBAHAN"),
        ("wi_pasang_ac_2pk", "WI.PASANG.", "Pasang Ac 2Pk", "unit", "AHSP PUPR", "TAMBAHAN"),
        ("wi_pasang_apar", "WI.PASANG.", "Pasang Apar", "unit", "AHSP PUPR", "TAMBAHAN"),
        ("wi_pasang_bollard", "WI.PASANG.", "Pasang Bollard", "unit", "AHSP PUPR", "TAMBAHAN"),
        ("wi_pasang_ducting_ac", "WI.PASANG.", "Pasang Ducting Ac", "unit", "AHSP PUPR", "TAMBAHAN"),
        ("wi_pasang_kaca_tempered", "WI.PASANG.", "Pasang Kaca Tempered", "unit", "AHSP PUPR", "TAMBAHAN"),
        ("wi_pasang_karpet_tile", "WI.PASANG.", "Pasang Karpet Tile", "unit", "AHSP PUPR", "TAMBAHAN"),
        ("wi_pasang_kitchen_set", "WI.PASANG.", "Pasang Kitchen Set", "unit", "AHSP PUPR", "TAMBAHAN"),
        ("wi_pasang_kloset", "WI.PASANG.", "Pasang Kloset", "unit", "AHSP PUPR", "TAMBAHAN"),
        ("wi_pasang_lantai_spc", "WI.PASANG.", "Pasang Lantai Spc", "unit", "AHSP PUPR", "TAMBAHAN"),
        ("wi_pasang_partisi_aluminium", "WI.PASANG.", "Pasang Partisi Aluminium", "unit", "AHSP PUPR", "TAMBAHAN"),
        ("wi_pasang_rambu", "WI.PASANG.", "Pasang Rambu", "unit", "AHSP PUPR", "TAMBAHAN"),
        ("wi_pasang_septic_tank", "WI.PASANG.", "Pasang Septic Tank", "unit", "AHSP PUPR", "TAMBAHAN"),
        ("wi_pasang_wastafel", "WI.PASANG.", "Pasang Wastafel", "unit", "AHSP PUPR", "TAMBAHAN"),
        ("wi_pasang_water_heater", "WI.PASANG.", "Pasang Water Heater", "unit", "AHSP PUPR", "TAMBAHAN"),
        ("wi_pc_girder_erection", "WI.PC.GIRD", "Pc Girder Erection", "unit", "AHSP PUPR", "TAMBAHAN"),
        ("wi_perbaikan_atap_bocor", "WI.PERBAIK", "Perbaikan Atap Bocor", "unit", "AHSP PUPR", "TAMBAHAN"),
        ("wi_perbaikan_beton_retak", "WI.PERBAIK", "Perbaikan Beton Retak", "unit", "AHSP PUPR", "TAMBAHAN"),
        ("wi_perbaikan_instalasi_listrik", "WI.PERBAIK", "Perbaikan Instalasi Listrik", "unit", "AHSP PUPR", "TAMBAHAN"),
        ("wi_perbaikan_plafon", "WI.PERBAIK", "Perbaikan Plafon", "unit", "AHSP PUPR", "TAMBAHAN"),
        ("wi_pintu_panel", "WI.PINTU.P", "Pintu Panel", "unit", "AHSP PUPR", "TAMBAHAN"),
        ("wi_pipa_air_bersih_1_2", "WI.PIPA.AI", "Pipa Air Bersih 1 2", "unit", "AHSP PUPR", "TAMBAHAN"),
        ("wi_pipa_air_kotor_4", "WI.PIPA.AI", "Pipa Air Kotor 4", "unit", "AHSP PUPR", "TAMBAHAN"),
        ("wi_pipa_drainase", "WI.PIPA.DR", "Pipa Drainase", "unit", "AHSP PUPR", "TAMBAHAN"),
        ("wi_plafon_gypsum", "WI.PLAFON.", "Plafon Gypsum", "unit", "AHSP PUPR", "TAMBAHAN"),
        ("wi_plafon_tripleks", "WI.PLAFON.", "Plafon Tripleks", "unit", "AHSP PUPR", "TAMBAHAN"),
        ("wi_plesteran", "WI.PLESTER", "Plesteran", "unit", "AHSP PUPR", "TAMBAHAN"),
        ("wi_pondasi_batu", "WI.PONDASI", "Pondasi Batu", "unit", "AHSP PUPR", "TAMBAHAN"),
        ("wi_saluran_drainase", "WI.SALURAN", "Saluran Drainase", "unit", "AHSP PUPR", "TAMBAHAN"),
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

    logger.info("Auto-generated Relasi SNI: %d item pekerjaan dimuat", len(validated_domain_models))
