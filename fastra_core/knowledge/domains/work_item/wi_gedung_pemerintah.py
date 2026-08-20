"""Domain Work Item: Gedung Pemerintah & Fasilitas Publik"""
def load_wi_gedung_pemerintah(kg):
    from fastra_core.knowledge.nodes import WorkItemNode
    items = [
        ("wi-data-center-pem", "PEM.001", "Pembangunan Ruang Server Data Center Pemerintah (Raised Floor, AC Presisi, Fire Suppression)", "unit", "Standar Pemerintah", "GEDUNG_PEMERINTAH"),
        ("wi-command-center", "PEM.002", "Pemasangan Sistem Command Center / Situation Room (Video Wall, Console, UPS N+1)", "unit", "Standar Pemerintah", "GEDUNG_PEMERINTAH"),
        ("wi-perimeter-security", "PEM.003", "Instalasi Sistem Pengamanan Perimeter Multi-Layer (CCTV Analytics, Barrier Gate, Bollard)", "unit", "Standar Pemerintah", "GEDUNG_PEMERINTAH"),
        ("wi-led-display-sign", "PEM.004", "Pemasangan Papan Informasi Elektronik / LED Display Sign Outdoor", "unit", "Standar Pemerintah", "GEDUNG_PEMERINTAH"),
        ("wi-queuing-system", "PEM.005", "Instalasi Antrian Elektronik Terpadu (Queuing System) Mesin Tiket + Display", "unit", "Standar Pemerintah", "GEDUNG_PEMERINTAH"),
        ("wi-detention-room", "PEM.006", "Pembangunan Ruang Tahanan Sementara / Detention Room (Dinding Beton, CCTV 24 Jam)", "unit", "Standar Pemerintah", "GEDUNG_PEMERINTAH"),
        ("wi-podium-ruang-rapat", "PEM.007", "Pemasangan Podium / Mimbar Ruang Rapat Besar (Tata Suara Terintegrasi)", "unit", "Standar Pemerintah", "GEDUNG_PEMERINTAH"),
        ("wi-video-conference", "PEM.008", "Pemasangan Sistem Teleconference Ruang Rapat (Layar, Kamera PTZ, Panel Sentuh)", "unit", "Standar Pemerintah", "GEDUNG_PEMERINTAH"),
        ("wi-lobby-penerimaan", "PEM.009", "Pembangunan Lobby Penerimaan Publik Skala Besar (Resepsionis, Backdrop, Ruang Tunggu)", "unit", "Standar Pemerintah", "GEDUNG_PEMERINTAH"),
        ("wi-flagpole-set", "PEM.010", "Pemasangan Flagpole Set (Tiang Bendera Dalam Ruangan + Bendera Merah Putih & Instansi)", "set", "Standar Pemerintah", "GEDUNG_PEMERINTAH"),
        ("wi-mobile-shelving", "PEM.011", "Instalasi Sistem Arsip Bergerak (Mobile Shelving / Roll O'Pack) Rel Lantai", "unit", "Standar Pemerintah", "GEDUNG_PEMERINTAH"),
        ("wi-double-gate-post", "PEM.012", "Pembangunan Pos Jaga Ganda (Double Gate Security Post) Palang Otomatis", "unit", "Standar Pemerintah", "GEDUNG_PEMERINTAH"),
    ]
    for args in items:
        kg.add_work_item(WorkItemNode(*args))
    print(f"  Gedung Pemerintah: {len(items)} item pekerjaan dimuat")