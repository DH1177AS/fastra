# fastra_core/compiler/parser.py

from __future__ import annotations

import enum
import logging
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, ConfigDict, Field

from fastra_core.ccm.common import Opening, OpeningType
from fastra_core.ccm.physical import (
    Beam,
    BeamType,
    Column,
    ColumnType,
    ConstructionWallType,
    Coordinate,
    Door,
    DoorType,
    Foundation,
    FoundationType,
    GlazingType,
    Ramp,
    RampSurfaceType,
    Roof,
    RoofStructureType,
    RoofType,
    Slab,
    SlabType,
    Stair,
    StairStructureType,
    StructuralWallType,
    Wall,
    Window,
    WindowType,
)
from fastra_core.ccm.spatial import Room, RoomType

logger = logging.getLogger(__name__)


class ParserErrorCode(str, enum.Enum):
    PAR_001 = "PAR-001"  # Malformed relationship syntax / graph break
    PAR_002 = "PAR-002"  # Domain object instantiation crash / structural mutation


class ParserErrorLogDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    error_code: ParserErrorCode = Field(...)
    message: str = Field(..., min_length=5, max_length=1024)


def _point_in_polygon_precise(poly: List[Coordinate], pt: Coordinate) -> bool:
    n = len(poly)
    if n < 3:
        return False

    inside = False
    px, py = float(pt.x), float(pt.y)

    for i in range(n):
        x1, y1 = float(poly[i].x), float(poly[i].y)
        x2, y2 = float(poly[(i + 1) % n].x), float(poly[(i + 1) % n].y)

        # Deteksi perpotongan sinar horizontal
        if ((y1 > py) != (y2 > py)) and (
            px < (x2 - x1) * (py - y1) / (y2 - y1 + 1e-12) + x1
        ):
            inside = not inside

    return inside


class Parser:
    def __init__(self) -> None:
        self.entities: Dict[str, Any] = {}
        self.graph: Dict[str, List[Tuple[str, str]]] = {}
        self._errors: List[Dict[str, Any]] = []
        self._warnings: List[str] = []

    @property
    def errors(self) -> List[Dict[str, Any]]:
        return list(self._errors)

    @property
    def warnings(self) -> List[str]:
        return list(self._warnings)

    def parse(
        self, envelope: Any
    ) -> Tuple[Dict[str, Any], Dict[str, List[Tuple[str, str]]]]:
        self.entities.clear()
        self.graph.clear()
        self._errors.clear()
        self._warnings.clear()

        for rel in getattr(envelope, "relationships", []) or []:
            src = rel.get("source")
            tgt = rel.get("target")
            rel_type = rel.get("type")
            if src and tgt and rel_type:
                self.graph.setdefault(src, []).append((str(rel_type), str(tgt)))

        for e in getattr(envelope, "entities", []) or []:
            uid = e.get("uuid")
            t = e.get("type")
            name = e.get("name", "")
            geom = e.get("geometry", {})

            if not uid or not t:
                continue

            try:
                self._instantiate_entity(uid, t, e, geom)
            except Exception as exc:
                logger.exception("Gagal instansiasi entitas %s tipe %s", uid, t)
                self._add_error(
                    ParserErrorCode.PAR_002,
                    f"Gagal instansiasi memori elemen UUID '{uid}' tipe '{t}': {exc}",
                )

        self._derive_spatial_relations()

        return self.entities, self.graph

    def _instantiate_entity(
        self, uid: str, entity_type: str, raw: Dict[str, Any], geom: Dict[str, Any]
    ) -> None:
        if entity_type == "Wall":
            axis_pts = [
                Coordinate(p["x"], p["y"], p.get("z", 0.0))
                for p in geom["axis_line"]["points"]
            ]
            openings_pool: List[Opening] = []
            for op in raw.get("openings", []) or []:
                openings_pool.append(
                    Opening(
                        width=float(op["width"]),
                        height=float(op["height"]),
                        position=float(op.get("position", 0.0)),
                        opening_type=OpeningType(op.get("opening_type", "DOOR")),
                    )
                )
            self.entities[uid] = Wall(
                axis_line=axis_pts,
                height=float(geom["height"]),
                thickness=float(geom.get("thickness", 0.15)),
                structural_type=StructuralWallType(
                    raw.get("structural_type", "NON_LOAD_BEARING")
                ),
                construction_type=ConstructionWallType(
                    raw.get("construction_type", "BATA_MERAH")
                ),
                base_elevation=float(raw.get("base_elevation", 0.0)),
                openings=openings_pool,
            )

        elif entity_type == "Column":
            self.entities[uid] = Column(
                width=float(geom.get("width", 0.3)),
                depth=float(geom.get("depth", 0.3)),
                height=float(geom["height"]),
                base_elevation=float(geom.get("base_elevation", 0.0)),
                structural_type=ColumnType(
                    raw.get("structural_type", "KOLOM_STRUKTUR")
                ),
                material_id=raw.get("material_id"),
            )

        elif entity_type == "Beam":
            self.entities[uid] = Beam(
                width=float(geom.get("width", 0.25)),
                depth=float(geom.get("depth", 0.4)),
                length=float(geom["length"]),
                beam_type=BeamType(raw.get("beam_type", "BALOK_INDUK")),
                start_connection=raw.get("start_connection"),
                end_connection=raw.get("end_connection"),
            )

        elif entity_type == "Slab":
            boundary_pts = [
                Coordinate(p["x"], p["y"], p.get("z", 0.0))
                for p in geom["boundary"]["points"]
            ]
            self.entities[uid] = Slab(
                boundary=boundary_pts,
                thickness=float(geom["thickness"]),
                slab_type=SlabType(raw.get("slab_type", "PLAT_LANTAI")),
                elevation=float(raw.get("elevation", 0.0)),
                supports=raw.get("supports", []),
                name=raw.get("name", "Slab"),
            )

        elif entity_type == "Foundation":
            footprint_pts = [
                Coordinate(p["x"], p["y"], p.get("z", 0.0))
                for p in geom["footprint"]["points"]
            ]
            self.entities[uid] = Foundation(
                footprint=footprint_pts,
                depth=float(geom["depth"]),
                foundation_type=FoundationType(
                    raw.get("foundation_type", "FOOTPLATE")
                ),
                material_id=raw.get("material_id"),
            )

        elif entity_type == "Roof":
            footprint_pts = [
                Coordinate(p["x"], p["y"], p.get("z", 0.0))
                for p in geom["footprint"]["points"]
            ]
            ridge_pts = [
                Coordinate(p["x"], p["y"], p.get("z", 0.0))
                for p in geom.get("ridge_line", {}).get("points", [])
            ]
            self.entities[uid] = Roof(
                roof_type=RoofType(raw.get("roof_type", "GABLE")),
                structure_type=RoofStructureType(
                    raw.get("structure_type", "BAJA_RINGAN")
                ),
                slope=float(geom["slope"]),
                footprint=footprint_pts,
                ridge_line=ridge_pts,
                overhang=float(raw.get("overhang", 0.5)),
                covering_material_id=raw.get("covering_material_id"),
            )

        elif entity_type == "Door":
            self.entities[uid] = Door(
                width=float(geom["width"]),
                height=float(geom["height"]),
                door_type=DoorType(raw.get("door_type", "SINGLE")),
                position_on_wall=float(raw.get("position_on_wall", 0.0)),
                sill_height=float(raw.get("sill_height", 0.0)),
                material_id=raw.get("material_id"),
                host_wall=raw.get("host_wall"),
            )

        elif entity_type == "Window":
            self.entities[uid] = Window(
                width=float(geom["width"]),
                height=float(geom["height"]),
                window_type=WindowType(raw.get("window_type", "CASEMENT")),
                position_on_wall=float(raw.get("position_on_wall", 0.0)),
                sill_height=float(geom.get("sill_height", 0.9)),
                glazing_type=GlazingType(raw.get("glazing_type", "CLEAR")),
                material_id=raw.get("material_id"),
                host_wall=raw.get("host_wall"),
            )

        elif entity_type == "Stairs":
            self.entities[uid] = Stair(
                number_of_risers=int(geom["number_of_risers"]),
                riser_height=float(geom["riser_height"]),
                tread_depth=float(geom["tread_depth"]),
                width=float(geom["width"]),
                start_elevation=float(raw.get("start_elevation", 0.0)),
                end_elevation=float(raw.get("end_elevation", 3.5)),
                structural_type=StairStructureType(
                    raw.get("structural_type", "CONCRETE")
                ),
            )

        elif entity_type == "Ramp":
            self.entities[uid] = Ramp(
                length=float(geom["length"]),
                width=float(geom["width"]),
                slope=float(geom["slope"]),
                start_elevation=float(raw.get("start_elevation", 0.0)),
                end_elevation=float(raw.get("end_elevation", 0.6)),
                surface_type=RampSurfaceType(raw.get("surface_type", "CONCRETE")),
                handrail=bool(raw.get("handrail", True)),
            )

        elif entity_type == "Room":
            boundary_pts = [
                Coordinate(p["x"], p["y"], p.get("z", 0.0))
                for p in geom["boundary"]["points"]
            ]
            room_name = raw.get("name") or raw.get("Name") or "Unnamed Room"
            self.entities[uid] = Room(
                name=room_name,
                room_type=RoomType(raw.get("room_type", "LIVING")),
                boundary=boundary_pts,
                storey_id=raw.get("storey_id"),
                finish=raw.get("finish"),
            )

        else:
            self._warnings.append(
                f"Mekanisme kompilasi melewati tipe elemen tak dikenal: '{entity_type}'"
            )

    def _derive_spatial_relations(self) -> None:
        rooms = {uid: ent for uid, ent in self.entities.items() if isinstance(ent, Room)}
        openings = {
            uid: ent
            for uid, ent in self.entities.items()
            if isinstance(ent, (Door, Window))
        }

        for ruid, room in rooms.items():
            if not hasattr(room, "_boundary"):
                continue

            for duid, opening in openings.items():
                host_wall_id = getattr(opening, "_host_wall", None) or getattr(
                    opening, "host_wall", None
                )
                if not host_wall_id:
                    continue

                wall = self.entities.get(host_wall_id)
                if not isinstance(wall, Wall):
                    continue

                axis_line = getattr(wall, "_axis_line", None)
                if not axis_line:
                    continue

                start = axis_line[0]
                end = axis_line[-1]
                total_len = float(start.distance_to(end))
                if total_len <= 0.0:
                    continue

                pos = float(getattr(opening, "_position_on_wall", 0.0))
                factor = max(0.0, min(1.0, pos / total_len))

                px = float(start.x) + (float(end.x) - float(start.x)) * factor
                py = float(start.y) + (float(end.y) - float(start.y)) * factor
                pz = float(start.z) + (float(end.z) - float(start.z)) * factor
                target_pt = Coordinate(px, py, pz)

                try:
                    if _point_in_polygon_precise(room._boundary, target_pt):
                        self.graph.setdefault(ruid, []).append(("CONTAINS", duid))
                except Exception as exc:
                    self._warnings.append(
                        f"Evaluasi spasial CONTAINS poligon dilewati: {exc}"
                    )

    def _add_error(self, code: ParserErrorCode, msg: str) -> None:
        error_payload = {
            "error_code": code,
            "message": msg,
        }
        try:
            validated_error = ParserErrorLogDTO.model_validate(error_payload)
            self._errors.append(validated_error.model_dump())
        except Exception:
            # Fallback jika DTO gagal (misalnya karena code tidak valid)
            logger.warning("Gagal membungkus error parser: %s", error_payload)
            self._errors.append(
                {"error_code": "PAR-002", "message": msg}
            )