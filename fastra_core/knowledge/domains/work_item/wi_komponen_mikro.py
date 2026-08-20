"""Domain Work Item: Detail Komponen Mikro, Sambungan & Aksesoris Material - Kelompok XII"""
def load_wi_komponen_mikro(kg):
    from fastra_core.knowledge.nodes import WorkItemNode
    items = [
        ("wi-dynabolt-kusen", "MIK.001", "Pemasangan Dynabolt / Anchor Bolt Kusen (Angkur Besi Pengikat)", "buah", "AHSP PUPR", "KOMPONEN_MIKRO"),
        ("wi-silikon-sealant-kusen", "MIK.002", "Pekerjaan Silikon Sealant Kusen & Kaca (Lem Silikon Anti-Air)", "m'", "AHSP PUPR", "KOMPONEN_MIKRO"),
        ("wi-skrup-drywall", "MIK.003", "Pemasangan Skrup Drywall Plafon (Sekrup Khusus Anti-Karat Kepala Rata)", "buah", "AHSP PUPR", "KOMPONEN_MIKRO"),
        ("wi-fiber-tape", "MIK.004", "Pemasangan Kassa Plafon (Fiber Tape) Perekat Jaring Sambungan Gipsum", "m'", "AHSP PUPR", "KOMPONEN_MIKRO"),
        ("wi-drop-bolt", "MIK.005", "Pemasangan Drop Bolt Pintu (Slot Kunci Tanam Vertikal Pintu Ganda)", "set", "AHSP PUPR", "KOMPONEN_MIKRO"),
        ("wi-door-stop-magnet", "MIK.006", "Pemasangan Door Stop / Magnetic Catch (Penahan Pintu Magnetis)", "buah", "AHSP PUPR", "KOMPONEN_MIKRO"),
        ("wi-roofing-screw", "MIK.007", "Pemasangan Skrup Drilling Rangka Atap (Sekrup Baja Ringan Kepala Kunci)", "buah", "AHSP PUPR", "KOMPONEN_MIKRO"),
        ("wi-pipe-clamp", "MIK.008", "Pemasangan Klem Pipa Air (Pipe Clamp/Hanger) Dudukan Besi Gantung", "buah", "AHSP PUPR", "KOMPONEN_MIKRO"),
        ("wi-heat-fusion-ppr", "MIK.009", "Pekerjaan Penyambungan Pipa Metode Heat Fusion (PPR) Mesin Welding", "titik", "SNI Plumbing", "KOMPONEN_MIKRO"),
        ("wi-clean-out", "MIK.010", "Pemasangan Clean Out Pipa Air Kotor (Lubang Sumbat Berulir)", "unit", "SNI Plumbing", "KOMPONEN_MIKRO"),
        ("wi-roof-drain-castiron", "MIK.011", "Pemasangan Roof Drain Cast Iron (Saringan Dak Beton Besi Cor)", "unit", "AHSP PUPR", "KOMPONEN_MIKRO"),
        ("wi-kawat-las", "MIK.012", "Pemasangan Kawat Las (Welding Electrode) Struktur (Tipe E7018)", "kg", "SNI 1729", "KOMPONEN_MIKRO"),
        ("wi-lasdop", "MIK.013", "Pemasangan Wire Connector / Lasdop (Penutup Plastik Isolasi Kabel)", "buah", "PUIL", "KOMPONEN_MIKRO"),
        ("wi-fischer", "MIK.014", "Pemasangan Fischer Dinding (Selongsong Plastik Bor Dinding Cengkeram Sekrup)", "buah", "AHSP PUPR", "KOMPONEN_MIKRO"),
        ("wi-cable-lug", "MIK.015", "Pemasangan Kabel Skun (Cable Lug) Sepatu Kabel Tembaga Panel Utama", "buah", "PUIL", "KOMPONEN_MIKRO"),
        ("wi-gland-kabel", "MIK.016", "Pemasangan Gland Kabel Panel (Pengunci Lubang Kabel Kedap Debu)", "buah", "PUIL", "KOMPONEN_MIKRO"),
        ("wi-kabel-ties", "MIK.017", "Pemasangan Ties Wrap / Kabel Ties (Pengikat Plastik Jalur Kabel)", "paket", "PUIL", "KOMPONEN_MIKRO"),
        ("wi-flexible-conduit", "MIK.018", "Pemasangan Metal Conduit Flexibel (Pipa Besi Lentur Pembungkus Kabel)", "m'", "PUIL", "KOMPONEN_MIKRO"),
        ("wi-tile-adhesive-c2", "MIK.019", "Pemasangan Perekat Ubin Instan Tipe Premium (C2) Ubin Besar/Kolam", "m²", "AHSP PUPR", "KOMPONEN_MIKRO"),
        ("wi-zinc-chromate", "MIK.020", "Pekerjaan Pelapisan Primer Coated Baja (Zinc Chromate Anti-Karat)", "m²", "SNI 1729", "KOMPONEN_MIKRO"),
        ("wi-thermostat", "MIK.021", "Pemasangan Thermostat Kamar (Panel Pengatur Suhu Digital Dinding)", "unit", "AHSP PUPR", "KOMPONEN_MIKRO"),
        ("wi-acoustic-sealant", "MIK.022", "Pemasangan Acoustic Sealant (Lem Kedap Suara Sekeliling Partisi)", "m'", "AHSP PUPR", "KOMPONEN_MIKRO"),
        ("wi-seal-tape", "MIK.023", "Pemasangan Seal Tape Teflon (Lilitan Pita Putih Ulir Keran Anti Bocor)", "buah", "SNI Plumbing", "KOMPONEN_MIKRO"),
        ("wi-corner-bead", "MIK.024", "Pemasangan Corner Bead PVC/Aluminium (Profil Pelindung Sudut Acian)", "m'", "AHSP PUPR", "KOMPONEN_MIKRO"),
        ("wi-flexible-joint", "MIK.025", "Pemasangan Flexible Joint Pipa (Karet/Kawat Anyam Peredam Getaran Pompa)", "unit", "SNI Plumbing", "KOMPONEN_MIKRO"),
    ]
    for args in items:
        kg.add_work_item(WorkItemNode(*args))
    print(f"  Komponen Mikro: {len(items)} item pekerjaan dimuat")