"""Domain Material: Cat dan Pelapis"""
def load_cat_pelapis(kg):
    from fastra_core.knowledge.nodes import MaterialNode
    items = [
        ("mat-cat-interior-dulux-25kg", "Cat Interior Dulux Pentalite 25kg", "pail", "CAT_INTERIOR", {"merek":"Dulux","kemasan":"25kg","harga_patokan":340000}),
        ("mat-cat-interior-nippon-25kg", "Cat Interior Nippon Vinilex 25kg", "pail", "CAT_INTERIOR", {"merek":"Nippon","kemasan":"25kg","harga_patokan":155000}),
        ("mat-cat-interior-avian-25kg", "Cat Interior Avian 25kg", "pail", "CAT_INTERIOR", {"merek":"Avian","kemasan":"25kg","harga_patokan":130000}),
        ("mat-cat-interior-mowilex-25kg", "Cat Interior Mowilex Emulsion 25kg", "pail", "CAT_INTERIOR", {"merek":"Mowilex","kemasan":"25kg","harga_patokan":310000}),
        ("mat-cat-eksterior-dulux-25kg", "Cat Eksterior Dulux Weathershield 25kg", "pail", "CAT_EKSTERIOR", {"merek":"Dulux","kemasan":"25kg","harga_patokan":480000}),
        ("mat-cat-eksterior-nippon-25kg", "Cat Eksterior Nippon Weatherbond 25kg", "pail", "CAT_EKSTERIOR", {"merek":"Nippon","kemasan":"25kg","harga_patokan":420000}),
        ("mat-cat-kayu-melamik", "Cat Melamik Kayu", "kg", "CAT_KAYU", {"harga_patokan":42000}),
        ("mat-cat-besi-anti-karat", "Cat Anti Karat Zinc Chromate", "kg", "CAT_BESI", {"harga_patokan":38000}),
        ("mat-cat-intumescent", "Cat Fireproofing Intumescent", "m²", "CAT_FIRE", {"fungsi":"Anti Api","harga_patokan":185000}),
        ("mat-plamir", "Plamir Dinding", "kg", "PLAMIR", {"harga_patokan":18000}),
        ("mat-dempul-kayu", "Dempul Kayu", "kg", "DEMPUL", {"harga_patokan":25000}),
        ("mat-thinner", "Thinner", "liter", "THINNER", {"harga_patokan":22000}),
    ]
    for args in items:
        kg.add_material(MaterialNode(*args))
    print(f"  ✅ Cat & Pelapis: {len(items)} material dimuat")
