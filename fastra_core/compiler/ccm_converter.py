# fastra_core\compiler\ccm_converter.py

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------------------------
# Namespace deterministik untuk UUID v5
# ---------------------------------------------------------------------------
NAMESPACE = uuid.UUID("5f8e3b2a-9c7e-4b1e-8d3f-2a6f1e9c4b7d")


# ---------------------------------------------------------------------------
# Inbound DTOs – Pydantic Strict Gateway & Sanitization (Fail-Fast)
# ---------------------------------------------------------------------------
class CoordinatePointDTO(BaseModel):
   
    model_config = ConfigDict(extra="allow", str_strip_whitespace=True, strict=True)
    x: float = Field(..., ge=-1e6, le=1e6, allow_inf_nan=False)
    y: float = Field(..., ge=-1e6, le=1e6, allow_inf_nan=False)
    z: float = Field(default=0.0, ge=-1e4, le=1e4, allow_inf_nan=False)


class MasterCCMPayloadDTO(BaseModel):
    model_config = ConfigDict(extra="allow", str_strip_whitespace=True, strict=True)

    BuildingEntities: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    BuildingEntities_Extension: Optional[Dict[str, Any]] = Field(default_factory=dict)
    InfrastructureSystems: Optional[Dict[str, Any]] = Field(default_factory=dict)
    RelationsGraph: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    ModelMetadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

# ---------------------------------------------------------------------------
# Core Utilities – Konversi Numerik Aman & Deterministis
# ---------------------------------------------------------------------------
def _safe_float(value: Any, default: float, field_name: str) -> float:
   
    if value is None:
        return default
    if not isinstance(value, (int, float)):
        raise TypeError(f"Field '{field_name}' harus berupa angka (int/float).")
    result = float(value)
    if result != result or result in (float("inf"), float("-inf")):
        raise ValueError(f"Field '{field_name}' tidak boleh NaN atau tak hingga.")
    return result


def _safe_int(value: Any, default: int, field_name: str) -> int:
   
    if value is None:
        return default
    if not isinstance(value, int):
        raise TypeError(f"Field '{field_name}' harus berupa integer.")
    return value


def _uuid_from_id(text: str) -> str:
   
    if not text.strip():
        raise ValueError("Teks dasar untuk komputasi UUID v5 tidak boleh kosong.")
    return str(uuid.uuid5(NAMESPACE, text.strip()))


def _map_room_type(space_name: str, zone_name: str = "") -> str:
  
    name = space_name.strip().lower()
    if "tamu" in name or "keluarga" in name or "living" in name:
        return "LIVING"
    if "tidur" in name or "bedroom" in name:
        return "BEDROOM"
    if "mandi" in name or "bathroom" in name or "toilet" in name:
        return "BATHROOM"
    if "dapur" in name or "kitchen" in name:
        return "KITCHEN"
    if "koridor" in name or "circulation" in name or "sirkulasi" in name:
        return "CORRIDOR"
    if "makan" in name:
        return "KITCHEN"
  
    z = zone_name.strip().lower()
    if "serv" in z or "wet" in z:
        return "BATHROOM"
    if "publik" in z or "public" in z:
        return "LIVING"
    if "privat" in z or "private" in z:
        return "BEDROOM"
    return "STORAGE"


def _map_wall_construction(materials: List[str]) -> str:
    
    joined = " ".join([m.strip() for m in materials if m.strip()]).lower()
    if "bata ringan" in joined:
        return "BATA_RINGAN"
    if "bata merah" in joined:
        return "BATA_MERAH"
    if "beton" in joined:
        return "BETON_BERTULANG"
    if "kayu" in joined:
        return "KAYU"
    if "gypsum" in joined:
        return "GYPSUM"
    if "partisi" in joined:
        return "PARTISI"
    return "BATA_RINGAN"


def _points_to_list(points: Optional[List[Dict[str, float]]]) -> List[Dict[str, float]]:
   
    if not points:
        return []

    result: List[Dict[str, float]] = []
    for pt in points:
       
        validated_pt = CoordinatePointDTO(**pt)
        result.append(
            {
                "x": validated_pt.x,
                "y": validated_pt.y,
                "z": validated_pt.z,
            }
        )
   
    if result and (result[0]["x"] != result[-1]["x"] or result[0]["y"] != result[-1]["y"]):
        result.append(dict(result[0]))
    return result


def _iter_spaces(master: Dict[str, Any]):
   
    buildings = master.get("BuildingEntities", []) or []
    for building in buildings:
        for storey in building.get("Storeys", []) or []:
            for zone in storey.get("SpatialZones", []) or []:
                for space in zone.get("Spaces", []) or []:
                    yield space, zone.get("Name", "")
  
    ext = master.get("BuildingEntities_Extension", {}) or {}
    for zone in ext.get("SpatialZones_Service", []) or []:
        for space in zone.get("Spaces", []) or []:
            yield space, zone.get("Name", "")


# ---------------------------------------------------------------------------
# Fungsi Konversi Elemen (Deep Sub-Element Mapper)
# ---------------------------------------------------------------------------
def _convert_element(
    elem: Dict[str, Any],
    euuid: str,
    space_id: str,
    id_to_uuid: Dict[str, str],
) -> Optional[Dict[str, Any]]:
   
    etype = elem.get("Type")
    name = elem.get("name") or elem.get("ElementID") or etype
    geom = elem.get("geometry") or {}
    dims = elem.get("Dimensions") or {}

    if etype == "Wall":
        points = _points_to_list((geom.get("axis_line") or {}).get("points"))
        if not points:
            return None
        height = _safe_float(geom.get("height"), 3.4, "Wall.height")
        thickness = _safe_float(geom.get("thickness"), 0.15, "Wall.thickness")
        return {
            "uuid": euuid,
            "entity_type": "Physical",
            "type": "Wall",
            "name": name,
            "geometry": {
                "axis_line": {"points": points},
                "height": height,
                "thickness": thickness,
            },
            "construction_type": _map_wall_construction(elem.get("Materials", []) or []),
            "openings": [],
        }

    elif etype == "Column":
        width = _safe_float(geom.get("width"), 0.15, "Column.width")
        depth = _safe_float(geom.get("depth"), 0.15, "Column.depth")
        height = _safe_float(geom.get("height"), 3.4, "Column.height")
        return {
            "uuid": euuid,
            "entity_type": "Physical",
            "type": "Column",
            "name": name,
            "geometry": {
                "width": width,
                "depth": depth,
                "height": height,
            },
        }

    elif etype == "Beam":
        width = _safe_float(geom.get("width"), 0.15, "Beam.width")
        depth = _safe_float(geom.get("depth"), 0.2, "Beam.depth")
        length = _safe_float(geom.get("length"), 5.0, "Beam.length")
        start_id = elem.get("start_connection")
        end_id = elem.get("end_connection")
        start_uuid = str(id_to_uuid.get(start_id, "")) if start_id else None
        end_uuid = str(id_to_uuid.get(end_id, "")) if end_id else None
        return {
            "uuid": euuid,
            "entity_type": "Physical",
            "type": "Beam",
            "name": name,
            "geometry": {
                "width": width,
                "depth": depth,
                "length": length,
            },
            "start_connection": start_uuid,
            "end_connection": end_uuid,
        }

    elif etype == "Slab":
        points = _points_to_list((geom.get("boundary") or {}).get("points"))
        if not points:
            return None
        thickness = _safe_float(geom.get("thickness"), 0.12, "Slab.thickness")
        return {
            "uuid": euuid,
            "entity_type": "Physical",
            "type": "Slab",
            "name": name,
            "geometry": {
                "boundary": {"points": points},
                "thickness": thickness,
            },
            "supports": [],
        }

    elif etype == "Foundation":
        points = _points_to_list((geom.get("footprint") or {}).get("points"))
        if not points:
            return None
        depth = _safe_float(geom.get("depth"), 1.0, "Foundation.depth")
        return {
            "uuid": euuid,
            "entity_type": "Physical",
            "type": "Foundation",
            "name": name,
            "geometry": {
                "footprint": {"points": points},
                "depth": depth,
            },
            "foundation_type": "BATU_KALI",
        }

    elif etype == "Door":
        width = _safe_float(
            geom.get("width"),
            _safe_float(dims.get("Width_mm", 900), 900, "Door.Width_mm") / 1000.0,
            "Door.width",
        )
        height = _safe_float(
            geom.get("height"),
            _safe_float(dims.get("Height_mm", 2100), 2100, "Door.Height_mm") / 1000.0,
            "Door.height",
        )
        host = geom.get("host_wall_uuid")
        host_uuid = str(id_to_uuid.get(host, "")) if host else None
        pos = _safe_float(
            (geom.get("position_on_wall") or {}).get("distance_from_start_m", 0.0),
            0.0,
            "Door.position",
        )
        return {
            "uuid": euuid,
            "entity_type": "Physical",
            "type": "Door",
            "name": name,
            "geometry": {"width": width, "height": height},
            "door_type": "SINGLE",
            "host_wall": host_uuid,
            "position_on_wall": pos,
        }

    elif etype == "Window":
        width = _safe_float(
            geom.get("width"),
            _safe_float(dims.get("Width_mm", 1200), 1200, "Window.Width_mm") / 1000.0,
            "Window.width",
        )
        height = _safe_float(
            geom.get("height"),
            _safe_float(dims.get("Height_mm", 1200), 1200, "Window.Height_mm") / 1000.0,
            "Window.height",
        )
        host = geom.get("host_wall_uuid")
        host_uuid = str(id_to_uuid.get(host, "")) if host else None
        pos = _safe_float(
            (geom.get("position_on_wall") or {}).get("distance_from_start_m", 0.0),
            0.0,
            "Window.position",
        )
        sill = _safe_float(
            (geom.get("position_on_wall") or {}).get("sill_height_m", 1.0),
            1.0,
            "Window.sill_height",
        )
        return {
            "uuid": euuid,
            "entity_type": "Physical",
            "type": "Window",
            "name": name,
            "geometry": {"width": width, "height": height, "sill_height": sill},
            "window_type": "CASEMENT",
            "host_wall": host_uuid,
            "position_on_wall": pos,
        }

    return None


# ---------------------------------------------------------------------------
# Fungsi Konversi Utama
# ---------------------------------------------------------------------------
def convert_master_to_internal(master_ccm: Dict[str, Any]) -> Dict[str, Any]:
   
    MasterCCMPayloadDTO(**master_ccm)

    entities: List[Dict[str, Any]] = []
    relationships: List[Dict[str, Any]] = []
    id_to_uuid: Dict[str, str] = {}
  
    for space, zone_name in _iter_spaces(master_ccm):
        space_id = space.get("SpaceID", "UNKNOWN_SPACE")
        suuid = _uuid_from_id(space_id)
        id_to_uuid[space_id] = suuid

        boundary_points = (space.get("Boundary") or {}).get("Points")
        if boundary_points:
            pts = _points_to_list(boundary_points)
        else:
          
            area = _safe_float(
                (space.get("Dimensions") or {}).get("Area_m2", 1.0),
                1.0,
                "Space.Area_m2",
            )
            side = area**0.5
            pts = [
                {"x": 0.0, "y": 0.0, "z": 0.0},
                {"x": side, "y": 0.0, "z": 0.0},
                {"x": side, "y": side, "z": 0.0},
                {"x": 0.0, "y": side, "z": 0.0},
                {"x": 0.0, "y": 0.0, "z": 0.0},
            ]

        room_entity = {
            "uuid": suuid,
            "entity_type": "Spatial",
            "type": "Room",
            "name": space.get("Name", space_id),
            "room_type": _map_room_type(space.get("Name", ""), zone_name),
            "geometry": {"boundary": {"points": pts}},
        }
        entities.append(room_entity)
       
        for elem in space.get("BuildingElements", []) or []:
            elem_id = elem.get("ElementID", "UNKNOWN_ELEMENT")
            euuid = _uuid_from_id(elem_id)
            id_to_uuid[elem_id] = euuid
            entity = _convert_element(elem, euuid, space_id, id_to_uuid)
            if entity:
                entities.append(entity)
    
    structural = master_ccm.get("InfrastructureSystems", {}).get("StructuralSystem", {}) or {}
    for elem in structural.get("StructuralElements", []) or []:
        elem_id = elem.get("ElementID", "UNKNOWN_STRUCT")
        euuid = _uuid_from_id(elem_id)
        id_to_uuid[elem_id] = euuid
        entity = _convert_element(elem, euuid, "BUILDING_LEVEL", id_to_uuid)
        if entity:
            entities.append(entity)
   
    foundation_data = structural.get("Foundation") or {}
    if foundation_data and not any(e.get("type") == "Foundation" for e in entities):
        fid = "Foundation"
        fuuid = _uuid_from_id(fid)
        id_to_uuid[fid] = fuuid
        foot_points = _points_to_list(
            (foundation_data.get("geometry") or {}).get("footprint", {}).get("points")
        )
        if foot_points:
            depth = _safe_float(
                (foundation_data.get("geometry") or {}).get("depth", 1.0),
                1.0,
                "Foundation.depth",
            )
            entities.append(
                {
                    "uuid": fuuid,
                    "entity_type": "Physical",
                    "type": "Foundation",
                    "name": foundation_data.get("Type", "Foundation"),
                    "geometry": {
                        "footprint": {"points": foot_points},
                        "depth": depth,
                    },
                    "foundation_type": "BATU_KALI",
                }
            )
  
    for rel in master_ccm.get("RelationsGraph", []) or []:
        source_id = rel.get("source")
        target_id = rel.get("target")
        rel_type = rel.get("type")
        if not source_id or not target_id or not rel_type:
            continue

        src_uuid = id_to_uuid.get(source_id)
        tgt_uuid = id_to_uuid.get(target_id)
        if not src_uuid or not tgt_uuid:
            continue

        if rel_type == "SUPPORTS":
            relationships.append({"source": src_uuid, "target": tgt_uuid, "type": "SUPPORTS"})
        elif rel_type == "CONTAINS":
            relationships.append({"source": src_uuid, "target": tgt_uuid, "type": "CONTAINS"})
        elif rel_type == "HOSTS":
            relationships.append({"source": src_uuid, "target": tgt_uuid, "type": "HOSTS"})
        elif rel_type == "ADJACENT_TO":
            relationships.append({"source": src_uuid, "target": tgt_uuid, "type": "WALL_ADJACENT"})
 
    if not relationships:
        foundation_uuid = id_to_uuid.get("Foundation")
        columns = [e for e in entities if e["type"] == "Column"]
        beams = [e for e in entities if e["type"] == "Beam"]
        slabs = [e for e in entities if e["type"] == "Slab"]

        if foundation_uuid:
            for col in columns:
                relationships.append(
                    {"source": foundation_uuid, "target": col["uuid"], "type": "SUPPORTS"}
                )
        if columns and beams:
            for beam in beams:
                relationships.append(
                    {"source": columns[0]["uuid"], "target": beam["uuid"], "type": "SUPPORTS"}
                )
        if beams and slabs:
            for slab in slabs:
                relationships.append(
                    {"source": beams[0]["uuid"], "target": slab["uuid"], "type": "SUPPORTS"}
                )
    
    beam_uuids = [e["uuid"] for e in entities if e["type"] == "Beam"]
    for e in entities:
        if e["type"] == "Slab":
            support_rels = [
                r for r in relationships
                if r.get("target") == e["uuid"] and r.get("type") == "SUPPORTS"
            ]
            if support_rels:
                e["supports"] = [r["source"] for r in support_rels]
            else:
                # Jika tidak ada relasi, biarkan kosong (bukan dummy)
                e["supports"] = []

        if e["type"] == "Beam":
            support_rels = [
                r for r in relationships
                if r.get("target") == e["uuid"] and r.get("type") == "SUPPORTS"
            ]
            sources = [r["source"] for r in support_rels]
            if sources:
                e["start_connection"] = sources[0]
                e["end_connection"] = sources[-1] if len(sources) > 1 else sources[0]
            else:
                col_uuids = [x["uuid"] for x in entities if x["type"] == "Column"]
                if col_uuids:
                    e["start_connection"] = col_uuids[0]
                    e["end_connection"] = col_uuids[-1]
   
    project_id = (
        master_ccm.get("ModelMetadata", {})
        .get("ProjectContext", {})
        .get("ProjectID", "PRJ-INTERNAL")
    )

    return {
        "ccm_version": "1.0.0",
        "project_uuid": _uuid_from_id(project_id),
        "entities": entities,
        "relationships": relationships,
    }