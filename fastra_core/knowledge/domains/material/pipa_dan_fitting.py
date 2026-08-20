"""Domain Material: Pipa dan Fitting"""
def load_pipa_fitting(kg):
    from fastra_core.knowledge.nodes import MaterialNode
    items = []
    brands = ["Rucika", "Wavin", "Maspion", "Vinilon"]
    sizes = ["1/2\"", "3/4\"", "1\"", "1.5\"", "2\"", "3\"", "4\""]
    for brand in brands:
        for size in sizes:
            size_id = size.replace('"','').replace('/','-')
            items.append((f"mat-pipa-pvc-aw-{size_id}-{brand.lower()}", f"Pipa PVC AW {size} {brand}", "batang", "PIPA_PVC", {"merek":brand,"tipe":"AW","ukuran":size,"harga_patokan":50000}))
    for size in sizes:
        size_id = size.replace('"','').replace('/','-')
        items.append((f"mat-pipa-ppr-{size_id}", f"Pipa PPR PN-10 {size}", "batang", "PIPA_PPR", {"tipe":"PN-10","ukuran":size,"harga_patokan":65000}))
    fittings = [
        ("mat-fitting-elbow-90", "Fitting Elbow 90° PVC", "buah", "FITTING", {"tipe":"Elbow 90°","harga_patokan":4500}),
        ("mat-fitting-tee", "Fitting Tee PVC", "buah", "FITTING", {"tipe":"Tee","harga_patokan":4500}),
        ("mat-fitting-sock", "Fitting Sock PVC", "buah", "FITTING", {"tipe":"Sock","harga_patokan":3500}),
        ("mat-fitting-dop", "Fitting Dop/Cap PVC", "buah", "FITTING", {"tipe":"Dop","harga_patokan":3500}),
        ("mat-lem-pipa", "Lem Pipa PVC", "kaleng", "LEM_PIPA", {"harga_patokan":25000}),
        ("mat-seal-tape", "Seal Tape Teflon", "roll", "SEAL_TAPE", {"harga_patokan":5000}),
    ]
    items.extend(fittings)
    for args in items:
        kg.add_material(MaterialNode(*args))
    print(f"  ✅ Pipa & Fitting: {len(items)} material dimuat")
