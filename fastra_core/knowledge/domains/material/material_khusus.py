"""Domain Material: Material Khusus (Aluminium, Kaca, AC)"""
def load_material_khusus(kg):
    from fastra_core.knowledge.nodes import MaterialNode
    items = [
        ("mat-kusen-aluminium-4in", "Kusen Aluminium 4 inch Powder Coating", "m'", "KUSEN_ALUMINIUM", {"ukuran":"4\"","finish":"Powder Coating","harga_patokan":185000}),
        ("mat-kusen-aluminium-3in", "Kusen Aluminium 3 inch", "m'", "KUSEN_ALUMINIUM", {"ukuran":"3\"","harga_patokan":145000}),
        ("mat-pintu-aluminium", "Pintu Aluminium + Kaca", "unit", "PINTU_ALUMINIUM", {"harga_patokan":2200000}),
        ("mat-jendela-aluminium", "Jendela Aluminium + Kaca", "unit", "JENDELA_ALUMINIUM", {"harga_patokan":1500000}),
        ("mat-kaca-polos-5mm", "Kaca Polos 5mm", "m²", "KACA", {"tebal":"5mm","tipe":"Polos","harga_patokan":185000}),
        ("mat-kaca-polos-8mm", "Kaca Polos 8mm", "m²", "KACA", {"tebal":"8mm","tipe":"Polos","harga_patokan":285000}),
        ("mat-kaca-tempered-10mm", "Kaca Tempered 10mm", "m²", "KACA", {"tebal":"10mm","tipe":"Tempered","harga_patokan":450000}),
        ("mat-kaca-tempered-12mm", "Kaca Tempered 12mm", "m²", "KACA", {"tebal":"12mm","tipe":"Tempered","harga_patokan":550000}),
        ("mat-ac-split-1pk", "AC Split 1 PK Daikin", "unit", "AC", {"tipe":"Split","pk":"1","merek":"Daikin","harga_patokan":4830000}),
        ("mat-ac-split-2pk", "AC Split 2 PK Daikin", "unit", "AC", {"tipe":"Split","pk":"2","merek":"Daikin","harga_patokan":8280000}),
        ("mat-ac-cassette-3pk", "AC Cassette 3 PK", "unit", "AC", {"tipe":"Cassette","pk":"3","harga_patokan":12500000}),
        ("mat-exhaust-fan-10in", "Exhaust Fan 10 inch", "unit", "VENTILASI", {"ukuran":"10\"","harga_patokan":350000}),
        ("mat-exhaust-fan-12in", "Exhaust Fan 12 inch", "unit", "VENTILASI", {"ukuran":"12\"","harga_patokan":450000}),
        ("mat-acp-panel", "ACP (Aluminium Composite Panel)", "m²", "FASAD", {"bahan":"ACP","harga_patokan":285000}),
        ("mat-curtain-wall", "Curtain Wall Aluminium + Kaca", "m²", "FASAD", {"bahan":"Aluminium+Kaca","harga_patokan":850000}),
    ]
    for args in items:
        kg.add_material(MaterialNode(*args))
    print(f"  ✅ Material Khusus: {len(items)} material dimuat")
