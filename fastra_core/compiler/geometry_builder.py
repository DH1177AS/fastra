# fastra_core\compiler\geometry_builder.py

from __future__ import annotations

import logging
from typing import Any, Dict, List

from fastra_core.ccm.physical import (
    Beam,
    Column,
    Foundation,
    Roof,
    Slab,
    Wall,
)

logger = logging.getLogger(__name__)


class GeometryBuilder:
    def __init__(self) -> None:
        self._errors: List[Dict[str, Any]] = []
        self._warnings: List[Dict[str, Any]] = []

    @property
    def warnings(self) -> List[Dict[str, Any]]:
        return list(self._warnings)

    def validate(self, entities: Dict[str, Any]) -> List[Dict[str, Any]]:
        self._errors.clear()
        self._warnings.clear()

        for uid, ent in entities.items():
            try:
                self._validate_single_entity(uid, ent)
            except Exception as exc:
                logger.exception("Gagal memvalidasi entitas %s", uid)
                self._errors.append({
                    "error_code": "GEO-001",
                    "message": f"Crash saat validasi entitas {uid}: {str(exc)}",
                })

        return self._errors

    def _validate_single_entity(self, uid: str, ent: Any) -> None:
        if isinstance(ent, Wall):
            try:
                gross_area = float(ent.calculate_gross_area().value)
            except Exception:
                gross_area = 0.0
            if gross_area <= 0:
                self._errors.append({
                    "error_code": "GEO-003",
                    "message": f"Wall area nol atau negatif (entity: {uid})",
                })
        elif isinstance(ent, Column):
            try:
                volume = float(ent.calculate_volume().value)
            except Exception:
                volume = 0.0
            if volume <= 0:
                self._errors.append({
                    "error_code": "GEO-003",
                    "message": f"Column volume nol atau negatif (entity: {uid})",
                })
        elif isinstance(ent, Beam):
            try:
                volume = float(ent.calculate_volume().value)
            except Exception:
                volume = 0.0
            if volume <= 0:
                self._errors.append({
                    "error_code": "GEO-003",
                    "message": f"Beam volume nol atau negatif (entity: {uid})",
                })
        elif isinstance(ent, Slab):
            try:
                area = float(ent.calculate_area().value)
                volume = float(ent.calculate_volume().value)
            except Exception:
                area = 0.0
                volume = 0.0
            if area <= 0 or volume <= 0:
                self._errors.append({
                    "error_code": "GEO-003",
                    "message": f"Slab area/volume nol atau negatif (entity: {uid})",
                })
        elif isinstance(ent, Foundation):
            try:
                volume = float(ent.calculate_volume().value)
            except Exception:
                volume = 0.0
            if volume <= 0:
                self._errors.append({
                    "error_code": "GEO-003",
                    "message": f"Foundation volume nol atau negatif (entity: {uid})",
                })
        elif isinstance(ent, Roof):
            try:
                area = float(ent.calculate_projected_area().value)
            except Exception:
                area = 0.0
            if area <= 0:
                self._errors.append({
                    "error_code": "GEO-003",
                    "message": f"Roof area nol atau negatif (entity: {uid})",
                })
        else:
            logger.debug("Entitas %s dengan tipe %s dilewati oleh GeometryBuilder", uid, type(ent).__name__)