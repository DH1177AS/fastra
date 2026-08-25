# mypy: ignore-errors
from typing import Dict, List, Optional
from fastra_core.knowledge.nodes import MaterialNode, LaborNode, EquipmentNode, WorkItemNode, SupplierNode
from fastra_core.knowledge.edges import MaterialRequirement, LaborRequirement, PriceRecord, EquipmentRequirement
from fastra_core.primitives.currency import Currency

class KnowledgeGraph:
    def __init__(self):
        self.materials: Dict[str, MaterialNode] = {}
        self.labors: Dict[str, LaborNode] = {}
        self.equipments: Dict[str, EquipmentNode] = {}
        self.work_items: Dict[str, WorkItemNode] = {}
        self.suppliers: Dict[str, SupplierNode] = {}
        self.material_requirements: Dict[str, List[MaterialRequirement]] = {}
        self.labor_requirements: Dict[str, List[LaborRequirement]] = {}
        self.equipment_requirements: Dict[str, List[EquipmentRequirement]] = {}
        self.prices: Dict[str, List[PriceRecord]] = {}
        self.price_history: List = []
        self.templates: List = []
        self.segment_overrides: Dict[str, Dict[str, Dict]] = {}

    def add_material(self, m: MaterialNode): self.materials[m.id] = m
    def add_labor(self, l: LaborNode):
        key = f"{l.id}::{l.region}"
        self.labors[key] = l
    def add_equipment(self, e: EquipmentNode): self.equipments[e.id] = e
    def add_work_item(self, w: WorkItemNode): self.work_items[w.id] = w
    def add_supplier(self, s: SupplierNode): self.suppliers[s.id] = s

    def add_material_requirement(self, work_item_id: str, req: MaterialRequirement):
        self.material_requirements.setdefault(work_item_id, []).append(req)

    def add_labor_requirement(self, work_item_id: str, req: LaborRequirement):
        self.labor_requirements.setdefault(work_item_id, []).append(req)

    def add_equipment_requirement(self, work_item_id: str, req: EquipmentRequirement):
        self.equipment_requirements.setdefault(work_item_id, []).append(req)

    def add_price(self, material_id: str, price: PriceRecord):
        self.prices.setdefault(material_id, []).append(price)

    def export_summary(self):
        """Ringkasan isi Knowledge Graph."""
        from datetime import datetime, timezone
        regions = set()
        for prices in self.prices.values():
            for p in prices:
                regions.add(p.region)
        return {
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
            "regions": sorted(regions),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
    def get_unit_price(self, wi_id: str, region: str, price_date: str = None) -> dict:
        """Menghitung harga satuan work item dengan breakdown untuk ACES-500."""
        material_cost = 0.0
        labor_cost = 0.0
        equipment_cost = 0.0
        material_breakdown = []
        labor_breakdown = []
        equipment_breakdown = []
        errors = []

        # Material
        for mat_req in self.material_requirements.get(wi_id, []):
            price = None
            for pr in self.prices.get(mat_req.material_id, []):
                if pr.region == region:
                    price = pr
                    break
            if price is None and self.prices.get(mat_req.material_id):
                price = self.prices[mat_req.material_id][0]
            if price is None:
                errors.append({"type": "missing_price", "material_id": mat_req.material_id})
                continue

            # Validasi rentang waste factor
            waste = mat_req.waste_factor
            if waste < 1.0 or waste > 1.3:
                raise ValueError(f"Waste factor {waste} di luar batas untuk {mat_req.material_id}")

            # Validasi tanggal harga jika price_date disediakan
            if price_date is not None:
                try:
                    from datetime import datetime
                    pd = datetime.fromisoformat(price_date)
                    vf = datetime.fromisoformat(str(price.valid_from))
                    vu = None
                    if price.valid_until is not None:
                        vu = datetime.fromisoformat(str(price.valid_until))
                    if pd < vf or (vu is not None and pd > vu):
                        errors.append({"type": "expired_price", "material_id": mat_req.material_id, "price_date": price_date})
                        continue
                except Exception as e:
                    errors.append({"type": "invalid_price_date", "material_id": mat_req.material_id, "message": str(e)})
                    continue

            price_value = price.price
            if hasattr(price_value, 'value'):
                price_value = price_value.value
            cost = mat_req.coefficient * waste * float(price_value)
            material_cost += cost
            mat_node = self.materials.get(mat_req.material_id)
            volatility = getattr(mat_node, 'volatility_factor', 0.0) if mat_node else 0.0
            material_breakdown.append({
                "material_id": mat_req.material_id,
                "coefficient": mat_req.coefficient,
                "waste_factor": waste,
                "unit_price": float(price_value),
                "cost": round(cost, 4),
                "volatility_factor": volatility,
                "price_source": f"{mat_req.material_id}/{price.region}/{price.valid_from}",
            })

        # Tenaga kerja
        for lab_req in self.labor_requirements.get(wi_id, []):
            lab_candidates = [l for l in self.labors.values() if l.id == lab_req.labor_id]
            lab = None
            # pilih labor dengan region cocok, jika tidak ada pilih yang region kosong
            for candidate in lab_candidates:
                if candidate.region == region:
                    lab = candidate
                    break
            if lab is None:
                for candidate in lab_candidates:
                    if candidate.region == "":
                        lab = candidate
                        break
            if lab is None and lab_candidates:
                lab = lab_candidates[0]
            if lab is None:
                errors.append({"type": "missing_labor", "labor_id": lab_req.labor_id})
                continue
            rate = lab.daily_rate
            if hasattr(rate, 'value'):
                rate = rate.value
            cost = lab_req.coefficient * float(rate)
            labor_cost += cost
            labor_breakdown.append({
                "labor_id": lab_req.labor_id,
                "coefficient": lab_req.coefficient,
                "daily_rate": float(rate),
                "region": lab.region or region,
                "cost": round(cost, 4),
                "wage_source": f"{lab_req.labor_id}/{lab.region or region}",
            })

        # Peralatan
        for eq_req in self.equipment_requirements.get(wi_id, []):
            eq = self.equipments.get(eq_req.equipment_id)
            if eq is None:
                errors.append({"type": "missing_equipment", "equipment_id": eq_req.equipment_id})
                continue
            rate = getattr(eq, 'rate_per_hour', 0) or getattr(eq, 'rate_per_day', 0) or 0
            if hasattr(rate, 'value'):
                rate = rate.value
            rate = float(rate)
            mobilization = getattr(eq, 'mobilization_cost', 0.0) or 0.0
            operator = (getattr(eq, 'operator_cost_per_day', 0.0) or 0.0) * eq_req.coefficient
            fuel = (getattr(eq, 'fuel_cost_per_hour', 0.0) or 0.0) * eq_req.coefficient
            cost = eq_req.coefficient * rate + mobilization + operator + fuel
            equipment_cost += cost
            equipment_breakdown.append({
                "equipment_id": eq_req.equipment_id,
                "coefficient": eq_req.coefficient,
                "rate": rate,
                "mobilization_cost": mobilization,
                "operator_cost": operator,
                "fuel_cost": fuel,
                "cost": round(cost, 4),
                "equipment_source": f"{eq_req.equipment_id}/{region}",
            })

        total = material_cost + labor_cost + equipment_cost
        return {
            "unit_price": round(total, 2),
            "material_cost": round(material_cost, 2),
            "labor_cost": round(labor_cost, 2),
            "equipment_cost": round(equipment_cost, 2),
            "material_breakdown": material_breakdown,
            "labor_breakdown": labor_breakdown,
            "equipment_breakdown": equipment_breakdown,
            "errors": errors,
        }
