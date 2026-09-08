# fastra_core/compiler/quantity_engine.py

from __future__ import annotations

import enum
import logging
from collections import defaultdict
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from fastra_core.ccm.physical import (
    Beam,
    Column,
    Door,
    Foundation,
    Ramp,
    Roof,
    Slab,
    Stair,
    Wall,
    Window,
)
from fastra_core.ccm.spatial import Room

logger = logging.getLogger(__name__)


class QTOErrorCode(str, enum.Enum):
    QTO_001 = "QTO-001"  # Malformed row structure
    QTO_002 = "QTO-002"  # Floating point data failure


class QTOOutputItemDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    entity_id: str = Field(
        ...,
        min_length=5,
        max_length=64,
        pattern=r"^[a-f0-9\-]{36}|[a-z0-9_]+$",
    )
    work_item_code: str = Field(
        ..., min_length=2, max_length=32, pattern=r"^[A-Z0-9_\-\.]+$"
    )
    description: str = Field(..., min_length=2, max_length=512)
    quantity: float = Field(..., ge=0.0, le=1e9, allow_inf_nan=False)
    unit: str = Field(
        ..., min_length=1, max_length=16, pattern=r"^[A-Za-z0-9²³\/()\s\u00B3]+$"
    )
    detail: str = Field(..., min_length=2, max_length=1024)
    source_entities: List[str] = Field(default_factory=list, max_length=100)


def _to_decimal(value: float | int | Decimal, field_name: str) -> Decimal:
    if isinstance(value, Decimal):
        return value
    if not isinstance(value, (int, float)):
        raise TypeError(f"Field '{field_name}' wajib bertipe numerik dasar (int/float/Decimal).")
    try:
        return Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError(
            f"Field '{field_name}' gagal dikonversi ke representasi Decimal imutabel."
        ) from exc


class QuantityEngine:
    def __init__(self) -> None:
        self.items: List[Dict[str, Any]] = []
        self._errors: List[Dict[str, Any]] = []
        self._warnings: List[str] = []

    @property
    def errors(self) -> List[Dict[str, Any]]:
        return list(self._errors)

    @property
    def warnings(self) -> List[str]:
        return list(self._warnings)

    def process(
        self,
        entities: Dict[str, Any],
        adjacency: Dict[str, List[tuple]] | None = None,
    ) -> List[Dict[str, Any]]:
        self.items.clear()
        self._errors.clear()
        self._warnings.clear()

        adjacency = adjacency or {}

        for uid, ent in entities.items():
            try:
                self._dispatch(uid, ent, entities, adjacency)
            except Exception as exc:
                logger.exception("Gagal memproses kuantitas untuk entitas %s", uid)
                self._errors.append({
                    "error_code": QTOErrorCode.QTO_001.value,
                    "message": f"Crash saat ekstraksi kuantitas {uid}: {exc}",
                })

        if self._errors:
            return []

        return self._aggregate()

    def _dispatch(
        self,
        uid: str,
        ent: Any,
        entities: Dict[str, Any],
        adjacency: Dict[str, List[tuple]],
    ) -> None:
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
            self._stair(uid, ent)
        elif isinstance(ent, Ramp):
            self._ramp(uid, ent)
        elif isinstance(ent, Room):
            self._room(uid, ent)
        else:
            self._warnings.append(f"Entitas {uid} tipe {type(ent).__name__} dilewati oleh QuantityEngine")

    # ------------------------------------------------------------------
    # Metode ekstraksi per tipe elemen
    # ------------------------------------------------------------------
    def _wall(
        self,
        uid: str,
        w: Wall,
        entities: Dict[str, Any],
        adjacency: Dict[str, List[tuple]],
    ) -> None:
        net_area_decimal = _to_decimal(w.calculate_net_area().value, "net_area")
        name = getattr(w, "name", "Wall")

        if w.construction_type.value in ("BATA_MERAH", "BATA_RINGAN"):
            self.items.append({
                "entity_id": uid,
                "work_item_code": "PEK.DIND.001",
                "description": f"Pasangan {name}",
                "quantity": net_area_decimal,
                "unit": "m²",
                "detail": f"Luas bersih pasangan bata {float(net_area_decimal):.4f} m²",
            })
        elif w.construction_type.value == "BETON_BERTULANG":
            volume = net_area_decimal * w.thickness.value
            self.items.append({
                "entity_id": uid,
                "work_item_code": "PEK.STR.003",
                "description": f"Cor beton {name}",
                "quantity": volume,
                "unit": "m³",
                "detail": f"Volume beton dinding {float(volume):.4f} m³",
            })
        
        if w.construction_type.value in ("BATA_MERAH", "BATA_RINGAN"):
            plaster_area = net_area_decimal * Decimal("2")
            self.items.append({
                "entity_id": uid,
                "work_item_code": "PEK.DIND.002",
                "description": f"Plesteran {name}",
                "quantity": plaster_area,
                "unit": "m²",
                "detail": f"Luas plesteran dua sisi {float(plaster_area):.4f} m²",
            })
            self.items.append({
                "entity_id": uid,
                "work_item_code": "PEK.DIND.003",
                "description": f"Acian {name}",
                "quantity": plaster_area,
                "unit": "m²",
                "detail": f"Luas acian dua sisi {float(plaster_area):.4f} m²",
            })

    def _column(self, uid: str, c: Column) -> None:
        vol_decimal = Decimal(str(c.calculate_volume().value))
        bekisting_decimal = Decimal(str(c.calculate_bekisting_area().value))
        name = getattr(c, "name", "Column")
        rebar_weight = vol_decimal * Decimal("150")

        self.items.append({
            "entity_id": uid,
            "work_item_code": "PEK.STR.001",
            "description": f"Bekisting {name}",
            "quantity": bekisting_decimal,
            "unit": "m²",
            "detail": f"Luas bekisting kolom {float(bekisting_decimal):.4f} m²",
        })        
        self.items.append({
            "entity_id": uid,
            "work_item_code": "PEK.STR.002",
            "description": f"Pembesian {name}",
            "quantity": rebar_weight,
            "unit": "kg",
            "detail": f"Volume {float(vol_decimal):.4f} m³ × 150 kg/m³ = {float(rebar_weight):.4f} kg",
        })
        self.items.append({
            "entity_id": uid,
            "work_item_code": "PEK.STR.003",
            "description": f"Cor beton {name}",
            "quantity": vol_decimal,
            "unit": "m³",
            "detail": f"Volume beton kolom {float(vol_decimal):.4f} m³",
        })

    def _beam(
        self,
        uid: str,
        b: Beam,
        entities: Dict[str, Any],
        adjacency: Dict[str, List[tuple]],
    ) -> None:
        vol_gross = Decimal(str(b.calculate_volume().value))
        deduction = Decimal("0.0000")
        for rel_type, tgt_uid in adjacency.get(uid, []):
            if rel_type == "INVERSE_SUPPORTS":
                support_ent = entities.get(tgt_uid)
                if isinstance(support_ent, Column):
                    col_w = _to_decimal(getattr(support_ent, "_width", 0), "col.width")
                    col_d = _to_decimal(getattr(support_ent, "_depth", 0), "col.depth")
                    beam_d = _to_decimal(getattr(b, "_depth", 0), "beam.depth")
                    deduction += col_w * col_d * beam_d
        vol_decimal = vol_gross - deduction

        bekisting = (2 * b.depth.value + b.width.value) * b.length.value
        name = getattr(b, "name", "Beam")
        rebar_weight = vol_decimal * Decimal("150")

        self.items.append({
            "entity_id": uid,
            "work_item_code": "PEK.STR.001",
            "description": f"Bekisting {name}",
            "quantity": bekisting,
            "unit": "m²",
            "detail": f"Luas bekisting balok {float(bekisting):.4f} m²",
        })
        self.items.append({
            "entity_id": uid,
            "work_item_code": "PEK.STR.002",
            "description": f"Pembesian {name}",
            "quantity": rebar_weight,
            "unit": "kg",
            "detail": f"Volume {float(vol_decimal):.4f} m³ × 150 kg/m³ = {float(rebar_weight):.4f} kg",
        })
        self.items.append({
            "entity_id": uid,
            "work_item_code": "STR.029",
            "description": f"Cor beton {name}",
            "quantity": vol_decimal,
            "unit": "m³",
            "detail": f"Volume beton balok {float(vol_decimal):.4f} m³",
        })

    def _slab(
        self,
        uid: str,
        s: Slab,
        entities: Dict[str, Any],
        adjacency: Dict[str, List[tuple]],
    ) -> None:
        area_decimal = _to_decimal(s.calculate_area().value, "slab_area")
        vol_gross_decimal = _to_decimal(s.calculate_volume().value, "slab_volume")
        name = getattr(s, "name", "Slab")
        slab_thickness = _to_decimal(s.thickness.value, "slab_thickness")

        deduction = Decimal("0.0000")
        for beam_uid in getattr(s, "supports", []):
            beam_ent = entities.get(beam_uid)
            if isinstance(beam_ent, Beam):
                beam_width = _to_decimal(beam_ent.width.value, "beam.width")
                beam_depth = _to_decimal(beam_ent.depth.value, "beam.depth")
                beam_length = _to_decimal(beam_ent.length.value, "beam.length")
                if beam_depth > slab_thickness:
                    deduction += beam_width * (beam_depth - slab_thickness) * beam_length

        vol_decimal = vol_gross_decimal - deduction
        if vol_decimal < Decimal("0.0000"):
            vol_decimal = Decimal("0.0000")
        rebar_weight = vol_decimal * Decimal("150")

        self.items.append({
            "entity_id": uid,
            "work_item_code": "PEK.STR.001",
            "description": f"Bekisting {name}",
            "quantity": area_decimal,
            "unit": "m²",
            "detail": f"Luas bekisting plat {float(area_decimal):.4f} m²",
        })
        self.items.append({
            "entity_id": uid,
            "work_item_code": "PEK.STR.002",
            "description": f"Pembesian {name}",
            "quantity": rebar_weight,
            "unit": "kg",
            "detail": f"Volume {float(vol_decimal):.4f} m³ × 150 kg/m³ = {float(rebar_weight):.4f} kg",
        })
        self.items.append({
            "entity_id": uid,
            "work_item_code": "STR.029",
            "description": f"Cor beton {name}",
            "quantity": vol_decimal,
            "unit": "m³",
            "detail": f"Volume beton plat {float(vol_decimal):.4f} m³",
        })

    def _foundation(self, uid: str, f: Foundation) -> None:
        vol_decimal = Decimal(str(f.calculate_volume().value))
        name = getattr(f, "name", "Foundation")
        rebar_weight = vol_decimal * Decimal("150")

        self.items.append({
            "entity_id": uid,
            "work_item_code": "PEK.FND.001",
            "description": f"Cor Pondasi {name}",
            "quantity": vol_decimal,
            "unit": "m³",
            "detail": f"Volume pondasi eksak {float(vol_decimal):.4f} m³",
        })
        self.items.append({
            "entity_id": uid,
            "work_item_code": "PEK.FND.002",
            "description": f"Pembesian Pondasi {name}",
            "quantity": rebar_weight,
            "unit": "kg",
            "detail": f"Volume {float(vol_decimal):.4f} m³ × 150 kg/m³ = {float(rebar_weight):.4f} kg",
        })

    def _roof(self, uid: str, r: Roof) -> None:
        area_decimal = r.calculate_projected_area().value
        name = getattr(r, "name", "Roof")

        self.items.append({
            "entity_id": uid,
            "work_item_code": "PEK.ATP.001",
            "description": f"Rangka Atap {name}",
            "quantity": area_decimal,
            "unit": "m²",
            "detail": f"Luas bentang miring atap {float(area_decimal):.4f} m²",
        })
        self.items.append({
            "entity_id": uid,
            "work_item_code": "PEK.ATP.002",
            "description": f"Penutup Atap {name}",
            "quantity": area_decimal,
            "unit": "m²",
            "detail": f"Luas bidang penutup genteng {float(area_decimal):.4f} m²",
        })

    def _door(self, uid: str, d: Door) -> None:
        door_area_decimal = d.calculate_area().value
        name = getattr(d, "name", "Door")

        self.items.append({
            "entity_id": uid,
            "work_item_code": "PEK.PTU.001",
            "description": f"Pemasangan Pintu {name}",
            "quantity": Decimal("1.0000"),
            "unit": "unit",
            "detail": f"1 unit komponen bukaan pintu tipe {d.door_type.value}",
        })
        self.items.append({
            "entity_id": uid,
            "work_item_code": "PEK.PTU.002",
            "description": f"Finishing Pintu {name}",
            "quantity": door_area_decimal,
            "unit": "m²",
            "detail": f"Luas bidang permukaan daun pintu {float(door_area_decimal):.4f} m²",
        })

    def _window(self, uid: str, w: Window) -> None:
        window_area_decimal = w.calculate_area().value
        name = getattr(w, "name", "Window")

        self.items.append({
            "entity_id": uid,
            "work_item_code": "PEK.JND.001",
            "description": f"Pemasangan Jendela {name}",
            "quantity": Decimal("1.0000"),
            "unit": "unit",
            "detail": f"1 unit komponen bukaan jendela tipe {w.window_type.value}",
        })
        self.items.append({
            "entity_id": uid,
            "work_item_code": "PEK.JND.002",
            "description": f"Finishing Jendela {name}",
            "quantity": window_area_decimal,
            "unit": "m²",
            "detail": f"Luas penampang pasang kaca jendela {float(window_area_decimal):.4f} m²",
        })

    def _stair(self, uid: str, s: Stair) -> None:
        name = getattr(s, "name", "Stair")
       
        bekisting = (s.calculate_total_run().value + 2 * s.calculate_total_rise().value) * s.width.value

        self.items.append({
            "entity_id": uid,
            "work_item_code": "PEK.STR.041",
            "description": f"Bekisting Tangga {name}",
            "quantity": bekisting,
            "unit": "m²",
            "detail": f"Luas bekisting tangga {float(bekisting):.4f} m²",
        })

    def _ramp(self, uid: str, r: Ramp) -> None:
        volume = r.length.value * r.width.value * Decimal("0.2")
        name = getattr(r, "name", "Ramp")

        self.items.append({
            "entity_id": uid,
            "work_item_code": "PEK.STR.003",
            "description": f"Cor Beton {name}",
            "quantity": volume,
            "unit": "m³",
            "detail": f"Volume beton ramp {float(volume):.4f} m³ (asumsi tebal 0.2 m)",
        })

    def _room(self, uid: str, r: Room) -> None:
        room_area_decimal = r.calculate_room_area()
        name = getattr(r, "name", "Room")

        self.items.append({
            "entity_id": uid,
            "work_item_code": "PEK.LNT.001",
            "description": f"Keramik Lantai {name}",
            "quantity": room_area_decimal,
            "unit": "m²",
            "detail": f"Luas bersih hamparan lantai ruangan {float(room_area_decimal):.4f} m²",
        })
        self.items.append({
            "entity_id": uid,
            "work_item_code": "PEK.PLF.001",
            "description": f"Plafon Gypsum {name}",
            "quantity": room_area_decimal,
            "unit": "m²",
            "detail": f"Luas bentang rangka gantungan plafon {float(room_area_decimal):.4f} m²",
        })

    # ------------------------------------------------------------------
    # Agregasi & Validasi
    # ------------------------------------------------------------------
    def _aggregate(self) -> List[Dict[str, Any]]:
        agg = defaultdict(lambda: {
            "quantity": Decimal("0.0000"),
            "unit": "",
            "source_entities": [],
            "descriptions": [],
            "details": [],
        })

        for item in self.items:
            key = (item["work_item_code"], item["description"])
            quantity_decimal = _to_decimal(item["quantity"], f"items_payload[{key}].quantity")

            agg[key]["quantity"] += quantity_decimal
            agg[key]["unit"] = item["unit"]

            if item["entity_id"] not in agg[key]["source_entities"]:
                agg[key]["source_entities"].append(item["entity_id"])

            agg[key]["descriptions"].append(item["description"])
            agg[key]["details"].append(item.get("detail", ""))

        result: List[Dict[str, Any]] = []
        for (code, _desc_key), data in agg.items():
            desc_summary = " | ".join(data["descriptions"][:3])
            if len(data["descriptions"]) > 3:
                desc_summary += " ..."
            detail_summary = " | ".join(data["details"][:3])
            if len(data["details"]) > 3:
                detail_summary += " ..."

            output_payload = {
                "entity_id": "aggregated",
                "work_item_code": code,
                "description": desc_summary,
                "quantity": float(data["quantity"].quantize(Decimal("0.0001"))),
                "unit": data["unit"],
                "source_entities": list(data["source_entities"]),
                "detail": detail_summary,
            }

            try:
                validated_row = QTOOutputItemDTO.model_validate(output_payload)
                result.append({
                    "work_item_code": validated_row.work_item_code,
                    "description": validated_row.description,
                    "quantity": validated_row.quantity,
                    "unit": validated_row.unit,
                    "source_entities": validated_row.source_entities,
                    "detail": validated_row.detail,
                })
            except Exception as exc:
                logger.error("Baris QTO gagal validasi: %s -> %s", code, exc)
                self._errors.append({
                    "error_code": QTOErrorCode.QTO_001.value,
                    "message": f"Baris QTO untuk {code} gagal validasi: {exc}",
                })
                return []

        return result