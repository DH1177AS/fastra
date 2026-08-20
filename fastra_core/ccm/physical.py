from dataclasses import dataclass, field
from typing import List, Optional
from fastra_core.ontology.universal_object import UniversalObject
from fastra_core.ontology.entity_type import EntityType
from fastra_core.primitives.length import Length
from fastra_core.primitives.area import Area
from fastra_core.primitives.volume import Volume
from fastra_core.primitives.angle import Angle
from fastra_core.spatial.coordinate import Coordinate
from fastra_core.spatial.vector import Vector
from fastra_core.ccm.common import Opening, ReinforcementSpec, FinishSpec


def _ensure_closed(points: List[Coordinate], epsilon: float = 1e-6) -> List[Coordinate]:
    """Salin list titik dan pastikan tertutup (titik pertama == terakhir)."""
    if not points:
        return points
    pts = list(points)
    if pts[0] != pts[-1]:
        pts.append(pts[0])
    return pts


@dataclass
class Wall(UniversalObject):
    axis_line: List[Coordinate] = field(default_factory=list)
    height: Length = Length(0)
    thickness: Length = Length(0.15)
    structural_type: str = "NON_LOAD_BEARING"
    construction_type: str = "BATA_MERAH"
    base_elevation: Length = Length(0)
    openings: List[Opening] = field(default_factory=list)
    finish: Optional[FinishSpec] = None
    entity_type: EntityType = EntityType.PHYSICAL

    def __post_init__(self):
        super().__post_init__()
        if self.height.value <= 0:
            raise ValueError("Tinggi dinding harus > 0")
        if self.thickness.value <= 0:
            raise ValueError("Ketebalan dinding harus > 0")
        if len(self.axis_line) < 2:
            raise ValueError("Wall axis_line minimal 2 titik")
        # Constraint: total luas bukaan < luas dinding
        gross = self.gross_area.value
        total_opening = sum(op.width.value * op.height.value for op in self.openings)
        if total_opening > gross:
            raise ValueError("Total luas bukaan tidak boleh melebihi luas dinding")
        valid_construction_types = {"BATA_MERAH", "BATA_RINGAN", "BETON_BERTULANG", "KAYU", "GYPSUM", "PARTISI"}
        if self.construction_type not in valid_construction_types:
            raise ValueError(f"construction_type tidak valid: {self.construction_type}")
        valid_structural_types = {"LOAD_BEARING", "NON_LOAD_BEARING", "SHEAR", "RETAINING"}
        if self.structural_type not in valid_structural_types:
            raise ValueError(f"structural_type tidak valid: {self.structural_type}")

    @property
    def gross_area(self) -> Area:
        if not self.axis_line:
            return Area(0)
        total_length = sum(
            self.axis_line[i].distance_to(self.axis_line[i + 1]).value
            for i in range(len(self.axis_line) - 1)
        )
        return Area(total_length * self.height.value)


@dataclass
class Column(UniversalObject):
    width: Length = Length(0.3)
    depth: Length = Length(0.3)
    height: Length = Length(0)
    base_elevation: Length = Length(0)
    structural_type: str = "KOLOM_STRUKTUR"
    material_id: Optional[str] = None
    reinforcement: Optional[ReinforcementSpec] = None
    entity_type: EntityType = EntityType.PHYSICAL

    def __post_init__(self):
        super().__post_init__()
        if self.width.value <= 0:
            raise ValueError("Lebar kolom harus > 0")
        if self.depth.value <= 0:
            raise ValueError("Depth kolom harus > 0")
        if self.height.value <= 0:
            raise ValueError("Tinggi kolom harus > 0")
        # Invariant: base_elevation < top_elevation
        if self.base_elevation.value >= self.base_elevation.value + self.height.value:
            raise ValueError("Elevasi dasar kolom tidak valid")
        valid_structural_types = {"TIANG", "KOLOM_STRUKTUR", "KOLOM_PRAKTIS"}
        if self.structural_type not in valid_structural_types:
            raise ValueError(f"structural_type tidak valid: {self.structural_type}")

    @property
    def volume(self) -> Volume:
        return Volume(self.width.value * self.depth.value * self.height.value)

    @property
    def bekisting_area(self) -> Area:
        return Area(2 * (self.width.value + self.depth.value) * self.height.value)


@dataclass
class Beam(UniversalObject):
    width: Length = Length(0.25)
    depth: Length = Length(0.4)
    length: Length = Length(0)
    beam_type: str = "BALOK_INDUK"
    start_connection: Optional[str] = None
    end_connection: Optional[str] = None
    reinforcement: Optional[ReinforcementSpec] = None
    entity_type: EntityType = EntityType.PHYSICAL

    def __post_init__(self):
        super().__post_init__()
        if self.width.value <= 0:
            raise ValueError("Lebar balok harus > 0")
        if self.depth.value <= 0:
            raise ValueError("Depth balok harus > 0")
        if self.length.value <= 0:
            raise ValueError("Panjang balok harus > 0")
        valid_beam_types = {"SLOOF", "BALOK_INDUK", "BALOK_ANAK", "RING_BALK"}
        if self.beam_type not in valid_beam_types:
            raise ValueError(f"beam_type tidak valid: {self.beam_type}")

    @property
    def volume(self) -> Volume:
        return Volume(self.width.value * self.depth.value * self.length.value)


@dataclass
class Slab(UniversalObject):
    boundary: List[Coordinate] = field(default_factory=list)
    thickness: Length = Length(0.12)
    slab_type: str = "PLAT_LANTAI"
    elevation: Length = Length(0)
    supports: List[str] = field(default_factory=list)
    reinforcement: Optional[ReinforcementSpec] = None
    entity_type: EntityType = EntityType.PHYSICAL

    def __post_init__(self):
        super().__post_init__()
        if self.thickness.value <= 0:
            raise ValueError("Ketebalan plat harus > 0")
        if len(self.boundary) < 3:
            raise ValueError("Boundary slab minimal 3 titik")
        self.boundary = _ensure_closed(self.boundary)
        from fastra_core.geometry.polygon import is_self_intersecting
        if is_self_intersecting(self.boundary):
            raise ValueError("Boundary slab self-intersecting")
        valid_slab_types = {"PLAT_LANTAI", "PLAT_ATAP", "PLAT_CANTILEVER"}
        if self.slab_type not in valid_slab_types:
            raise ValueError(f"slab_type tidak valid: {self.slab_type}")
        if len(self.supports) < 1:
            raise ValueError("Slab supports minimal 1")

    @property
    def area(self) -> Area:
        from fastra_core.geometry.polygon import area as poly_area
        a = poly_area(self.boundary)
        if a.value <= 0:
            raise ValueError("Area slab harus > 0")
        return a

    @property
    def volume(self) -> Volume:
        v = self.area.value * self.thickness.value
        if v <= 0:
            raise ValueError("Volume slab harus > 0")
        return Volume(v)


@dataclass
class Foundation(UniversalObject):
    footprint: List[Coordinate] = field(default_factory=list)
    depth: Length = Length(1.0)
    foundation_type: str = "FOOTPLATE"
    material_id: Optional[str] = None
    entity_type: EntityType = EntityType.PHYSICAL

    def __post_init__(self):
        super().__post_init__()
        if self.depth.value <= 0:
            raise ValueError("Kedalaman pondasi harus > 0")
        if len(self.footprint) < 3:
            raise ValueError("Footprint pondasi minimal 3 titik")
        self.footprint = _ensure_closed(self.footprint)
        from fastra_core.geometry.polygon import is_self_intersecting
        if is_self_intersecting(self.footprint):
            raise ValueError("Footprint atap self-intersecting")
        from fastra_core.geometry.polygon import is_self_intersecting
        if is_self_intersecting(self.footprint):
            raise ValueError("Footprint pondasi self-intersecting")
        valid_roof_types = {"GABLE", "HIP", "FLAT", "SHED", "DOME", "CUSTOM"}
        if self.roof_type not in valid_roof_types:
            raise ValueError(f"roof_type tidak valid: {self.roof_type}")
        valid_structure_types = {"BAJA_RINGAN", "KAYU", "BAJA_BERAT", "BETON"}
        if self.structure_type not in valid_structure_types:
            raise ValueError(f"structure_type tidak valid: {self.structure_type}")
        valid_foundation_types = {"FOOTPLATE", "BATU_KALI", "BORE_PILE", "TIANG_PANCANG", "RAFT"}
        if self.foundation_type not in valid_foundation_types:
            raise ValueError(f"foundation_type tidak valid: {self.foundation_type}")

    @property
    def volume(self) -> Volume:
        from fastra_core.geometry.polygon import area as poly_area
        a = poly_area(self.footprint).value
        if a <= 0:
            raise ValueError("Area footprint pondasi harus > 0")
        v = a * self.depth.value
        if v <= 0:
            raise ValueError("Volume pondasi harus > 0")
        return Volume(v)


@dataclass
class Roof(UniversalObject):
    roof_type: str = "GABLE"
    structure_type: str = "BAJA_RINGAN"
    covering_material_id: Optional[str] = None
    slope: Angle = Angle(30)
    footprint: List[Coordinate] = field(default_factory=list)
    ridge_line: List[Coordinate] = field(default_factory=list)
    overhang: Length = Length(0.5)
    entity_type: EntityType = EntityType.PHYSICAL

    def __post_init__(self):
        super().__post_init__()
        if self.slope.value < 0 or self.slope.value > 90:
            raise ValueError("Slope harus antara 0-90 derajat")
        if len(self.footprint) < 3:
            raise ValueError("Footprint atap minimal 3 titik")
        self.footprint = _ensure_closed(self.footprint)

    @property
    def area(self) -> Area:
        from fastra_core.geometry.polygon import area as poly_area
        base_area = poly_area(self.footprint)
        import math
        slope_factor = 1.0 / max(0.01, abs(math.cos(math.radians(self.slope.value))))
        return Area(base_area.value * slope_factor)


@dataclass
class Door(UniversalObject):
    width: Length = Length(0.9)
    height: Length = Length(2.1)
    door_type: str = "SINGLE"
    material_id: Optional[str] = None
    host_wall: Optional[str] = None
    position_on_wall: Length = Length(0)
    sill_height: Length = Length(0)
    swing_direction: str = "INWARD"
    entity_type: EntityType = EntityType.PHYSICAL

    def __post_init__(self):
        super().__post_init__()
        if self.width.value <= 0:
            raise ValueError("Lebar pintu harus > 0")
        if self.height.value <= 0:
            raise ValueError("Tinggi pintu harus > 0")
        if self.sill_height.value < 0:
            raise ValueError("Sill height tidak boleh negatif")
        valid_window_types = {"CASEMENT", "SLIDING", "FIXED", "AWNING"}
        if self.window_type not in valid_window_types:
            raise ValueError(f"window_type tidak valid: {self.window_type}")
        valid_glazing = {"CLEAR", "TINTED", "REFLECTIVE", "LOW_E"}
        if self.glazing_type not in valid_glazing:
            raise ValueError(f"glazing_type tidak valid: {self.glazing_type}")
        valid_door_types = {"SINGLE", "DOUBLE", "SLIDING", "FOLDING"}
        if self.door_type not in valid_door_types:
            raise ValueError(f"door_type tidak valid: {self.door_type}")
        valid_swing = {"INWARD", "OUTWARD", "LEFT", "RIGHT"}
        if self.swing_direction not in valid_swing:
            raise ValueError(f"swing_direction tidak valid: {self.swing_direction}")

    @property
    def area(self) -> Area:
        return Area(self.width.value * self.height.value)


@dataclass
class Window(UniversalObject):
    width: Length = Length(1.2)
    height: Length = Length(1.5)
    window_type: str = "CASEMENT"
    material_id: Optional[str] = None
    host_wall: Optional[str] = None
    position_on_wall: Length = Length(0)
    sill_height: Length = Length(0.9)
    glazing_type: str = "CLEAR"
    entity_type: EntityType = EntityType.PHYSICAL

    def __post_init__(self):
        super().__post_init__()
        if self.width.value <= 0:
            raise ValueError("Lebar jendela harus > 0")
        if self.height.value <= 0:
            raise ValueError("Tinggi jendela harus > 0")
        if self.sill_height.value < 0:
            raise ValueError("Sill height tidak boleh negatif")
        valid_window_types = {"CASEMENT", "SLIDING", "FIXED", "AWNING"}
        if self.window_type not in valid_window_types:
            raise ValueError(f"window_type tidak valid: {self.window_type}")
        valid_glazing = {"CLEAR", "TINTED", "REFLECTIVE", "LOW_E"}
        if self.glazing_type not in valid_glazing:
            raise ValueError(f"glazing_type tidak valid: {self.glazing_type}")
        valid_door_types = {"SINGLE", "DOUBLE", "SLIDING", "FOLDING"}
        if self.door_type not in valid_door_types:
            raise ValueError(f"door_type tidak valid: {self.door_type}")
        valid_swing = {"INWARD", "OUTWARD", "LEFT", "RIGHT"}
        if self.swing_direction not in valid_swing:
            raise ValueError(f"swing_direction tidak valid: {self.swing_direction}")

    @property
    def area(self) -> Area:
        return Area(self.width.value * self.height.value)


@dataclass
class Stair(UniversalObject):
    number_of_risers: int = 12
    riser_height: Length = Length(0.175)
    tread_depth: Length = Length(0.28)
    width: Length = Length(1.0)
    start_elevation: Length = Length(0)
    end_elevation: Length = Length(3.5)
    structural_type: str = 'CONCRETE'
    entity_type: EntityType = EntityType.PHYSICAL

    def __post_init__(self):
        super().__post_init__()
        if self.number_of_risers <= 0:
            raise ValueError('Jumlah anak tangga harus > 0')
        if self.riser_height.value <= 0:
            raise ValueError('Tinggi riser harus > 0')
        if self.tread_depth.value <= 0:
            raise ValueError('Kedalaman tread harus > 0')
        if self.width.value <= 0:
            raise ValueError('Lebar tangga harus > 0')
        if self.end_elevation.value <= self.start_elevation.value:
            raise ValueError('Elevasi akhir tangga harus > elevasi awal')
        if self.structural_type not in {"CONCRETE", "STEEL", "WOOD"}:
            raise ValueError(f"structural_type tidak valid: {self.structural_type}")

    @property
    def total_rise(self) -> Length:
        return Length(self.number_of_risers * self.riser_height.value)

    @property
    def total_run(self) -> Length:
        return Length((self.number_of_risers - 1) * self.tread_depth.value)

    @property
    def area(self) -> Area:
        return Area(self.total_run.value * self.width.value)


@dataclass
class Ramp(UniversalObject):
    length: Length = Length(6.0)
    width: Length = Length(1.5)
    slope: Angle = Angle(10)
    start_elevation: Length = Length(0)
    end_elevation: Length = Length(0.6)
    surface_type: str = 'CONCRETE'
    handrail: bool = True
    entity_type: EntityType = EntityType.PHYSICAL

    def __post_init__(self):
        super().__post_init__()
        if self.length.value <= 0:
            raise ValueError('Panjang ramp harus > 0')
        if self.width.value <= 0:
            raise ValueError('Lebar ramp harus > 0')
        if self.slope.value < 0 or self.slope.value > 15:
            raise ValueError('Slope ramp maksimal 15 derajat')
        if self.end_elevation.value <= self.start_elevation.value:
            raise ValueError('Elevasi akhir ramp harus > elevasi awal')
        if self.surface_type not in {"CONCRETE", "ASPHALT", "PAVING"}:
            raise ValueError(f"surface_type tidak valid: {self.surface_type}")
        if not isinstance(self.handrail, bool):
            raise ValueError("handrail harus boolean")

    @property
    def area(self) -> Area:
        return Area(self.length.value * self.width.value)
