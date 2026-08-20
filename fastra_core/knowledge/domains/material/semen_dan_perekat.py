"""
Domain Material: Semen dan Perekat
Mencakup semua varian semen portland, semen putih, mortar instan, dan perekat.
"""

def load_semen(kg):
    """Load semua varian semen dan perekat ke Knowledge Graph."""
    
    from fastra_core.knowledge.nodes import MaterialNode
    
    # Semen Portland - 6 merek × 2 varian = 12 node
    brands = [
        ("Semen Tiga Roda", "PT Indocement Tunggal Prakarsa", 68000, 55760),
        ("Semen Gresik", "PT Semen Gresik", 66000, 54120),
        ("Semen Holcim", "PT Holcim Indonesia", 67000, 54940),
        ("Semen Dynamix", "PT Solusi Bangun Indonesia", 67000, 54940),
        ("Semen Padang", "PT Semen Padang", 65000, 53300),
        ("Semen Merah Putih", "PT Cemindo Gemilang", 64000, 52480),
    ]
    
    for brand, manufacturer, harga_50, harga_40 in brands:
        for variant, harga in [("50kg", harga_50), ("40kg", harga_40)]:
            kg.add_material(MaterialNode(
                id=f"mat-semen-{brand.lower().replace(' ', '-')}-{variant}",
                name=f"{brand} Portland Type I ({variant})",
                unit="sak",
                category="SEMEN",
                specifications={
                    "merek": brand,
                    "produsen": manufacturer,
                    "tipe": "Portland Type I",
                    "berat": variant,
                    "harga_patokan": harga,
                    "standar": "SNI 15-2049-2004"
                }
            ))
    
    # Semen Putih
    for brand, harga in [("Semen Tiga Roda Putih", 95000), ("Semen Gresik Putih", 92000)]:
        kg.add_material(MaterialNode(
            id=f"mat-semen-putih-{brand.lower().replace(' ', '-')}",
            name=f"{brand} (40kg)",
            unit="sak",
            category="SEMEN_PUTIH",
            specifications={
                "merek": brand,
                "warna": "putih",
                "berat": "40kg",
                "harga_patokan": harga,
                "standar": "SNI 15-0129-2004"
            }
        ))
    
    # Mortar Instan
    mortar_brands = [
        ("Mortar Utama (MU)", "PT Cipta Mortar Utama"),
        ("Drymix", "PT Drymix Indonesia"),
        ("SikaGrout", "PT Sika Indonesia"),
    ]
    
    for brand, manufacturer in mortar_brands:
        kg.add_material(MaterialNode(
            id=f"mat-mortar-{brand.lower().replace(' ', '-').replace('(', '').replace(')', '')}",
            name=f"Mortar Instan {brand} (25kg)",
            unit="sak",
            category="MORTAR",
            specifications={
                "merek": brand,
                "produsen": manufacturer,
                "berat": "25kg",
                "harga_patokan": 75000,
                "standar": "SNI 6882:2014"
            }
        ))
    
    print(f"  ✅ Semen & Perekat: {len(brands)*2 + 2 + len(mortar_brands)} material dimuat")

