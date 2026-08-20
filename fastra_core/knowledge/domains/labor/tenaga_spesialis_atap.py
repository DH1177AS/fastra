"""Domain Labor: Tenaga Spesialis Atap"""
def load_tenaga_spesialis_atap(kg):
    from fastra_core.knowledge.nodes import LaborNode
    from fastra_core.primitives.currency import Currency
    items = [
        ("lab-tukang-atap", "Tukang Atap/Genteng", "TUKANG_ATAP", 150000),
        ("lab-tukang-spandek", "Tukang Pasang Spandek/Zincalume", "TUKANG_SPANDEK", 155000),
    ]
    for args in items:
        kg.add_labor(LaborNode(*args))
    print(f"  ✅ Spesialis Atap: {len(items)} tenaga kerja dimuat")
