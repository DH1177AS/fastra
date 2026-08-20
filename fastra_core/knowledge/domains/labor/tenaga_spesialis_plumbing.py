"""Domain Labor: Tenaga Spesialis Plumbing"""
def load_tenaga_spesialis_plumbing(kg):
    from fastra_core.knowledge.nodes import LaborNode
    from fastra_core.primitives.currency import Currency
    items = [
        ("lab-tukang-plumbing", "Tukang Plumbing/Pipa", "TUKANG_PLUMBING", 150000),
        ("lab-tukang-pompa", "Teknisi Pompa Air", "TEKNISI_POMPA", 160000),
        ("lab-tukang-sanitasi", "Tukang Sanitasi/Kloset", "TUKANG_SANITASI", 145000),
    ]
    for args in items:
        kg.add_labor(LaborNode(*args))
    print(f"  ✅ Spesialis Plumbing: {len(items)} tenaga kerja dimuat")
