"""Domain Material: Plafon dan Rangka"""
def load_plafon_rangka(kg):
    from fastra_core.knowledge.nodes import MaterialNode
    items = [
        ("mat-gypsum-9mm", "Papan Gypsum 9mm", "lembar", "GYPSUM", {"tebal":"9mm","harga_patokan":65000}),
        ("mat-gypsum-12mm", "Papan Gypsum 12mm", "lembar", "GYPSUM", {"tebal":"12mm","harga_patokan":85000}),
        ("mat-grc-board", "Papan GRC Board", "lembar", "GRC", {"harga_patokan":75000}),
        ("mat-kalsiboard", "Papan Kalsiboard", "lembar", "KALSIBOARD", {"harga_patokan":55000}),
        ("mat-plafon-pvc", "Plafon PVC Panel", "m²", "PLAFON_PVC", {"harga_patokan":45000}),
        ("mat-plafon-akustik", "Plafon Akustik Tile 60x60cm", "m²", "PLAFON_AKUSTIK", {"ukuran":"60x60","harga_patokan":95000}),
        ("mat-hollow-2x4", "Rangka Hollow Galvalum 2x4cm", "batang", "RANGKA_HOLLOW", {"ukuran":"2x4cm","harga_patokan":21500}),
        ("mat-hollow-4x4", "Rangka Hollow Galvalum 4x4cm", "batang", "RANGKA_HOLLOW", {"ukuran":"4x4cm","harga_patokan":38000}),
        ("mat-list-gypsum", "List Profil Gypsum 5cm", "m'", "LIST_PLAFON", {"lebar":"5cm","harga_patokan":8500}),
        ("mat-list-gypsum-10cm", "List Profil Gypsum 10cm", "m'", "LIST_PLAFON", {"lebar":"10cm","harga_patokan":12500}),
    ]
    for args in items:
        kg.add_material(MaterialNode(*args))
    print(f"  ✅ Plafon & Rangka: {len(items)} material dimuat")
