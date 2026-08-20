"""Domain Material: Atap dan Genteng"""
def load_atap_genteng(kg):
    from fastra_core.knowledge.nodes import MaterialNode
    items = [
        ("mat-genteng-beton-flat", "Genteng Beton Flat", "buah", "GENTENG", {"tipe":"Beton Flat","harga_patokan":6500}),
        ("mat-genteng-keramik-kanmuri", "Genteng Keramik Kanmuri", "buah", "GENTENG", {"tipe":"Keramik Kanmuri","harga_patokan":11500}),
        ("mat-genteng-metal-berpasir", "Genteng Metal Berpasir", "buah", "GENTENG", {"tipe":"Metal Berpasir","harga_patokan":8500}),
        ("mat-genteng-aspal-bitumen", "Genteng Aspal Bitumen", "buah", "GENTENG", {"tipe":"Aspal Bitumen","harga_patokan":45000}),
        ("mat-spandek-025mm", "Atap Spandek Galvalum 0.25mm", "m", "ATAP_LOGAM", {"tebal":"0.25mm","harga_patokan":45000}),
        ("mat-spandek-030mm", "Atap Spandek Galvalum 0.30mm", "m", "ATAP_LOGAM", {"tebal":"0.30mm","harga_patokan":55000}),
        ("mat-spandek-035mm", "Atap Spandek Galvalum 0.35mm", "m", "ATAP_LOGAM", {"tebal":"0.35mm","harga_patokan":65000}),
        ("mat-spandek-040mm", "Atap Spandek Galvalum 0.40mm", "m", "ATAP_LOGAM", {"tebal":"0.40mm","harga_patokan":78000}),
        ("mat-zincalume-040mm", "Atap Zincalume 0.40mm", "m²", "ATAP_LOGAM", {"tipe":"Zincalume","tebal":"0.40mm","harga_patokan":65000}),
        ("mat-genteng-nok", "Genteng Nok/Bubungan", "buah", "GENTENG", {"tipe":"Nok","harga_patokan":12000}),
        ("mat-aluminium-foil-single", "Aluminium Foil Single Side", "m²", "INSULASI", {"tipe":"Single","harga_patokan":15000}),
        ("mat-aluminium-foil-double", "Aluminium Foil Double Side", "m²", "INSULASI", {"tipe":"Double","harga_patokan":25000}),
        ("mat-glasswool", "Glasswool Insulation", "m²", "INSULASI", {"bahan":"Glasswool","harga_patokan":35000}),
        ("mat-rockwool", "Rockwool Insulation", "m²", "INSULASI", {"bahan":"Rockwool","harga_patokan":45000}),
        ("mat-polycarbonate", "Atap Polycarbonate", "m²", "ATAP_PLASTIK", {"bahan":"Polycarbonate","harga_patokan":85000}),
        ("mat-talang-pvc", "Talang Horizontal PVC", "m'", "TALANG", {"bahan":"PVC","harga_patokan":45000}),
        ("mat-talang-galvalum", "Talang Horizontal Galvalum", "m'", "TALANG", {"bahan":"Galvalum","harga_patokan":65000}),
        ("mat-lisplank-grc", "Lisplank GRC", "m'", "LISPLANK", {"bahan":"GRC","harga_patokan":38000}),
        ("mat-lisplank-kayu", "Lisplank Kayu Kamper", "m'", "LISPLANK", {"bahan":"Kayu Kamper","harga_patokan":55000}),
    ]
    for args in items:
        kg.add_material(MaterialNode(*args))
    print(f"  ✅ Atap & Genteng: {len(items)} material dimuat")
