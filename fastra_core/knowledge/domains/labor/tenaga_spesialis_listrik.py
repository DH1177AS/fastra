"""Domain Labor: Tenaga Spesialis Listrik"""
def load_tenaga_spesialis_listrik(kg):
    from fastra_core.knowledge.nodes import LaborNode
    from fastra_core.primitives.currency import Currency
    items = [
        ("lab-tukang-listrik", "Tukang Listrik", "TUKANG_LISTRIK", 155000),
        ("lab-tukang-panel", "Tukang Panel/Panel Maker", "TUKANG_PANEL", 170000),
        ("lab-tukang-cctv", "Teknisi CCTV/Data", "TEKNISI_CCTV", 165000),
        ("lab-tukang-sound", "Teknisi Sound System", "TEKNISI_SOUND", 160000),
        ("lab-tukang-surya", "Teknisi Panel Surya", "TEKNISI_SURYA", 175000),
    ]
    for args in items:
        kg.add_labor(LaborNode(*args))
    print(f"  ✅ Spesialis Listrik: {len(items)} tenaga kerja dimuat")
