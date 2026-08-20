"""Domain Work Item: Pra-Konstruksi, Legalitas & Persiapan (Kelompok I)"""
def load_wi_pra_konstruksi(kg):
    from fastra_core.knowledge.nodes import WorkItemNode
    items = [
        ("wi-pbg", "PRA.001", "Pengurusan Persetujuan Bangunan Gedung (PBG / Eks IMB)", "Ls", "UU Jasa Konstruksi", "PRA_KONSTRUKSI"),
        ("wi-andalalin", "PRA.002", "Pengurusan Andalalin (Analisis Dampak Lalu Lintas)", "Ls", "UU LLAJ", "PRA_KONSTRUKSI"),
        ("wi-uklupl", "PRA.003", "Pengurusan Dokumen UKL-UPL / Amdal Lingkungan", "Ls", "UU LH", "PRA_KONSTRUKSI"),
        ("wi-slo-listrik", "PRA.004", "Pengurusan Izin Penyambungan Baru Daya PLN", "Ls", "Peraturan PLN", "PRA_KONSTRUKSI"),
        ("wi-slo-pdam", "PRA.005", "Pengurusan Izin Sambungan Baru Air Bersih PDAM", "Ls", "Peraturan PDAM", "PRA_KONSTRUKSI"),
        ("wi-shopdraw-arsitek", "PRA.006", "Penyusunan Gambar Kerja Arsitektur (Shop Drawings)", "Ls", "Standar Gambar", "PRA_KONSTRUKSI"),
        ("wi-shopdraw-struktur", "PRA.007", "Penyusunan Gambar Struktur & Perhitungan Pembebanan", "Ls", "SNI 2847", "PRA_KONSTRUKSI"),
        ("wi-shopdraw-mep", "PRA.008", "Penyusunan Gambar Instalasi MEP", "Ls", "Standar MEP", "PRA_KONSTRUKSI"),
        ("wi-survei-batas", "PRA.009", "Pengukuran Batas Lahan dengan GPS / Total Station", "Ls", "Standar Geomatik", "PRA_KONSTRUKSI"),
        ("wi-benchmark", "PRA.010", "Pembuatan Titik Benchmark (BM) Utama Elevasi Proyek", "titik", "Standar Geomatik", "PRA_KONSTRUKSI"),
        ("wi-papan-proyek", "PRA.011", "Pemasangan Papan Nama Legalitas Proyek", "unit", "UU Jasa Konstruksi", "PRA_KONSTRUKSI"),
        ("wi-land-clearing", "PRA.012", "Pembersihan Lahan Tahap Awal (Land Clearing) dari Semak", "m²", "AHSP PUPR", "PRA_KONSTRUKSI"),
        ("wi-tebang-pohon", "PRA.013", "Penebangan Pohon Eksisting & Pembongkaran Akar Tanam", "pohon", "AHSP PUPR", "PRA_KONSTRUKSI"),
        ("wi-stripping-topsoil", "PRA.014", "Pengupasan Lapisan Tanah Subur Atas (Stripping Top Soil) 20 cm", "m³", "AHSP PUPR", "PRA_KONSTRUKSI"),
        ("wi-buang-topsoil", "PRA.015", "Pembuangan Tanah Kupasan Keluar Area Site Proyek", "m³", "AHSP PUPR", "PRA_KONSTRUKSI"),
        ("wi-pagar-keliling", "PRA.016", "Pemasangan Pagar Keliling Proyek Bahan Spandek Tinggi 2m", "m'", "AHSP PUPR", "PRA_KONSTRUKSI"),
        ("wi-pintu-gerbang", "PRA.017", "Pembuatan Pintu Gerbang Utama Akses Truk Proyek", "unit", "AHSP PUPR", "PRA_KONSTRUKSI"),
        ("wi-direksikit", "PRA.018", "Pembangunan Kantor Sementara Pengawas (Direksikit)", "m²", "AHSP PUPR", "PRA_KONSTRUKSI"),
        ("wi-barak-pekerja", "PRA.019", "Pembangunan Barak Tempat Tinggal Sementara Pekerja", "m²", "AHSP PUPR", "PRA_KONSTRUKSI"),
        ("wi-gudang-tertutup", "PRA.020", "Pembangunan Gudang Tertutup Khusus Semen & Alat Presisi", "m²", "AHSP PUPR", "PRA_KONSTRUKSI"),
        ("wi-gudang-terbuka", "PRA.021", "Pembangunan Gudang Terbuka Khusus Besi & Material Berat", "m²", "AHSP PUPR", "PRA_KONSTRUKSI"),
        ("wi-bedeng-toilet", "PRA.022", "Pembuatan Bedeng Toilet Sementara & Septic Tank Pekerja", "unit", "AHSP PUPR", "PRA_KONSTRUKSI"),
        ("wi-sumur-bor-sementara", "PRA.023", "Pembuatan Sumur Bor Sementara untuk Air Kerja Proyek", "unit", "AHSP PUPR", "PRA_KONSTRUKSI"),
        ("wi-jetpump-sementara", "PRA.024", "Pemasangan Pompa Air Jetpump Sementara untuk Air Kerja", "unit", "AHSP PUPR", "PRA_KONSTRUKSI"),
        ("wi-genset-proyek", "PRA.025", "Penyewaan Genset Utama Proyek Kapasitas Besar (Silenced)", "unit", "AHSP PUPR", "PRA_KONSTRUKSI"),
        ("wi-kabel-induk-genset", "PRA.026", "Penarikan Kabel Induk dari Genset ke Panel Distribusi Kerja", "m'", "PUIL", "PRA_KONSTRUKSI"),
        ("wi-bak-air-kerja", "PRA.027", "Pembuatan Bak Penampung Air Kerja Kapasitas 2000 Liter", "unit", "AHSP PUPR", "PRA_KONSTRUKSI"),
        ("wi-bouwplank", "PRA.028", "Pemasangan Papan Pengukur Koordinat Dinding (Bouwplank)", "m'", "Standar Konstruksi", "PRA_KONSTRUKSI"),
        ("wi-benang-as", "PRA.029", "Pemasangan Paku As Bangunan & Penarikan Benang Levelling", "m'", "Standar Konstruksi", "PRA_KONSTRUKSI"),
        ("wi-mobilisasi-excavator", "PRA.030", "Mobilisasi Ekskavator PC200 ke Lokasi Proyek", "unit", "AHSP PUPR", "PRA_KONSTRUKSI"),
        ("wi-mobilisasi-dumptruck", "PRA.031", "Mobilisasi Truk Jungkit (Dump Truck) 8 Kubik", "unit", "AHSP PUPR", "PRA_KONSTRUKSI"),
        ("wi-mobilisasi-stamper", "PRA.032", "Mobilisasi Mesin Stamper Kodok & Stamper Kuda", "unit", "AHSP PUPR", "PRA_KONSTRUKSI"),
        ("wi-apd-k3", "PRA.033", "Penyediaan Alat Pelindung Diri (APD) K3 untuk Pekerja", "set", "PP K3", "PRA_KONSTRUKSI"),
        ("wi-rambu-k3", "PRA.034", "Pemasangan Rambu Bahaya & Spanduk K3 Keliling Proyek", "unit", "PP K3", "PRA_KONSTRUKSI"),
        ("wi-drainase-sementara", "PRA.035", "Pembuatan Saluran Air Pembuangan Sementara Area Proyek", "m'", "AHSP PUPR", "PRA_KONSTRUKSI"),
    ]
    for args in items:
        kg.add_work_item(WorkItemNode(*args))
    print(f"  ✅ Pra-Konstruksi: {len(items)} item pekerjaan dimuat")
