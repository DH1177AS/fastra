"""
Domain Material: Beton dan Agregat
Mencakup beton ready mix berbagai mutu dan supplier, agregat, pasir, batu.
"""

def load_beton_agregat(kg):
    """Load semua varian beton dan agregat ke Knowledge Graph."""
    
    from fastra_core.knowledge.nodes import MaterialNode
    
    # Beton Ready Mix
    suppliers = ["Holcim", "SCG", "Adhimix", "Pionir Beton"]
    mutu_list = [
        ("K-175", "14.5 MPa", 820000),
        ("K-225", "18.6 MPa", 890000),
        ("K-250", "20.7 MPa", 930000),
        ("K-275", "22.6 MPa", 960000),
        ("K-300", "24.9 MPa", 990000),
        ("K-350", "29.0 MPa", 1080000),
    ]
    
    for supplier in suppliers:
        for mutu, fc, harga in mutu_list:
            kg.add_material(MaterialNode(
                id=f"mat-beton-{mutu.lower()}-{supplier.lower()}",
                name=f"Beton Ready Mix {mutu} (fc' {fc}) — {supplier}",
                unit="m³",
                category="BETON_READY_MIX",
                specifications={
                    "supplier": supplier,
                    "mutu": mutu,
                    "fc": fc,
                    "slump": "10-12 cm",
                    "harga_patokan": harga,
                    "standar": "SNI 2847:2019"
                }
            ))
    
    # Agregat dan Pasir
    agregat = [
        ("Pasir Beton", "m³", 280000),
        ("Pasir Pasang", "m³", 240000),
        ("Pasir Urug", "m³", 180000),
        ("Batu Split 1-2 cm", "m³", 320000),
        ("Batu Split 2-3 cm", "m³", 290000),
        ("Screening", "m³", 210000),
        ("Sirtu", "m³", 195000),
    ]
    
    for name, unit, harga in agregat:
        kg.add_material(MaterialNode(
            id=f"mat-{name.lower().replace(' ', '-')}",
            name=f"{name}",
            unit=unit,
            category="AGREGAT",
            specifications={
                "nama": name,
                "harga_patokan": harga
            }
        ))
    
    count = len(suppliers) * len(mutu_list) + len(agregat)
    print(f"  ✅ Beton & Agregat: {count} material dimuat")

