# fastra_core/geometry/solid.py

from __future__ import annotations

import logging
import math
from typing import Any, List

from pydantic import BaseModel, ConfigDict, Field, model_validator

from fastra_core.spatial.coordinate import Coordinate
from fastra_core.primitives.volume import Volume
from fastra_core.primitives.area import Area

logger = logging.getLogger("fastra.geometry.solid")


class BoundingBox(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        strict=True,
        frozen=True,
        allow_inf_nan=False,
        arbitrary_types_allowed=True,  # Izinkan tipe custom Coordinate
    )

    def __init__(self, *args, **kwargs):
        if args:
            if len(args) > 2:
                raise TypeError("BoundingBox only accepts up to two positional arguments (min, max)")
            names = ['min', 'max']
            for i, val in enumerate(args):
                kwargs.setdefault(names[i], val)
        super().__init__(**kwargs)

    min: Coordinate = Field(..., description="Titik batas koordinat minimum (South-West-Bottom)")
    max: Coordinate = Field(..., description="Titik batas koordinat maksimum (North-East-Top)")

    @model_validator(mode="after")
    def verify_spatial_directional_sanity(self) -> "BoundingBox":
        if self.max.x < self.min.x:
            raise ValueError("SPATIAL_INVERSION_DETECTED_MAX_X_CANNOT_BE_LESS_THAN_MIN_X")
        if self.max.y < self.min.y:
            raise ValueError("SPATIAL_INVERSION_DETECTED_MAX_Y_CANNOT_BE_LESS_THAN_MIN_Y")
        if self.max.z < self.min.z:
            raise ValueError("SPATIAL_INVERSION_DETECTED_MAX_Z_CANNOT_BE_LESS_THAN_MIN_Z")
        return self

    def volume(self) -> Volume:
        dx = self.max.x - self.min.x
        dy = self.max.y - self.min.y
        dz = self.max.z - self.min.z

        if dx <= 0.0 or dy <= 0.0 or dz <= 0.0:
            return Volume(value=0.0)

        calculated_volume = dx * dy * dz
        if math.isnan(calculated_volume) or math.isinf(calculated_volume):
            raise ValueError("NUMERIC_ANOMALY_DETECTED_BOUNDING_BOX_VOLUME_CORRUPTED")

        return Volume(value=calculated_volume)

    def surface_area(self) -> Area:
        dx = max(0.0, self.max.x - self.min.x)
        dy = max(0.0, self.max.y - self.min.y)
        dz = max(0.0, self.max.z - self.min.z)

        calculated_area = 2.0 * (dx * dy + dx * dz + dy * dz)
        if math.isnan(calculated_area) or math.isinf(calculated_area):
            raise ValueError("NUMERIC_ANOMALY_DETECTED_BOUNDING_BOX_SURFACE_AREA_CORRUPTED")

        return Area(value=calculated_area)

    @classmethod
    def from_points(cls, points: Any) -> "BoundingBox":
        if not isinstance(points, list):
            raise TypeError("POINTS_INPUT_MUST_BE_A_VALID_LIST_OF_COORDINATES")
        if not points:
            raise ValueError("QUANTITY_CONSTRAINT_VIOLATION_CANNOT_CONSTRUCT_BOUNDING_BOX_FROM_EMPTY_LIST")

        for idx, vertex in enumerate(points):
            if not isinstance(vertex, Coordinate):
                raise TypeError(f"POINT_ELEMENT_AT_INDEX_{idx}_MUST_BE_A_PURE_COORDINATE_INSTANCE")

        first_point = points[0]
        min_x, max_x = first_point.x, first_point.x
        min_y, max_y = first_point.y, first_point.y
        min_z, max_z = first_point.z, first_point.z

        for p in points[1:]:
            x, y, z = p.x, p.y, p.z
            if x < min_x:
                min_x = x
            if x > max_x:
                max_x = x
            if y < min_y:
                min_y = y
            if y > max_y:
                max_y = y
            if z < min_z:
                min_z = z
            if z > max_z:
                max_z = z

        return cls(
            min=Coordinate(x=min_x, y=min_y, z=min_z),
            max=Coordinate(x=max_x, y=max_y, z=max_z),
        )


def intersect_box(b1: Any, b2: Any) -> BoundingBox:
    if not isinstance(b1, BoundingBox) or not isinstance(b2, BoundingBox):
        raise TypeError("SOLID_OPERATION_VIOLATION_OPERANDS_MUST_BE_PURE_BOUNDING_BOX_INSTANCES")

    min_x = max(b1.min.x, b2.min.x)
    min_y = max(b1.min.y, b2.min.y)
    min_z = max(b1.min.z, b2.min.z)

    max_x = min(b1.max.x, b2.max.x)
    max_y = min(b1.max.y, b2.max.y)
    max_z = min(b1.max.z, b2.max.z)

    if min_x >= max_x or min_y >= max_y or min_z >= max_z:
        zero_coord = Coordinate(x=0.0, y=0.0, z=0.0)
        return BoundingBox(min=zero_coord, max=zero_coord)

    return BoundingBox(
        min=Coordinate(x=min_x, y=min_y, z=min_z),
        max=Coordinate(x=max_x, y=max_y, z=max_z),
    )


def union_box(b1: Any, b2: Any) -> BoundingBox:
    if not isinstance(b1, BoundingBox) or not isinstance(b2, BoundingBox):
        raise TypeError("SOLID_OPERATION_VIOLATION_OPERANDS_MUST_BE_PURE_BOUNDING_BOX_INSTANCES")

    return BoundingBox.from_points([b1.min, b1.max, b2.min, b2.max])