
"""
Stage 4: Topology Builder - Adjacency dua arah + deteksi wall adjacency.
"""
from typing import Dict, Any, List, Tuple
from fastra_core.ccm.physical import Wall
from collections import defaultdict

class TopologyBuilder:
    def __init__(self) -> None:
        self.adjacency: Dict[str, List[tuple]] = {}
        self.errors: List[Dict[str, Any]] = []
        self.warnings: List[Dict[str, Any]] = []

    def build(self, entities: Dict[str, Any], graph: Dict[str, List[tuple]]) -> Tuple[Dict[str, List[tuple]], List[Dict[str, Any]]]:
        # Inisialisasi adjacency untuk semua entity
        for uid in entities:
            self.adjacency[uid] = []

        # Salin relasi dari graph
        for src, rels in graph.items():
            for rel_type, tgt in rels:
                self.adjacency.setdefault(src, []).append((rel_type, tgt))

        # Tambahkan inverse relasi SUPPORTS/CONNECTED_TO
        for src in list(self.adjacency.keys()):
            for rel_type, tgt in self.adjacency[src]:
                if rel_type in ("SUPPORTS", "CONNECTED_TO"):
                    self.adjacency.setdefault(tgt, []).append(("INVERSE_" + rel_type, src))

        # Deteksi wall adjacency (T/L/X sederhana)
        self._detect_wall_adjacency(entities)

        # Validasi dasar
        for uid, ent in entities.items():
            if ent.__class__.__name__ == "Beam":
                has_support = any(
                    rel in ("SUPPORTS", "INVERSE_SUPPORTS", "CONNECTED_TO", "INVERSE_CONNECTED_TO")
                    for rel, _ in self.adjacency.get(uid, [])
                )
                if not has_support and not (getattr(ent, "start_connection", None) or getattr(ent, "end_connection", None)):
                    self.warnings.append({"warning_code": "TOP-001", "entity_uuid": uid, "message": "Beam unconnected"})
            elif ent.__class__.__name__ == "Column":
                if not self.adjacency.get(uid):
                    self.warnings.append({"warning_code": "TOP-002", "entity_uuid": uid, "message": "Column floating"})
            elif ent.__class__.__name__ == "Slab":
                if not getattr(ent, "supports", []):
                    self.warnings.append({"warning_code": "TOP-004", "entity_uuid": uid, "message": "Slab unsupported"})
        return self.adjacency, self.warnings

    def _detect_wall_adjacency(self, entities: Dict[str, Any]) -> None:
        """Deteksi dinding yang berdekatan berdasarkan endpoint (toleransi 1 mm)."""
        from collections import defaultdict
        walls = {uid: ent for uid, ent in entities.items() if isinstance(ent, Wall)}
        endpoint_map = defaultdict(set)
        for uid, wall in walls.items():
            for p in wall.axis_line:
                key = (round(p.x, 3), round(p.y, 3), round(p.z, 3))
                endpoint_map[key].add(uid)
        seen_pairs = set()
        for uids_at_point in endpoint_map.values():
            uid_list = list(uids_at_point)
            if len(uid_list) < 2:
                continue
            for i in range(len(uid_list)):
                w1 = uid_list[i]
                for j in range(i+1, len(uid_list)):
                    w2 = uid_list[j]
                    pair = (w1, w2) if w1 < w2 else (w2, w1)
                    if pair not in seen_pairs:
                        seen_pairs.add(pair)
                        self.adjacency.setdefault(w1, []).append(("WALL_ADJACENT", w2))
                        self.adjacency.setdefault(w2, []).append(("WALL_ADJACENT", w1))
