# fastra_core\knowledge\domains\work_item\wi_kolam_renang.py

from __future__ import annotations

import logging
from enum import Enum
from typing import Any, List, Dict, Tuple, Set

from pydantic import BaseModel, ConfigDict, Field, field_validator

logger = logging.getLogger("fastra.knowledge.work_item.kolam_renang")


class WorkItemUnit(str, Enum):
    MTR_CUBIC = "m³"
    MTR_SQUARE = "m²"
    KG = "kg"
    BUAH = "buah"
    TITIK = "titik"
    MTR_RUNNING = "m'"
    UNIT = "unit"


class WorkItemSpecification(str, Enum):
    AHSP_PUPR = "AHSP PUPR"
    SNI_2847 = "SNI 2847"


class WorkItemCategory(str, Enum):
    KOLAM_RENANG = "KOLAM_RENANG"


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


def load_wi_kolam_renang(kg: Any) -> None:
    if kg is None:
        raise ValueError("KNOWLEDGE_GRAPH_INSTANCE_CANNOT_BE_NULL")

    if not hasattr(kg, "add_work_item") or not hasattr(kg, "remove_work_item"):
        raise AttributeError("KNOWLEDGE_GRAPH_MUST_HAVE_ADD_AND_REMOVE_WORK_ITEM_METHODS")

    from fastra_core.knowledge.nodes import WorkItemNode

    raw_items: List[Tuple[str, str, str, str, str, str]] = [
        ("wi_galian_kolam_renang", "KOL.001", "Pekerjaan Galian Tanah Kolam Renang Skala Besar (Excavator)", "m³", "AHSP PUPR", "KOLAM_RENANG"),
        ("wi_shoring_kolam", "KOL.002", "Pemasangan Dinding Penahan Tanah Darurat (Wooden Shoring) Galian Kolam", "m²", "AHSP PUPR", "KOLAM_RENANG"),
        ("wi_lantai_kerja_b0", "KOL.003", "Pembuatan Lantai Kerja Beton Kurus (B0) Dasar Kolam", "m²", "AHSP PUPR", "KOLAM_RENANG"),
        ("wi_batako_keliling", "KOL.004", "Pemasangan Batako Keliling Badan Kolam (Bekisting Luar Permanen)", "m²", "AHSP PUPR", "KOLAM_RENANG"),
        ("wi_pembesian_layer_bawah", "KOL.005", "Pembesian Kolam Renang - Layer Bawah (D10/D12)", "kg", "SNI 2847", "KOLAM_RENANG"),
        ("wi_cakar_ayam_kolam", "KOL.006", "Pemasangan Besi Cakar Ayam Penyangga Struktur Lantai Kolam", "buah", "SNI 2847", "KOLAM_RENANG"),
        ("wi_pembesian_layer_atas", "KOL.007", "Pembesian Kolam Renang - Layer Atas (Struktur Ganda Tebal 20cm)", "kg", "SNI 2847", "KOLAM_RENANG"),
        ("wi_overflow_gutter", "KOL.011", "Pembuatan Jalur Selokan Keliling Kolam (Overflow Gutter) Beton", "m'", "AHSP PUPR", "KOLAM_RENANG"),
        ("wi_balancing_tank", "KOL.012", "Pembuatan Kamar Penampungan Air Limpahan (Balancing Tank) Beton", "unit", "AHSP PUPR", "KOLAM_RENANG"),
        ("wi_pump_room", "KOL.013", "Pembuatan Ruang Mesin Kolam (Pump Room) Bawah Tanah Bertangga Besi", "unit", "AHSP PUPR", "KOLAM_RENANG"),
        ("wi_waterstop_pvc", "KOL.014", "Pemasangan Karet Penyumbat Air (Waterstop PVC Strip) Sambungan Cor", "m'", "AHSP PUPR", "KOLAM_RENANG"),
        ("wi_cor_monolitik", "KOL.015", "Pengecoran Monolitik Beton Kolam Renang (K-350/K-400 Waterproof)", "m³", "SNI 2847", "KOLAM_RENANG"),
        ("wi_shotcrete", "KOL.016", "Pekerjaan Semprot Beton Tekan (Shotcrete) Kolam Lengkung (Alternatif)", "m²", "AHSP PUPR", "KOLAM_RENANG"),
        ("wi_bongkar_bekisting_kolam", "KOL.017", "Pekerjaan Pembongkaran Bekisting Dalam Kolam (Setelah 14-21 Hari)", "m²", "AHSP PUPR", "KOLAM_RENANG"),
        ("wi_plester_siku_kolam", "KOL.018", "Pekerjaan Plesteran Akurasi Siku Dinding Kolam (Corner Rounded)", "m²", "AHSP PUPR", "KOLAM_RENANG"),
        ("wi_waterproofing_pu", "KOL.019", "Pekerjaan Waterproofing Kolam Renang Polyurethane (PU) Base 3 Lapis", "m²", "AHSP PUPR", "KOLAM_RENANG"),
        ("wi_hydrotest_pool", "KOL.020", "Pengujian Rendam Air (Hydrotest Pool) 14 Hari Penuh Anti Bocor", "unit", "AHSP PUPR", "KOLAM_RENANG"),
        ("wi_mosaic_tile", "KOL.021", "Pemasangan Ubin Mozaik Kolam Renang (Mosaic Tile 5x5/10x10) Biru Muda", "m²", "AHSP PUPR", "KOLAM_RENANG"),
        ("wi_pool_coping", "KOL.022", "Pemasangan Batu Alam Bibir Kolam (Pool Coping) Andesit/Kerobokan", "m'", "AHSP PUPR", "KOLAM_RENANG"),
        ("wi_epoxy_grout_pool", "KOL.023", "Pekerjaan Pengisian Nat Mozaik Bahan Epoksi (Epoxy Grout) Anti Lumut", "m²", "AHSP PUPR", "KOLAM_RENANG"),
        ("wi_tangga_stainless_pool", "KOL.024", "Pemasangan Tangga Kolam Stainless Steel SUS 316 Anti Karat", "unit", "AHSP PUPR", "KOLAM_RENANG"),
        ("wi_underwater_light_niche", "KOL.025", "Pemasangan Rumah Lampu Kolam Tanam Dinding (Underwater Light Niche)", "unit", "AHSP PUPR", "KOLAM_RENANG"),
        ("wi_led_underwater", "KOL.026", "Pemasangan Lampu LED Kolam Renang LED Underwater (12V) RGB", "unit", "AHSP PUPR", "KOLAM_RENANG"),
        ("wi_transformer_12v", "KOL.027", "Pemasangan Trafo Penurun Tegangan Listrik (Step-down Transformer IP65)", "unit", "AHSP PUPR", "KOLAM_RENANG"),
        ("wi_centrifugal_pump", "KOL.028", "Pemasangan Mesin Pompa Kolam Renang Khusus (Centrifugal Pool Pump)", "unit", "AHSP PUPR", "KOLAM_RENANG"),
        ("wi_sand_filter", "KOL.029", "Pemasangan Tabung Filter Pasir Besar (Sand Filter) Fiberglass", "unit", "AHSP PUPR", "KOLAM_RENANG"),
        ("wi_media_pasir_filter", "KOL.030", "Pengisian Media Pasir Silika / Glass Media ke Tabung Filter", "unit", "AHSP PUPR", "KOLAM_RENANG"),
        ("wi_multiport_valve", "KOL.031", "Pemasangan Katup Kontrol Multiport (Multiport Selector Valve) Filter", "unit", "AHSP PUPR", "KOLAM_RENANG"),
        ("wi_salt_chlorinator", "KOL.032", "Instalasi Sistem Klorinator Garam (Salt Chlorinator Generator) Air Asin", "unit", "AHSP PUPR", "KOLAM_RENANG"),
        ("wi_pool_heat_pump", "KOL.033", "Pemasangan Alat Pemanas Air Kolam (Pool Heat Pump Generator) Hangat", "unit", "AHSP PUPR", "KOLAM_RENANG"),
        ("wi_gutter_grating", "KOL.034", "Pemasangan Kisi-Kisi Tutup Parit (Gutter Overflow Grating) Plastik/ABS", "m'", "AHSP PUPR", "KOLAM_RENANG"),
        ("wi_chemical_shock", "KOL.035", "Pekerjaan Pengisian Air Pertama & Penjernihan Kimiawi (Chemical Shock)", "unit", "AHSP PUPR", "KOLAM_RENANG"),
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

    logger.info("Kolam Renang: %d item pekerjaan dimuat", len(validated_domain_models))
