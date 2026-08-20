"""
Stage 5: Semantic Analyzer - Validasi makna teknik sesuai ACES-400 §10.
"""
from typing import Dict, Any, Optional
from fastra_core.ccm.physical import Wall, Door, Window, Beam, Column
from fastra_core.ccm.spatial import Room, Storey, Building


class SemanticAnalyzer:
    def __init__(self):
        self.errors = []
        self.warnings = []

    def analyze(self, entities: Dict[str, Any], adjacency: Optional[Dict[str, list]] = None):
        adjacency = adjacency or {}
        for uid, ent in entities.items():
            if isinstance(ent, Wall):
                for op in ent.openings:
                    if op.height.value > ent.height.value:
                        self.errors.append({"error_code": "SEM-008", "entity_uuid": uid, "message": "Opening taller than wall"})
            elif isinstance(ent, Door):
                if ent.host_wall:
                    host = entities.get(ent.host_wall)
                    if host and isinstance(host, Wall):
                        if ent.height.value > host.height.value:
                            self.errors.append({"error_code": "SEM-008", "entity_uuid": uid, "message": "Door taller than host wall"})
                        wall_length = host.gross_area.value / host.height.value
                        if ent.position_on_wall.value + ent.width.value > wall_length:
                            self.errors.append({"error_code": "SEM-009", "entity_uuid": uid, "message": "Door extends beyond wall boundary"})
                        elif ent.position_on_wall.value < 0:
                            self.errors.append({"error_code": "SEM-009", "entity_uuid": uid, "message": "Door position negative"})
            elif isinstance(ent, Window):
                if ent.host_wall:
                    host = entities.get(ent.host_wall)
                    if host and isinstance(host, Wall):
                        if ent.sill_height.value + ent.height.value > host.height.value:
                            self.errors.append({"error_code": "SEM-010", "entity_uuid": uid, "message": "Window exceeds wall height"})
            elif isinstance(ent, Room):
                if not ent.is_closed:
                    self.errors.append({"error_code": "SEM-001", "entity_uuid": uid, "message": "Room polygon not closed"})
            elif isinstance(ent, Beam):
                if not ent.start_connection:
                    self.errors.append({"error_code": "SEM-006", "entity_uuid": uid, "message": "Beam missing start connection"})
                if not ent.end_connection:
                    self.errors.append({"error_code": "SEM-007", "entity_uuid": uid, "message": "Beam missing end connection"})
            elif isinstance(ent, Column):
                # SEM-004: Column struktural tanpa beam terhubung
                if ent.structural_type == "KOLOM_STRUKTUR":
                    has_beam = any(
                        rel in ("SUPPORTS", "INVERSE_SUPPORTS", "CONNECTED_TO", "INVERSE_CONNECTED_TO")
                        for rel, _ in adjacency.get(uid, [])
                    )
                    if not has_beam:
                        self.warnings.append({"warning_code": "SEM-004", "entity_uuid": uid, "message": "Column has no connected beam"})
                    # SEM-005: Column tanpa foundation
                    has_foundation = any(
                        rel in ("SUPPORTS", "INVERSE_SUPPORTS")
                        for rel, _ in adjacency.get(uid, [])
                    )
                    if not has_foundation:
                        self.warnings.append({"warning_code": "SEM-005", "entity_uuid": uid, "message": "Column has no foundation"})
            elif isinstance(ent, Storey):
                if ent.building_id:
                    building = entities.get(ent.building_id)
                    if building and isinstance(building, Building):
                        if ent.elevation.value + ent.height.value > building.height.value:
                            self.warnings.append({"warning_code": "SEM-011", "entity_uuid": uid, "message": "Storey exceeds building height"})
        return self.errors, self.warnings
