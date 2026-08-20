"""Domain Labor: Tenaga Profesional"""
def load_tenaga_profesional(kg):
    from fastra_core.knowledge.nodes import LaborNode
    from fastra_core.primitives.currency import Currency
    items = [
        ("lab-engineer-sipil", "Civil/Structural Engineer", "ENGINEER_SIPIL", 350000),
        ("lab-engineer-mep", "MEP Engineer", "ENGINEER_MEP", 350000),
        ("lab-arsitek", "Architect/Arsitek", "ARSITEK", 350000),
        ("lab-qs-estimator", "Quantity Surveyor/Estimator", "QS_ESTIMATOR", 350000),
        ("lab-drafter", "Drafter CAD/BIM", "DRAFTER", 200000),
        ("lab-supervisor", "Supervisor Lapangan", "SUPERVISOR", 250000),
        ("lab-safety-officer", "Safety Officer/K3", "SAFETY_OFFICER", 225000),
        ("lab-surveyor", "Surveyor/Geomatik", "SURVEYOR", 200000),
    ]
    for args in items:
        kg.add_labor(LaborNode(*args))
    print(f"  ✅ Tenaga Profesional: {len(items)} tenaga kerja dimuat")
