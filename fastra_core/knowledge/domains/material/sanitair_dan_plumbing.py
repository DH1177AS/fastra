"""Domain Material: Sanitair dan Plumbing"""
def load_sanitair_plumbing(kg):
    from fastra_core.knowledge.nodes import MaterialNode
    items = [
        ("mat-kloset-duduk", "Kloset Duduk Toto", "unit", "SANITAIR", {"tipe":"Duduk","merek":"Toto","harga_patokan":2100000}),
        ("mat-kloset-jongkok", "Kloset Jongkok INA", "unit", "SANITAIR", {"tipe":"Jongkok","merek":"INA","harga_patokan":450000}),
        ("mat-wastafel", "Wastafel Toto", "unit", "SANITAIR", {"merek":"Toto","harga_patokan":1150000}),
        ("mat-kran-tembok", "Kran Tembok Standar", "buah", "KRAN", {"tipe":"Tembok","harga_patokan":85000}),
        ("mat-kran-angsa", "Kran Angsa Wastafel", "buah", "KRAN", {"tipe":"Angsa","harga_patokan":150000}),
        ("mat-shower-set", "Kran Shower Set", "buah", "KRAN", {"tipe":"Shower Set","harga_patokan":350000}),
        ("mat-floor-drain", "Floor Drain Stainless", "buah", "FLOOR_DRAIN", {"bahan":"Stainless","harga_patokan":55000}),
        ("mat-jet-pump", "Pompa Air Jet Pump", "unit", "POMPA_AIR", {"tipe":"Jet Pump","harga_patokan":2250000}),
        ("mat-submersible-pump", "Pompa Submersible/Sumur Dalam", "unit", "POMPA_AIR", {"tipe":"Submersible","harga_patokan":3500000}),
        ("mat-booster-pump", "Pompa Dorong Booster Pump", "unit", "POMPA_AIR", {"tipe":"Booster","harga_patokan":1800000}),
        ("mat-tandon-1000l", "Tandon Air 1000L HDPE", "unit", "TANDON", {"kapasitas":"1000L","bahan":"HDPE","harga_patokan":1800000}),
        ("mat-tandon-500l", "Tandon Air 500L HDPE", "unit", "TANDON", {"kapasitas":"500L","bahan":"HDPE","harga_patokan":950000}),
        ("mat-water-heater-listrik", "Water Heater Listrik 30L", "unit", "WATER_HEATER", {"tipe":"Listrik","kapasitas":"30L","harga_patokan":2500000}),
        ("mat-septic-biotank", "Bio Septic Tank 2m³", "unit", "SEPTIC", {"tipe":"Biotank","kapasitas":"2m³","harga_patokan":4500000}),
    ]
    for args in items:
        kg.add_material(MaterialNode(*args))
    print(f"  ✅ Sanitair & Plumbing: {len(items)} material dimuat")
