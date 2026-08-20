"""
ACES-200 CCM Envelope & Validator (diperkuat)
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import uuid


def _is_valid_uuid(s):
    try:
        uuid.UUID(str(s))
        return True
    except (ValueError, AttributeError):
        return False


def _validate_coordinate(coord: Any, entity_uid: str, errors: list):
    """Validasi format coordinate: harus memiliki x, y, z numerik."""
    if not isinstance(coord, dict):
        errors.append({"error_code": "LEX-006", "message": f"Entity {entity_uid}: coordinate harus berupa dict"})
        return
    for axis in ("x", "y", "z"):
        val = coord.get(axis)
        if not isinstance(val, (int, float)):
            errors.append({"error_code": "LEX-006", "message": f"Entity {entity_uid}: coordinate.{axis} harus numerik"})


@dataclass
class CCMEnvelope:
    ccm_version: str
    project_uuid: str
    entities: List[Dict[str, Any]]
    relationships: List[Dict[str, Any]] = field(default_factory=list)

    def validate(self):
        errors = []
        if self.ccm_version != "1.0.0":
            errors.append({"error_code": "LEX-002", "message": "ccm_version must be 1.0.0"})
        if not _is_valid_uuid(self.project_uuid):
            errors.append({"error_code": "LEX-004", "message": "Invalid project_uuid"})

        seen_uuids = set()
        for ent in self.entities:
            if not isinstance(ent, dict):
                errors.append({"error_code": "LEX-001", "message": "Entity harus berupa object"})
                continue
            ent_uuid = ent.get("uuid")
            if ent_uuid is None:
                errors.append({"error_code": "LEX-004", "message": "Entity missing uuid"})
                continue
            if not _is_valid_uuid(ent_uuid):
                errors.append({"error_code": "LEX-004", "message": f"Invalid entity UUID: {ent_uuid}"})
                continue
            if ent_uuid in seen_uuids:
                errors.append({"error_code": "LEX-005", "message": f"Duplicate UUID: {ent_uuid}"})
            seen_uuids.add(ent_uuid)

            if "entity_type" not in ent:
                errors.append({"error_code": "LEX-003", "message": f"Entity {ent_uuid} missing entity_type"})
            if "type" not in ent:
                errors.append({"error_code": "LEX-003", "message": f"Entity {ent_uuid} missing type"})

            # Validasi geometri dasar per tipe
            etype = ent.get("type")
            geom = ent.get("geometry")
            if not isinstance(geom, dict):
                errors.append({"error_code": "LEX-007", "message": f"Entity {ent_uuid}: geometry harus dict"})
                continue

            if etype == "Wall":
                axis = geom.get("axis_line", {})
                if isinstance(axis, dict):
                    points = axis.get("points", [])
                    if not isinstance(points, list) or len(points) < 2:
                        errors.append({"error_code": "LEX-006", "message": f"Wall {ent_uuid}: axis_line minimal 2 titik"})
                    for p in points:
                        _validate_coordinate(p, ent_uuid, errors)
                else:
                    errors.append({"error_code": "LEX-006", "message": f"Wall {ent_uuid}: axis_line harus dict"})
                if "height" not in geom or not isinstance(geom["height"], (int, float)) or geom["height"] <= 0:
                    errors.append({"error_code": "GEO-002", "message": f"Wall {ent_uuid}: height harus > 0"})
                if "thickness" in geom and (not isinstance(geom["thickness"], (int, float)) or geom["thickness"] <= 0):
                    errors.append({"error_code": "GEO-002", "message": f"Wall {ent_uuid}: thickness harus > 0"})

            elif etype == "Column":
                for dim in ("width", "depth", "height"):
                    if dim not in geom or not isinstance(geom[dim], (int, float)) or geom[dim] <= 0:
                        errors.append({"error_code": "GEO-002", "message": f"Column {ent_uuid}: {dim} harus > 0"})

            elif etype == "Beam":
                for dim in ("width", "depth", "length"):
                    if dim not in geom or not isinstance(geom[dim], (int, float)) or geom[dim] <= 0:
                        errors.append({"error_code": "GEO-002", "message": f"Beam {ent_uuid}: {dim} harus > 0"})

            elif etype == "Slab":
                if "thickness" not in geom or not isinstance(geom["thickness"], (int, float)) or geom["thickness"] <= 0:
                    errors.append({"error_code": "GEO-002", "message": f"Slab {ent_uuid}: thickness harus > 0"})
                boundary = geom.get("boundary", {})
                if isinstance(boundary, dict):
                    pts = boundary.get("points", [])
                    if not isinstance(pts, list) or len(pts) < 4:
                        errors.append({"error_code": "GEO-001", "message": f"Slab {ent_uuid}: boundary minimal 4 titik"})
                    for p in pts:
                        _validate_coordinate(p, ent_uuid, errors)
                else:
                    errors.append({"error_code": "GEO-001", "message": f"Slab {ent_uuid}: boundary harus dict"})

            elif etype == "Door" or etype == "Window":
                for dim in ("width", "height"):
                    if dim not in geom or not isinstance(geom[dim], (int, float)) or geom[dim] <= 0:
                        errors.append({"error_code": "GEO-002", "message": f"{etype} {ent_uuid}: {dim} harus > 0"})
                if "position" in geom and geom["position"] < 0:
                    errors.append({"error_code": "GEO-002", "message": f"{etype} {ent_uuid}: position tidak boleh negatif"})

            elif etype == "Room":
                boundary = geom.get("boundary", {})
                if isinstance(boundary, dict):
                    pts = boundary.get("points", [])
                    if not isinstance(pts, list) or len(pts) < 4:
                        errors.append({"error_code": "GEO-001", "message": f"Room {ent_uuid}: boundary minimal 4 titik"})
                    for p in pts:
                        _validate_coordinate(p, ent_uuid, errors)
                else:
                    errors.append({"error_code": "GEO-001", "message": f"Room {ent_uuid}: boundary harus dict"})

        # Validasi relationship
        for rel in self.relationships:
            if not isinstance(rel, dict):
                errors.append({"error_code": "LEX-001", "message": "Relationship harus dict"})
                continue
            if "source" not in rel or not _is_valid_uuid(rel.get("source")):
                errors.append({"error_code": "LEX-004", "message": f"Relationship invalid source: {rel.get('source')}"})
            if "target" not in rel or not _is_valid_uuid(rel.get("target")):
                errors.append({"error_code": "LEX-004", "message": f"Relationship invalid target: {rel.get('target')}"})
            if "type" not in rel:
                errors.append({"error_code": "LEX-003", "message": "Relationship missing type"})

        return errors
