"""
ACES-000 §10.3: Operasi solid sederhana.
Representasi solid: kumpulan permukaan (mesh) atau primitif sederhana.
Untuk tahap awal, kita gunakan bounding box & volume sederhana untuk balok.
"""

from dataclasses import dataclass
from typing import List
from fastra_core.spatial.coordinate import Coordinate
from fastra_core.primitives.volume import Volume
from fastra_core.primitives.area import Area

@dataclass
class BoundingBox:
    min: Coordinate
    max: Coordinate

    def volume(self) -> Volume:
        dx = self.max.x - self.min.x
        dy = self.max.y - self.min.y
        dz = self.max.z - self.min.z
        if dx <= 0 or dy <= 0 or dz <= 0:
            return Volume(0.0)
        return Volume(dx * dy * dz)

    def surface_area(self) -> Area:
        dx = max(0, self.max.x - self.min.x)
        dy = max(0, self.max.y - self.min.y)
        dz = max(0, self.max.z - self.min.z)
        return Area(2 * (dx*dy + dx*dz + dy*dz))

    @classmethod
    def from_points(cls, points: List[Coordinate]) -> 'BoundingBox':
        if not points:
            raise ValueError("Tidak bisa membuat bounding box dari list kosong")
        min_x = min(p.x for p in points)
        min_y = min(p.y for p in points)
        min_z = min(p.z for p in points)
        max_x = max(p.x for p in points)
        max_y = max(p.y for p in points)
        max_z = max(p.z for p in points)
        return cls(Coordinate(min_x, min_y, min_z), Coordinate(max_x, max_y, max_z))

# Fungsi-fungsi solid (intersection/union) untuk primitif balok sederhana:
def intersect_box(b1: BoundingBox, b2: BoundingBox) -> BoundingBox:
    min_x = max(b1.min.x, b2.min.x)
    min_y = max(b1.min.y, b2.min.y)
    min_z = max(b1.min.z, b2.min.z)
    max_x = min(b1.max.x, b2.max.x)
    max_y = min(b1.max.y, b2.max.y)
    max_z = min(b1.max.z, b2.max.z)
    if min_x >= max_x or min_y >= max_y or min_z >= max_z:
        return BoundingBox(Coordinate(0,0,0), Coordinate(0,0,0))  # empty
    return BoundingBox(Coordinate(min_x, min_y, min_z), Coordinate(max_x, max_y, max_z))

def union_box(b1: BoundingBox, b2: BoundingBox) -> BoundingBox:
    return BoundingBox.from_points([b1.min, b1.max, b2.min, b2.max])