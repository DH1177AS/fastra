"""Domain Labor: Tenaga Spesialis Kayu"""
def load_tenaga_spesialis_kayu(kg):
    from fastra_core.knowledge.nodes import LaborNode
    from fastra_core.primitives.currency import Currency
    items = [
        ("lab-tukang-kayu", "Tukang Kayu", "TUKANG_KAYU", 165000),
        ("lab-tukang-kusen", "Tukang Kusen/Pintu", "TUKANG_KUSEN", 170000),
        ("lab-tukang-plafon", "Tukang Plafon/Partisi", "TUKANG_PLAFON", 155000),
        ("lab-tukang-furniture", "Tukang Furniture Custom", "TUKANG_FURNITURE", 175000),
    ]
    for args in items:
        kg.add_labor(LaborNode(*args))
    print(f"  ✅ Spesialis Kayu: {len(items)} tenaga kerja dimuat")
