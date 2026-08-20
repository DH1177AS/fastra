"""Domain Work Item: Jalan / Perkerasan Raya - Kelompok XXIII"""
def load_wi_jalan(kg):
    from fastra_core.knowledge.nodes import WorkItemNode
    items = [
        ("wi-survei-trase", "JAL.001", "Pekerjaan Survei Trase dan Rekayasa Geometrik Jalan", "Ls", "Spesifikasi Bina Marga", "JALAN"),
        ("wi-stripping-jalan", "JAL.002", "Pengupasan Tanah Lapisan Atas (Stripping/Scarifying)", "m³", "Spesifikasi Bina Marga", "JALAN"),
        ("wi-galian-jalan", "JAL.003", "Galian Tanah Lunak Semenjana untuk Badan Jalan", "m³", "Spesifikasi Bina Marga", "JALAN"),
        ("wi-buang-tanah-jalan", "JAL.004", "Pembuangan Tanah Sisa Galian Jalur Jalan Keluar Site", "m³", "Spesifikasi Bina Marga", "JALAN"),
        ("wi-timbunan-pilihan", "JAL.005", "Pekerjaan Timbunan Tanah Pilihan Peninggi Elevasi Jalan", "m³", "Spesifikasi Bina Marga", "JALAN"),
        ("wi-subgrade-roller", "JAL.006", "Pemadatan Tanah Dasar (Subgrade) Menggunakan Vibratory Roller", "m²", "Spesifikasi Bina Marga", "JALAN"),
        ("wi-sandcone-jalan", "JAL.007", "Pengujian Kepadatan Tanah Lapangan (Sand Cone Test) per Lapisan", "titik", "Spesifikasi Bina Marga", "JALAN"),
        ("wi-geotextile-woven", "JAL.008", "Pemasangan Lapisan Geotextile Woven Penstabil Tanah Dasar", "m²", "Spesifikasi Bina Marga", "JALAN"),
        ("wi-lpa-b", "JAL.009", "Penghamparan Batu Belah Fondasi Bawah (LPA Kelas B)", "m³", "Spesifikasi Bina Marga", "JALAN"),
        ("wi-pemadatan-lpa-b", "JAL.010", "Pemadatan dan Penyiraman Air Agregat Kelas B", "m³", "Spesifikasi Bina Marga", "JALAN"),
        ("wi-lpa-a", "JAL.011", "Penghamparan Batu Pecah Fondasi Atas (LPA Kelas A)", "m³", "Spesifikasi Bina Marga", "JALAN"),
        ("wi-pemadatan-lpa-a", "JAL.012", "Pemadatan Maksimal Agregat Kelas A (Pneumatic Tire Roller)", "m³", "Spesifikasi Bina Marga", "JALAN"),
        ("wi-cbr-test", "JAL.013", "Pengujian Kepadatan Agregat (CBR Lapangan / DCP Test)", "titik", "Spesifikasi Bina Marga", "JALAN"),
        ("wi-bersih-debu-agregat", "JAL.014", "Pembersihan Debu Agregat Menggunakan Air Compressor", "m²", "Spesifikasi Bina Marga", "JALAN"),
        ("wi-prime-coat", "JAL.015", "Penyemprotan Aspal Cair Perekat Pengikat Dasar (Prime Coat)", "liter", "Spesifikasi Bina Marga", "JALAN"),
        ("wi-tack-coat", "JAL.016", "Penyemprotan Aspal Cair Perekat Antar Lapisan (Tack Coat)", "liter", "Spesifikasi Bina Marga", "JALAN"),
        ("wi-ac-base", "JAL.017", "Penghamparan Aspal Kasar Lapisan Pondasi (AC-Base)", "ton", "Spesifikasi Bina Marga", "JALAN"),
        ("wi-pemadatan-ac-base", "JAL.018", "Pemadatan Awal Aspal AC-Base Menggunakan Tandem Roller", "ton", "Spesifikasi Bina Marga", "JALAN"),
        ("wi-ac-bc", "JAL.019", "Penghamparan Aspal Pengikat Tengah (AC-BC)", "ton", "Spesifikasi Bina Marga", "JALAN"),
        ("wi-ac-wc", "JAL.020", "Penghamparan Aspal Halus Lapis Aus Atas (AC-WC)", "ton", "Spesifikasi Bina Marga", "JALAN"),
        ("wi-pemadatan-ptr", "JAL.021", "Pemadatan Akhir Aspal Jalan Menggunakan Pneumatic Tire Roller", "ton", "Spesifikasi Bina Marga", "JALAN"),
        ("wi-core-drill", "JAL.022", "Pengujian Ketebalan & Kepadatan Aspal Laboratorium (Core Drill Test)", "titik", "Spesifikasi Bina Marga", "JALAN"),
        ("wi-dowel-tie-bar", "JAL.023", "Pemasangan Rangka Besi Dudukan Jalan Beton (Dowel & Tie Bar)", "kg", "Spesifikasi Bina Marga", "JALAN"),
        ("wi-bekisting-jalan-beton", "JAL.024", "Pemasangan Bekisting Samping Cor Beton Jalan (Besi Plat)", "m'", "Spesifikasi Bina Marga", "JALAN"),
        ("wi-plastik-alas-cor", "JAL.025", "Penghamparan Plastik Alas Cor Jalan Beton", "m²", "Spesifikasi Bina Marga", "JALAN"),
        ("wi-rigid-pavement", "JAL.026", "Pengecoran Jalan Beton Mutu Tinggi (FS 45 / K-350) Pakai Paver Machine", "m³", "Spesifikasi Bina Marga", "JALAN"),
        ("wi-grooving-jalan", "JAL.027", "Pekerjaan Pembuatan Tekstur Gores Kain Rami / Alur Ban Jalan", "m²", "Spesifikasi Bina Marga", "JALAN"),
        ("wi-curing-compound", "JAL.028", "Penyemprotan Cairan Perawatan Beton (Curing Compound) Jalan", "m²", "Spesifikasi Bina Marga", "JALAN"),
        ("wi-joint-cutter", "JAL.029", "Pemotongan Celah Sambungan Beton Jalan (Concrete Cutting)", "m'", "Spesifikasi Bina Marga", "JALAN"),
        ("wi-asphalt-sealant", "JAL.030", "Pengisian Celah Potongan Jalan Beton Menggunakan Asphalt Sealant", "m'", "Spesifikasi Bina Marga", "JALAN"),
        ("wi-kanstin-beton", "JAL.031", "Pemasangan Batu Kanstin Beton Pembatas Pinggir Jalan (Kanstin)", "m'", "Spesifikasi Bina Marga", "JALAN"),
        ("wi-backing-kanstin", "JAL.032", "Pengecoran Cor Beton Pengunci Belakang Kanstin (Backing Concrete)", "m'", "Spesifikasi Bina Marga", "JALAN"),
        ("wi-marka-thermoplastic", "JAL.033", "Pengecatan Marka Jalan Garis Putih/Kuning (Thermoplastic Paint Resin)", "m²", "Spesifikasi Bina Marga", "JALAN"),
        ("wi-road-stud", "JAL.034", "Pemasangan Marka Jalan Timbul Paku Bumi Reflektor (Glass Road Stud)", "buah", "Spesifikasi Bina Marga", "JALAN"),
        ("wi-rambu-jalan", "JAL.035", "Pemasangan Rambu Lalu Lintas dan Petunjuk Arah Jalan", "buah", "Spesifikasi Bina Marga", "JALAN"),
    ]
    for args in items:
        kg.add_work_item(WorkItemNode(*args))
    print(f"  ✅ Jalan: {len(items)} item pekerjaan dimuat")
