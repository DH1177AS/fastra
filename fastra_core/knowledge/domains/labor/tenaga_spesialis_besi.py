"""Domain Labor: Tenaga Spesialis Besi"""
def load_tenaga_spesialis_besi(kg):
    from fastra_core.knowledge.nodes import LaborNode
    from fastra_core.primitives.currency import Currency
    items = [
        ("lab-tukang-besi", "Tukang Besi/Baja", "TUKANG_BESI", 165000),
        ("lab-tukang-las", "Tukang Las Konstruksi", "TUKANG_LAS", 175000),
        ("lab-tukang-baja-ringan", "Tukang Baja Ringan", "TUKANG_BAJA_RINGAN", 160000),
        ("lab-tukang-baja-berat", "Tukang Baja Berat/Erector", "TUKANG_BAJA_BERAT", 185000),
    ]
    for args in items:
        kg.add_labor(LaborNode(*args))
    print(f"  ✅ Spesialis Besi: {len(items)} tenaga kerja dimuat")
