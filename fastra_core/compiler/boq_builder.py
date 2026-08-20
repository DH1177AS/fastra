
"""
Stage 8: BOQ Builder - BOQ deterministik + TraceLog sesuai ACES-400 §13.4.
"""
import hashlib
import json
from datetime import datetime, timezone
from typing import Dict, List
from fastra_core.compiler.trace import TraceLog

class BOQBuilder:
    def __init__(self, kg, generated_at=None):
        self.kg = kg
        self.generated_at = generated_at or datetime.now(timezone.utc).isoformat()
        self.pe_to_work_item = {
            'PEK.DIND.001': 'wi-bata-merah-taman',
            'PEK.DIND.002': 'wi-plester-dalam',
            'PEK.DIND.003': 'wi-acian-dalam',
            'PEK.STR.001': 'wi-kolom-bekisting',
            'PEK.STR.002': 'wi-kolom-lt1-rebar-fab',
            'PEK.STR.003': 'wi-kolom-cor-lt1',
            'PEK.STR.004': 'wi-bekisting-balok-lt2',
            'PEK.STR.005': 'wi-balok-lt2-rebar',
            'PEK.STR.006': 'wi-cor-massal-lt2',
            'PEK.STR.007': 'wi-bekisting-plat-lt2',
            'PEK.STR.008': 'wi-plat-lt2-wiremesh',
            'PEK.STR.009': 'wi-cor-massal-lt2',
            'PEK.STR.041': 'wi-tangga-bekisting',
            'PEK.FND.001': 'wi-pile-cap-cor',
            'PEK.FND.002': 'wi-pile-cap-rebar',
            'PEK.ATP.001': 'wi-kudakuda-fab',
            'PEK.ATP.002': 'wi-genteng-utama',
            'PEK.PTU.001': 'wi-daun-pintu-utama',
            'PEK.PTU.002': 'wi-cat-duco-pintu',
            'PEK.JND.001': 'wi-jendela-casement',
            'PEK.JND.002': 'wi-kaca-polos-5mm',
            'PEK.LNT.001': 'wi-granit-rt',
            'PEK.PLF.001': 'wi-gypsum-9mm',
        }
        self._wi_by_id = {wi.id: wi for wi in self.kg.work_items.values()}

    def build(self, quantities: List[Dict], region: str, project_uuid: str) -> Dict:
        divisions = {}
        for q in quantities:
            code = q["work_item_code"]
            wi = self._find_work_item(code)
            item_code = wi.code if wi else code
            item_name = wi.name if wi else q["description"]
            unit = (wi.unit if wi else q["unit"]).replace("m²", "m²").replace("m³", "m³")
            unit_price_data = self.kg.get_unit_price(wi.id, region) if wi else {"unit_price": 0.0}
            div = self._division(item_code, wi.category if wi else "")
            if div not in divisions:
                divisions[div] = {"division_code": div, "division_name": div,
                                  "items": [], "subtotal": 0.0}

            trace = TraceLog(generated_at=self.generated_at)
            trace.add_step(
                stage="GEOMETRY_BUILDER",
                operation="Calculate Gross Quantity",
                input_entity=q["source_entities"][0] if q["source_entities"] else None,
                operation_detail=q.get("detail", ""),
                output_value=f"{q['quantity']} {unit}"
            )
            trace.add_step(
                stage="QUANTITY_GENERATOR",
                operation="Apply Deduction & Net Quantity",
                operation_detail=q.get("detail", ""),
                output_value=f"{q['quantity']} {unit}"
            )
            trace.add_step(
                stage="BOQ_GENERATOR",
                operation="Map to WorkItem",
                mapped_to=item_code,
                output_value=f"{q['quantity']} {unit}"
            )

            boq_item_uuid = hashlib.sha256(
                json.dumps({"item_code": item_code, "quantity": q["quantity"], "entities": q["source_entities"]},
                           sort_keys=True, default=str).encode()
            ).hexdigest()

            boq_item = {
                "boq_item_uuid": boq_item_uuid,
                "item_code": item_code,
                "item_name": item_name,
                "description": q["description"],
                "quantity": q["quantity"],
                "unit": unit,
                "unit_price": unit_price_data.get("unit_price", 0.0),
                "total_price": round(q["quantity"] * unit_price_data.get("unit_price", 0.0), 2),
                "source_entities": q["source_entities"],
                "trace_log": trace.to_dict(),
            }
            divisions[div]["items"].append(boq_item)
            divisions[div]["subtotal"] = round(divisions[div]["subtotal"] + boq_item["total_price"], 2)
        total = round(sum(d["subtotal"] for d in divisions.values()), 2)
        boq_uuid = hashlib.sha256(json.dumps({
            "project_uuid": project_uuid,
            "generated_at": self.generated_at,
            "quantities": quantities
        }, sort_keys=True, default=str).encode()).hexdigest()
        return {
            "boq_uuid": boq_uuid,
            "project_uuid": project_uuid,
            "generated_at": self.generated_at,
            "compiler_version": "1.0.0",
            "total_items": len(quantities),
            "project_total": total,
            "divisions": list(divisions.values()),
            "generated_by": "FASTRA ACES-400 Full Compliance",
        }

    def _find_work_item(self, code):
        wid = self.pe_to_work_item.get(code)
        if wid and wid in self._wi_by_id:
            return self._wi_by_id[wid]
        return None

    def _division(self, code, category=""):
        if category:
            if "STRUKTUR" in category.upper(): return "DIV-04 Pekerjaan Struktur"
            if "DINDING" in category.upper(): return "DIV-05 Pekerjaan Dinding"
            if "ATAP" in category.upper(): return "DIV-08 Pekerjaan Atap"
            if "LANTAI" in category.upper(): return "DIV-06 Pekerjaan Lantai"
            if "PLAFON" in category.upper(): return "DIV-07 Pekerjaan Plafon"
            if "PONDASI" in category.upper(): return "DIV-03 Pekerjaan Pondasi"
            if "KUSEN" in category.upper(): return "DIV-09 Pekerjaan Kusen"
        return "DIV-00 Umum"
