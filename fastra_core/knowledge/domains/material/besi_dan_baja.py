"""
Domain Material: Besi dan Baja
Mencakup besi beton polos/ulir berbagai diameter dan merek, baja ringan, wiremesh.
"""

def load_besi_baja(kg):
    """Load semua varian besi dan baja ke Knowledge Graph."""
    
    from fastra_core.knowledge.nodes import MaterialNode
    
    brands = [
        ("Krakatau Steel", "PT Krakatau Steel"),
        ("Master Steel", "PT Master Steel Indonesia"),
        ("Gunung Garuda", "PT Gunung Garuda Steel"),
        ("Hanil Jaya", "PT Hanil Jaya Steel"),
    ]
    
    diameters = [6, 8, 10, 12, 13, 16, 19, 22, 25]
    
    # Harga patokan per batang (12m) untuk diameter tertentu
    harga_patokan = {
        6: 32000, 8: 46000, 10: 69000, 12: 98000,
        13: 118000, 16: 178000, 19: 252000, 22: 335000, 25: 430000
    }
    
    # Besi Polos
    for brand, manufacturer in brands:
        for d in diameters:
            kg.add_material(MaterialNode(
                id=f"mat-besi-polos-d{d}-{brand.lower().replace(' ', '-')}",
                name=f"Besi Beton Polos D{d}mm — {brand}",
                unit="batang",
                category="BESI_POLOS",
                specifications={
                    "merek": brand,
                    "produsen": manufacturer,
                    "tipe": "Polos (BJTP 280)",
                    "diameter_mm": d,
                    "panjang": "12m",
                    "harga_patokan": harga_patokan.get(d, 0),
                    "standar": "SNI 2052:2017"
                }
            ))
    
    # Besi Ulir
    for brand, manufacturer in brands:
        for d in diameters:
            kg.add_material(MaterialNode(
                id=f"mat-besi-ulir-d{d}-{brand.lower().replace(' ', '-')}",
                name=f"Besi Beton Ulir D{d}mm — {brand}",
                unit="batang",
                category="BESI_ULIR",
                specifications={
                    "merek": brand,
                    "produsen": manufacturer,
                    "tipe": "Ulir (BJTS 420)",
                    "diameter_mm": d,
                    "panjang": "12m",
                    "harga_patokan": int(harga_patokan.get(d, 0) * 1.08),
                    "standar": "SNI 2052:2017"
                }
            ))
    
    # Baja Ringan
    baja_ringan = [
        ("Kanal C75 0.75mm", "batang", 85000),
        ("Kanal C75 1.0mm", "batang", 105000),
        ("Reng R30 0.45mm", "batang", 42000),
        ("Reng R32 0.5mm", "batang", 48000),
    ]
    
    for name, unit, harga in baja_ringan:
        kg.add_material(MaterialNode(
            id=f"mat-baja-ringan-{name.lower().replace(' ', '-').replace('.', '')}",
            name=f"Baja Ringan {name}",
            unit=unit,
            category="BAJA_RINGAN",
            specifications={
                "nama": name,
                "harga_patokan": harga,
                "standar": "SNI 8393:2017"
            }
        ))
    
    # Wiremesh
    wiremesh_sizes = [
        ("M4 (2.1m x 5.4m)", "lembar", 185000),
        ("M5 (2.1m x 5.4m)", "lembar", 225000),
        ("M6 (2.1m x 5.4m)", "lembar", 320000),
        ("M8 (2.1m x 5.4m)", "lembar", 485000),
    ]
    
    for name, unit, harga in wiremesh_sizes:
        kg.add_material(MaterialNode(
            id=f"mat-wiremesh-{name.lower().replace(' ', '-').replace('.', '').replace('(', '').replace(')', '')}",
            name=f"Wiremesh {name}",
            unit=unit,
            category="WIREMESH",
            specifications={
                "nama": name,
                "harga_patokan": harga,
                "standar": "SNI 07-0663-2002"
            }
        ))
    
    count = len(brands) * len(diameters) * 2 + len(baja_ringan) + len(wiremesh_sizes)
    print(f"  ✅ Besi & Baja: {count} material dimuat")

