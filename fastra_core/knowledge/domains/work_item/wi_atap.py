"""Domain Work Item: Rangka Atap & Material Penutup (Roofing) - Kelompok IV"""
def load_wi_atap(kg):
    from fastra_core.knowledge.nodes import WorkItemNode
    items = [
        ("wi-angkur-baja-atap", "ATP.001", "Pemasangan Baut Angkur Baja (Anchor Bolt) di Atas Ring Balk", "titik", "AHSP PUPR", "ATAP"),
        ("wi-baseplate-atap", "ATP.002", "Pengelasan Pelat Dudukan Baja Kuda-Kuda Atas Ring Balk", "unit", "SNI 1729", "ATAP"),
        ("wi-kudakuda-fab", "ATP.003", "Fabrikasi Kuda-Kuda Atap Baja Ringan Kanal C Tinggi Standar", "m²", "SNI 7973", "ATAP"),
        ("wi-kudakuda-assembly", "ATP.004", "Perakitan Kuda-Kuda Atap Baja Ringan di Area Bawah Lapangan", "m²", "SNI 7973", "ATAP"),
        ("wi-kudakuda-erection", "ATP.005", "Pengangkatan Kuda-Kuda Baja Ringan ke Atas Ring Balk Manual", "m²", "AHSP PUPR", "ATAP"),
        ("wi-bracing-atap", "ATP.006", "Pemasangan Batang Pengikat Antar Kuda-Kuda (Bracing)", "m'", "SNI 7973", "ATAP"),
        ("wi-reng-atap", "ATP.007", "Pemasangan Batang Horisontal Penyangga Genteng (Reng) Baja Ringan", "m'", "SNI 7973", "ATAP"),
        ("wi-jarak-reng", "ATP.008", "Pengukuran Jarak Antar Reng Sesuai Spesifikasi Panjang Genteng", "m²", "AHSP PUPR", "ATAP"),
        ("wi-jurai-dalam", "ATP.009", "Pemasangan Batang Jurai Dalam / Jurai Luar Baja Ringan", "m'", "SNI 7973", "ATAP"),
        ("wi-foil-single", "ATP.010", "Pemasangan Lapisan Aluminium Foil Single Sided Penahan Panas", "m²", "AHSP PUPR", "ATAP"),
        ("wi-wiremesh-foil", "ATP.011", "Pemasangan Jaring Kawat Penyangga Aluminium Foil (Wire Mesh Net)", "m²", "AHSP PUPR", "ATAP"),
        ("wi-glasswool-atap", "ATP.012", "Pemasangan Lapisan Peredam Suara Hujan Lembaran Glasswool", "m²", "AHSP PUPR", "ATAP"),
        ("wi-genteng-utama", "ATP.013", "Pemasangan Genteng Utama (Genteng Keramik Berglazur)", "m²", "SNI 0096", "ATAP"),
        ("wi-genteng-skrup", "ATP.014", "Penguncian Genteng Utama Paku Skrup Galvalum pada Batang Reng", "titik", "AHSP PUPR", "ATAP"),
        ("wi-genteng-nok", "ATP.015", "Pemasangan Genteng Nok / Bubungan Atas Pertemuan Atap", "m'", "SNI 0096", "ATAP"),
        ("wi-adukan-nok", "ATP.016", "Pasangan Adukan Semen Warna untuk Pengikat Genteng Nok", "m'", "AHSP PUPR", "ATAP"),
        ("wi-flashing-atap", "ATP.017", "Pemasangan Flashing Seng/Aluminium Pembatas Atap & Dinding Tetangga", "m'", "AHSP PUPR", "ATAP"),
        ("wi-talang-gantung", "ATP.018", "Pemasangan Talang Air Horisontal Bahan Fiberglass Gantung", "m'", "AHSP PUPR", "ATAP"),
        ("wi-braket-talang", "ATP.019", "Pemasangan Braket Besi Penyangga Talang Gantung Tiap Jarak 1m", "buah", "AHSP PUPR", "ATAP"),
        ("wi-corong-talang", "ATP.020", "Pemasangan Corong Output Jalur Talang Gantung menuju Pipa Turun", "titik", "AHSP PUPR", "ATAP"),
        ("wi-skylight", "ATP.021", "Pemasangan Atap Kaca Transparan (Skylight) Rangka Besi Kotak", "m²", "AHSP PUPR", "ATAP"),
        ("wi-silikon-skylight", "ATP.022", "Pemasangan Lapisan Karet Silikon Sealant Sambungan Atap Skylight", "m'", "AHSP PUPR", "ATAP"),
        ("wi-kanopi-polycarbonate", "ATP.023", "Pemasangan Penutup Atap Kanopi Belakang Bahan Polycarbonate", "m²", "AHSP PUPR", "ATAP"),
        ("wi-skrup-polycarbonate", "ATP.024", "Pemasangan Skrup Atap Polycarbonate Lengkap dengan Karet Ring", "titik", "AHSP PUPR", "ATAP"),
        ("wi-lisplang-grc", "ATP.025", "Pemasangan Lisplang Papan Fiber Semen (GRC) Pinggiran Atap", "m'", "AHSP PUPR", "ATAP"),
        ("wi-cat-lisplang", "ATP.026", "Pengecatan Lembaran Lisplang GRC Paku Cat Minyak Eksterior", "m'", "AHSP PUPR", "ATAP"),
        ("wi-ventilasi-atap", "ATP.027", "Pemasangan Ventilasi Atap Bahan Aluminium Louver Kisi-Kisi", "unit", "AHSP PUPR", "ATAP"),
        ("wi-kawat-nyamuk-atap", "ATP.028", "Pemasangan Kawat Nyamuk Baja pada Kisi-Kisi Ventilasi Atap", "unit", "AHSP PUPR", "ATAP"),
        ("wi-terminal-petir", "ATP.029", "Pemasangan Pemutus Arus Petir Terminal Udara (Tombak Tembaga) Atap", "unit", "SNI 03-7015", "ATAP"),
        ("wi-kabel-petir-turun", "ATP.030", "Penarikan Kabel Tembaga BC 50mm dari Atap Turun ke Tanah", "m'", "SNI 03-7015", "ATAP"),
    ]
    for args in items:
        kg.add_work_item(WorkItemNode(*args))
    print(f"  ✅ Atap & Roofing: {len(items)} item pekerjaan dimuat")
