"""Domain Work Item: Sekolah & Laboratorium"""
def load_wi_sekolah(kg):
    from fastra_core.knowledge.nodes import WorkItemNode
    items = [
        ("wi-tiang-bendera", "SEK.001", "Pembangunan Tiang Bendera Utama Lapangan Upacara 12-15m Katrol", "unit", "Standar Sekolah", "SEKOLAH"),
        ("wi-lapangan-upacara", "SEK.002", "Pengecoran Lapangan Upacara Beton / Paving Block", "m²", "Standar Sekolah", "SEKOLAH"),
        ("wi-mimbar-upacara", "SEK.003", "Pembangunan Panggung / Mimbar Upacara Permanen (Cor Beton + Keramik)", "unit", "Standar Sekolah", "SEKOLAH"),
        ("wi-tribun-sekolah", "SEK.004", "Pemasangan Kursi Tribun Lipat / Beton Lapangan", "m²", "Standar Sekolah", "SEKOLAH"),
        ("wi-meja-lab", "SEK.005", "Instalasi Meja Lab Tahan Asam + Bak Cuci Porselen + Gas LPG", "unit", "Standar Sekolah", "SEKOLAH"),
        ("wi-fume-hood", "SEK.006", "Instalasi Lemari Asam (Fume Hood) Lab + Ducting Exhaust", "unit", "Standar Sekolah", "SEKOLAH"),
        ("wi-papan-tulis-projector", "SEK.007", "Pemasangan Papan Tulis / Whiteboard + Proyektor Classroom Mount", "unit", "Standar Sekolah", "SEKOLAH"),
        ("wi-sound-system-sekolah", "SEK.008", "Pemasangan Sound System & Speaker Kelas / Koridor (Bel & Pengumuman)", "unit", "Standar Sekolah", "SEKOLAH"),
        ("wi-loker-sekolah", "SEK.009", "Pemasangan Loker Besi / Kayu Koridor Sekolah (Tempel Permanen)", "unit", "Standar Sekolah", "SEKOLAH"),
        ("wi-perlengkapan-olahraga-sekolah", "SEK.010", "Pemasangan Perlengkapan Lapangan Olahraga Sekolah (Ring Basket, Voli, Futsal)", "set", "Standar Sekolah", "SEKOLAH"),
    ]
    for args in items:
        kg.add_work_item(WorkItemNode(*args))
    print(f"  Sekolah: {len(items)} item pekerjaan dimuat")