# fastra_core\knowledge\domains\work_item\wi_interior.py

from __future__ import annotations

import logging
from enum import Enum
from typing import Any, List, Dict, Tuple, Set

from pydantic import BaseModel, ConfigDict, Field, field_validator

logger = logging.getLogger("fastra.knowledge.work_item.interior")


class WorkItemUnit(str, Enum):
    MTR_SQUARE = "m²"
    MTR_RUNNING = "m'"
    SET = "set"
    UNIT = "unit"


class WorkItemSpecification(str, Enum):
    AHSP_PUPR = "AHSP PUPR"


class WorkItemCategory(str, Enum):
    INTERIOR = "INTERIOR"


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


def load_wi_interior(kg: Any) -> None:
    if kg is None:
        raise ValueError("KNOWLEDGE_GRAPH_INSTANCE_CANNOT_BE_NULL")

    if not hasattr(kg, "add_work_item") or not hasattr(kg, "remove_work_item"):
        raise AttributeError("KNOWLEDGE_GRAPH_MUST_HAVE_ADD_AND_REMOVE_WORK_ITEM_METHODS")

    from fastra_core.knowledge.nodes import WorkItemNode

    raw_items: List[Tuple[str, str, str, str, str, str]] = [
        ("wi_site_marking", "INT.001", "Pekerjaan Site Marking Interior: Garis Pola Furnitur Skala 1:1 di Lantai", "m²", "AHSP PUPR", "INTERIOR"),
        ("wi_partisi_double_stud", "INT.002", "Pemasangan Rangka Dinding Partisi Double Stud (Insulasi Suara Maksimal)", "m²", "AHSP PUPR", "INTERIOR"),
        ("wi_mdf_backing", "INT.003", "Pemasangan Papan MDF / Multiplek Backing Dinding", "m²", "AHSP PUPR", "INTERIOR"),
        ("wi_hpl_laminasi", "INT.004", "Pemasangan HPL (High Pressure Laminate) Motif Kayu/Marmer", "m²", "AHSP PUPR", "INTERIOR"),
        ("wi_edging_pvc", "INT.005", "Pemasangan Edging PVC Otomatis Pinggiran Furnitur", "m'", "AHSP PUPR", "INTERIOR"),
        ("wi_edging_akrilik", "INT.006", "Pemasangan Edging Akrilik / 3D Edging Premium", "m'", "AHSP PUPR", "INTERIOR"),
        ("wi_cat_duco_plamir", "INT.007", "Finishing Cat Duco - Tahap Plamir Kayu", "m²", "AHSP PUPR", "INTERIOR"),
        ("wi_cat_duco_dasar", "INT.008", "Finishing Cat Duco - Tahap Cat Dasar (Surfacer)", "m²", "AHSP PUPR", "INTERIOR"),
        ("wi_cat_duco_warna", "INT.009", "Finishing Cat Duco - Tahap Warna Utama (Matt/Glossy/Satin)", "m²", "AHSP PUPR", "INTERIOR"),
        ("wi_cat_duco_topcoat", "INT.010", "Finishing Cat Duco - Tahap Clear Coat / Top Coat Pelindung", "m²", "AHSP PUPR", "INTERIOR"),
        ("wi_melamic_politur", "INT.011", "Finishing Melamic / Politur Semprot Transparan Serat Kayu", "m²", "AHSP PUPR", "INTERIOR"),
        ("wi_engsel_softclose", "INT.012", "Pemasangan Engsel Soft-Close / Slow-Motion Pintu Lemari", "set", "AHSP PUPR", "INTERIOR"),
        ("wi_rel_laci_undermount", "INT.013", "Pemasangan Rel Laci Double Track Under-Mount (Beban Berat)", "set", "AHSP PUPR", "INTERIOR"),
        ("wi_push_to_open", "INT.014", "Pemasangan Rel Laci Sistem Push-to-Open (Tanpa Handle)", "set", "AHSP PUPR", "INTERIOR"),
        ("wi_over_x_sliding", "INT.015", "Pemasangan Sistem Pintu Geser Lemari Over-X (Sejajar Rapi)", "set", "AHSP PUPR", "INTERIOR"),
        ("wi_wardrobe_lift", "INT.016", "Pemasangan Gantungan Baju Sistem Tarik (Pull-Down Wardrobe Lift)", "unit", "AHSP PUPR", "INTERIOR"),
        ("wi_lazy_susan", "INT.017", "Pemasangan Rak Dapur Sudut Putar (Lazy Susan / Magic Corner)", "unit", "AHSP PUPR", "INTERIOR"),
        ("wi_rak_piring_tarik", "INT.018", "Pemasangan Rak Piring Tarik Stainless Steel Dalam Kabinet Atas", "unit", "AHSP PUPR", "INTERIOR"),
        ("wi_led_strip_lemari", "INT.019", "Pemasangan Lampu LED Strip Sensor Buka Pintu Dalam Lemari", "unit", "AHSP PUPR", "INTERIOR"),
        ("wi_led_kolong_kabinet", "INT.020", "Pemasangan Lampu LED Indirect Kolong Kabinet Dapur", "m'", "AHSP PUPR", "INTERIOR"),
        ("wi_led_profile", "INT.021", "Pemasangan Profil Aluminium LED (LED Profile/Channel) Penanam Strip", "m'", "AHSP PUPR", "INTERIOR"),
        ("wi_popup_socket", "INT.022", "Pemasangan Stop Kontak Tanam Meja Sistem Putar (Rotatable Pop-Up Socket)", "unit", "AHSP PUPR", "INTERIOR"),
        ("wi_padded_headboard", "INT.023", "Pemasangan Kepala Ranjang Bungkus Kain (Padded Headboard)", "unit", "AHSP PUPR", "INTERIOR"),
        ("wi_cermin_berlian", "INT.024", "Pemasangan Kaca Cermin Bevel Berpola (Pola Berlian/Kotak Dinding)", "m²", "AHSP PUPR", "INTERIOR"),
        ("wi_wall_moulding", "INT.025", "Pemasangan Wall Moulding Klasik (Bahan Kayu/PVC) Gaya American Classic", "m'", "AHSP PUPR", "INTERIOR"),
        ("wi_wpc_kisi_interior", "INT.026", "Pemasangan Kisi-Kisi WPC (Wood Plastic Composite) Interior", "m²", "AHSP PUPR", "INTERIOR"),
        ("wi_fluted_akrilik", "INT.027", "Pemasangan Fluted Panel Akrilik Dinding Gelombang", "m²", "AHSP PUPR", "INTERIOR"),
        ("wi_top_table_kuarsa", "INT.028", "Pemasangan Top Table Kuarsa (Quartz Surface) Meja Dapur", "m'", "AHSP PUPR", "INTERIOR"),
        ("wi_top_table_marmer", "INT.029", "Pemasangan Top Table Marmer Alami + Coating Sealer", "m'", "AHSP PUPR", "INTERIOR"),
        ("wi_cowakan_sink", "INT.030", "Pekerjaan Cowakan Sink Joint (Top Table) - Potong Melingkar Presisi", "unit", "AHSP PUPR", "INTERIOR"),
        ("wi_siku_pinggul", "INT.031", "Pekerjaan Siku Pinggul / Bullnose Granit Penggerindaan Sudut Tumpul", "m'", "AHSP PUPR", "INTERIOR"),
        ("wi_kaca_backsplash", "INT.032", "Pemasangan Kaca Backsplash Dapur (Tempered Lacobel) Anti Minyak", "m²", "AHSP PUPR", "INTERIOR"),
        ("wi_subway_tile", "INT.033", "Pemasangan Keramik Motif Subway Tile Dapur + Semen Nat Kontras", "m²", "AHSP PUPR", "INTERIOR"),
        ("wi_vinyl_lantai_click", "INT.034", "Pemasangan Vinyl Lantai Sistem Click Tanpa Lem Motif Kayu", "m²", "AHSP PUPR", "INTERIOR"),
        ("wi_spc_lantai", "INT.035", "Pemasangan Lantai SPC (Stone Plastic Composite) 100% Tahan Air", "m²", "AHSP PUPR", "INTERIOR"),
        ("wi_karpet_tile_kantor", "INT.036", "Pemasangan Karpet Tile Kantor Berperekat Khusus", "m²", "AHSP PUPR", "INTERIOR"),
        ("wi_gorden_blackout", "INT.037", "Pemasangan Gorden Sistem Blackout 100% Penahan Cahaya", "m'", "AHSP PUPR", "INTERIOR"),
        ("wi_vitrase_gorden", "INT.038", "Pemasangan Vitrase Gorden (Kain Tipis Transparan Putih)", "m'", "AHSP PUPR", "INTERIOR"),
        ("wi_roller_blinds", "INT.039", "Pemasangan Jendela Gulung Roller Blinds / Zebra Blinds Rantai Tarik", "unit", "AHSP PUPR", "INTERIOR"),
        ("wi_handrail_custom", "INT.040", "Pemasangan Pegangan Tangan Tangga Kayu Custom (Meliuk Ikuti Tangga)", "m'", "AHSP PUPR", "INTERIOR"),
        ("wi_rotating_louvre", "INT.041", "Pemasangan Kisi-Kisi Penyekat Ruangan Pusing (Rotating Louvre Louver)", "m²", "AHSP PUPR", "INTERIOR"),
        ("wi_barrisol_ceiling", "INT.042", "Pemasangan Plafon Kain Kelambu Regang (Barrisol Ceiling) LED Massal", "m²", "AHSP PUPR", "INTERIOR"),
        ("wi_sound_diffuser", "INT.043", "Pemasangan Panel Akustik Penyerap Gema (Sound Diffuser) Ruang Karaoke", "m²", "AHSP PUPR", "INTERIOR"),
        ("wi_rfid_cabinet_lock", "INT.044", "Pemasangan Kunci Lemari Sistem Kartu (RFID Cabinet Lock) Elektronik", "unit", "AHSP PUPR", "INTERIOR"),
        ("wi_de_formaldehyde", "INT.045", "Pembersihan Uap Furnitur Baru (De-formaldehyde Treatment) Aman Hirup", "unit", "AHSP PUPR", "INTERIOR"),
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

    logger.info("Interior & Fit-Out: %d item pekerjaan dimuat", len(validated_domain_models))
