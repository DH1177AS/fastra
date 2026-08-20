"""
Domain Labor: Tenaga Spesialis Batu dan Pekerjaan Dinding
"""

def load_tenaga_spesialis_batu(kg):
    """Load tenaga spesialis batu, dinding, plester."""
    
    from fastra_core.knowledge.nodes import LaborNode
    from fastra_core.primitives.currency import Currency
    
    tenaga = [
        ("lab-tukang-gali", "Tukang Gali Tanah", "TUKANG_GALI", 125000),
        ("lab-tukang-batu", "Tukang Batu", "TUKANG_BATU", 160000),
        ("lab-tukang-keramik", "Tukang Keramik", "TUKANG_KERAMIK", 145000),
        ("lab-tukang-waterproofing", "Tukang Waterproofing", "TUKANG_WATERPROOFING", 150000),
        ("lab-tukang-finishing", "Tukang Finishing Dinding", "TUKANG_FINISHING", 140000),
        ("lab-tukang-bekisting", "Tukang Bekisting", "TUKANG_BEKISTING", 145000),
    ]
    
    for args in tenaga:
        kg.add_labor(LaborNode(*args))
    
    print(f"  ✅ Spesialis Batu: {len(tenaga)} tenaga kerja dimuat")

