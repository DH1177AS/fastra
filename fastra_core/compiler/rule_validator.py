"""
Stage 6: Rule Validator - Aturan konstruksi standar + SPA & QTY.
Mendukung custom rules sesuai ACES-400 Â§11.3.
"""
import ast
from typing import Dict, Any, List, Optional
from fastra_core.ccm.physical import Beam, Column, Slab, Door, Window
from fastra_core.ccm.spatial import Room


class RuleValidator:
    def __init__(self, custom_rules: Optional[List[Dict[str, Any]]] = None):
        self.errors: List[Dict[str, Any]] = []
        self.warnings: List[Dict[str, Any]] = []
        self.custom_rules = custom_rules or []



    @staticmethod
    def _evaluate_condition_safe(condition: str, context: Dict[str, Any]) -> bool:
        """Evaluasi ekspresi boolean sederhana tanpa eval/exec.

        Hanya mengizinkan struktur: Bandingkan, UnaryOp (Not), BoolOp (And/Or),
        Name (variabel yang diambil dari context), Constant, dan Attribute sederhana.
        """
        if not condition:
            return False
        try:
            tree = ast.parse(condition, mode="eval")
        except SyntaxError:
            return False

        allowed_node_types = (
            ast.Expression, ast.BoolOp, ast.UnaryOp, ast.Not, ast.Compare,
            ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE,
            ast.Constant, ast.Name, ast.Load, ast.And, ast.Or,
            ast.Attribute, ast.Subscript, ast.Index, ast.Tuple, ast.List
        )

        def _eval(node):
            if isinstance(node, ast.Expression):
                return _eval(node.body)
            if isinstance(node, ast.Constant):
                return node.value
            if isinstance(node, ast.Name):
                return context.get(node.id)
            if isinstance(node, ast.BoolOp):
                values = [_eval(v) for v in node.values]
                if isinstance(node.op, ast.And):
                    return all(values)
                if isinstance(node.op, ast.Or):
                    return any(values)
                return False
            if isinstance(node, ast.UnaryOp):
                operand = _eval(node.operand)
                if isinstance(node.op, ast.Not):
                    return not operand
                return False
            if isinstance(node, ast.Compare):
                left = _eval(node.left)
                for op, comparator in zip(node.ops, node.comparators):
                    right = _eval(comparator)
                    if isinstance(op, ast.Eq): result = (left == right)
                    elif isinstance(op, ast.NotEq): result = (left != right)
                    elif isinstance(op, ast.Lt): result = (left < right)
                    elif isinstance(op, ast.LtE): result = (left <= right)
                    elif isinstance(op, ast.Gt): result = (left > right)
                    elif isinstance(op, ast.GtE): result = (left >= right)
                    else: return False
                    if not result:
                        return False
                    left = right
                return True
            if isinstance(node, ast.Attribute):
                obj = _eval(node.value)
                return getattr(obj, node.attr, False)
            if isinstance(node, ast.Subscript):
                value = _eval(node.value)
                index = _eval(node.slice)
                try:
                    return value[index]
                except Exception:
                    return False
            return False

        for n in ast.walk(tree):
            if not isinstance(n, allowed_node_types):
                return False
        return bool(_eval(tree))

    def validate(self, entities: Dict[str, Any], adjacency: Dict[str, list]):
        total_room_area = 0.0
        total_window_area = 0.0

        # Buat mapping room -> windows dari adjacency (relasi CONTAINS/HOSTS)
        room_windows: Dict[str, List[Any]] = {uid: [] for uid, ent in entities.items() if isinstance(ent, Room)}
        for uid, ent in entities.items():
            if isinstance(ent, Window):
                # Cari room yang mengandung window melalui relasi CONTAINS atau HOSTS
                for rel_type, target_id in adjacency.get(uid, []):
                    if rel_type in ("CONTAINS", "HOSTS") and target_id in room_windows:
                        room_windows[target_id].append(ent)
                        break

        for uid, ent in entities.items():
            if isinstance(ent, Beam):
                if ent.length.value > 1.5:
                    self.warnings.append({
                        "warning_code": "RULE-STR-004",
                        "entity_uuid": uid,
                        "message": "Cantilever > 1.5m"
                    })
            elif isinstance(ent, Column):
                if not any(rel in ("SUPPORTS", "CONNECTED_TO") for rel, _ in adjacency.get(uid, [])):
                    self.warnings.append({
                        "warning_code": "RULE-STR-002",
                        "entity_uuid": uid,
                        "message": "Column may lack foundation"
                    })
                               # RULE-QTY-002: rasio tulangan (perkiraan)
                vol = ent.volume.value
                if vol > 0:
                    if ent.reinforcement:
                        # Asumsikan berat jenis baja 7850 kg/m3, volume tulangan = luas penampang Ã— panjang
                        # untuk kolom: gunakan rasio volume tulangan terhadap volume kolom
                        main_diameter_m = ent.reinforcement.main_diameter.value / 1000.0
                        area_steel = (3.14159 / 4) * (main_diameter_m ** 2) * ent.reinforcement.main_quantity
                        # estimasi panjang tulangan sama dengan tinggi kolom (sederhana)
                        steel_volume = area_steel * ent.height.value
                        ratio = steel_volume / vol
                        if not (0.01 <= ratio <= 0.08):
                            self.warnings.append({
                                "warning_code": "RULE-QTY-002",
                                "entity_uuid": uid,
                                "message": f"Reinforcement ratio {ratio:.4f} out of range"
                            })
                    else:
                        self.warnings.append({
                            "warning_code": "RULE-QTY-002",
                            "entity_uuid": uid,
                            "message": "Reinforcement data not available; ratio assumed 0.02"
                        })
            elif isinstance(ent, Slab):
                if len(getattr(ent, "supports", [])) < 3:
                    self.warnings.append({
                        "warning_code": "RULE-STR-003",
                        "entity_uuid": uid,
                        "message": "Slab supports < 3"
                    })
                if ent.volume.value <= 0:
                    self.errors.append({
                        "error_code": "RULE-QTY-001",
                        "entity_uuid": uid,
                        "message": "Concrete volume non-zero required"
                    })
            elif isinstance(ent, Room):
                total_room_area += ent.area.value
                min_area = {"BEDROOM": 9.0, "BATHROOM": 3.0}
                req = min_area.get(ent.room_type.upper(), 0)
                if ent.area.value < req:
                    self.warnings.append({
                        "warning_code": "RULE-SPA-001",
                        "entity_uuid": uid,
                        "message": f"Room area < {req}mÂ²"
                    })

                # RULE-SPA-003 per-room
                win_area = sum(w.area.value for w in room_windows.get(uid, []))
                total_window_area += win_area
                if ent.area.value > 0 and win_area < 0.1 * ent.area.value:
                    self.warnings.append({
                        "warning_code": "RULE-SPA-003",
                        "entity_uuid": uid,
                        "message": f"Window area {win_area:.2f}mÂ² < 10% room area {ent.area.value:.2f}mÂ²"
                    })
            elif isinstance(ent, Door):
                if ent.door_type == "MAIN_ENTRANCE" and ent.width.value < 0.8:
                    self.warnings.append({
                        "warning_code": "RULE-SPA-002",
                        "entity_uuid": uid,
                        "message": "Door width < 0.8m"
                    })
            elif isinstance(ent, Window):
                total_window_area += ent.area.value
                # RULE-SPA-003 global fallback jika tidak ada room
                # (akan ditangani juga di Room loop)

        # Jika tidak ada Room, gunakan global check
        if not any(isinstance(ent, Room) for ent in entities.values()):
            if total_room_area > 0 and total_window_area < 0.1 * total_room_area:
                self.warnings.append({
                    "warning_code": "RULE-SPA-003",
                    "entity_uuid": "GLOBAL",
                    "message": f"Window area {total_window_area:.2f}mÂ² < 10% room area {total_room_area:.2f}mÂ²"
                })

        # Evaluasi custom rules (jika ada)
        for rule in self.custom_rules:
            rule_id = rule.get("rule_id", "CUSTOM")
            severity = rule.get("severity", "WARNING")
            description = rule.get("description", "Custom rule")
            condition = rule.get("condition", None)

            # Evaluasi kondisi sederhana; jika tidak ada kondisi, dianggap False
            ok = False
            if condition:
                try:
                    ok = self._evaluate_condition_safe(condition, {"entities": entities, "adjacency": adjacency})
                except Exception:
                    ok = False

            if ok:
                continue  # Rule terpenuhi, tidak ada pelanggaran

            entry = {
                "warning_code": rule_id if severity != "ERROR" else "ERROR",
                "entity_uuid": rule.get("entity_uuid", "GLOBAL"),
                "message": description
            }
            if severity == "ERROR":
                entry["error_code"] = rule_id
                self.errors.append(entry)
            else:
                self.warnings.append(entry)

        return self.errors, self.warnings
