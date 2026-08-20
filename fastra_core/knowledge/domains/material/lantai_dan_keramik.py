"""Domain Material: Lantai dan Keramik"""
def load_lantai_keramik(kg):
    from fastra_core.knowledge.nodes import MaterialNode
    items = [
        ("mat-keramik-40x40-kw1", "Keramik Lantai 40x40 KW1", "dus", "KERAMIK", {"ukuran":"40x40","kw":"1","harga_patokan":62000}),
        ("mat-keramik-50x50-kw1", "Keramik Lantai 50x50 KW1", "dus", "KERAMIK", {"ukuran":"50x50","kw":"1","harga_patokan":85000}),
        ("mat-keramik-60x60-kw1", "Keramik Lantai 60x60 KW1", "dus", "KERAMIK", {"ukuran":"60x60","kw":"1","harga_patokan":120000}),
        ("mat-keramik-dinding-25x40", "Keramik Dinding 25x40cm", "dus", "KERAMIK_DINDING", {"ukuran":"25x40","harga_patokan":48000}),
        ("mat-keramik-dinding-30x60", "Keramik Dinding 30x60cm Motif Marmer", "dus", "KERAMIK_DINDING", {"ukuran":"30x60","motif":"Marmer","harga_patokan":65000}),
        ("mat-granit-60x60", "Granit Tile 60x60cm", "dus", "GRANIT", {"ukuran":"60x60","harga_patokan":165000}),
        ("mat-granit-80x80", "Granit Tile 80x80cm", "dus", "GRANIT", {"ukuran":"80x80","harga_patokan":285000}),
        ("mat-granit-100x100", "Granit Tile 100x100cm", "dus", "GRANIT", {"ukuran":"100x100","harga_patokan":450000}),
        ("mat-marmer-lokal-60x60", "Marmer Lokal 60x60cm", "dus", "MARmer", {"ukuran":"60x60","harga_patokan":380000}),
        ("mat-homogeneous-60x60", "Homogeneous Tile 60x60 KW1", "dus", "HOMOGENEOUS", {"ukuran":"60x60","harga_patokan":145000}),
        ("mat-vinyl-plank", "Vinyl Plank Click System", "m²", "VINYL", {"tipe":"Click","harga_patokan":85000}),
        ("mat-vinyl-sheet", "Vinyl Sheet 2mm", "m²", "VINYL", {"tebal":"2mm","harga_patokan":55000}),
        ("mat-karpet-tile", "Karpet Tile 50x50cm", "m²", "KARPET", {"ukuran":"50x50","harga_patokan":95000}),
        ("mat-parket-engineered", "Parket Engineered Oak 15mm", "m²", "PARKET", {"kayu":"Oak","tebal":"15mm","harga_patokan":285000}),
        ("mat-lantai-spc", "Lantai SPC (Stone Plastic Composite)", "m²", "SPC", {"harga_patokan":125000}),
    ]
    for args in items:
        kg.add_material(MaterialNode(*args))
    print(f"  ✅ Lantai & Keramik: {len(items)} material dimuat")
