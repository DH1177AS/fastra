# fastra_core/knowledge/graph.py

from __future__ import annotations

import enum
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional, Set

from pydantic import BaseModel, ConfigDict, Field

from fastra_core.knowledge.edges import (
    EquipmentRequirement,
    LaborRequirement,
    MaterialRequirement,
    PriceRecord,
)
from fastra_core.knowledge.nodes import (
    EquipmentNode,
    LaborNode,
    MaterialNode,
    SupplierNode,
    WorkItemNode,
)


class KGErrorCode(str, enum.Enum):
    KG_001 = "KG-001"  # Kontradiksi tipe parameter atau kegagalan inisialisasi node
    KG_002 = "KG-002"  # Data rekam jejak harga satuan komoditas regional tidak ditemukan


# ---------------------------------------------------------------------------
# Inbound DTOs – Pydantic Strict Gateway & Validation Matrix (Fail-Fast)
# ---------------------------------------------------------------------------
class KGUnitPriceQueryDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, strict=True)

    wi_id: str = Field(..., min_length=5, max_length=64)
    region: str = Field(..., min_length=2, max_length=64, pattern=r"^[A-Z0-9_\-\s]+$")
    price_date: Optional[str] = Field(
        default=None, min_length=10, max_length=10, pattern=r"^\d{4}-\d{2}-\d{2}$"
    )


class KGSummaryReportDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    materials_count: int = Field(..., ge=0, le=1000000)
    labors_count: int = Field(..., ge=0, le=1000000)
    equipments_count: int = Field(..., ge=0, le=1000000)
    work_items_count: int = Field(..., ge=0, le=1000000)
    material_requirements_count: int = Field(..., ge=0, le=5000000)
    labor_requirements_count: int = Field(..., ge=0, le=5000000)
    equipment_requirements_count: int = Field(..., ge=0, le=5000000)
    price_records_count: int = Field(..., ge=0, le=10000000)
    price_history_count: int = Field(..., ge=0, le=10000000)
    templates_count: int = Field(..., ge=0, le=100000)
    regions: List[str] = Field(..., max_length=1000)
    generated_at: str = Field(..., min_length=10, max_length=32)


# ---------------------------------------------------------------------------
# Core Utilities – Jaminan Keamanan Type Casting
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Domain Models & Core Knowledge Graph
# ---------------------------------------------------------------------------
class KnowledgeGraph:
    def __init__(self) -> None:
        # Existing collections
        self.materials: Dict[str, MaterialNode] = {}
        self.labors: Dict[str, LaborNode] = {}
        self.equipments: Dict[str, EquipmentNode] = {}
        self.work_items: Dict[str, WorkItemNode] = {}
        self.suppliers: Dict[str, SupplierNode] = {}
        self.material_requirements: Dict[str, List[MaterialRequirement]] = {}
        self.labor_requirements: Dict[str, List[LaborRequirement]] = {}
        self.equipment_requirements: Dict[str, List[EquipmentRequirement]] = {}
        self.prices: Dict[str, List[PriceRecord]] = {}
        self.price_history: List[Any] = []
        self.templates: List[Any] = []
        self.segment_overrides: Dict[str, Dict[str, Dict]] = {}

        # Additional attributes required by other modules
        self.regions: Dict[str, Any] = {}
        self.sni_relations: List[Any] = []
        self.ppn_rate: float = 0.11
        self.pph_rate: float = 0.02
        self.tax_rates: Dict[str, float] = {}
        self.risk_register: List[Any] = []
        self.schedule_weights: Dict[str, float] = {}
        self.template_definitions: Dict[str, Any] = {}
        self.alternative_materials: List[Any] = []
        # For compatibility with API demo (physical_entities & relationships)
        self.physical_entities: Dict[str, Any] = {}
        self.relationships: List[Dict[str, Any]] = []

    def remove_work_item(self, code: str) -> None:    
        if hasattr(self, "work_items"):
            self.work_items.pop(code, None)

    # ------------------------------------------------------------------
    # Metode penambahan data
    # ------------------------------------------------------------------
    def add_material(self, m: MaterialNode) -> None:
        if not isinstance(m, MaterialNode):
            raise TypeError("Parameter harus berupa MaterialNode")
        self.materials[str(m.id).strip()] = m

    def add_labor(self, l: LaborNode) -> None:
        if not isinstance(l, LaborNode):
            raise TypeError("Parameter harus berupa LaborNode")
        key = f"{str(l.id).strip()}::{str(l.region).strip().upper()}"
        self.labors[key] = l

    def add_equipment(self, e: EquipmentNode) -> None:
        if not isinstance(e, EquipmentNode):
            raise TypeError("Parameter harus berupa EquipmentNode")
        self.equipments[str(e.id).strip()] = e

    def add_work_item(self, w: WorkItemNode) -> None:
        if not isinstance(w, WorkItemNode):
            raise TypeError("Parameter harus berupa WorkItemNode")
        self.work_items[str(w.id).strip()] = w

    def add_supplier(self, s: SupplierNode) -> None:
        if not isinstance(s, SupplierNode):
            raise TypeError("Parameter harus berupa SupplierNode")
        self.suppliers[str(s.id).strip()] = s

    def add_material_requirement(self, work_item_id: str, req: MaterialRequirement) -> None:
        if not isinstance(req, MaterialRequirement):
            raise TypeError("req harus berupa MaterialRequirement")
        self.material_requirements.setdefault(str(work_item_id).strip(), []).append(req)

    def add_labor_requirement(self, work_item_id: str, req: LaborRequirement) -> None:
        if not isinstance(req, LaborRequirement):
            raise TypeError("req harus berupa LaborRequirement")
        self.labor_requirements.setdefault(str(work_item_id).strip(), []).append(req)

    def add_equipment_requirement(self, work_item_id: str, req: EquipmentRequirement) -> None:
        if not isinstance(req, EquipmentRequirement):
            raise TypeError("req harus berupa EquipmentRequirement")
        self.equipment_requirements.setdefault(str(work_item_id).strip(), []).append(req)

    def add_price(self, material_id: str, price: PriceRecord) -> None:
        if not isinstance(price, PriceRecord):
            raise TypeError("price harus berupa PriceRecord")
        self.prices.setdefault(str(material_id).strip(), []).append(price)

    # ------------------------------------------------------------------
    # Metode ekspor ringkasan
    # ------------------------------------------------------------------
    def export_summary(self) -> Dict[str, Any]:
        regions: Set[str] = set()
        for prices_list in self.prices.values():
            for p in prices_list:
                regions.add(p.region)

        report_payload = {
            "materials_count": len(self.materials),
            "labors_count": len(self.labors),
            "equipments_count": len(self.equipments),
            "work_items_count": len(self.work_items),
            "material_requirements_count": sum(len(v) for v in self.material_requirements.values()),
            "labor_requirements_count": sum(len(v) for v in self.labor_requirements.values()),
            "equipment_requirements_count": sum(len(v) for v in self.equipment_requirements.values()),
            "price_records_count": sum(len(v) for v in self.prices.values()),
            "price_history_count": len(self.price_history),
            "templates_count": len(self.templates),
            "regions": sorted(list(regions)),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

        validated_report = KGSummaryReportDTO.model_validate(report_payload)
        return validated_report.model_dump()

    # ------------------------------------------------------------------
    # Metode perhitungan harga satuan
    # ------------------------------------------------------------------
    def get_unit_price(self, wi_id: str, region: str, price_date: Optional[str] = None) -> Dict[str, Any]:
        query_dto = KGUnitPriceQueryDTO.model_validate({
            "wi_id": wi_id,
            "region": region,
            "price_date": price_date,
        })

        material_cost = Decimal("0.0000")
        labor_cost = Decimal("0.0000")
        equipment_cost = Decimal("0.0000")

        material_breakdown: List[Dict[str, Any]] = []
        labor_breakdown: List[Dict[str, Any]] = []
        equipment_breakdown: List[Dict[str, Any]] = []
        errors: List[Dict[str, Any]] = []

        # ------------------------------------------------------------------
        # Komponen biaya material
        # ------------------------------------------------------------------
        for mat_req in self.material_requirements.get(query_dto.wi_id, []):
            price_record: Optional[PriceRecord] = None

            for pr in self.prices.get(mat_req.material_id, []):
                if pr.region == query_dto.region:
                    price_record = pr
                    break

            if price_record is None and self.prices.get(mat_req.material_id):
                price_record = self.prices[mat_req.material_id][0]

            if price_record is None:
                errors.append({"type": "missing_price", "material_id": mat_req.material_id})
                continue

            waste_val = _to_decimal(mat_req.waste_factor, "material.waste_factor")
            if not (Decimal("1.0") <= waste_val <= Decimal("1.3")):
                raise ValueError(
                    f"Pelanggaran batas teknis: waste_factor {float(waste_val)} untuk "
                    f"material '{mat_req.material_id}' melanggar batas regulasi."
                )

            if query_dto.price_date is not None:
                if not price_record.is_valid_at_date(query_dto.price_date):
                    errors.append({
                        "type": "expired_price",
                        "material_id": mat_req.material_id,
                        "price_date": query_dto.price_date,
                        "valid_from": getattr(price_record, "valid_from", ""),
                        "valid_until": getattr(price_record, "valid_until", ""),
                    })
                    continue

            price_raw = getattr(price_record.price, "value", price_record.price)
            unit_price_val = _to_decimal(price_raw, "material.unit_price")
            coef_val = _to_decimal(mat_req.coefficient, "material.coefficient")

            item_cost = coef_val * waste_val * unit_price_val
            material_cost += item_cost

            mat_node = self.materials.get(mat_req.material_id)
            volatility = (
                float(_to_decimal(getattr(mat_node, "volatility_factor", 0.0), "volatility"))
                if mat_node
                else 0.0
            )

            material_breakdown.append({
                "material_id": mat_req.material_id,
                "coefficient": float(coef_val),
                "waste_factor": float(waste_val),
                "unit_price": float(unit_price_val),
                "cost": float(item_cost.quantize(Decimal("0.0001"))),
                "volatility_factor": volatility,
                "price_source": f"{mat_req.material_id}/{price_record.region}/{getattr(price_record, 'valid_from', '')}",
            })

        # ------------------------------------------------------------------
        # Komponen biaya tenaga kerja
        # ------------------------------------------------------------------
        for lab_req in self.labor_requirements.get(query_dto.wi_id, []):
            lab_candidates = [l for l in self.labors.values() if l.id == lab_req.labor_id]
            lab_node: Optional[LaborNode] = None

            for candidate in lab_candidates:
                if getattr(candidate, "region", "") == query_dto.region:
                    lab_node = candidate
                    break

            if lab_node is None:
                for candidate in lab_candidates:
                    if not getattr(candidate, "region", "").strip():
                        lab_node = candidate
                        break
            if lab_node is None and lab_candidates:
                lab_node = lab_candidates[0]

            if lab_node is None:
                errors.append({"type": "missing_labor", "labor_id": lab_req.labor_id})
                continue

            daily_rate_raw = getattr(lab_node.daily_rate, "value", lab_node.daily_rate)
            daily_rate_val = _to_decimal(daily_rate_raw, "labor.daily_rate")
            coef_val = _to_decimal(lab_req.coefficient, "labor.coefficient")

            item_cost = coef_val * daily_rate_val
            labor_cost += item_cost

            labor_breakdown.append({
                "labor_id": lab_req.labor_id,
                "coefficient": float(coef_val),
                "daily_rate": float(daily_rate_val),
                "region": getattr(lab_node, "region", query_dto.region) or query_dto.region,
                "cost": float(item_cost.quantize(Decimal("0.0001"))),
                "wage_source": f"{lab_req.labor_id}/{getattr(lab_node, 'region', query_dto.region)}",
            })

        # ------------------------------------------------------------------
        # Komponen biaya peralatan
        # ------------------------------------------------------------------
        for eq_req in self.equipment_requirements.get(query_dto.wi_id, []):
            eq_node = self.equipments.get(eq_req.equipment_id)
            if eq_node is None:
                errors.append({"type": "missing_equipment", "equipment_id": eq_req.equipment_id})
                continue

            rate_raw = getattr(eq_node, "rate_per_hour", 0.0) or getattr(eq_node, "rate_per_day", 0.0) or 0.0
            rate_val = _to_decimal(getattr(rate_raw, "value", rate_raw), "equipment.rate")
            coef_val = _to_decimal(eq_req.coefficient, "equipment.coefficient")

            mobilization = _to_decimal(
                getattr(eq_node, "mobilization_cost", 0.0) or 0.0, "equipment.mobilization"
            )
            operator_base = _to_decimal(
                getattr(eq_node, "operator_cost_per_day", 0.0) or 0.0, "equipment.operator"
            )
            fuel_base = _to_decimal(
                getattr(eq_node, "fuel_cost_per_hour", 0.0) or 0.0, "equipment.fuel"
            )

            operator_cost = operator_base * coef_val
            fuel_cost = fuel_base * coef_val
            item_cost = (coef_val * rate_val) + mobilization + operator_cost + fuel_cost
            equipment_cost += item_cost

            equipment_breakdown.append({
                "equipment_id": eq_req.equipment_id,
                "coefficient": float(coef_val),
                "rate": float(rate_val),
                "mobilization_cost": float(mobilization),
                "operator_cost": float(operator_cost),
                "fuel_cost": float(fuel_cost),
                "cost": float(item_cost.quantize(Decimal("0.0001"))),
                "equipment_source": f"{eq_req.equipment_id}/{query_dto.region}",
            })

        # ------------------------------------------------------------------
        # Total harga satuan
        # ------------------------------------------------------------------
        total_sum_val = material_cost + labor_cost + equipment_cost

        return {
            "unit_price": float(total_sum_val.quantize(Decimal("0.01"))),
            "material_cost": float(material_cost.quantize(Decimal("0.01"))),
            "labor_cost": float(labor_cost.quantize(Decimal("0.01"))),
            "equipment_cost": float(equipment_cost.quantize(Decimal("0.01"))),
            "material_breakdown": material_breakdown,
            "labor_breakdown": labor_breakdown,
            "equipment_breakdown": equipment_breakdown,
            "errors": errors,
        }
