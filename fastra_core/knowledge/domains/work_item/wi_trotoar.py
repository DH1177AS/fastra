# fastra_core\knowledge\domains\work_item\wi_trotoar.py

from __future__ import annotations

import logging
from enum import Enum
from typing import Any, List, Dict, Tuple, Set

from pydantic import BaseModel, ConfigDict, Field, field_validator

logger = logging.getLogger("fastra.knowledge.work_item.trotoar")


class WorkItemUnit(str, Enum):
    MTR_RUNNING = "m'"
    MTR_CUBIC = "m³"
    MTR_SQUARE = "m²"
    BUAH = "buah"
    UNIT = "unit"


class WorkItemSpecification(str, Enum):
    SPESIFIKASI_TROTOAR = "Spesifikasi Trotoar"


class WorkItemCategory(str, Enum):
    TROTOAR = "TROTOAR"


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


def load_wi_trotoar(kg: Any) -> None:
    if kg is None:
        raise ValueError("KNOWLEDGE_GRAPH_INSTANCE_CANNOT_BE_NULL")

    if not hasattr(kg, "add_work_item") or not hasattr(kg, "remove_work_item"):
        raise AttributeError("KNOWLEDGE_GRAPH_MUST_HAVE_ADD_AND_REMOVE_WORK_ITEM_METHODS")

    from fastra_core.knowledge.nodes import WorkItemNode

    raw_items: List[Tuple[str, str, str, str, str, str]] = [
        ("wi_ukur_lebar_trotoar", "TRO.001", "Pengukuran Jalur Lebar Trotoar Sesuai Gambar Rencana Ruang Jalan", "m'", "Spesifikasi Trotoar", "TROTOAR"),
        ("wi_bobokan_aspal_trotoar", "TRO.002", "Pembobokan Aspal/Tanah Samping Jalan untuk Kedudukan Struktur Trotoar", "m'", "Spesifikasi Trotoar", "TROTOAR"),
        ("wi_kanstin_jepit", "TRO.003", "Pemasangan Batu Kanstin Jepit Beton Pracetak Batas Trotoar dengan Jalan Raya", "m'", "Spesifikasi Trotoar", "TROTOAR"),
        ("wi_mortar_sela_kanstin", "TRO.004", "Pengecoran Mortar Semen Pengunci Sela Antar Kanstin Trotoar", "m'", "Spesifikasi Trotoar", "TROTOAR"),
        ("wi_kanstin_stype", "TRO.005", "Pemasangan Batu Kanstin Jenis Berlubang untuk Saluran Tangkapan Air (Kanstin S-Type)", "m'", "Spesifikasi Trotoar", "TROTOAR"),
        ("wi_urugan_trotoar", "TRO.006", "Urugan Tanah Merah Lapisan Bawah Peninggi Level Trotoar", "m³", "Spesifikasi Trotoar", "TROTOAR"),
        ("wi_stamper_trotoar", "TRO.007", "Pemadatan Tanah Timbunan Trotoar Menggunakan Mesin Stamper Kodok", "m²", "Spesifikasi Trotoar", "TROTOAR"),
        ("wi_pasir_alas_trotoar", "TRO.008", "Penghamparan Lapisan Pasir Alas Ubin Trotoar Setebal 5-7 cm", "m²", "Spesifikasi Trotoar", "TROTOAR"),
        ("wi_wiremesh_trotoar", "TRO.009", "Pengecoran Lapisan Lantai Kerja Beton Bertulang Wiremesh M5 Tipis", "m²", "Spesifikasi Trotoar", "TROTOAR"),
        ("wi_paving_trotoar", "TRO.010", "Pemasangan Ubin Trotoar Jenis Paving Block / Interlocking Brick Motif", "m²", "Spesifikasi Trotoar", "TROTOAR"),
        ("wi_guiding_block_line", "TRO.011", "Pemasangan Ubin Jalur Pemandu Disabilitas Tunanetra Motif Garis (Guiding Block Line-Type)", "m'", "Spesifikasi Trotoar", "TROTOAR"),
        ("wi_guiding_block_dot", "TRO.012", "Pemasangan Ubin Jalur Pemandu Disabilitas Tunanetra Motif Titik Stop (Guiding Block Dot-Type)", "buah", "Spesifikasi Trotoar", "TROTOAR"),
        ("wi_nat_pasir_trotoar", "TRO.013", "Pekerjaan Pengisian Sela Nat Paving Trotoar Pasir Silika Halus Cor", "m²", "Spesifikasi Trotoar", "TROTOAR"),
        ("wi_batu_alam_trotoar", "TRO.014", "Pemasangan Ubin Trotoar Jenis Bahan Batu Alam Andesit Bakar Anti Licin", "m²", "Spesifikasi Trotoar", "TROTOAR"),
        ("wi_potong_presisi_paving", "TRO.015", "Pekerjaan Pemotongan Presisi Ubin Paving di Titik Sudut/Kanstin Lekuk", "m'", "Spesifikasi Trotoar", "TROTOAR"),
        ("wi_wheelchair_ramp", "TRO.016", "Pembuatan Konstruksi Tanjakan Landai Trotoar untuk Kursi Roda Disabilitas", "unit", "Spesifikasi Trotoar", "TROTOAR"),
        ("wi_bollard", "TRO.017", "Pemasangan Pagar Besi Pengaman Trotoar Pembatas Jalan (Pedestrian Bollard)", "buah", "Spesifikasi Trotoar", "TROTOAR"),
        ("wi_concrete_ball_bollard", "TRO.018", "Pemasangan Pilar Pembatas Batu Bulat Estetik (Concrete Ball Bollard)", "buah", "Spesifikasi Trotoar", "TROTOAR"),
        ("wi_tree_pit", "TRO.019", "Pembuatan Lubang Tanam Pohon Peneduh Trotoar (Tree Pit Concrete Ring)", "unit", "Spesifikasi Trotoar", "TROTOAR"),
        ("wi_tree_grate", "TRO.020", "Pemasangan Grill Besi Penutup Lubang Pohon Trotoar (Tree Grate Iron)", "unit", "Spesifikasi Trotoar", "TROTOAR"),
        ("wi_kursi_taman_trotoar", "TRO.021", "Pemasangan Kursi Taman Besi Tempa Permanen di Sepanjang Jalur Pedestrian", "unit", "Spesifikasi Trotoar", "TROTOAR"),
        ("wi_tempat_sampah_trotoar", "TRO.022", "Pemasangan Tempat Sampah Pilah Organik/Anorganik Bahan Stainless Tanam", "unit", "Spesifikasi Trotoar", "TROTOAR"),
        ("wi_tiang_lampu_pedestrian", "TRO.023", "Pemasangan Tiang Lampu Pedestrian Klasik Tinggi 3 Meter", "unit", "Spesifikasi Trotoar", "TROTOAR"),
        ("wi_kabel_bawah_trotoar", "TRO.024", "Penarikan Jaringan Kabel Listrik Tiang Lampu Bawah Tanah (Underground Cable)", "m'", "Spesifikasi Trotoar", "TROTOAR"),
        ("wi_konduit_hdpe_trotoar", "TRO.025", "Pemasangan Pipa Konduit Pelindung Kabel Bawah Trotoar (PVC High Density)", "m'", "Spesifikasi Trotoar", "TROTOAR"),
        ("wi_handhole_utility", "TRO.026", "Pembuatan Bak Kontrol Utilitas Kabel Bawah Tanah Trotoar (Handhole Utility)", "unit", "Spesifikasi Trotoar", "TROTOAR"),
        ("wi_peta_informasi_trotoar", "TRO.027", "Pemasangan Papan Informasi Jalur Wisata Pedestrian Besi", "unit", "Spesifikasi Trotoar", "TROTOAR"),
        ("wi_halte_bus", "TRO.028", "Pemasangan Halte Bus Penumpang Terintegrasi di Jalur Trotoar", "unit", "Spesifikasi Trotoar", "TROTOAR"),
        ("wi_bersih_trotoar", "TRO.029", "Pekerjaan Penyiraman dan Pembersihan Total Noda Semen Permukaan Ubin Trotoar", "m²", "Spesifikasi Trotoar", "TROTOAR"),
        ("wi_uji_bollard", "TRO.030", "Pengujian Kekuatan Dudukan Bollard Pagar Terhadap Uji Tekan Benturan", "unit", "Spesifikasi Trotoar", "TROTOAR"),
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

    logger.info("Trotoar: %d item pekerjaan dimuat", len(validated_domain_models))
