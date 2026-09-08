# fastra_core/compiler/rule_validator.py

from __future__ import annotations

import ast
import enum
import logging
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, ConfigDict, Field

from fastra_core.ccm.physical import (
    Beam,
    Column,
    Door,
    Foundation,
    Roof,
    Slab,
    Wall,
    Window,
)
from fastra_core.ccm.spatial import Room

logger = logging.getLogger(__name__)


class RuleValidationCode(str, enum.Enum):
    RULE_STR_001 = "RULE-STR-001"
    RULE_STR_002 = "RULE-STR-002"
    RULE_STR_003 = "RULE-STR-003"
    RULE_STR_004 = "RULE-STR-004"
    RULE_QTY_001 = "RULE-QTY-001"
    RULE_QTY_002 = "RULE-QTY-002"
    RULE_SPA_001 = "RULE-SPA-001"
    RULE_SPA_002 = "RULE-SPA-002"
    RULE_SPA_003 = "RULE-SPA-003"
    RULE_ARC_001 = "RULE-ARC-001"


class RuleLogDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, strict=True)

    warning_code: str = Field(..., min_length=2, max_length=16)
    entity_uuid: str = Field(
        ...,
        min_length=5,
        max_length=64,
        pattern=r"^[a-f0-9\-]{36}|[A-Za-z0-9_]+$",
    )
    message: str = Field(..., min_length=5, max_length=512)

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


class RuleValidator:
    def __init__(self, custom_rules: Optional[List[Dict[str, Any]]] = None) -> None:
        self._errors: List[Dict[str, Any]] = []
        self._warnings: List[Dict[str, Any]] = []
        self._custom_rules = custom_rules or []

    @property
    def errors(self) -> List[Dict[str, Any]]:
        return list(self._errors)

    @property
    def warnings(self) -> List[Dict[str, Any]]:
        return list(self._warnings)

    @property
    def custom_rules(self) -> List[Dict[str, Any]]:
        return list(self._custom_rules)

    @staticmethod
    def _evaluate_condition_safe(condition: str, context: Dict[str, Any]) -> bool:
        if not condition or not condition.strip():
            return False
        try:
            tree = ast.parse(condition.strip(), mode="eval")
        except SyntaxError:
            return False

        allowed_node_types = (
            ast.Expression,
            ast.BoolOp,
            ast.UnaryOp,
            ast.Not,
            ast.Compare,
            ast.Eq,
            ast.NotEq,
            ast.Lt,
            ast.LtE,
            ast.Gt,
            ast.GtE,
            ast.Constant,
            ast.Name,
            ast.Load,
            ast.And,
            ast.Or,
            ast.Attribute,
            ast.Subscript,
        )

        def _eval(node: Any) -> Any:
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
                    if isinstance(op, ast.Eq):
                        result = left == right
                    elif isinstance(op, ast.NotEq):
                        result = left != right
                    elif isinstance(op, ast.Lt):
                        result = left < right
                    elif isinstance(op, ast.LtE):
                        result = left <= right
                    elif isinstance(op, ast.Gt):
                        result = left > right
                    elif isinstance(op, ast.GtE):
                        result = left >= right
                    else:
                        return False
                    if not result:
                        return False
                    left = right
                return True
            if isinstance(node, ast.Attribute):
                obj = _eval(node.value)
                return getattr(obj, node.attr, False)
            if isinstance(node, ast.Subscript):
                value = _eval(node.value)
                if hasattr(node.slice, "value"):
                    idx = node.slice.value
                else:
                    idx = _eval(node.slice)
                try:
                    return value[idx]
                except Exception:
                    return False
            return False

        for n in ast.walk(tree):
            if not isinstance(n, allowed_node_types):
                return False
        try:
            return bool(_eval(tree))
        except Exception:
            return False

    def validate(
        self,
        entities: Dict[str, Any],
        adjacency: Dict[str, List[Tuple[str, str]]],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        self._errors.clear()
        self._warnings.clear()

        total_room_area = Decimal("0.0000")
        total_window_area = Decimal("0.0000")

        room_windows: Dict[str, List[Any]] = {}
        for uid, ent in entities.items():
            if isinstance(ent, Room):
                room_windows[uid] = []
        for uid, ent in entities.items():
            if isinstance(ent, Window):
                for rel_type, target_id in adjacency.get(uid, []) or []:
                    if rel_type in ("CONTAINS", "HOSTS") and target_id in room_windows:
                        room_windows[target_id].append(ent)
                        break

        for uid, ent in entities.items():
            try:
                if isinstance(ent, Beam):
                    self._validate_beam(uid, ent)
                elif isinstance(ent, Column):
                    self._validate_column(uid, ent, adjacency)
                elif isinstance(ent, Slab):
                    self._validate_slab(uid, ent, adjacency)
                elif isinstance(ent, Foundation):
                    self._validate_foundation(uid, ent)
                elif isinstance(ent, Wall):
                    self._validate_wall(uid, ent)
                elif isinstance(ent, Door):
                    self._validate_door(uid, ent)
                elif isinstance(ent, Window):
                    self._validate_window(uid, ent)
                elif isinstance(ent, Room):
                    area = ent.calculate_room_area()
                    total_room_area += area
                    self._validate_room(uid, ent, area)
            except Exception as exc:
                logger.exception("Gagal memvalidasi entitas %s", uid)
                self._add_error_log(
                    RuleValidationCode.RULE_STR_001,
                    uid,
                    f"Kegagalan evaluasi regulasi: {exc}",
                )

        if total_room_area > Decimal("0"):
            for uid, ent in entities.items():
                if isinstance(ent, Window):
                    total_window_area += _to_decimal(ent.calculate_area().value, "window.area")
            ratio = total_window_area / total_room_area
            if ratio < Decimal("0.10"):
                self._add_error_log(
                    RuleValidationCode.RULE_SPA_003,
                    "GLOBAL",
                    f"Rasio ventilasi alami {float(ratio * 100):.2f}% di bawah ambang batas 10%.",
                )

        for rule in self._custom_rules:
            condition = rule.get("condition", "")
            context = rule.get("context", {})
            context.setdefault("entities", entities)
            try:
                if self._evaluate_condition_safe(condition, context):
                    severity = rule.get("severity", "warning")
                    code_value = rule.get("code", "RULE-STR-001")
                    try:
                        code_enum = RuleValidationCode(code_value)
                    except ValueError:
                        code_enum = RuleValidationCode.RULE_STR_001
                    message = rule.get("message", "Custom rule violation")
                    entity_id = rule.get("entity_uuid", "GLOBAL")
                    if severity == "error":
                        self._add_error_log(code_enum, entity_id, message)
                    else:
                        self._add_log(code_enum, entity_id, message)
            except Exception as exc:
                logger.warning("Gagal evaluasi custom rule: %s", exc)

        return self._errors, self._warnings

    # ------------------------------------------------------------------
    # Metode validasi per tipe entitas
    # ------------------------------------------------------------------
    def _validate_beam(self, uid: str, ent: Beam) -> None:
        length = ent.length.value  # Decimal
        if length > Decimal("1.5"):
            self._add_log(
                RuleValidationCode.RULE_STR_004,
                uid,
                f"Panjang kantilever balok {float(length):.2f}m melampaui ambang batas aman 1.5m.",
            )

    def _validate_column(self, uid: str, ent: Column, adjacency: Dict[str, List[Tuple[str, str]]]) -> None:
        edges = adjacency.get(uid, []) or []
        has_support = any(rel in ("SUPPORTS", "CONNECTED_TO") for rel, _ in edges)
        if not has_support:
            self._add_log(
                RuleValidationCode.RULE_STR_002,
                uid,
                "Kolom berpotensi melayang bebas (tanpa dukungan pondasi).",
            )

        volume = ent.calculate_volume().value
        if volume > Decimal("0"):
            reinforcement = getattr(ent, "_reinforcement", None)
            if reinforcement:
                main_dia = _to_decimal(
                    getattr(reinforcement, "_main_diameter", 0.0), "main_diameter"
                )
                main_qty = int(getattr(reinforcement, "_main_quantity", 0))
                if main_dia > 0 and main_qty > 0:
                    area_steel = (Decimal("3.1415926535") / Decimal("4.00")) * (main_dia ** 2) * Decimal(main_qty)
                    height = ent.height.value
                    steel_volume = area_steel * height
                    ratio = steel_volume / volume
                    if not (Decimal("0.01") <= ratio <= Decimal("0.08")):
                        self._add_error_log(
                            RuleValidationCode.RULE_QTY_002,
                            uid,
                            f"Rasio volume baja tulangan kolom {float(ratio * 100):.2f}% di luar ambang batas 1%-8%.",
                        )

    def _validate_slab(self, uid: str, ent: Slab, adjacency: Dict[str, List[Tuple[str, str]]]) -> None:
        edges = adjacency.get(uid, []) or []
        has_support = any(rel == "SUPPORTS" for rel, _ in edges)
        if not has_support:
            self._add_error_log(
                RuleValidationCode.RULE_STR_003,
                uid,
                "Plat lantai kekurangan tumpuan lateral (tidak ada relasi SUPPORTS).",
            )

        volume = ent.calculate_volume().value
        if volume <= Decimal("0"):
            self._add_error_log(
                RuleValidationCode.RULE_QTY_001,
                uid,
                "Volume beton plat lantai bernilai nol.",
            )

    def _validate_foundation(self, uid: str, ent: Foundation) -> None:
        volume = ent.calculate_volume().value
        if volume <= Decimal("0"):
            self._add_error_log(
                RuleValidationCode.RULE_QTY_001,
                uid,
                "Volume pondasi bernilai nol.",
            )

    def _validate_wall(self, uid: str, ent: Wall) -> None:
        area = ent.calculate_gross_area().value
        if area <= Decimal("0"):
            self._add_error_log(
                RuleValidationCode.RULE_QTY_001,
                uid,
                "Luas dinding bernilai nol.",
            )

    def _validate_door(self, uid: str, ent: Door) -> None:
        width = ent.width.value
        if width < Decimal("0.80"):
            self._add_log(
                RuleValidationCode.RULE_SPA_002,
                uid,
                f"Lebar pintu {float(width):.2f}m di bawah ambang batas 0.80m untuk aksesibilitas.",
            )

    def _validate_window(self, uid: str, ent: Window) -> None:
        pass

    def _validate_room(self, uid: str, ent: Room, area: Decimal) -> None:
        if area < Decimal("9.0"):
            self._add_log(
                RuleValidationCode.RULE_SPA_001,
                uid,
                f"Luas ruangan {float(area):.2f}m² kurang dari minimal 9.0m².",
            )

    # ------------------------------------------------------------------
    # Pencatatan log
    # ------------------------------------------------------------------
    def _add_log(self, code: RuleValidationCode, entity_uuid: str, msg: str) -> None:
        log_payload = {
            "warning_code": code.value,
            "entity_uuid": entity_uuid,
            "message": msg,
        }
        try:
            validated_log = RuleLogDTO.model_validate(log_payload)
            self._warnings.append(validated_log.model_dump())
        except Exception as exc:
            logger.warning("Gagal membungkus warning: %s", exc)

    def _add_error_log(self, code: RuleValidationCode, entity_uuid: str, msg: str) -> None:
        log_payload = {
            "warning_code": code.value,
            "entity_uuid": entity_uuid,
            "message": msg,
        }
        try:
            validated_log = RuleLogDTO.model_validate(log_payload)
            self._warnings.append(validated_log.model_dump())
        except Exception as exc:
            logger.warning("Gagal membungkus warning: %s", exc)