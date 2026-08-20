"""Domain Work Item: Taman & Landscape - Kelompok XIX"""
def load_wi_taman(kg):
    from fastra_core.knowledge.nodes import WorkItemNode
    items = [
        ("wi-olah-tanah", "TAM.001", "Pekerjaan Pengolahan & Penggemburan Tanah Taman", "m²", "AHSP PUPR", "TAMAN"),
        ("wi-media-tanam", "TAM.002", "Pencampuran Media Tanam Premium (Tanah, Pupuk, Sekam, Cocopeat)", "m³", "AHSP PUPR", "TAMAN"),
        ("wi-mounding", "TAM.003", "Pembuatan Kontur Tanah (Mounding Taman) Gundukan Estetik", "m³", "AHSP PUPR", "TAMAN"),
        ("wi-grass-border", "TAM.004", "Pemasangan Pembatas Rumput (Grass Border / Edging) Plastik/Beton", "m'", "AHSP PUPR", "TAMAN"),
        ("wi-rumput-gajah", "TAM.005", "Penanaman Rumput Gajah Mini / Rumput Jepang Lembaran", "m²", "AHSP PUPR", "TAMAN"),
        ("wi-pemukulan-rumput", "TAM.006", "Pekerjaan Pemukulan & Pemadatan Rumput Baru (Menyatu Akar)", "m²", "AHSP PUPR", "TAMAN"),
        ("wi-pohon-pelindung", "TAM.007", "Penanaman Pohon Pelindung Utama (Pule/Kamboja Fosil) + Tripod", "pohon", "AHSP PUPR", "TAMAN"),
        ("wi-staking-bambu", "TAM.008", "Pemasangan Tiang Bambu Penyangga Pohon (Staking) 3-4 Batang", "pohon", "AHSP PUPR", "TAMAN"),
        ("wi-shrubs", "TAM.009", "Penanaman Tanaman Semak Tinggi (Shrubs) Latar Belakang Taman", "m²", "AHSP PUPR", "TAMAN"),
        ("wi-groundcover", "TAM.010", "Penanaman Tanaman Penutup Tanah (Groundcover) Pengisi Celah", "m²", "AHSP PUPR", "TAMAN"),
        ("wi-stepping-stone", "TAM.011", "Pembuatan Jalur Setapak Taman (Stepping Stone) Batu Alam", "m'", "AHSP PUPR", "TAMAN"),
        ("wi-batu-koral-sikat", "TAM.012", "Pemasangan Batu Koral Sikat (Lantai Teras Motif Kerikil)", "m²", "AHSP PUPR", "TAMAN"),
        ("wi-batu-koral-hampar", "TAM.013", "Penghamparan Batu Koral Putih / Hitam Alor + Kain Mulsa", "m²", "AHSP PUPR", "TAMAN"),
        ("wi-sprinkler-system", "TAM.014", "Instalasi Pipa Penyiram Taman Otomatis (Sprinkler System) Bawah Tanah", "m'", "AHSP PUPR", "TAMAN"),
        ("wi-sprinkler-head", "TAM.015", "Pemasangan Kepala Sprinkler Pop-Up (Muncul Otomatis Saat Air Hidup)", "unit", "AHSP PUPR", "TAMAN"),
        ("wi-timer-solenoid", "TAM.016", "Pemasangan Mesin Kontrol Penyiram Otomatis (Timer Solenoid Valve)", "unit", "AHSP PUPR", "TAMAN"),
        ("wi-drip-line", "TAM.017", "Instalasi Pipa Irigasi Tetes (Drip Line System) Tanaman Pot", "m'", "AHSP PUPR", "TAMAN"),
        ("wi-vertical-garden", "TAM.018", "Pembuatan Taman Dinding (Vertical Garden Felt System) + Rangka", "m²", "AHSP PUPR", "TAMAN"),
        ("wi-tree-spotlight", "TAM.019", "Pemasangan Lampu Taman Sorot Pohon (Tree Spotlight) Warm White", "unit", "AHSP PUPR", "TAMAN"),
        ("wi-tiang-lampu-taman", "TAM.020", "Pemasangan Lampu Taman Tiang Minimalis Tinggi 50-100cm", "unit", "AHSP PUPR", "TAMAN"),
        ("wi-bak-kontrol-taman", "TAM.021", "Pembuatan Bak Kontrol Drainase Taman (Resapan Berlubang)", "unit", "AHSP PUPR", "TAMAN"),
        ("wi-pasir-silika-dinding", "TAM.022", "Pembuatan Ornamen Dinding Taman Pasir Silika (Kamprot Kasar)", "m²", "AHSP PUPR", "TAMAN"),
        ("wi-kursi-taman-cor", "TAM.023", "Pemasangan Kursi Taman & Meja Beton Custom Cor di Tempat", "unit", "AHSP PUPR", "TAMAN"),
        ("wi-vitamin-akar", "TAM.024", "Penyemprotan Vitamin Akar & Anti Hama Awal (Cairan B1 + Pestisida)", "m²", "AHSP PUPR", "TAMAN"),
    ]
    for args in items:
        kg.add_work_item(WorkItemNode(*args))
    print(f"  ✅ Taman & Landscape: {len(items)} item pekerjaan dimuat")
