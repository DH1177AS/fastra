# fastra_core\compiler\topology_builder.py

from __future__ import annotations

import enum
from collections import defaultdict
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Tuple

from pydantic import BaseModel, ConfigDict, Field

from fastra_core.ccm.physical import Wall


class TopologyValidationCode(str, enum.Enum):
   
    TOP_001 = "TOP-001"  # Balok struktural terdeteksi putus/melayang tanpa koneksi
    TOP_002 = "TOP-002"  # Kolom struktur utama melayang bebas tanpa matriks relasi
    TOP_004 = "TOP-004"  # Plat lantai (Slab) kehilangan jejak tumpuan pendukung


class TopologyLogDTO(BaseModel):
   
    model_config = ConfigDict(extra="forbid", strict=True)

    warning_code: TopologyValidationCode = Field(...)
    entity_uuid: str = Field(
        ...,
        min_length=36,
        max_length=64,
        pattern=r"^[a-f0-9\-]+|[a-z0-9_]+$",
    )
    message: str = Field(..., min_length=5, max_length=512)


class AdjacencyEdgeDTO(BaseModel):
   
    model_config = ConfigDict(extra="forbid", strict=True)

    relation_type: str = Field(..., min_length=2, max_length=64, pattern=r"^[A-Z0-9_]+$")
    target_uuid: str = Field(
        ...,
        min_length=36,
        max_length=64,
        pattern=r"^[a-f0-9\-]+|[a-z0-9_]+$",
    )


def _quantize_spasial_key(x: Any, y: Any, z: Any) -> Tuple[str, str, str]:
   
    try:
        dec_x = Decimal(str(x)).quantize(Decimal("0.001"))
        dec_y = Decimal(str(y)).quantize(Decimal("0.001"))
        dec_z = Decimal(str(z)).quantize(Decimal("0.001"))
        return str(dec_x), str(dec_y), str(dec_z)
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError("Kegagalan kritis: Gagal melakukan kuantisasi koordinat spasial.") from exc


class TopologyBuilder:
    
    def __init__(self) -> None:
        self.adjacency: Dict[str, List[Tuple[str, str]]] = {}
        self._errors: List[Dict[str, Any]] = []
        self._warnings: List[Dict[str, Any]] = []

    @property
    def errors(self) -> List[Dict[str, Any]]:
        return list(self._errors)

    @property
    def warnings(self) -> List[Dict[str, Any]]:
        return list(self._warnings)

    def build(
        self,
        entities: Dict[str, Any],
        graph: Dict[str, List[Tuple[str, str]]],
    ) -> Tuple[Dict[str, List[Tuple[str, str]]], List[Dict[str, Any]]]:
        
        self._errors.clear()
        self._warnings.clear()
        self.adjacency.clear()
       
        for uid in entities:
            self.adjacency[uid] = []
        
        for src_uuid, edges in graph.items():
            if src_uuid not in entities:
                continue
            for rel_type, tgt_uuid in edges:
                if tgt_uuid not in entities:
                    continue

                edge_payload = {"relation_type": str(rel_type), "target_uuid": str(tgt_uuid)}
                try:
                    validated_edge = AdjacencyEdgeDTO.model_validate(edge_payload)
                except Exception as exc:
                    logger.warning("Edge tidak valid dilewati: %s", exc)
                    continue

                self.adjacency.setdefault(src_uuid, []).append(
                    (validated_edge.relation_type, validated_edge.target_uuid)
                )
        
        for src_uuid in list(self.adjacency.keys()):
            for rel_type, tgt_uuid in self.adjacency[src_uuid]:
                if rel_type in ("SUPPORTS", "CONNECTED_TO"):
                    inv_type = f"INVERSE_{rel_type}"
                    self.adjacency.setdefault(tgt_uuid, []).append((inv_type, src_uuid))
       
        self._detect_wall_adjacency(entities)
       
        for uid, ent in entities.items():
            etype = ent.__class__.__name__

            if etype == "Beam":
                has_support = any(
                    rel in ("SUPPORTS", "INVERSE_SUPPORTS", "CONNECTED_TO", "INVERSE_CONNECTED_TO")
                    for rel, _ in self.adjacency.get(uid, [])
                )
                start_conn = getattr(ent, "_start_connection", None)
                end_conn = getattr(ent, "_end_connection", None)

                if not has_support and not (start_conn or end_conn):
                    self._add_warning(
                        code=TopologyValidationCode.TOP_001,
                        entity_uuid=uid,
                        msg="Pelanggaran pembebanan: Balok/Beam terdeteksi melayang bebas tanpa koneksi struktur tumpuan.",
                    )

            elif etype == "Column":
                if not self.adjacency.get(uid):
                    self._add_warning(
                        code=TopologyValidationCode.TOP_002,
                        entity_uuid=uid,
                        msg="Bahaya struktural: Elemen Kolom berstatus melayang (floating node) tanpa matriks relasi pengikat.",
                    )

            elif etype == "Slab":
                supports_list = getattr(ent, "_supports", []) or []
                if not supports_list:
                    self._add_warning(
                        code=TopologyValidationCode.TOP_004,
                        entity_uuid=uid,
                        msg="Peringatan teknik: Plat Lantai/Slab terdeteksi mengambang bebas tanpa daftar balok pendukung (unsupported).",
                    )

        return self.adjacency, list(self._warnings)

    def _detect_wall_adjacency(self, entities: Dict[str, Any]) -> None:
                
        walls = {uid: ent for uid, ent in entities.items() if ent.__class__.__name__ == "Wall"}
        endpoint_map: Dict[Tuple[str, str, str], set] = defaultdict(set)
       
        for uid, wall in walls.items():
            axis_pts = getattr(wall, "_axis_line", []) or []
            for p in axis_pts:
               
                spatial_key = _quantize_spasial_key(p.x, p.y, p.z)
                endpoint_map[spatial_key].add(uid)

        seen_pairs: set = set()
       
        for uids_at_point in endpoint_map.values():
            uid_list = list(uids_at_point)
            if len(uid_list) < 2:
                continue
           
            for i in range(len(uid_list)):
                for j in range(i + 1, len(uid_list)):
                    a, b = uid_list[i], uid_list[j]
                    pair_key = tuple(sorted([a, b]))
                    if pair_key in seen_pairs:
                        continue
                    seen_pairs.add(pair_key)

                    # Tambahkan relasi dua arah
                    self.adjacency.setdefault(a, []).append(("WALL_ADJACENT", b))
                    self.adjacency.setdefault(b, []).append(("WALL_ADJACENT", a))

    def _add_warning(self, code: TopologyValidationCode, entity_uuid: str, msg: str) -> None:        
        warning_payload = {
            "warning_code": code.value,
            "entity_uuid": entity_uuid,
            "message": msg,
        }
        try:
            validated_warning = TopologyLogDTO.model_validate(warning_payload)
            self._warnings.append(validated_warning.model_dump())
        except Exception:
           
            self._warnings.append(
                {
                    "warning_code": code.value,
                    "entity_uuid": entity_uuid,
                    "message": msg,
                }
            )