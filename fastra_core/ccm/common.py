from dataclasses import dataclass
from typing import Optional, List
from fastra_core.primitives.length import Length
from fastra_core.spatial.coordinate import Coordinate
from fastra_core.spatial.vector import Vector
from fastra_core.primitives.angle import Angle

@dataclass
class Opening:
    width: Length
    height: Length
    position: Length
    opening_type: str = "DOOR"

    def __post_init__(self):
        if self.width.value <= 0:
            raise ValueError("Lebar bukaan harus > 0")
        if self.height.value <= 0:
            raise ValueError("Tinggi bukaan harus > 0")
        if self.position.value < 0:
            raise ValueError("Posisi bukaan tidak boleh negatif")

@dataclass
class ReinforcementSpec:
    main_diameter: Length
    main_quantity: int
    main_grade: str = "BJTS 420"
    stirrup_diameter: Optional[Length] = None
    stirrup_spacing: Optional[Length] = None
    cover: Length = Length(0.04)

    def __post_init__(self):
        if self.main_diameter.value <= 0:
            raise ValueError("Diameter besi utama harus > 0")
        if self.main_quantity <= 0:
            raise ValueError("Jumlah besi utama harus > 0")
        if self.cover.value < 0:
            raise ValueError("Cover tidak boleh negatif")

@dataclass
class FinishSpec:
    finish_type: str
    material_id: Optional[str] = None
    thickness: Optional[Length] = None
    area: Optional[float] = None

    def __post_init__(self):
        valid = ["PLESTER", "ACIAN", "CAT", "KERAMIK", "GYPSUM", "EXPOSED"]
        if self.finish_type not in valid:
            raise ValueError(f"Finish type tidak valid: {self.finish_type}")
        if self.thickness is not None and self.thickness.value < 0:
            raise ValueError("Thickness finish tidak boleh negatif")
        if self.area is not None and self.area < 0:
            raise ValueError("Area finish tidak boleh negatif")
