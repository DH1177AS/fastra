
"""
Stage 3: Geometry Builder - Validasi geometri & gross quantity.
"""
from typing import Dict, Any
from fastra_core.ccm.physical import Wall, Column, Beam, Slab, Foundation, Roof

class GeometryBuilder:
    def __init__(self):
        self.errors = []
        self.warnings = []

    def validate(self, entities: Dict[str, Any]):
        for uid, ent in entities.items():
            try:
                if isinstance(ent, Wall):
                    if ent.gross_area.value <= 0:
                        self.errors.append({"error_code": "GEO-003", "entity_uuid": uid, "message": "Wall area nol"})
                elif isinstance(ent, Column):
                    if ent.volume.value <= 0:
                        self.errors.append({"error_code": "GEO-003", "entity_uuid": uid, "message": "Column volume nol"})
                elif isinstance(ent, Beam):
                    if ent.volume.value <= 0:
                        self.errors.append({"error_code": "GEO-003", "entity_uuid": uid, "message": "Beam volume nol"})
                elif isinstance(ent, Slab):
                    if ent.area.value <= 0 or ent.volume.value <= 0:
                        self.errors.append({"error_code": "GEO-003", "entity_uuid": uid, "message": "Slab area/volume nol"})
                elif isinstance(ent, Foundation):
                    if ent.volume.value <= 0:
                        self.errors.append({"error_code": "GEO-003", "entity_uuid": uid, "message": "Foundation volume nol"})
                elif isinstance(ent, Roof):
                    if ent.area.value <= 0:
                        self.errors.append({"error_code": "GEO-003", "entity_uuid": uid, "message": "Roof area nol"})
            except Exception as ex:
                self.errors.append({"error_code": "GEO-001", "entity_uuid": uid, "message": str(ex)})
        return self.errors
