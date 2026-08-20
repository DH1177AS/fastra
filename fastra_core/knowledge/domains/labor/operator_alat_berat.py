"""Domain Labor: Operator Alat Berat"""
def load_operator_alat_berat(kg):
    from fastra_core.knowledge.nodes import LaborNode
    from fastra_core.primitives.currency import Currency
    items = [
        ("lab-operator-excavator", "Operator Excavator", "OPERATOR_ALAT", 250000),
        ("lab-operator-bulldozer", "Operator Bulldozer", "OPERATOR_ALAT", 260000),
        ("lab-operator-crane", "Operator Crane Mobile 25Ton", "OPERATOR_CRANE", 280000),
        ("lab-operator-roller", "Operator Tandem/Pneumatic Roller", "OPERATOR_ROLLER", 240000),
        ("lab-operator-paver", "Operator Asphalt/Concrete Paver", "OPERATOR_PAVER", 260000),
        ("lab-operator-grader", "Operator Motor Grader", "OPERATOR_GRADER", 255000),
        ("lab-operator-borepile", "Operator Mesin Bore Pile", "OPERATOR_BOREPILE", 270000),
        ("lab-operator-jackin", "Operator Jack-In Pile Hidrolik", "OPERATOR_JACKIN", 265000),
        ("lab-operator-forklift", "Operator Forklift", "OPERATOR_FORKLIFT", 200000),
        ("lab-operator-tbm", "Operator TBM (Tunnel Boring Machine)", "OPERATOR_TBM", 350000),
    ]
    for args in items:
        kg.add_labor(LaborNode(*args))
    print(f"  ✅ Operator Alat Berat: {len(items)} tenaga kerja dimuat")
