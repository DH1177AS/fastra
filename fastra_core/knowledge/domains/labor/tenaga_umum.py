"""
Domain Labor: Tenaga Kerja Umum
Mencakup pekerja, kenek, mandor, kepala tukang, dan operator umum.
"""

def load_tenaga_umum(kg):
    """Load tenaga kerja umum ke Knowledge Graph."""
    
    from fastra_core.knowledge.nodes import LaborNode
    from fastra_core.primitives.currency import Currency
    
    tenaga = [
        ("lab-kenek", "Kenek / Pembantu Tukang", "KENEK", 95000),
        ("lab-pekerja", "Pekerja", "PEKERJA", 130000),
        ("lab-mandor", "Mandor Lapangan", "MANDOR", 200000),
        ("lab-kepala-tukang", "Kepala Tukang", "KEPALA_TUKANG", 180000),
        ("lab-drafter", "Drafter Lapangan", "DRAFTER", 175000),
        ("lab-surveyor", "Surveyor", "SURVEYOR", 185000),
        ("lab-operator-excavator", "Operator Alat Berat/Excavator", "OPERATOR_ALAT", 250000),
        ("lab-sopir-truk", "Sopir Truk/Dump Truck", "SOPIR", 220000),
        ("lab-operator-crane", "Operator Crane Mobile", "OPERATOR_CRANE", 280000),
        ("lab-operator-paver", "Operator Asphalt/Concrete Paver", "OPERATOR_PAVER", 260000),
        ("lab-operator-roller", "Operator Tandem/Pneumatic Roller", "OPERATOR_ROLLER", 240000),
    ]
    
    for args in tenaga:
        kg.add_labor(LaborNode(*args))
    
    print(f"  ✅ Tenaga Umum: {len(tenaga)} tenaga kerja dimuat")

