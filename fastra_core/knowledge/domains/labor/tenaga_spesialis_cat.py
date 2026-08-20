"""Domain Labor: Tenaga Spesialis Cat"""
def load_tenaga_spesialis_cat(kg):
    from fastra_core.knowledge.nodes import LaborNode
    from fastra_core.primitives.currency import Currency
    items = [
        ("lab-tukang-cat", "Tukang Cat", "TUKANG_CAT", 155000),
        ("lab-tukang-cat-duco", "Tukang Cat Duco/Semprot", "TUKANG_CAT_DUCO", 175000),
        ("lab-tukang-politur", "Tukang Politur/Melamik", "TUKANG_POLITUR", 165000),
        ("lab-tukang-waterproofing", "Tukang Waterproofing", "TUKANG_WATERPROOFING", 150000),
    ]
    for args in items:
        kg.add_labor(LaborNode(*args))
    print(f"  ✅ Spesialis Cat: {len(items)} tenaga kerja dimuat")
