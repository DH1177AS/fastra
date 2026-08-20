
"""
Stage 7: Quantity Engine - Full compliance dengan interseksi dan detail perhitungan.
"""
from typing import Dict, Any, List, Optional
from collections import defaultdict
from fastra_core.ccm.physical import Wall, Column, Beam, Slab, Foundation, Roof, Door, Window, Stair, Ramp
from fastra_core.ccm.spatial import Room

class QuantityEngine:
    def __init__(self):
        self.items = []
        self.warnings = []

    def process(self, entities: Dict[str, Any], adjacency: Optional[Dict[str, List[tuple]]] = None) -> List[Dict]:
        adjacency = adjacency or {}
        for uid, ent in entities.items():
            if isinstance(ent, Wall):
                self._wall(uid, ent, entities, adjacency)
            elif isinstance(ent, Column):
                self._column(uid, ent)
            elif isinstance(ent, Beam):
                self._beam(uid, ent, entities, adjacency)
            elif isinstance(ent, Slab):
                self._slab(uid, ent, entities, adjacency)
            elif isinstance(ent, Foundation):
                self._foundation(uid, ent)
            elif isinstance(ent, Roof):
                self._roof(uid, ent)
            elif isinstance(ent, Door):
                self._door(uid, ent)
            elif isinstance(ent, Window):
                self._window(uid, ent)
            elif isinstance(ent, Stair):
                self.items.append({"entity_id": uid, "work_item_code": "PEK.STR.041",
                                   "description": f"Bekisting Tangga - {ent.name}",
                                   "quantity": ent.area.value, "unit": "m²",
                                   "detail": f"Area tangga {ent.area.value} m²"})
            elif isinstance(ent, Ramp):
                self.items.append({"entity_id": uid, "work_item_code": "PEK.STR.007",
                                   "description": f"Bekisting Ramp - {ent.name}",
                                   "quantity": ent.area.value, "unit": "m²",
                                   "detail": f"Area ramp {ent.area.value} m²"})
            elif isinstance(ent, Room):
                self._room(uid, ent)
        return self._aggregate()

    def _wall(self, uid, w: Wall, entities=None, adjacency=None):
        gross = w.gross_area.value
        deductions = []
        for op in w.openings:
            area = op.width.value * op.height.value
            if area > 0.5:
                deductions.append((f"Deduct {op.opening_type} {op.width.value}x{op.height.value}", area))
        total_ded = sum(area for _, area in deductions)
        net = max(0, gross - total_ded)
        detail = f"Gross: {w.gross_area.value} m²; " + "; ".join(f"{d[0]} = {d[1]} m²" for d in deductions) + f"; Net: {net} m²"
        self.items.append({"entity_id": uid, "work_item_code": "PEK.DIND.001",
                           "description": f"Pasangan Dinding {w.name}", "quantity": net, "unit": "m²", "detail": detail})
        adjacent_count = sum(1 for rel, _ in (adjacency or {}).get(uid, []) if rel == "WALL_ADJACENT")
        contact_deduction = adjacent_count * w.height.value * w.thickness.value
        plaster = max(0, net * 2 - contact_deduction)
        self.items.append({"entity_id": uid, "work_item_code": "PEK.DIND.002",
                           "description": f"Plesteran {w.name}", "quantity": plaster, "unit": "m²",
                           "detail": f"Net wall area {net} m² × 2 = {plaster} m²"})
        self.items.append({"entity_id": uid, "work_item_code": "PEK.DIND.003",
                           "description": f"Acian {w.name}", "quantity": plaster, "unit": "m²",
                           "detail": f"Sama dengan plesteran: {plaster} m²"})

    def _column(self, uid, c: Column):
        vol = c.volume.value
        self.items.append({"entity_id": uid, "work_item_code": "PEK.STR.001",
                           "description": f"Bekisting Kolom {c.name}", "quantity": c.bekisting_area.value, "unit": "m²",
                           "detail": f"Perimeter {2*(c.width.value+c.depth.value)} m × height {c.height.value} m"})
        self.items.append({"entity_id": uid, "work_item_code": "PEK.STR.002",
                           "description": f"Pembesian Kolom {c.name}", "quantity": vol * 185, "unit": "kg",
                           "detail": f"Volume {vol} m³ × 185 kg/m³"})
        self.items.append({"entity_id": uid, "work_item_code": "PEK.STR.003",
                           "description": f"Beton Kolom {c.name}", "quantity": vol, "unit": "m³",
                           "detail": f"Gross volume {vol} m³"})

    def _beam(self, uid, b: Beam, entities, adjacency):
        vol = b.volume.value
        intersection = 0.0
        for rel, target_id in adjacency.get(uid, []):
            if rel in ("SUPPORTS", "INVERSE_SUPPORTS", "CONNECTED_TO", "INVERSE_CONNECTED_TO"):
                target = entities.get(target_id)
                if isinstance(target, Column):
                    intersection += target.width.value * target.depth.value * b.depth.value
        net_vol = max(0, vol - intersection)
        detail = f"Gross {vol} m³ - intersection {intersection} m³ = {net_vol} m³"
        self.items.append({"entity_id": uid, "work_item_code": "PEK.STR.004",
                           "description": f"Bekisting Balok {b.name}", "quantity": (2*b.depth.value + b.width.value)*b.length.value, "unit": "m²",
                           "detail": f"(2×{b.depth.value}+{b.width.value}) × {b.length.value} m"})
        self.items.append({"entity_id": uid, "work_item_code": "PEK.STR.005",
                           "description": f"Pembesian Balok {b.name}", "quantity": vol * 200, "unit": "kg",
                           "detail": f"Volume {vol} m³ × 200 kg/m³"})
        self.items.append({"entity_id": uid, "work_item_code": "PEK.STR.006",
                           "description": f"Beton Balok {b.name}", "quantity": net_vol, "unit": "m³", "detail": detail})

    def _slab(self, uid, s: Slab, entities, adjacency):
        vol = s.volume.value
        # Interseksi slab-beam: kurangi volume beam yang menyatu
        intersection = 0.0
        for rel, target_id in adjacency.get(uid, []):
            if rel in ("SUPPORTS", "INVERSE_SUPPORTS"):
                target = entities.get(target_id)
                if isinstance(target, Beam):
                    # Hanya beam yang benar-benar menonjol di bawah slab yang memotong volume slab
                    if target.depth.value > s.thickness.value:
                        intersection += target.width.value * (target.depth.value - s.thickness.value) * target.length.value
        net_vol = max(0, vol - intersection)
        detail = f"Gross {vol} m³ - slab-beam intersection {intersection} m³ = {net_vol} m³"
        self.items.append({"entity_id": uid, "work_item_code": "PEK.STR.007",
                           "description": f"Bekisting Plat {s.name}", "quantity": s.area.value, "unit": "m²",
                           "detail": f"Slab area {s.area.value} m²"})
        self.items.append({"entity_id": uid, "work_item_code": "PEK.STR.008",
                           "description": f"Pembesian Plat {s.name}", "quantity": vol * 150, "unit": "kg",
                           "detail": f"Volume {vol} m³ × 150 kg/m³"})
        self.items.append({"entity_id": uid, "work_item_code": "PEK.STR.009",
                           "description": f"Beton Plat {s.name}", "quantity": net_vol, "unit": "m³", "detail": detail})

    def _foundation(self, uid, f: Foundation):
        vol = f.volume.value
        code = "PEK.FND.001" if f.foundation_type == "BATU_KALI" else "PEK.FND.002"
        self.items.append({"entity_id": uid, "work_item_code": code,
                           "description": f"Pondasi {f.name}", "quantity": vol, "unit": "m³",
                           "detail": f"Volume {vol} m³"})
        self.items.append({"entity_id": uid, "work_item_code": "PEK.FND.002",
                           "description": f"Pembesian Pondasi {f.name}", "quantity": vol * 150, "unit": "kg",
                           "detail": f"Volume {vol} m³ × 150 kg/m³"})

    def _roof(self, uid, r: Roof):
        area = r.area.value
        self.items.append({"entity_id": uid, "work_item_code": "PEK.ATP.001",
                           "description": f"Rangka Atap {r.name}", "quantity": area, "unit": "m²",
                           "detail": f"Roof area {area} m²"})
        self.items.append({"entity_id": uid, "work_item_code": "PEK.ATP.002",
                           "description": f"Penutup Atap {r.name}", "quantity": area, "unit": "m²",
                           "detail": f"Roof area {area} m²"})

    def _door(self, uid, d: Door):
        self.items.append({"entity_id": uid, "work_item_code": "PEK.PTU.001",
                           "description": f"Pemasangan Pintu {d.name}", "quantity": 1, "unit": "unit",
                           "detail": f"1 unit pintu {d.door_type}"})
        self.items.append({"entity_id": uid, "work_item_code": "PEK.PTU.002",
                           "description": f"Finishing Pintu {d.name}", "quantity": d.area.value, "unit": "m²",
                           "detail": f"Pintu area {d.area.value} m²"})

    def _window(self, uid, w: Window):
        self.items.append({"entity_id": uid, "work_item_code": "PEK.JND.001",
                           "description": f"Pemasangan Jendela {w.name}", "quantity": 1, "unit": "unit",
                           "detail": f"1 unit jendela {w.window_type}"})
        self.items.append({"entity_id": uid, "work_item_code": "PEK.JND.002",
                           "description": f"Finishing Jendela {w.name}", "quantity": w.area.value, "unit": "m²",
                           "detail": f"Jendela area {w.area.value} m²"})

    def _room(self, uid, r: Room):
        area = r.area.value
        self.items.append({"entity_id": uid, "work_item_code": "PEK.LNT.001",
                           "description": f"Keramik Lantai {r.name}", "quantity": area, "unit": "m²",
                           "detail": f"Room area {area} m²"})
        self.items.append({"entity_id": uid, "work_item_code": "PEK.PLF.001",
                           "description": f"Plafon Gypsum {r.name}", "quantity": area, "unit": "m²",
                           "detail": f"Room area {area} m²"})

    def _aggregate(self):
        agg = defaultdict(lambda: {"quantity": 0.0, "unit": "", "source_entities": [], "descriptions": [], "details": []})
        for item in self.items:
            key = item["work_item_code"]
            agg[key]["quantity"] += item["quantity"]
            agg[key]["unit"] = item["unit"]
            if item["entity_id"] not in agg[key]["source_entities"]:
                agg[key]["source_entities"].append(item["entity_id"])
            agg[key]["descriptions"].append(item["description"])
            agg[key]["details"].append(item.get("detail", ""))
        result = []
        for code, data in agg.items():
            result.append({
                "work_item_code": code,
                "description": " | ".join(data["descriptions"][:3]) + (" ..." if len(data["descriptions"])>3 else ""),
                "quantity": round(data["quantity"], 4),
                "unit": data["unit"],
                "source_entities": data["source_entities"],
                "detail": " | ".join(data["details"][:3]) + (" ..." if len(data["details"])>3 else ""),
            })
        return result
