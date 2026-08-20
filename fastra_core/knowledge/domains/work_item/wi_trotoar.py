"""Domain Work Item: Trotoar & Pedestrian - Kelompok XXVI"""
def load_wi_trotoar(kg):
    from fastra_core.knowledge.nodes import WorkItemNode
    items = [
        ("wi-ukur-lebar-trotoar", "TRO.001", "Pengukuran Jalur Lebar Trotoar Sesuai Gambar Rencana Ruang Jalan", "m'", "Spesifikasi Trotoar", "TROTOAR"),
        ("wi-bobokan-aspal-trotoar", "TRO.002", "Pembobokan Aspal/Tanah Samping Jalan untuk Kedudukan Struktur Trotoar", "m'", "Spesifikasi Trotoar", "TROTOAR"),
        ("wi-kanstin-jepit", "TRO.003", "Pemasangan Batu Kanstin Jepit Beton Pracetak Batas Trotoar dengan Jalan Raya", "m'", "Spesifikasi Trotoar", "TROTOAR"),
        ("wi-mortar-sela-kanstin", "TRO.004", "Pengecoran Mortar Semen Pengunci Sela Antar Kanstin Trotoar", "m'", "Spesifikasi Trotoar", "TROTOAR"),
        ("wi-kanstin-stype", "TRO.005", "Pemasangan Batu Kanstin Jenis Berlubang untuk Saluran Tangkapan Air (Kanstin S-Type)", "m'", "Spesifikasi Trotoar", "TROTOAR"),
        ("wi-urugan-trotoar", "TRO.006", "Urugan Tanah Merah Lapisan Bawah Peninggi Level Trotoar", "m³", "Spesifikasi Trotoar", "TROTOAR"),
        ("wi-stamper-trotoar", "TRO.007", "Pemadatan Tanah Timbunan Trotoar Menggunakan Mesin Stamper Kodok", "m²", "Spesifikasi Trotoar", "TROTOAR"),
        ("wi-pasir-alas-trotoar", "TRO.008", "Penghamparan Lapisan Pasir Alas Ubin Trotoar Setebal 5-7 cm", "m²", "Spesifikasi Trotoar", "TROTOAR"),
        ("wi-wiremesh-trotoar", "TRO.009", "Pengecoran Lapisan Lantai Kerja Beton Bertulang Wiremesh M5 Tipis", "m²", "Spesifikasi Trotoar", "TROTOAR"),
        ("wi-paving-trotoar", "TRO.010", "Pemasangan Ubin Trotoar Jenis Paving Block / Interlocking Brick Motif", "m²", "Spesifikasi Trotoar", "TROTOAR"),
        ("wi-guiding-block-line", "TRO.011", "Pemasangan Ubin Jalur Pemandu Disabilitas Tunanetra Motif Garis (Guiding Block Line-Type)", "m'", "Spesifikasi Trotoar", "TROTOAR"),
        ("wi-guiding-block-dot", "TRO.012", "Pemasangan Ubin Jalur Pemandu Disabilitas Tunanetra Motif Titik Stop (Guiding Block Dot-Type)", "buah", "Spesifikasi Trotoar", "TROTOAR"),
        ("wi-nat-pasir-trotoar", "TRO.013", "Pekerjaan Pengisian Sela Nat Paving Trotoar Pasir Silika Halus Cor", "m²", "Spesifikasi Trotoar", "TROTOAR"),
        ("wi-batu-alam-trotoar", "TRO.014", "Pemasangan Ubin Trotoar Jenis Bahan Batu Alam Andesit Bakar Anti Licin", "m²", "Spesifikasi Trotoar", "TROTOAR"),
        ("wi-potong-presisi-paving", "TRO.015", "Pekerjaan Pemotongan Presisi Ubin Paving di Titik Sudut/Kanstin Lekuk", "m'", "Spesifikasi Trotoar", "TROTOAR"),
        ("wi-wheelchair-ramp", "TRO.016", "Pembuatan Konstruksi Tanjakan Landai Trotoar untuk Kursi Roda Disabilitas", "unit", "Spesifikasi Trotoar", "TROTOAR"),
        ("wi-bollard", "TRO.017", "Pemasangan Pagar Besi Pengaman Trotoar Pembatas Jalan (Pedestrian Bollard)", "buah", "Spesifikasi Trotoar", "TROTOAR"),
        ("wi-concrete-ball-bollard", "TRO.018", "Pemasangan Pilar Pembatas Batu Bulat Estetik (Concrete Ball Bollard)", "buah", "Spesifikasi Trotoar", "TROTOAR"),
        ("wi-tree-pit", "TRO.019", "Pembuatan Lubang Tanam Pohon Peneduh Trotoar (Tree Pit Concrete Ring)", "unit", "Spesifikasi Trotoar", "TROTOAR"),
        ("wi-tree-grate", "TRO.020", "Pemasangan Grill Besi Penutup Lubang Pohon Trotoar (Tree Grate Iron)", "unit", "Spesifikasi Trotoar", "TROTOAR"),
        ("wi-kursi-taman-trotoar", "TRO.021", "Pemasangan Kursi Taman Besi Tempa Permanen di Sepanjang Jalur Pedestrian", "unit", "Spesifikasi Trotoar", "TROTOAR"),
        ("wi-tempat-sampah-trotoar", "TRO.022", "Pemasangan Tempat Sampah Pilah Organik/Anorganik Bahan Stainless Tanam", "unit", "Spesifikasi Trotoar", "TROTOAR"),
        ("wi-tiang-lampu-pedestrian", "TRO.023", "Pemasangan Tiang Lampu Pedestrian Klasik Tinggi 3 Meter", "unit", "Spesifikasi Trotoar", "TROTOAR"),
        ("wi-kabel-bawah-trotoar", "TRO.024", "Penarikan Jaringan Kabel Listrik Tiang Lampu Bawah Tanah (Underground Cable)", "m'", "Spesifikasi Trotoar", "TROTOAR"),
        ("wi-konduit-hdpe-trotoar", "TRO.025", "Pemasangan Pipa Konduit Pelindung Kabel Bawah Trotoar (PVC High Density)", "m'", "Spesifikasi Trotoar", "TROTOAR"),
        ("wi-handhole-utility", "TRO.026", "Pembuatan Bak Kontrol Utilitas Kabel Bawah Tanah Trotoar (Handhole Utility)", "unit", "Spesifikasi Trotoar", "TROTOAR"),
        ("wi-peta-informasi-trotoar", "TRO.027", "Pemasangan Peta Lokasi / Papan Informasi Jalur Wisata Pedestrian Besi", "unit", "Spesifikasi Trotoar", "TROTOAR"),
        ("wi-halte-bus", "TRO.028", "Pemasangan Halte Bus Penumpang Terintegrasi di Jalur Trotoar", "unit", "Spesifikasi Trotoar", "TROTOAR"),
        ("wi-bersih-trotoar", "TRO.029", "Pekerjaan Penyiraman dan Pembersihan Total Noda Semen Permukaan Ubin Trotoar", "m²", "Spesifikasi Trotoar", "TROTOAR"),
        ("wi-uji-bollard", "TRO.030", "Pengujian Kekuatan Dudukan Bollard Pagar Terhadap Uji Tekan Benturan", "unit", "Spesifikasi Trotoar", "TROTOAR"),
    ]
    for args in items:
        kg.add_work_item(WorkItemNode(*args))
    print(f"  ✅ Trotoar: {len(items)} item pekerjaan dimuat")
