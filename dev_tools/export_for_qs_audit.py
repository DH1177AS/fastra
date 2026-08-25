import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pandas as pd
from fastra_core.knowledge.loader import create_fastra_knowledge_graph

OUTPUT = os.path.join(os.path.dirname(__file__), "FASTRA_QS_Audit_Package.xlsx")

def main():
    kg = create_fastra_knowledge_graph()

    mat = [{"id": m.id, "name": m.name, "unit": m.unit, "category": m.category} for m in kg.materials.values()]
    lab = [{"key": k, "id": l.id, "name": l.name, "role": l.role, "region": getattr(l, "region", ""), "daily_rate": float(l.daily_rate.value)} for k, l in kg.labors.items()]
    eq = [{"id": e.id, "name": e.name, "unit": e.unit, "rate_per_day": e.rate_per_day} for e in kg.equipments.values()]
    wi = [{"id": w.id, "code": w.code, "name": w.name, "unit": w.unit, "sni_ref": w.sni_ref} for w in kg.work_items.values()]

    prices = []
    for mid, plist in kg.prices.items():
        for p in plist:
            prices.append({"material_id": mid, "region": p.region, "price": p.price, "valid_from": str(p.valid_from), "valid_until": str(p.valid_until), "source": p.source})

    mat_req = [{"work_item_id": wi_id, "material_id": r.material_id, "coefficient": r.coefficient, "waste_factor": r.waste_factor} for wi_id, reqs in kg.material_requirements.items() for r in reqs]
    lab_req = [{"work_item_id": wi_id, "labor_id": r.labor_id, "coefficient": r.coefficient} for wi_id, reqs in kg.labor_requirements.items() for r in reqs]

    with pd.ExcelWriter(OUTPUT, engine="openpyxl") as writer:
        pd.DataFrame(mat).to_excel(writer, sheet_name="Materials", index=False)
        pd.DataFrame(lab).to_excel(writer, sheet_name="Labor", index=False)
        pd.DataFrame(eq).to_excel(writer, sheet_name="Equipment", index=False)
        pd.DataFrame(wi).to_excel(writer, sheet_name="WorkItems", index=False)
        pd.DataFrame(prices).to_excel(writer, sheet_name="Prices", index=False)
        pd.DataFrame(mat_req).to_excel(writer, sheet_name="Material_Req", index=False)
        pd.DataFrame(lab_req).to_excel(writer, sheet_name="Labor_Req", index=False)

    print(f"Export selesai: {OUTPUT}")

if __name__ == "__main__":
    main()
