# mypy: ignore-errors
from fastra_core.numerical.geometry import point_in_polygon

"""
Stage 2: Parser - Ubah CCM entities menjadi object graph.
"""
from typing import Dict, Any, List
from fastra_core.compiler.ccm_envelope import CCMEnvelope
from fastra_core.ccm.physical import Wall, Column, Beam, Slab, Foundation, Roof, Door, Window, Stair, Ramp
from fastra_core.ccm.spatial import Room, Zone
from fastra_core.ccm.common import Opening
from fastra_core.primitives.length import Length
from fastra_core.primitives.angle import Angle
from fastra_core.spatial.coordinate import Coordinate

class Parser:
    def __init__(self):
        self.entities: Dict[str, Any] = {}
        self.graph: Dict[str, List[tuple]] = {}
        self.errors = []
        self.warnings = []

    def parse(self, envelope: CCMEnvelope):
        # Build lookup
        lookup = {}
        for e in envelope.entities:
            uid = e.get("uuid")
            if uid:
                lookup[uid] = e

        # Relationships
        for rel in envelope.relationships:
            src = rel.get("source"); tgt = rel.get("target"); rel_type = rel.get("type")
            if src and tgt:
                self.graph.setdefault(src, []).append((rel_type, tgt))

        # Convert entities
        for e in envelope.entities:
            uid = e.get("uuid")
            t = e.get("type")
            ent: Any = None
            try:
                if t == "Wall":
                    axis = [Coordinate(p["x"], p["y"], p.get("z",0)) for p in e["geometry"]["axis_line"]["points"]]
                    height = Length(e["geometry"]["height"])
                    thickness = Length(e["geometry"].get("thickness", 0.15))
                    openings = []
                    for op in e.get("openings", []):
                        openings.append(Opening(
                            width=Length(op["width"]),
                            height=Length(op["height"]),
                            position=Length(op.get("position", 0)),
                            opening_type=op.get("type", "DOOR")
                        ))
                    ent = Wall(uuid=uid, name=e.get("name",""), axis_line=axis,
                               height=height, thickness=thickness,
                               construction_type=e.get("construction_type","BATA_MERAH"),
                               openings=openings)
                elif t == "Column":
                    ent = Column(uuid=uid, name=e.get("name",""),
                                 width=Length(e["geometry"].get("width",0.3)),
                                 depth=Length(e["geometry"].get("depth",0.3)),
                                 height=Length(e["geometry"]["height"]))
                elif t == "Beam":
                    ent = Beam(uuid=uid, name=e.get("name",""),
                               width=Length(e["geometry"].get("width",0.25)),
                               depth=Length(e["geometry"].get("depth",0.4)),
                               length=Length(e["geometry"]["length"]),
                               start_connection=e.get("start_connection"),
                               end_connection=e.get("end_connection"))
                elif t == "Slab":
                    pts = [Coordinate(p["x"], p["y"], p.get("z",0)) for p in e["geometry"]["boundary"]["points"]]
                    ent = Slab(uuid=uid, name=e.get("name",""), boundary=pts,
                               thickness=Length(e["geometry"]["thickness"]),
                               supports=e.get("supports", []))
                elif t == "Foundation":
                    pts = [Coordinate(p["x"], p["y"], p.get("z",0)) for p in e["geometry"]["footprint"]["points"]]
                    ent = Foundation(uuid=uid, name=e.get("name",""), footprint=pts,
                                     depth=Length(e["geometry"]["depth"]),
                                     foundation_type=e.get("foundation_type","FOOTPLATE"))
                elif t == "Roof":
                    pts = [Coordinate(p["x"], p["y"], p.get("z",0)) for p in e["geometry"]["footprint"]["points"]]
                    ent = Roof(uuid=uid, name=e.get("name",""), footprint=pts,
                               slope=Angle(e["geometry"]["slope"]))
                elif t == "Door":
                    ent = Door(uuid=uid, name=e.get("name",""),
                               width=Length(e["geometry"]["width"]),
                               height=Length(e["geometry"]["height"]),
                               door_type=e.get("door_type","SINGLE"),
                               host_wall=e.get("host_wall"),
                               position_on_wall=Length(e.get("position_on_wall", 0)))
                elif t == "Window":
                    ent = Window(uuid=uid, name=e.get("name",""),
                                 width=Length(e["geometry"]["width"]),
                                 height=Length(e["geometry"]["height"]),
                                 sill_height=Length(e["geometry"].get("sill_height",0.9)),
                                 window_type=e.get("window_type","CASEMENT"),
                                 host_wall=e.get("host_wall"),
                                 position_on_wall=Length(e.get("position_on_wall", 0)))
                elif t == "Stairs":
                    ent = Stair(uuid=uid, name=e.get("name",""),
                                number_of_risers=e["geometry"]["number_of_risers"],
                                riser_height=Length(e["geometry"]["riser_height"]),
                                tread_depth=Length(e["geometry"]["tread_depth"]),
                                width=Length(e["geometry"]["width"]))
                elif t == "Ramp":
                    ent = Ramp(uuid=uid, name=e.get("name",""),
                               length=Length(e["geometry"]["length"]),
                               width=Length(e["geometry"]["width"]),
                               slope=Angle(e["geometry"]["slope"]))
                elif t == "Room":
                    pts = [Coordinate(p["x"], p["y"], p.get("z",0)) for p in e["geometry"]["boundary"]["points"]]
                    ent = Room(uuid=uid, name=e.get("name",""), boundary=pts,
                               room_type=e.get("room_type","LIVING"))
                else:
                    self.warnings.append(f"Skip unknown type {t}")
                    continue
                self.entities[uid] = ent
            except Exception as ex:
                self.errors.append({"error_code": "PAR-002", "message": f"Entity {uid}: {ex}"})
        # Bangun relasi CONTAINS dari Room ke Door/Window (jika berada di dalam)
        for ruid, rent in list(self.entities.items()):
            if isinstance(rent, Room):
                for duid, dent in list(self.entities.items()):
                    if isinstance(dent, (Door, Window)) and dent.host_wall:
                        wall = self.entities.get(dent.host_wall)
                        if wall and isinstance(wall, Wall) and wall.axis_line:
                            # Hitung posisi global sederhana: asumsi axis_line garis lurus
                            start = wall.axis_line[0]
                            end = wall.axis_line[-1]
                            total_len = start.distance_to(end).value
                            pos = dent.position_on_wall.value
                            if total_len > 0:
                                t = pos / total_len
                                t = max(0, min(1, t))
                                px = start.x + (end.x - start.x) * t
                                py = start.y + (end.y - start.y) * t
                                pz = start.z + (end.z - start.z) * t
                                point = Coordinate(px, py, pz)
                                try:
                                    if point_in_polygon(rent.boundary, point):
                                        self.graph.setdefault(ruid, []).append(("CONTAINS", duid))
                                except Exception as ex:
                                    self.warnings.append(f"CONTAINS point_in_polygon skip: {ex}")
        return self.entities, self.graph

