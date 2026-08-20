"""Domain Material: Kabel dan Listrik"""
def load_kabel_listrik(kg):
    from fastra_core.knowledge.nodes import MaterialNode
    items = [
        ("mat-kabel-nym-2x15", "Kabel NYM 2x1.5mm²", "m", "KABEL", {"tipe":"NYM 2x1.5","harga_patokan":12000}),
        ("mat-kabel-nym-2x25", "Kabel NYM 2x2.5mm²", "m", "KABEL", {"tipe":"NYM 2x2.5","harga_patokan":18000}),
        ("mat-kabel-nym-3x25", "Kabel NYM 3x2.5mm²", "m", "KABEL", {"tipe":"NYM 3x2.5","harga_patokan":25000}),
        ("mat-kabel-nym-4x4", "Kabel NYM 4x4mm²", "m", "KABEL", {"tipe":"NYM 4x4","harga_patokan":42000}),
        ("mat-kabel-nyy-4x10", "Kabel NYY 4x10mm²", "m", "KABEL", {"tipe":"NYY 4x10","harga_patokan":85000}),
        ("mat-kabel-nyy-4x16", "Kabel NYY 4x16mm²", "m", "KABEL", {"tipe":"NYY 4x16","harga_patokan":125000}),
        ("mat-mcb-6a", "MCB 6A Schneider", "buah", "MCB", {"ampere":"6A","merek":"Schneider","harga_patokan":58000}),
        ("mat-mcb-10a", "MCB 10A Schneider", "buah", "MCB", {"ampere":"10A","merek":"Schneider","harga_patokan":68000}),
        ("mat-mcb-16a", "MCB 16A Schneider", "buah", "MCB", {"ampere":"16A","merek":"Schneider","harga_patokan":72000}),
        ("mat-mcb-20a", "MCB 20A Schneider", "buah", "MCB", {"ampere":"20A","merek":"Schneider","harga_patokan":76000}),
        ("mat-saklar-tunggal", "Saklar Tunggal Panasonic", "buah", "SAKLAR", {"tipe":"Tunggal","merek":"Panasonic","harga_patokan":22000}),
        ("mat-saklar-ganda", "Saklar Ganda Panasonic", "buah", "SAKLAR", {"tipe":"Ganda","merek":"Panasonic","harga_patokan":29000}),
        ("mat-stop-kontak", "Stop Kontak Panasonic", "buah", "STOP_KONTAK", {"merek":"Panasonic","harga_patokan":26000}),
        ("mat-pipa-konduit-20mm", "Pipa Konduit PVC 20mm", "batang", "KONDUIT", {"diameter":"20mm","harga_patokan":12000}),
        ("mat-box-sekring", "Box Sekring 4 Group", "unit", "BOX_SEKRING", {"group":4,"harga_patokan":185000}),
        ("mat-panel-lvmdp", "Panel LVMDP 100A", "unit", "PANEL", {"kapasitas":"100A","harga_patokan":2500000}),
        ("mat-lampu-led-9w", "Lampu LED Bulb 9W", "buah", "LAMPU", {"daya":"9W","harga_patokan":45000}),
        ("mat-lampu-led-18w", "Lampu LED Bulb 18W", "buah", "LAMPU", {"daya":"18W","harga_patokan":95000}),
        ("mat-downlight-6w", "Downlight LED 6W", "buah", "LAMPU", {"tipe":"Downlight","daya":"6W","harga_patokan":55000}),
        ("mat-kabel-lan-cat6", "Kabel LAN Cat6", "m", "KABEL_DATA", {"tipe":"Cat6","harga_patokan":8500}),
    ]
    for args in items:
        kg.add_material(MaterialNode(*args))
    print(f"  ✅ Kabel & Listrik: {len(items)} material dimuat")
