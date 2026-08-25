
"""
Parser untuk Segment_Calibration.xlsx.
Memuat override AHSP per segmen ke dalam kg.segment_overrides.
"""
import pandas as pd
from typing import Any, Dict, List, Optional
from collections import defaultdict

SEGMENT_FILE = r"D:\fastra_projects\Segment_Calibration.xlsx"

def load_segment_calibration(kg: Any) -> None:
    """Baca Segment_Calibration.xlsx dan isi kg.segment_overrides."""
    if not kg:
        return
    try:
        df = pd.read_excel(SEGMENT_FILE, sheet_name="Segment_Calibration")
    except Exception as e:
        print(f"Gagal baca Segment_Calibration: {e}")
        kg.segment_overrides = {}
        return

    kg.segment_overrides = defaultdict(lambda: defaultdict(lambda: {
        "materials": [],
        "labors": [],
        "equipments": [],
        "audit_check_price": None,
    }))

    for _, row in df.iterrows():
        segment = str(row.get("Segment", "")).strip()
        wi_code = str(row.get("WorkItem_Code", "")).strip()
        if not segment or not wi_code:
            continue

        over = kg.segment_overrides[segment][wi_code]

        material_id = row.get("Material_ID")
        labor_id = row.get("Labor_ID")
        equipment_id = row.get("Equipment_ID")
        coeff = row.get("Coefficient_Override")
        price = row.get("Price_Override")
        waste_override = row.get("Waste_Override")

        # Baris AUDIT-CHECK bukan resource; simpan HSP resmi
        if str(material_id).upper() == "AUDIT-CHECK":
            if pd.notna(price):
                over["audit_check_price"] = float(price)
            continue

        try:
            coeff = float(coeff) if pd.notna(coeff) else None
        except (TypeError, ValueError):
            coeff = None

        try:
            price_val = float(price) if pd.notna(price) else None
        except (TypeError, ValueError):
            price_val = None

        try:
            waste_extra = float(waste_override) if pd.notna(waste_override) else 0.0
        except (TypeError, ValueError):
            waste_extra = 0.0
        waste_factor = 1.0 + waste_extra

        source = str(row.get("Source", "")).strip()

        if pd.notna(material_id) and coeff is not None and price_val is not None:
            over["materials"].append({
                "id": str(material_id).strip(),
                "coefficient": coeff,
                "price": price_val,
                "waste_factor": waste_factor,
                "source": source,
            })
        if pd.notna(labor_id) and coeff is not None and price_val is not None:
            over["labors"].append({
                "id": str(labor_id).strip(),
                "coefficient": coeff,
                "price": price_val,
                "source": source,
            })
        if pd.notna(equipment_id) and coeff is not None and price_val is not None:
            over["equipments"].append({
                "id": str(equipment_id).strip(),
                "coefficient": coeff,
                "price": price_val,
                "source": source,
            })

    print(f"Segment calibration dimuat: {len(kg.segment_overrides)} segmen")


def calculate_unit_price_from_override(override: Dict[str, Any]) -> Dict[str, Any]:
    """Hitung unit price dari data override per segmen."""
    material_cost = 0.0
    labor_cost = 0.0
    equipment_cost = 0.0
    material_breakdown = []
    labor_breakdown = []
    equipment_breakdown = []

    for m in override.get("materials", []):
        cost = m["coefficient"] * m["price"] * m.get("waste_factor", 1.0)
        material_cost += cost
        material_breakdown.append({
            "material_id": m["id"],
            "coefficient": m["coefficient"],
            "waste_factor": m.get("waste_factor", 1.0),
            "unit_price": m["price"],
            "cost": round(cost, 4),
            "price_source": m.get("source", ""),
        })

    for l in override.get("labors", []):
        cost = l["coefficient"] * l["price"]
        labor_cost += cost
        labor_breakdown.append({
            "labor_id": l["id"],
            "coefficient": l["coefficient"],
            "daily_rate": l["price"],
            "cost": round(cost, 4),
            "wage_source": l.get("source", ""),
        })

    for e in override.get("equipments", []):
        cost = e["coefficient"] * e["price"]
        equipment_cost += cost
        equipment_breakdown.append({
            "equipment_id": e["id"],
            "coefficient": e["coefficient"],
            "rate": e["price"],
            "cost": round(cost, 4),
            "equipment_source": e.get("source", ""),
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
        "errors": [],
    }
