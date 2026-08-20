# template_gedung_lengkap.py - ACES-300 Layer 2: Semantic Layer
# Klasifikasi Work Item 10 Divisi berdasarkan ACES-300 Section 7.2
# Auto-generated dari 35+ domain Work Item Fase 1

def load_workitem_classification():
    """Mengembalikan klasifikasi Work Item dalam 10 Divisi ACES-300."""
    divisions = {
        "DIV-01 Pekerjaan Persiapan": {
            "code": "PREP",
            "sub_divisi": {
                "1.1 Pembersihan Lahan": ["wi-pembersihan-lahan", "wi-clearing"],
                "1.2 Bouwplank": ["wi-bouwplank"],
                "1.3 Mobilisasi/Demobilisasi": ["wi-mobilisasi", "wi-demobilisasi"],
                "1.4 Pengukuran": ["wi-pengukuran", "wi-survey"],
            }
        },
        "DIV-02 Pekerjaan Tanah": {
            "code": "TNH",
            "sub_divisi": {
                "2.1 Galian Tanah Biasa": ["wi-galian-tanah", "wi-galian-pondasi-spesifik"],
                "2.2 Galian Tanah Keras": ["wi-galian-tanah-keras"],
                "2.3 Urugan Tanah Kembali": ["wi-urugan-tanah"],
                "2.4 Pemadatan Tanah": ["wi-pemadatan"],
                "2.5 Urugan Pasir": ["wi-urugan-pasir", "wi-pasir-alas-pondasi"],
            }
        },
        "DIV-03 Pekerjaan Pondasi": {
            "code": "FND",
            "sub_divisi": {
                "3.1 Pondasi Batu Kali": ["wi-pondasi-batu", "wi-pasangan-batu-kali-irigasi"],
                "3.2 Pondasi Footplate": ["wi-pondasi-footplate"],
                "3.3 Pondasi Bore Pile": ["wi-bore-pile-jembatan", "wi-bore-pile"],
                "3.4 Pondasi Sumuran": ["wi-sumuran"],
                "3.5 Pondasi Raft": ["wi-raft-foundation"],
                "3.6 Pondasi Talud": ["wi-talud-batu"],
            }
        },
        "DIV-04 Pekerjaan Struktur Beton": {
            "code": "STR",
            "sub_divisi": {
                "4.1 Bekisting": ["wi-bekisting-kolom", "wi-bekisting-balok", "wi-bekisting-plat-lt2", "wi-sloof-bekisting"],
                "4.2 Pembesian": ["wi-besi-polos", "wi-besi-ulir", "wi-kolom-lt1-rebar-fab", "wi-kolom-lt1-sengkang"],
                "4.3 Pengecoran": ["wi-beton-k225", "wi-beton-k250", "wi-beton-k300", "wi-beton-k350", "wi-beton-k400"],
                "4.4 Beton Precast": ["wi-precast-column", "wi-precast-beam"],
                "4.5 Struktur Baja": ["wi-baja-profil", "wi-baja-wf"],
            }
        },
        "DIV-05 Pekerjaan Dinding": {
            "code": "DIN",
            "sub_divisi": {
                "5.1 Pasangan Bata Merah": ["wi-pas-bata", "wi-bata-merah-taman"],
                "5.2 Pasangan Bata Ringan (Hebel)": ["wi-hebel-lt1", "wi-hebel-lt2", "wi-pas-bata-ringan"],
                "5.3 Plesteran": ["wi-plesteran", "wi-plester-dalam", "wi-plester-luar", "wi-plester-kasar-km"],
                "5.4 Acian": ["wi-acian", "wi-acian-dalam", "wi-acian-luar"],
                "5.5 Pengecatan": ["wi-cat-tembok", "wi-cat-dinding"],
                "5.6 Waterproofing": ["wi-waterproofing-pu", "wi-waterproofing"],
            }
        },
        "DIV-06 Pekerjaan Lantai": {
            "code": "LNT",
            "sub_divisi": {
                "6.1 Keramik Lantai": ["wi-keramik-lantai", "wi-keramik-dinding"],
                "6.2 Granit Lantai": ["wi-granit-lantai"],
                "6.3 Plint Lantai": ["wi-plint-lantai"],
                "6.4 Screed Lantai": ["wi-screed-lantai"],
                "6.5 Lantai Beton": ["wi-lantai-kerja-b0", "wi-rigid-pavement"],
            }
        },
        "DIV-07 Pekerjaan Plafon": {
            "code": "PLF",
            "sub_divisi": {
                "7.1 Rangka Plafon": ["wi-rangka-plafon-4x4", "wi-plafon-gypsum"],
                "7.2 Penutup Plafon Gypsum": ["wi-plafon-gypsum"],
                "7.3 Plafon Tripleks": ["wi-plafon-tripleks"],
            }
        },
        "DIV-08 Pekerjaan Atap": {
            "code": "ATP",
            "sub_divisi": {
                "8.1 Rangka Atap Baja Ringan": ["wi-atap-baja-ringan", "wi-kudakuda-fab", "wi-kudakuda-assembly"],
                "8.2 Rangka Atap Kayu": ["wi-rangka-atap-kayu"],
                "8.3 Penutup Genteng": ["wi-genteng-beton", "wi-genteng-metal", "wi-genteng-utama"],
                "8.4 Penutup Metal": ["wi-spandek", "wi-genteng-metal-berpasir"],
            }
        },
        "DIV-09 Pekerjaan Kusen, Pintu, Jendela": {
            "code": "KUS",
            "sub_divisi": {
                "9.1 Kusen Kayu": ["wi-kusen-kayu"],
                "9.2 Kusen Aluminium": ["wi-kusen-jendela-aluminium", "wi-kusen-pintu-kamar"],
                "9.3 Daun Pintu": ["wi-pintu-panel", "wi-daun-pintu-utama"],
                "9.4 Daun Jendela": ["wi-jendela-kayu", "wi-jendela-casement", "wi-jendela-sliding"],
            }
        },
        "DIV-10 Pekerjaan MEP": {
            "code": "MEP",
            "sub_divisi": {
                "10.1 Instalasi Listrik": ["wi-instalasi-titik-lampu", "wi-instalasi-stop-kontak", "wi-instalasi-panel"],
                "10.2 Instalasi Plumbing": ["wi-pipa-air-bersih-1-2", "wi-pipa-air-kotor-4", "wi-pasang-kloset", "wi-pasang-wastafel"],
                "10.3 Instalasi AC": ["wi-ac-wc", "wi-instalasi-ac"],
            }
        },
    }
    return divisions
