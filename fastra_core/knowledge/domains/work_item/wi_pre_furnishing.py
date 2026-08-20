"""Domain Work Item: Pre-Furnishing & Fixture Peralatan - Kelompok XIV"""
def load_wi_pre_furnishing(kg):
    from fastra_core.knowledge.nodes import WorkItemNode
    items = [
        ("wi-closet-rod", "PRF.001", "Pemasangan Gantungan Baju Tanam (Walk-in Closet Rod) Stainless Steel", "unit", "AHSP PUPR", "PRE_FURNISHING"),
        ("wi-motorized-curtain", "PRF.002", "Pemasangan Rel Gorden Otomatis (Smart Motorized Curtain Track) Plafon", "unit", "AHSP PUPR", "PRE_FURNISHING"),
        ("wi-floor-socket-popup", "PRF.003", "Pemasangan Stop Kontak Lantai (Floor Socket Pop-up) Kuningan/Stainless", "unit", "PUIL", "PRE_FURNISHING"),
        ("wi-rotatable-tv-mount", "PRF.004", "Pembuatan Dudukan Televisi Berputar (Rotatable TV Mount Structure) 180°", "unit", "AHSP PUPR", "PRE_FURNISHING"),
        ("wi-smart-mirror", "PRF.005", "Pemasangan Cermin LED Sentuh (Smart Touchscreen Mirror) Kamar Mandi", "unit", "AHSP PUPR", "PRE_FURNISHING"),
        ("wi-kompor-tanam", "PRF.006", "Pemasangan Kompor Tanam Induksi/Gas + Kabel Daya Besar", "unit", "AHSP PUPR", "PRE_FURNISHING"),
        ("wi-cooker-hood", "PRF.007", "Pemasangan Cooker Hood (Penyedot Asap Dapur) + Pipa Pembuangan", "unit", "AHSP PUPR", "PRE_FURNISHING"),
        ("wi-kulkas-tanam", "PRF.008", "Pemasangan Kulkas Tanam (Integrated Refrigerator Fit-out) Panel Kayu", "unit", "AHSP PUPR", "PRE_FURNISHING"),
        ("wi-oven-tanam", "PRF.009", "Pemasangan Oven & Microwave Tanam (Built-in Oven) Tall Cabinet", "unit", "AHSP PUPR", "PRE_FURNISHING"),
        ("wi-dispenser-tanam", "PRF.010", "Pemasangan Dispenser Air Bawah (Bottom Loading Built-in Dispenser)", "unit", "AHSP PUPR", "PRE_FURNISHING"),
        ("wi-undermount-sink", "PRF.011", "Pemasangan Wastafel Dapur Sistem Under-Mount (Bibir Tersembunyi)", "unit", "AHSP PUPR", "PRE_FURNISHING"),
        ("wi-food-waste-disposer", "PRF.012", "Pemasangan Penghancur Sampah Makanan (Food Waste Disposer) Bawah Wastafel", "unit", "AHSP PUPR", "PRE_FURNISHING"),
        ("wi-towel-warmer", "PRF.013", "Pemasangan Gantungan Handuk Hangat (Towel Warmer Rail) Elemen Pemanas", "unit", "AHSP PUPR", "PRE_FURNISHING"),
        ("wi-trampolin-net", "PRF.014", "Pemasangan Trampolin Net / Jaring Santai Void (Tali Tambang Nilon Tebal)", "unit", "AHSP PUPR", "PRE_FURNISHING"),
        ("wi-bedside-light", "PRF.015", "Pemasangan Lampu Baca Dinding Kepala Ranjang (Bedside Reading Light)", "unit", "PUIL", "PRE_FURNISHING"),
    ]
    for args in items:
        kg.add_work_item(WorkItemNode(*args))
    print(f"  Pre-Furnishing: {len(items)} item pekerjaan dimuat")