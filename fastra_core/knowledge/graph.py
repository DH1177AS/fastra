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

    def add_material(self, m: MaterialNode): self.materials[m.id] = m
    def add_labor(self, l: LaborNode): self.labors[l.id] = l
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
    def get_unit_price(self, wi_id: str, region: str) -> dict:
        """Menghitung harga satuan work item berdasarkan data produksi (Fase 2)."""
        material_cost = 0.0; labor_cost = 0.0; equipment_cost = 0.0
        for mat_req in self.material_requirements.get(wi_id, []):
            price = None
            if mat_req.material_id in self.prices:
                for pr in self.prices[mat_req.material_id]:
                    if pr.region == region: price = pr.price; break
                if not price and self.prices[mat_req.material_id]: price = self.prices[mat_req.material_id][0].price
            if price:
                if hasattr(price, 'value'): price = price.value
                material_cost += mat_req.coefficient * (mat_req.waste_factor if hasattr(mat_req,'waste_factor') else 1.0) * float(price)
        for lab_req in self.labor_requirements.get(wi_id, []):
            lab = self.labors.get(lab_req.labor_id)
            if lab:
                rate = lab.daily_rate; 
                if hasattr(rate, 'value'): rate = rate.value
                labor_cost += lab_req.coefficient * float(rate)
        for eq_req in self.equipment_requirements.get(wi_id, []):
            eq = self.equipments.get(eq_req.equipment_id)
            if eq:
                rate = getattr(eq, 'rate_per_hour', 0) or 0
                if hasattr(rate, 'value'): rate = rate.value
                equipment_cost += eq_req.coefficient * float(rate)
        up = material_cost + labor_cost + equipment_cost
        return {"unit_price": round(up,2),"material_cost":round(material_cost,2),"labor_cost":round(labor_cost,2),"equipment_cost":round(equipment_cost,2)}
