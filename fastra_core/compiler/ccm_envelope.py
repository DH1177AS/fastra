# fastra_core\compiler\ccm_envelope.py

from __future__ import annotations

import enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ErrorCode(str, enum.Enum):
   
    LEX_001 = "LEX-001"  # Malformed object schema
    LEX_002 = "LEX-002"  # Version mismatch
    LEX_003 = "LEX-003"  # Missing mandatory meta type
    LEX_004 = "LEX-004"  # Invalid cryptographic identifier (UUID)
    LEX_005 = "LEX-005"  # Duplicate identifier collision
    LEX_006 = "LEX-006"  # Coordinate syntax corruption
    LEX_007 = "LEX-007"  # Geometry structural breakdown
    GEO_001 = "GEO-001"  # Topological boundary loop violation
    GEO_002 = "GEO-002"  # Non-physical engineering dimension


class EnvelopeEntityType(str, enum.Enum):
    PHYSICAL = "Physical"
    SPATIAL = "Spatial"


class EnvelopeElementSubtype(str, enum.Enum):
    WALL = "Wall"
    COLUMN = "Column"
    BEAM = "Beam"
    SLAB = "Slab"
    FOUNDATION = "Foundation"
    DOOR = "Door"
    WINDOW = "Window"
    ROOM = "Room"


class EnvelopeRelationType(str, enum.Enum):
    SUPPORTS = "SUPPORTS"
    CONTAINS = "CONTAINS"
    HOSTS = "HOSTS"
    WALL_ADJACENT = "WALL_ADJACENT"


# ---------------------------------------------------------------------------
# Inbound DTOs – Pydantic Strict Gateway & Validation Matrix (Fail-Fast)
# ---------------------------------------------------------------------------
class EnvelopeCoordinateDTO(BaseModel):
   
    model_config = ConfigDict(extra="forbid", strict=True)

    x: float = Field(..., ge=-1e6, le=1e6, allow_inf_nan=False)
    y: float = Field(..., ge=-1e6, le=1e6, allow_inf_nan=False)
    z: float = Field(default=0.0, ge=-1e4, le=1e4, allow_inf_nan=False)


class PointsContainerDTO(BaseModel):
   
    model_config = ConfigDict(extra="forbid", strict=True)

    points: List[EnvelopeCoordinateDTO] = Field(..., min_length=2, max_length=1000)


class EnvelopeGeometryDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False, strict=True)

    axis_line: Optional[PointsContainerDTO] = None
    boundary: Optional[PointsContainerDTO] = None
    footprint: Optional[PointsContainerDTO] = None

    height: Optional[float] = Field(default=None, gt=0.0, le=1000.0)
    thickness: Optional[float] = Field(default=None, gt=0.0, le=10.0)
    width: Optional[float] = Field(default=None, gt=0.0, le=100.0)
    depth: Optional[float] = Field(default=None, gt=0.0, le=100.0)
    length: Optional[float] = Field(default=None, gt=0.0, le=1000.0)
    position: Optional[float] = Field(default=None, ge=0.0, le=5000.0)
    sill_height: Optional[float] = Field(default=None, ge=0.0, le=100.0)


class EnvelopeEntityDTO(BaseModel):
    model_config = ConfigDict(extra="allow", str_strip_whitespace=True, strict=True)

    uuid: str = Field(
        ...,
        min_length=36,
        max_length=36,
        pattern=r"^[a-f0-9]{8}-[a-f0-9]{4}-[1-5][a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$",
    )
    entity_type: str = Field(..., min_length=1, max_length=64)
    type: str = Field(..., min_length=1, max_length=64)
    name: str = Field(..., min_length=1, max_length=256)
    geometry: EnvelopeGeometryDTO


class EnvelopeRelationshipDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, strict=True)

    source: str = Field(
        ...,
        min_length=36,
        max_length=36,
        pattern=r"^[a-f0-9]{8}-[a-f0-9]{4}-[1-5][a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$",
    )
    target: str = Field(
        ...,
        min_length=36,
        max_length=36,
        pattern=r"^[a-f0-9]{8}-[a-f0-9]{4}-[1-5][a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$",
    )
    type: str = Field(..., min_length=1, max_length=64)


class CCMEnvelopeInboundDTO(BaseModel):
   
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, strict=True)

    ccm_version: str = Field(..., min_length=5, max_length=16)
    project_uuid: str = Field(
        ...,
        min_length=36,
        max_length=36,
        pattern=r"^[a-f0-9]{8}-[a-f0-9]{4}-[1-5][a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$",
    )
    entities: List[EnvelopeEntityDTO] = Field(..., max_length=50000)
    relationships: List[EnvelopeRelationshipDTO] = Field(
        default_factory=list, max_length=200000
    )


# ---------------------------------------------------------------------------
# Domain Models – Pure Business & Geometrical Verification Envelope
# ---------------------------------------------------------------------------
class CCMEnvelope:
    
    def __init__(
        self,
        ccm_version: str,
        project_uuid: str,
        entities: List[Dict[str, Any]],
        relationships: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        self._ccm_version = ccm_version
        self._project_uuid = project_uuid
        self._raw_entities = list(entities)
        self._raw_relationships = list(relationships or [])
        self._errors: List[Dict[str, str]] = []

    @property
    def entities(self) -> List[Dict[str, Any]]:
        return list(self._raw_entities)

    @property
    def relationships(self) -> List[Dict[str, Any]]:
        return list(self._raw_relationships)

    @property
    def project_uuid(self) -> str:
        return self._project_uuid

    @property
    def ccm_version(self) -> str:
        return self._ccm_version
    
    def validate(self) -> List[Dict[str, str]]:
       
        self._errors.clear()
       
        try:
            validated_bundle = CCMEnvelopeInboundDTO(
                ccm_version=self._ccm_version,
                project_uuid=self._project_uuid,
                entities=self._raw_entities,
                relationships=self._raw_relationships,
            )
        except Exception as exc:
            self._errors.append(
                {
                    "error_code": ErrorCode.LEX_001.value,
                    "message": f"Kegagalan fatal parsing skema amplop dokumen: {str(exc)}",
                }
            )
            return self._errors
        
        if validated_bundle.ccm_version != "1.0.0":
            self._errors.append(
                {
                    "error_code": ErrorCode.LEX_002.value,
                    "message": f"Versi '{validated_bundle.ccm_version}' tidak didukung. Wajib '1.0.0'.",
                }
            )
       
        seen_uuids: set[str] = set()
        for ent in validated_bundle.entities:
            if ent.uuid in seen_uuids:
                self._errors.append(
                    {
                        "error_code": ErrorCode.LEX_005.value,
                        "message": f"Duplikasi UUID '{ent.uuid}' terdeteksi.",
                    }
                )
            seen_uuids.add(ent.uuid)

            self._verify_element_geometry_invariants(ent)
       
        for rel in validated_bundle.relationships:
            if rel.source not in seen_uuids:
                self._errors.append(
                    {
                        "error_code": ErrorCode.LEX_004.value,
                        "message": f"Relasi source '{rel.source}' tidak terdaftar di entitas.",
                    }
                )
            if rel.target not in seen_uuids:
                self._errors.append(
                    {
                        "error_code": ErrorCode.LEX_004.value,
                        "message": f"Relasi target '{rel.target}' tidak terdaftar di entitas.",
                    }
                )
            if rel.source == rel.target:
                self._errors.append(
                    {
                        "error_code": ErrorCode.LEX_001.value,
                        "message": f"Relasi sirkular pada '{rel.source}' dilarang.",
                    }
                )

        return list(self._errors)

    def _verify_element_geometry_invariants(self, entity: EnvelopeEntityDTO) -> None:
        etype = entity.type
        geom = entity.geometry

        if etype == "Wall":
            if geom.axis_line is None or len(geom.axis_line.points) < 2:
                self._errors.append({
                    "error_code": ErrorCode.GEO_001.value,
                    "message": f"Wall '{entity.uuid}': axis_line minimal 2 titik.",
                })
            if geom.height is None or geom.height <= 0.0:
                self._errors.append({
                    "error_code": ErrorCode.GEO_002.value,
                    "message": f"Wall '{entity.uuid}': height wajib positif.",
                })
            if geom.thickness is None or geom.thickness <= 0.0:
                self._errors.append({
                    "error_code": ErrorCode.GEO_002.value,
                    "message": f"Wall '{entity.uuid}': thickness wajib positif.",
                })

        elif etype == "Column":
            for dim_name, dim_val in [("width", geom.width), ("depth", geom.depth), ("height", geom.height)]:
                if dim_val is None or dim_val <= 0.0:
                    self._errors.append({
                        "error_code": ErrorCode.GEO_002.value,
                        "message": f"Column '{entity.uuid}': {dim_name} wajib positif.",
                    })

        elif etype == "Beam":
            for dim_name, dim_val in [("width", geom.width), ("depth", geom.depth), ("length", geom.length)]:
                if dim_val is None or dim_val <= 0.0:
                    self._errors.append({
                        "error_code": ErrorCode.GEO_002.value,
                        "message": f"Beam '{entity.uuid}': {dim_name} wajib positif.",
                    })

        elif etype == "Slab":
            if geom.thickness is None or geom.thickness <= 0.0:
                self._errors.append({
                    "error_code": ErrorCode.GEO_002.value,
                    "message": f"Slab '{entity.uuid}': thickness wajib positif.",
                })
            if geom.boundary is None or len(geom.boundary.points) < 4:
                self._errors.append({
                    "error_code": ErrorCode.GEO_001.value,
                    "message": f"Slab '{entity.uuid}': boundary minimal 4 titik.",
                })

        elif etype == "Foundation":
            if geom.footprint is None or len(geom.footprint.points) < 4:
                self._errors.append({
                    "error_code": ErrorCode.GEO_001.value,
                    "message": f"Foundation '{entity.uuid}': footprint minimal 4 titik.",
                })
            if geom.depth is None or geom.depth <= 0.0:
                self._errors.append({
                    "error_code": ErrorCode.GEO_002.value,
                    "message": f"Foundation '{entity.uuid}': depth wajib positif.",
                })

        elif etype in ("Door", "Window"):
            for dim_name, dim_val in [("width", geom.width), ("height", geom.height)]:
                if dim_val is None or dim_val <= 0.0:
                    self._errors.append({
                        "error_code": ErrorCode.GEO_002.value,
                        "message": f"{etype} '{entity.uuid}': {dim_name} wajib positif.",
                    })

        elif etype == "Room":
            if geom.boundary is None or len(geom.boundary.points) < 4:
                self._errors.append({
                    "error_code": ErrorCode.GEO_001.value,
                    "message": f"Room '{entity.uuid}': boundary minimal 4 titik.",
                })

        elif etype == EnvelopeElementSubtype.FOUNDATION:
            if geom.footprint is None or len(geom.footprint.points) < 4:
                self._errors.append(
                    {
                        "error_code": ErrorCode.GEO_001.value,
                        "message": f"Foundation '{entity.uuid}': footprint minimal 4 titik.",
                    }
                )
            if geom.depth is None or geom.depth <= 0.0:
                self._errors.append(
                    {
                        "error_code": ErrorCode.GEO_002.value,
                        "message": f"Foundation '{entity.uuid}': depth wajib positif.",
                    }
                )

        elif etype in (
            EnvelopeElementSubtype.DOOR,
            EnvelopeElementSubtype.WINDOW,
        ):
            for dim_name, dim_val in [
                ("width", geom.width),
                ("height", geom.height),
            ]:
                if dim_val is None or dim_val <= 0.0:
                    self._errors.append(
                        {
                            "error_code": ErrorCode.GEO_002.value,
                            "message": f"{etype.value} '{entity.uuid}': {dim_name} wajib positif.",
                        }
                    )

        elif etype == EnvelopeElementSubtype.ROOM:
            if geom.boundary is None or len(geom.boundary.points) < 4:
                self._errors.append(
                    {
                        "error_code": ErrorCode.GEO_001.value,
                        "message": f"Room '{entity.uuid}': boundary minimal 4 titik.",
                    }
                )