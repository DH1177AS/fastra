"""
ACES-500 Cost Engine
Menerjemahkan BOQ menjadi RAB lengkap.
"""

from typing import Optional, Dict
from fastra_core.knowledge.graph import KnowledgeGraph

class CostEngine:
    def __init__(self, kg: KnowledgeGraph, config: Optional[Dict] = None):
        self.kg = kg
        self.config = config or {
            "overhead_pct": 10.0,
            "profit_pct": 10.0,
            "ppn_pct": 11.0,
            "pph_pct": 3.0,
            "contingency_pct": 5.0,
            "inflation_pct": 3.5,
            "duration_months": 12,
            "location_factor": 1.0,
        }

    def generate_rab(self, boq: Dict, region: str) -> Dict:
        # A. Direct Cost (dari BOQ)
        direct_cost = boq["project_total"]

        # B. Overhead
        overhead = direct_cost * self.config["overhead_pct"] / 100

        # C. Profit
        profit = (direct_cost + overhead) * self.config["profit_pct"] / 100

        # D. Dasar Pengenaan Pajak
        dpp = direct_cost + overhead + profit

        # E. PPN
        ppn = dpp * self.config["ppn_pct"] / 100

        # F. PPh Final
        pph = dpp * self.config["pph_pct"] / 100

        # G. Kontingensi
        contingency = direct_cost * self.config["contingency_pct"] / 100

        # H. Eskalasi (sederhana: inflasi tahunan Ã— durasi)
        escalation = dpp * (self.config["inflation_pct"] / 100) * (self.config["duration_months"] / 12)

        # Grand Total
        grand_total = dpp + ppn + pph + contingency + escalation

        return {
            "direct_cost": round(direct_cost, 2),
            "overhead": round(overhead, 2),
            "profit": round(profit, 2),
            "dpp": round(dpp, 2),
            "ppn": round(ppn, 2),
            "pph_final": round(pph, 2),
            "contingency": round(contingency, 2),
            "escalation": round(escalation, 2),
            "grand_total": round(grand_total, 2),
            "location_factor": self.config.get("location_factor", 1.0),
            "generated_by": "FASTRA Cost Engine v1.0",
            "divisions": boq["divisions"],
        }
