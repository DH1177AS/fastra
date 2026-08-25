
"""
Konverter CCM Master (CCM-MASTER-2026.V1) ke format internal FASTRA.
Memetakan Spaces -> Room, BuildingElements -> Wall/Column/Beam/Slab/Foundation/Door/Window,
RelationsGraph -> relationships internal.
"""
from typing import Any, Dict, List, Optional, Tuple
import uuid

NAMESPACE = uuid.UUID("5f8e3b2a-9c7e-4b1e-8d3f-2a6f1e9c4b7d")

def _uuid_from_id(text: str) -> str:
    """Generate UUID v5 deterministik dari ID teks."""
    return str(uuid.uuid5(NAMESPACE, text))

def _map_room_type(space_name: str, zone_name: str = "") -> str:
    name = space_name.lower()
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
    # zone fallback
    z = zone_name.lower()
    if "serv" in z or "wet" in z:
        return "BATHROOM"
    if "publik" in z or "public" in z:
        return "LIVING"
    if "privat" in z or "private" in z:
        return "BEDROOM"
    return "STORAGE"

def _map_wall_construction(materials: List[str]) -> str:
    joined = " ".join(materials).lower()
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
    result = []
    for pt in points:
        result.append({
            "x": float(pt.get("x", 0)),
            "y": float(pt.get("y", 0)),
            "z": float(pt.get("z", 0)) if pt.get("z") is not None else 0.0,
        })
    # Pastikan poligon tertutup
    if result and result[0] != result[-1]:
        result.append(dict(result[0]))
    return result

def _iter_spaces(master: Dict[str, Any]):
    buildings = master.get("BuildingEntities", []) or []
    for building in buildings:
        for storey in building.get("Storeys", []) or []:
            for zone in storey.get("SpatialZones", []) or []:
                for space in zone.get("Spaces", []) or []:
                    yield space, zone.get("Name", "")

    # Ekstensi layanan (Part2 style)
    ext = master.get("BuildingEntities_Extension", {}) or {}
    for zone in ext.get("SpatialZones_Service", []) or []:
        for space in zone.get("Spaces", []) or []:
            yield space, zone.get("Name", "")

def convert_master_to_internal(master_ccm: Dict[str, Any]) -> Dict[str, Any]:
    """Konversi CCM master ke CCM internal FASTRA."""
    entities: List[Dict[str, Any]] = []
    relationships: List[Dict[str, Any]] = []
    id_to_uuid: Dict[str, str] = {}

    # Ruang + elemen dalam ruang
    for space, zone_name in _iter_spaces(master_ccm):
        space_id = space.get("SpaceID", "UNKNOWN_SPACE")
        suuid = _uuid_from_id(space_id)
        id_to_uuid[space_id] = suuid

        boundary_points = (space.get("Boundary") or {}).get("Points")
        if boundary_points:
            pts = _points_to_list(boundary_points)
        else:
            # fallback persegi dari area/perimeter â€” harusnya tidak terjadi pada demo ready
            area = space.get("Dimensions", {}).get("Area_m2", 1)
            side = float(area) ** 0.5
            pts = [
                {"x": 0.0, "y": 0.0, "z": 0.0},
                {"x": side, "y": 0.0, "z": 0.0},
                {"x": side, "y": side, "z": 0.0},
                {"x": 0.0, "y": side, "z": 0.0},
            ]

        room_entity = {
            "uuid": suuid,
            "entity_type": "Spatial",
            "type": "Room",
            "name": space.get("Name", space_id),
            "room_type": _map_room_type(space.get("Name", ""), zone_name),
            "geometry": {
                "boundary": {"points": pts},
            },
        }
        entities.append(room_entity)

        # Elemen dalam ruang
        for elem in space.get("BuildingElements", []) or []:
            elem_id = elem.get("ElementID", "UNKNOWN_ELEMENT")
            euuid = _uuid_from_id(elem_id)
            id_to_uuid[elem_id] = euuid
            etype = elem.get("Type")
            entity = _convert_element(elem, euuid, space_id, id_to_uuid)
            if entity:
                entities.append(entity)

    # Elemen struktur global
    structural = master_ccm.get("InfrastructureSystems", {}).get("StructuralSystem", {}) or {}
    for elem in structural.get("StructuralElements", []) or []:
        elem_id = elem.get("ElementID", "UNKNOWN_STRUCT")
        euuid = _uuid_from_id(elem_id)
        id_to_uuid[elem_id] = euuid
        entity = _convert_element(elem, euuid, "BUILDING_LEVEL", id_to_uuid)
        if entity:
            entities.append(entity)

    # Foundation (jika tidak ada StructuralElements)
    foundation = structural.get("Foundation") or {}
    if foundation and not any(e.get("type") == "Foundation" for e in entities):
        fid = "Foundation"
        fuuid = _uuid_from_id(fid)
        id_to_uuid[fid] = fuuid
        foot_points = _points_to_list((foundation.get("geometry") or {}).get("footprint", {}).get("points"))
        if foot_points:
            entities.append({
                "uuid": fuuid,
                "entity_type": "Physical",
                "type": "Foundation",
                "name": foundation.get("Type", "Foundation"),
                "geometry": {
                    "footprint": {"points": foot_points},
                    "depth": float((foundation.get("geometry") or {}).get("depth") or 1.0),
                },
                "foundation_type": "BATU_KALI",
            })

    # RelationsGraph
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

        # Mapping tipe relasi
        if rel_type == "SUPPORTS":
            relationships.append({"source": src_uuid, "target": tgt_uuid, "type": "SUPPORTS"})
        elif rel_type == "CONTAINS":
            relationships.append({"source": src_uuid, "target": tgt_uuid, "type": "CONTAINS"})
        elif rel_type == "HOSTS":
            # host_wall sudah dihandle di elemen; tambahkan juga relasi HOSTS
            relationships.append({"source": src_uuid, "target": tgt_uuid, "type": "HOSTS"})
        elif rel_type == "ADJACENT_TO":
            relationships.append({"source": src_uuid, "target": tgt_uuid, "type": "WALL_ADJACENT"})

    # Fallback: jika relasi masih kosong, bangun relasi dasar dari elemen struktur
    if not relationships:
        foundation_uuid = id_to_uuid.get("Foundation")
        columns = [e for e in entities if e["type"] == "Column"]
        beams = [e for e in entities if e["type"] == "Beam"]
        slabs = [e for e in entities if e["type"] == "Slab"]

        if foundation_uuid:
            for col in columns:
                relationships.append({"source": foundation_uuid, "target": col["uuid"], "type": "SUPPORTS"})
        # Paling sederhana: kolom pertama menopang semua balok, balok pertama menopang semua slab
        if columns and beams:
            for beam in beams:
                relationships.append({"source": columns[0]["uuid"], "target": beam["uuid"], "type": "SUPPORTS"})
        if beams and slabs:
            for slab in slabs:
                relationships.append({"source": beams[0]["uuid"], "target": slab["uuid"], "type": "SUPPORTS"})

    # Pastikan semua Slab punya supports
    beam_uuids = [e["uuid"] for e in entities if e["type"] == "Beam"]
    for e in entities:
        if e["type"] == "Slab":
            support_rels = [r for r in relationships if r.get("target") == e["uuid"] and r.get("type") == "SUPPORTS"]
            if support_rels:
                e["supports"] = [r["source"] for r in support_rels]
            else:
                e["supports"] = [beam_uuids[0]] if beam_uuids else ["dummy-support"]

    # Isi start_connection/end_connection untuk Beam dari relasi SUPPORTS
    for e in entities:
        if e["type"] == "Beam":
            support_rels = [r for r in relationships if r.get("target") == e["uuid"] and r.get("type") == "SUPPORTS"]
            sources = [r["source"] for r in support_rels]
            if sources:
                e["start_connection"] = sources[0]
                e["end_connection"] = sources[-1] if len(sources) > 1 else sources[0]
            else:
                col_uuids = [x["uuid"] for x in entities if x["type"] == "Column"]
                if col_uuids:
                    e["start_connection"] = col_uuids[0]
                    e["end_connection"] = col_uuids[-1]

    project_id = master_ccm.get("ModelMetadata", {}).get("ProjectContext", {}).get("ProjectID", "PRJ-INTERNAL")
    return {
        "ccm_version": "1.0.0",
        "project_uuid": _uuid_from_id(project_id),
        "entities": entities,
        "relationships": relationships,
    }

def _convert_element(elem: Dict[str, Any], euuid: str, space_id: str, id_to_uuid: Dict[str, str]) -> Optional[Dict[str, Any]]:
    etype = elem.get("Type")
    name = elem.get("name") or elem.get("ElementID") or etype
    if etype == "Wall":
        geom = elem.get("geometry") or {}
        points = _points_to_list((geom.get("axis_line") or {}).get("points"))
        if not points:
            return None
        return {
            "uuid": euuid,
            "entity_type": "Physical",
            "type": "Wall",
            "name": name,
            "geometry": {
                "axis_line": {"points": points},
                "height": float(geom.get("height") or 3.4),
                "thickness": float(geom.get("thickness") or 0.15),
            },
            "construction_type": _map_wall_construction(elem.get("Materials", []) or []),
            "openings": [],
        }
    elif etype == "Column":
        geom = elem.get("geometry") or {}
        return {
            "uuid": euuid,
            "entity_type": "Physical",
            "type": "Column",
            "name": name,
            "geometry": {
                "width": float(geom.get("width") or 0.15),
                "depth": float(geom.get("depth") or 0.15),
                "height": float(geom.get("height") or 3.4),
            },
        }
    elif etype == "Beam":
        geom = elem.get("geometry") or {}
        return {
            "uuid": euuid,
            "entity_type": "Physical",
            "type": "Beam",
            "name": name,
            "geometry": {
                "width": float(geom.get("width") or 0.15),
                "depth": float(geom.get("depth") or 0.2),
                "length": float(geom.get("length") or 5.0),
            },
            "start_connection": str(id_to_uuid.get(elem.get("start_connection", ""), "")) if elem.get("start_connection") else None,
            "end_connection": str(id_to_uuid.get(elem.get("end_connection", ""), "")) if elem.get("end_connection") else None,
        }
    elif etype == "Slab":
        geom = elem.get("geometry") or {}
        points = _points_to_list((geom.get("boundary") or {}).get("points"))
        if not points:
            return None
        return {
            "uuid": euuid,
            "entity_type": "Physical",
            "type": "Slab",
            "name": name,
            "geometry": {
                "boundary": {"points": points},
                "thickness": float(geom.get("thickness") or 0.12),
            },
            "supports": [],
        }
    elif etype == "Foundation":
        geom = elem.get("geometry") or {}
        points = _points_to_list((geom.get("footprint") or {}).get("points"))
        if not points:
            return None
        return {
            "uuid": euuid,
            "entity_type": "Physical",
            "type": "Foundation",
            "name": name,
            "geometry": {
                "footprint": {"points": points},
                "depth": float(geom.get("depth") or 1.0),
            },
            "foundation_type": "BATU_KALI",
        }
    elif etype == "Door":
        geom = elem.get("geometry") or {}
        dims = elem.get("Dimensions") or {}
        width = float(geom.get("width") or (dims.get("Width_mm", 900) / 1000))
        height = float(geom.get("height") or (dims.get("Height_mm", 2100) / 1000))
        host = geom.get("host_wall_uuid")
        host_uuid = id_to_uuid.get(host) if host else None
        pos = (geom.get("position_on_wall") or {}).get("distance_from_start_m", 0.0)
        return {
            "uuid": euuid,
            "entity_type": "Physical",
            "type": "Door",
            "name": name,
            "geometry": {"width": width, "height": height},
            "door_type": "SINGLE",
            "host_wall": host_uuid,
            "position_on_wall": float(pos),
        }
    elif etype == "Window":
        geom = elem.get("geometry") or {}
        dims = elem.get("Dimensions") or {}
        width = float(geom.get("width") or (dims.get("Width_mm", 1200) / 1000))
        height = float(geom.get("height") or (dims.get("Height_mm", 1200) / 1000))
        host = geom.get("host_wall_uuid")
        host_uuid = id_to_uuid.get(host) if host else None
        pos = (geom.get("position_on_wall") or {}).get("distance_from_start_m", 0.0)
        sill = (geom.get("position_on_wall") or {}).get("sill_height_m", 1.0)
        return {
            "uuid": euuid,
            "entity_type": "Physical",
            "type": "Window",
            "name": name,
            "geometry": {"width": width, "height": height, "sill_height": float(sill)},
            "window_type": "CASEMENT",
            "host_wall": host_uuid,
            "position_on_wall": float(pos),
        }
    return None
