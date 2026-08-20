"""Domain Material: Dinding dan Partisi"""
def load_dinding_partisi(kg):
    from fastra_core.knowledge.nodes import MaterialNode
    items = [
        ("mat-bata-merah", "Bata Merah Oven", "buah", "BATA", {"ukuran":"5x11x22cm","harga_patokan":900}),
        ("mat-bata-ringan-10cm", "Bata Ringan AAC 10cm", "m³", "BATA_RINGAN", {"tebal":"10cm","harga_patokan":650000}),
        ("mat-bata-ringan-7cm", "Bata Ringan AAC 7.5cm", "m³", "BATA_RINGAN", {"tebal":"7.5cm","harga_patokan":620000}),
        ("mat-batako", "Batako Semen", "buah", "BATAKO", {"ukuran":"10x20x40cm","harga_patokan":3500}),
        ("mat-glass-block", "Glass Block 20x20cm", "buah", "GLASS_BLOCK", {"ukuran":"20x20cm","harga_patokan":25000}),
        ("mat-partisi-gypsum", "Partisi Gypsum 9mm Double", "m²", "PARTISI", {"tebal":"9mm","tipe":"Double","harga_patokan":65000}),
        ("mat-partisi-aluminium", "Partisi Aluminium + Kaca", "m²", "PARTISI", {"bahan":"Aluminium+Kaca","harga_patokan":450000}),
        ("mat-panel-wpc", "Panel Dinding WPC", "m²", "PANEL_DINDING", {"bahan":"WPC","harga_patokan":165000}),
        ("mat-batu-alam-andesit", "Batu Alam Andesit Bakar", "m²", "BATU_ALAM", {"jenis":"Andesit","finish":"Bakar","harga_patokan":350000}),
        ("mat-batu-alam-palimanan", "Batu Alam Palimanan", "m²", "BATU_ALAM", {"jenis":"Palimanan","harga_patokan":280000}),
        ("mat-batu-alam-candi", "Batu Alam Candi", "m²", "BATU_ALAM", {"jenis":"Candi","harga_patokan":320000}),
    ]
    for args in items:
        kg.add_material(MaterialNode(*args))
    print(f"  ✅ Dinding & Partisi: {len(items)} material dimuat")
