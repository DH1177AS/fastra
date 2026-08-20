"""Domain Work Item: Tambahan Penunjang & Dekorasi Luar Extra - Kelompok XXII"""
def load_wi_dekorasi_luar(kg):
    from fastra_core.knowledge.nodes import WorkItemNode
    items = [
        ("wi-deck-bengkirai", "DL.001", "Pembuatan Lantai Kayu Dek Luar Kolam (Wood Decking / Bengkirai)", "m²", "AHSP PUPR", "DEKORASI_LUAR"),
        ("wi-rangka-deck", "DL.002", "Pemasangan Rangka Dudukan Deck Kayu Besi Hollow Galvanis", "m²", "AHSP PUPR", "DEKORASI_LUAR"),
        ("wi-cat-deck", "DL.003", "Finishing Deck Kayu dengan Cat Ultran Lasur (Anti Matahari & Air)", "m²", "AHSP PUPR", "DEKORASI_LUAR"),
        ("wi-payung-taman", "DL.004", "Pemasangan Payung Taman Besar & Kursi Tidur Kolam (Sun Lounger)", "set", "AHSP PUPR", "DEKORASI_LUAR"),
        ("wi-shower-bilas", "DL.005", "Pemasangan Shower Bilas Luar Ruangan (Outdoor Pool Shower Column)", "unit", "AHSP PUPR", "DEKORASI_LUAR"),
        ("wi-spout-wall", "DL.006", "Pembuatan Dinding Fitur Pancuran Air (Spout Wall Feature)", "unit", "AHSP PUPR", "DEKORASI_LUAR"),
        ("wi-patung-pancuran", "DL.007", "Pemasangan Patung Pancuran Air Kolam (Bahan GRC/Batu Alam)", "unit", "AHSP PUPR", "DEKORASI_LUAR"),
        ("wi-fire-pit", "DL.008", "Pembuatan Area Bak Api Unggun Duduk Santai (Sunken Seating Area / Fire Pit)", "unit", "AHSP PUPR", "DEKORASI_LUAR"),
        ("wi-pipa-gas-firepit", "DL.009", "Instalasi Pipa Gas & Tungku Fire Pit Outdoor", "unit", "AHSP PUPR", "DEKORASI_LUAR"),
        ("wi-neon-flex-taman", "DL.010", "Pemasangan Lampu LED Neon Flex Dekorasi Taman", "m'", "AHSP PUPR", "DEKORASI_LUAR"),
        ("wi-jembatan-kayu-kolam", "DL.011", "Pembuatan Jembatan Kayu Penyeberangan Kolam (Footbridge)", "unit", "AHSP PUPR", "DEKORASI_LUAR"),
        ("wi-pool-safety-net", "DL.012", "Pemasangan Jaring Pengaman Kolam Anak (Pool Safety Net / Fence)", "m'", "AHSP PUPR", "DEKORASI_LUAR"),
        ("wi-gazebo-bambu", "DL.013", "Pembangunan Gazebo Bambu / Kayu Kelapa (Beratap Jerami/Genteng)", "unit", "AHSP PUPR", "DEKORASI_LUAR"),
        ("wi-wet-bar", "DL.014", "Pembuatan Bar Basah Tepi Kolam (Poolside Wet Bar) Cor Keramik", "unit", "AHSP PUPR", "DEKORASI_LUAR"),
        ("wi-submerged-stools", "DL.015", "Pemasangan Kursi Duduk Dalam Air Kolam (Submerged Pool Bar Stools)", "unit", "AHSP PUPR", "DEKORASI_LUAR"),
        ("wi-tebing-riam", "DL.016", "Pemasangan Ornaments Batu Lapis Dinding Air Terjun (Efek Gemericik)", "unit", "AHSP PUPR", "DEKORASI_LUAR"),
        ("wi-pool-storage", "DL.017", "Pembuatan Tempat Penyimpanan Alat Pembersih Kolam (Pool Equipment Storage Box)", "unit", "AHSP PUPR", "DEKORASI_LUAR"),
        ("wi-mosquito-trap", "DL.018", "Pemasangan Alat Pengusir Nyamuk Taman Elektrik (Mosquito Trap Outdoor IPX4)", "unit", "AHSP PUPR", "DEKORASI_LUAR"),
        ("wi-rock-speaker", "DL.019", "Pemasangan Sistem Musik Luar Ruangan Tahan Cuaca (Outdoor Rock Speakers)", "unit", "AHSP PUPR", "DEKORASI_LUAR"),
        ("wi-kabel-speaker-taman", "DL.020", "Instalasi Kabel Jalur Utama Sound System Taman (Bawah Tanah + Konduit)", "m'", "AHSP PUPR", "DEKORASI_LUAR"),
        ("wi-misting-system", "DL.021", "Pemasangan Sistem Kabut Taman (Outdoor Misting/Fogging System) Nozzle Mikro", "set", "AHSP PUPR", "DEKORASI_LUAR"),
        ("wi-pompa-kabut", "DL.022", "Instalasi Pompa Booster Tekanan Tinggi Sistem Kabut (Minimal 100 Bar)", "unit", "AHSP PUPR", "DEKORASI_LUAR"),
        ("wi-hammock-catwalk", "DL.023", "Pembuatan Tempat Berjemur Jaring Gantung Atas Kolam (Over-pool Hammock Catwalk)", "unit", "AHSP PUPR", "DEKORASI_LUAR"),
        ("wi-retractable-awning", "DL.024", "Pemasangan Payung Kanopi Lipat Otomatis (Retractable Awning Motorized)", "unit", "AHSP PUPR", "DEKORASI_LUAR"),
        ("wi-living-fence", "DL.025", "Pemasangan Pagar Tanaman Hidup (Living Green Fence/Topiary) Pucuk Merah", "m'", "AHSP PUPR", "DEKORASI_LUAR"),
        ("wi-topiary-art", "DL.026", "Pekerjaan Pemangkasan Bentuk Seni Pohon (Topiary Art Pruning) Bulat/Spiral", "unit", "AHSP PUPR", "DEKORASI_LUAR"),
        ("wi-rumput-sintetis-balkon", "DL.027", "Pemasangan Karpet Rumput Sintetis Lapisan Drainase (Drainage Cell Layer)", "m²", "AHSP PUPR", "DEKORASI_LUAR"),
        ("wi-glass-balustrade", "DL.028", "Pemasangan Kaca Pembatas Balkon Taman Atas (Frameless Glass Balustrade)", "m'", "AHSP PUPR", "DEKORASI_LUAR"),
        ("wi-geocell", "DL.029", "Pekerjaan Pembuatan Tanah Lereng Penahan Erosi (Geocell Grid System)", "m²", "AHSP PUPR", "DEKORASI_LUAR"),
        ("wi-wall-washer-rgb", "DL.030", "Pemasangan Lampu Sorot Fasad Kolam Variasi Warna (Wall Washer RGB Lamp)", "unit", "AHSP PUPR", "DEKORASI_LUAR"),
        ("wi-waterproofing-dak-taman", "DL.031", "Pekerjaan Waterproofing Dak Beton Taman Atas (Roof Garden Water Barrier)", "m²", "AHSP PUPR", "DEKORASI_LUAR"),
        ("wi-root-barrier", "DL.032", "Pemasangan Lapisan Penahan Akar Tanaman (Root Barrier Sheet) Taman Dak", "m²", "AHSP PUPR", "DEKORASI_LUAR"),
        ("wi-rainwater-harvesting", "DL.033", "Instalasi Sistem Penangkap Air Hujan (Rainwater Harvesting Tank) Siram Taman", "unit", "AHSP PUPR", "DEKORASI_LUAR"),
        ("wi-bersih-kerak-batu", "DL.034", "Pekerjaan Pembersihan Kerak Batu Alam Berkala Proyek (Cairan Asam Ringan)", "m²", "AHSP PUPR", "DEKORASI_LUAR"),
        ("wi-coating-batu-luar", "DL.035", "Pekerjaan Akhir Pelapisan Anti Air Batu Alam (Coating Gloss/Doft)", "m²", "AHSP PUPR", "DEKORASI_LUAR"),
    ]
    for args in items:
        kg.add_work_item(WorkItemNode(*args))
    print(f"  Dekorasi Luar: {len(items)} item pekerjaan dimuat")