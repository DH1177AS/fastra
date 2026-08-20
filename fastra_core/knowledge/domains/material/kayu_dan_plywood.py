"""Domain Material: Kayu dan Plywood"""
def load_kayu_plywood(kg):
    from fastra_core.knowledge.nodes import MaterialNode
    items = [
        ("mat-kayu-meranti-balok", "Kayu Meranti Balok", "m³", "KAYU", {"jenis":"Meranti","bentuk":"Balok","kelas":"II","harga_patokan":3200000}),
        ("mat-kayu-meranti-papan", "Kayu Meranti Papan", "m³", "KAYU", {"jenis":"Meranti","bentuk":"Papan","kelas":"II","harga_patokan":3360000}),
        ("mat-kayu-kamper-balok", "Kayu Kamper Balok", "m³", "KAYU", {"jenis":"Kamper","bentuk":"Balok","kelas":"II","harga_patokan":4500000}),
        ("mat-kayu-kamper-papan", "Kayu Kamper Papan", "m³", "KAYU", {"jenis":"Kamper","bentuk":"Papan","kelas":"II","harga_patokan":4725000}),
        ("mat-kayu-jati-balok", "Kayu Jati Balok", "m³", "KAYU", {"jenis":"Jati","bentuk":"Balok","kelas":"I","harga_patokan":12500000}),
        ("mat-kayu-jati-papan", "Kayu Jati Papan", "m³", "KAYU", {"jenis":"Jati","bentuk":"Papan","kelas":"I","harga_patokan":13125000}),
        ("mat-kayu-borneo-balok", "Kayu Borneo Balok", "m³", "KAYU", {"jenis":"Borneo","bentuk":"Balok","kelas":"III","harga_patokan":2600000}),
        ("mat-kayu-borneo-papan", "Kayu Borneo Papan", "m³", "KAYU", {"jenis":"Borneo","bentuk":"Papan","kelas":"III","harga_patokan":2730000}),
        ("mat-kayu-bengkirai-balok", "Kayu Bengkirai Balok", "m³", "KAYU", {"jenis":"Bengkirai","bentuk":"Balok","kelas":"I","harga_patokan":5800000}),
        ("mat-plywood-4mm", "Plywood 4mm", "lembar", "PLYWOOD", {"tebal":"4mm","harga_patokan":65000}),
        ("mat-plywood-6mm", "Plywood 6mm", "lembar", "PLYWOOD", {"tebal":"6mm","harga_patokan":85000}),
        ("mat-plywood-9mm", "Plywood 9mm", "lembar", "PLYWOOD", {"tebal":"9mm","harga_patokan":125000}),
        ("mat-plywood-12mm", "Plywood 12mm", "lembar", "PLYWOOD", {"tebal":"12mm","harga_patokan":165000}),
        ("mat-plywood-15mm", "Plywood 15mm", "lembar", "PLYWOOD", {"tebal":"15mm","harga_patokan":205000}),
        ("mat-plywood-18mm", "Plywood 18mm", "lembar", "PLYWOOD", {"tebal":"18mm","harga_patokan":245000}),
    ]
    for args in items:
        kg.add_material(MaterialNode(*args))
    print(f"  ✅ Kayu & Plywood: {len(items)} material dimuat")
