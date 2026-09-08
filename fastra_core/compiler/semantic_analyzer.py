# fastra_core\compiler\semantic_analyzer.py

from __future__ import annotations

import logging
import enum
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, ConfigDict, Field

from fastra_core.ccm.physical import Beam, Column, ColumnType, Door, Wall, Window
from fastra_core.ccm.spatial import Building, Room, Storey

logger = logging.getLogger(__name__)


class SemanticValidationCode(str, enum.Enum):

    SEM_001 = "SEM-001"  
    SEM_004 = "SEM-004"  
    SEM_005 = "SEM-005"  
    SEM_006 = "SEM-006"  
    SEM_007 = "SEM-007"  
    SEM_008 = "SEM-008"  
    SEM_009 = "SEM-009"  
    SEM_010 = "SEM-010"  
    SEM_011 = "SEM-011"  


class SemanticLogDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    error_code: str = Field(..., min_length=3, max_length=16)
    entity_uuid: str = Field(
        ...,
        min_length=5,
        max_length=64,
        pattern=r"^[a-f0-9\-]{36}|[A-Za-z0-9_]+$",
    )
    message: str = Field(..., min_length=5, max_length=512)


def _to_decimal(value: float | int | Decimal, field_name: str) -> Decimal:
   
    if isinstance(value, Decimal):
        return value
    if not isinstance(value, (int, float)):
        raise TypeError(f"Field '{field_name}' wajib bertipe numerik dasar (int/float/Decimal).")
    try:
        return Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError(
            f"Field '{field_name}' gagal dikonversi ke representasi Decimal imutabel."
        ) from exc


class SemanticAnalyzer:
   
    def __init__(self) -> None:
        self._errors: List[Dict[str, Any]] = []
        self._warnings: List[Dict[str, Any]] = []

    @property
    def errors(self) -> List[Dict[str, Any]]:
       
        return list(self._errors)

    @property
    def warnings(self) -> List[Dict[str, Any]]:
       
        return list(self._warnings)

    def analyze(
        self,
        entities: Dict[str, Any],
        adjacency: Optional[Dict[str, List[Tuple[str, str]]]] = None,
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        
        self._errors.clear()
        self._warnings.clear()

        adjacency_matrix = adjacency or {}

        for uid, ent in entities.items():
            try:
                self._analyze_entity(uid, ent, entities, adjacency_matrix)
            except Exception as exc:
                logger.exception("Gagal menganalisis entitas %s", uid)
                self._add_error(
                    SemanticValidationCode.SEM_001,
                    uid,
                    f"Kegagalan evaluasi semantik: {exc}",
                )

        return list(self._errors), list(self._warnings)

    def _analyze_entity(
        self,
        uid: str,
        ent: Any,
        entities: Dict[str, Any],
        adjacency: Dict[str, List[Tuple[str, str]]],
    ) -> None:
       
        if isinstance(ent, Wall):
            self._analyze_wall(uid, ent)
        elif isinstance(ent, Door):
            self._analyze_door(uid, ent, entities)
        elif isinstance(ent, Window):
            self._analyze_window(uid, ent, entities)
        elif isinstance(ent, Room):
            self._analyze_room(uid, ent)
        elif isinstance(ent, Beam):
            self._analyze_beam(uid, ent)
        elif isinstance(ent, Column):
            self._analyze_column(uid, ent, adjacency)
        elif isinstance(ent, Storey):
            self._analyze_storey(uid, ent, entities)

    def _analyze_wall(self, uid: str, wall: Wall) -> None:
       
        wall_height = _to_decimal(getattr(wall, "_height", 0.0), "wall.height")
        openings = getattr(wall, "_openings", []) or []
        for op in openings:
            op_height = _to_decimal(getattr(op, "_height", 0.0), "opening.height")
            if op_height > wall_height:
                self._add_error(
                    SemanticValidationCode.SEM_008,
                    uid,
                    f"Bukaan ({float(op_height)}m) lebih tinggi dari dinding induk ({float(wall_height)}m).",
                )

    def _analyze_door(self, uid: str, door: Door, entities: Dict[str, Any]) -> None:
        
        host_wall_id = getattr(door, "host_wall", None) or getattr(door, "_host_wall", None)
        if not host_wall_id:
            return

        host = entities.get(host_wall_id)
        if not isinstance(host, Wall):
            return

        host_height = _to_decimal(getattr(host, "_height", 0.0), "host_wall.height")
        door_height = _to_decimal(getattr(door, "_height", 0.0), "door.height")

        if door_height > host_height:
            self._add_error(
                SemanticValidationCode.SEM_008,
                uid,
                f"Pintu ({float(door_height)}m) melebihi tinggi dinding tumpuan ({float(host_height)}m).",
            )
       
        gross_area = _to_decimal(host.calculate_gross_area(), "host_wall.gross_area")
        wall_length = gross_area / host_height if host_height > 0 else Decimal("0")

        door_pos = _to_decimal(getattr(door, "_position_on_wall", 0.0), "door.position")
        door_width = _to_decimal(getattr(door, "_width", 0.0), "door.width")

        if (door_pos + door_width) > wall_length:
            self._add_error(
                SemanticValidationCode.SEM_009,
                uid,
                f"Posisi pintu melebihi batas panjang dinding ({float(wall_length)}m).",
            )
        elif door_pos < 0:
            self._add_error(
                SemanticValidationCode.SEM_009,
                uid,
                "Posisi pintu tidak boleh negatif.",
            )

    def _analyze_window(self, uid: str, window: Window, entities: Dict[str, Any]) -> None:
       
        host_wall_id = getattr(window, "host_wall", None) or getattr(window, "_host_wall", None)
        if not host_wall_id:
            return

        host = entities.get(host_wall_id)
        if not isinstance(host, Wall):
            return

        host_height = _to_decimal(getattr(host, "_height", 0.0), "host_wall.height")
        window_height = _to_decimal(getattr(window, "_height", 0.0), "window.height")
        sill_height = _to_decimal(getattr(window, "_sill_height", 0.0), "window.sill_height")

        if (sill_height + window_height) > host_height:
            self._add_error(
                SemanticValidationCode.SEM_010,
                uid,
                f"Ambang atas jendela ({float(sill_height + window_height)}m) melampaui puncak dinding ({float(host_height)}m).",
            )

    def _analyze_room(self, uid: str, room: Room) -> None:
       
        boundary_pts = getattr(room, "_boundary", [])
        if not boundary_pts:
            return
        start_pt, end_pt = boundary_pts[0], boundary_pts[-1]
        if float(start_pt.x) != float(end_pt.x) or float(start_pt.y) != float(end_pt.y):
            self._add_error(
                SemanticValidationCode.SEM_001,
                uid,
                "Garis keliling poligon ruangan tidak tertutup sempurna.",
            )

    def _analyze_beam(self, uid: str, beam: Beam) -> None:
      
        if not getattr(beam, "_start_connection", None):
            self._add_error(
                SemanticValidationCode.SEM_006,
                uid,
                "Balok kehilangan data referensi koneksi pangkal (start_connection).",
            )
        if not getattr(beam, "_end_connection", None):
            self._add_error(
                SemanticValidationCode.SEM_007,
                uid,
                "Balok kehilangan data referensi koneksi ujung (end_connection).",
            )

    def _analyze_column(
        self,
        uid: str,
        column: Column,
        adjacency: Dict[str, List[Tuple[str, str]]],
    ) -> None:
        
        if getattr(column, "_structural_type", None) != ColumnType.KOLOM_STRUKTUR:
            return

        edges = adjacency.get(uid, []) or []
       
        has_beam = any(rel in ("SUPPORTS", "INVERSE_SUPPORTS", "CONNECTED_TO", "INVERSE_CONNECTED_TO") for rel, _ in edges)
        if not has_beam:
            self._add_warning(
                SemanticValidationCode.SEM_004,
                uid,
                "Kolom struktur utama berdiri tanpa koneksi balok pengikat lateral.",
            )

        has_foundation = any(rel == "SUPPORTS" for rel, _ in edges)
        if not has_foundation:
            self._add_warning(
                SemanticValidationCode.SEM_005,
                uid,
                "Jalur pembebanan kolom terputus (tidak terikat pondasi).",
            )

    def _analyze_storey(self, uid: str, storey: Storey, entities: Dict[str, Any]) -> None:
      
        building_id = getattr(storey, "_building_id", None)
        if not building_id:
            return
        building = entities.get(building_id)
        if not isinstance(building, Building):
            return

        bld_height = _to_decimal(getattr(building, "_height", 0.0), "building.height")
        sty_elevation = _to_decimal(getattr(storey, "_elevation", 0.0), "storey.elevation")
        sty_height = _to_decimal(getattr(storey, "_height", 0.0), "storey.height")

        if (sty_elevation + sty_height) > bld_height:
            self._add_warning(
                SemanticValidationCode.SEM_011,
                uid,
                f"Elevasi storey ({float(sty_elevation + sty_height)}m) melampaui tinggi bangunan ({float(bld_height)}m).",
            )

    def _add_error(self, code: SemanticValidationCode, entity_uuid: str, msg: str) -> None:
       
        log_payload = {"error_code": code.value, "entity_uuid": entity_uuid, "message": msg}
        try:
            validated_log = SemanticLogDTO.model_validate(log_payload)
            self._errors.append(validated_log.model_dump())
        except Exception as exc:
            logger.warning("Gagal membungkus error: %s", exc)

    def _add_warning(self, code: SemanticValidationCode, entity_uuid: str, msg: str) -> None:
       
        log_payload = {"error_code": code.value, "entity_uuid": entity_uuid, "message": msg}
        try:
            validated_log = SemanticLogDTO.model_validate(log_payload)
            self._warnings.append(validated_log.model_dump())
        except Exception as exc:
            logger.warning("Gagal membungkus warning: %s", exc)