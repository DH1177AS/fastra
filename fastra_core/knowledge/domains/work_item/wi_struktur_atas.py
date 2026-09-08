# fastra_core\knowledge\domains\work_item\wi_struktur_atas.py

from __future__ import annotations

import logging
from enum import Enum
from typing import Any, List, Dict, Tuple, Set

from pydantic import BaseModel, ConfigDict, Field, field_validator

logger = logging.getLogger("fastra.knowledge.work_item.struktur_atas")


class WorkItemUnit(str, Enum):
    KG = "kg"
    BUAH = "buah"
    MTR_RUNNING = "m'"
    MTR_CUBIC = "m³"
    MTR_SQUARE = "m²"
    TITIK = "titik"
    SET = "set"
    UNIT = "unit"


class WorkItemSpecification(str, Enum):
    SNI_2847 = "SNI 2847"
    AHSP_PUPR = "AHSP PUPR"


class WorkItemCategory(str, Enum):
    STRUKTUR_ATAS = "STRUKTUR_ATAS"


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


def load_wi_struktur_atas(kg: Any) -> None:
    if kg is None:
        raise ValueError("KNOWLEDGE_GRAPH_INSTANCE_CANNOT_BE_NULL")

    if not hasattr(kg, "add_work_item") or not hasattr(kg, "remove_work_item"):
        raise AttributeError("KNOWLEDGE_GRAPH_MUST_HAVE_ADD_AND_REMOVE_WORK_ITEM_METHODS")

    from fastra_core.knowledge.nodes import WorkItemNode

    raw_items: List[Tuple[str, str, str, str, str, str]] = [
        ("wi_sloof_rebar_fab", "STR.001", "Fabrikasi Tulangan Besi Pokok Ulir D16 untuk Sloof Beton", "kg", "SNI 2847", "STRUKTUR_ATAS"),
        ("wi_sloof_sengkang", "STR.002", "Fabrikasi Tulangan Sengkang Besi Polos ø8 untuk Sloof", "kg", "SNI 2847", "STRUKTUR_ATAS"),
        ("wi_sloof_rebar_assembly", "STR.003", "Perakitan Tulangan Sloof Besi di Atas Pondasi", "kg", "SNI 2847", "STRUKTUR_ATAS"),
        ("wi_sloof_spacer", "STR.004", "Pemasangan Tahu Beton / Spacer Pengatur Selimut Beton Sloof", "buah", "AHSP PUPR", "STRUKTUR_ATAS"),
        ("wi_sloof_bekisting", "STR.005", "Pemasangan Bekisting Papan Kayu untuk Sloof 20x30 cm", "m'", "AHSP PUPR", "STRUKTUR_ATAS"),
        ("wi_sloof_cor", "STR.006", "Pengecoran Beton Sloof Mutu K-250 Ready Mix", "m³", "SNI 2847", "STRUKTUR_ATAS"),
        ("wi_sloof_bongkar_bekisting", "STR.007", "Pembongkaran Bekisting Kayu Sloof Setelah 24 Jam", "m'", "AHSP PUPR", "STRUKTUR_ATAS"),
        ("wi_sloof_curing", "STR.008", "Perawatan Beton Sloof Menggunakan Siraman Air (Curing)", "m'", "SNI 2847", "STRUKTUR_ATAS"),
        ("wi_kolom_lt1_rebar_fab", "STR.009", "Fabrikasi Tulangan Kolom Utama Struktur Lantai 1 (Besi D19)", "kg", "SNI 2847", "STRUKTUR_ATAS"),
        ("wi_kolom_lt1_sengkang", "STR.010", "Perakitan Sengkang Kolom Utama dengan Jarak Sesuai Gambar", "kg", "SNI 2847", "STRUKTUR_ATAS"),
        ("wi_kolom_stek_sambung", "STR.011", "Penyambungan Besi Stek Kolom Lantai Dasar ke Sloof (Overlapping)", "titik", "SNI 2847", "STRUKTUR_ATAS"),
        ("wi_kolom_bekisting", "STR.012", "Pemasangan Bekisting Kolom Utama Bahan Plywood Tebal 15mm", "m²", "AHSP PUPR", "STRUKTUR_ATAS"),
        ("wi_kolom_kaso_pengaku", "STR.013", "Pemasangan Rangka Kayu Kaso Pengaku Bekisting Kolom", "m'", "AHSP PUPR", "STRUKTUR_ATAS"),
        ("wi_kolom_scaffolding", "STR.014", "Pemasangan Pipa Scaffolding Steel Penyangga Tegak Kolom", "set", "AHSP PUPR", "STRUKTUR_ATAS"),
        ("wi_kolom_cor_lt1", "STR.015", "Pengecoran Beton Kolom Utama Lantai 1 Mutu K-300", "m³", "SNI 2847", "STRUKTUR_ATAS"),
        ("wi_kolom_bongkar_bekisting", "STR.016", "Pembongkaran Bekisting Kolom Utama Setelah Beton Mengeras", "m²", "AHSP PUPR", "STRUKTUR_ATAS"),
        ("wi_kolom_curing_karung", "STR.017", "Pemasangan Lembaran Karung Goni Basah Keliling Kolom Utama", "m'", "SNI 2847", "STRUKTUR_ATAS"),
        ("wi_scaffolding_balok_lt2", "STR.018", "Pemasangan Perancah (Scaffolding) Besi Penuh untuk Balok Lantai 2", "m³", "AHSP PUPR", "STRUKTUR_ATAS"),
        ("wi_uhead_jack", "STR.019", "Pemasangan Struktur U-Head Jack & Jack Base Scaffolding", "set", "AHSP PUPR", "STRUKTUR_ATAS"),
        ("wi_suri_suri", "STR.020", "Pemasangan Balok Kayu Suri-Suri di Atas U-Head Scaffolding", "m'", "AHSP PUPR", "STRUKTUR_ATAS"),
        ("wi_bekisting_plat_lt2", "STR.021", "Pemasangan Bekisting Dasar Piringan Plat Lantai 2", "m²", "AHSP PUPR", "STRUKTUR_ATAS"),
        ("wi_bekisting_balok_lt2", "STR.022", "Pemasangan Bekisting Dinding Samping Balok Struktur Lantai 2", "m²", "AHSP PUPR", "STRUKTUR_ATAS"),
        ("wi_balok_lt2_rebar", "STR.023", "Fabrikasi Tulangan Besi Utama Balok Gantung Lantai 2", "kg", "SNI 2847", "STRUKTUR_ATAS"),
        ("wi_plat_lt2_wiremesh", "STR.024", "Perakitan Anyaman Besi Plat Lantai 2 Model 2 Lapis (D10)", "kg", "SNI 2847", "STRUKTUR_ATAS"),
        ("wi_plat_lt2_paku", "STR.025", "Pemasangan Paku Pengunci & Kawat Bendrat Anyaman Plat Lantai", "m²", "AHSP PUPR", "STRUKTUR_ATAS"),
        ("wi_sparing_kabel_lt2", "STR.026", "Penanaman Pipa Sparing Kabel Listrik Tembus Plat Lantai 2", "titik", "AHSP PUPR", "STRUKTUR_ATAS"),
        ("wi_sparing_airkotor_lt2", "STR.027", "Penanaman Pipa Sparing Air Kotor Kamar Mandi Tembus Plat Lantai", "titik", "AHSP PUPR", "STRUKTUR_ATAS"),
        ("wi_bersih_bekisting", "STR.028", "Pekerjaan Pembersihan Sampah Serbuk Kayu di Dalam Bekisting Balok", "m²", "AHSP PUPR", "STRUKTUR_ATAS"),
        ("wi_cor_massal_lt2", "STR.029", "Pengecoran Massal Balok & Plat Lantai 2 Paku Concrete Pump Truck", "m³", "SNI 2847", "STRUKTUR_ATAS"),
        ("wi_ratakan_cor_plat", "STR.030", "Perataan Permukaan Cor Beton Plat Lantai Paku Jidar Aluminium", "m²", "AHSP PUPR", "STRUKTUR_ATAS"),
        ("wi_curing_plat_lt2", "STR.031", "Perawatan Beton Plat Lantai 2 dengan Metode Penggenangan Air", "m²", "SNI 2847", "STRUKTUR_ATAS"),
        ("wi_bongkar_scaffolding_lt2", "STR.032", "Pembongkaran Perancah Scaffolding Balok Setelah Berusia 21 Hari", "m³", "AHSP PUPR", "STRUKTUR_ATAS"),
        ("wi_kolom_lt2_rebar", "STR.033", "Fabrikasi Besi Tulangan Kolom Utama Struktur Lantai 2", "kg", "SNI 2847", "STRUKTUR_ATAS"),
        ("wi_kolom_lt2_cor", "STR.034", "Pemasangan Bekisting & Pengecoran Kolom Utama Lantai 2 K-300", "m³", "SNI 2847", "STRUKTUR_ATAS"),
        ("wi_scaffolding_ringbalk", "STR.035", "Pemasangan Scaffolding Penyangga Balok Atap / Ring Balk", "m³", "AHSP PUPR", "STRUKTUR_ATAS"),
        ("wi_ringbalk_rebar", "STR.036", "Fabrikasi Besi & Pemasangan Bekisting Balok Atap (Ring Balk)", "kg", "SNI 2847", "STRUKTUR_ATAS"),
        ("wi_ringbalk_cor", "STR.037", "Pengecoran Beton Balok Atap (Ring Balk) Mutu K-225", "m³", "SNI 2847", "STRUKTUR_ATAS"),
        ("wi_dak_rebar", "STR.038", "Fabrikasi Besi Tulangan untuk Plat Dak Beton Atap Terbuka", "kg", "SNI 2847", "STRUKTUR_ATAS"),
        ("wi_roofdrain", "STR.039", "Pemasangan Pipa Drainase Air Hujan (Roof Drain) Tembus Dak", "titik", "AHSP PUPR", "STRUKTUR_ATAS"),
        ("wi_dak_cor", "STR.040", "Pengecoran Plat Dak Beton Atap Mutu K-250 Sistem Waterproof Admixture", "m³", "SNI 2847", "STRUKTUR_ATAS"),
        ("wi_tangga_bekisting", "STR.041", "Fabrikasi Besi & Bekisting Cetakan Tangga Beton Lantai 1 ke 2", "m²", "AHSP PUPR", "STRUKTUR_ATAS"),
        ("wi_tangga_rebar", "STR.042", "Perakitan Besi Tulangan Trap Anak Tangga Beton", "kg", "SNI 2847", "STRUKTUR_ATAS"),
        ("wi_tangga_cor", "STR.043", "Pengecoran Beton Tangga Bersamaan dengan Plat Lantai 2", "m³", "SNI 2847", "STRUKTUR_ATAS"),
        ("wi_kolom_praktis_rebar", "STR.044", "Fabrikasi Besi Tulangan Kolom Praktis 10x10 cm untuk Dinding", "kg", "SNI 2847", "STRUKTUR_ATAS"),
        ("wi_balok_lintel_rebar", "STR.045", "Perakitan Besi Balok Lintel / Balok Pengikat Kusen", "kg", "SNI 2847", "STRUKTUR_ATAS"),
        ("wi_kolom_praktis_cor", "STR.046", "Pengecoran Manual Kolom Praktis Campuran Site-Mix 1:2:3", "m³", "AHSP PUPR", "STRUKTUR_ATAS"),
        ("wi_angkur_dinding", "STR.047", "Pemasangan Besi Angkur Pengikat Dinding Bata ke Kolom Utama", "titik", "AHSP PUPR", "STRUKTUR_ATAS"),
        ("wi_konsol_kanopi", "STR.048", "Pekerjaan Dudukan Beton Konsol Kanopi Depan Rumah", "unit", "SNI 2847", "STRUKTUR_ATAS"),
        ("wi_meja_dapur_cor", "STR.049", "Pekerjaan Beton Meja Dapur (Kitchen Table) Cor di Tempat", "unit", "SNI 2847", "STRUKTUR_ATAS"),
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

    logger.info("Struktur Atas: %d item pekerjaan dimuat", len(validated_domain_models))
