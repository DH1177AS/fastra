from .semen_dan_perekat import load_semen
from .besi_dan_baja import load_besi_baja
from .beton_dan_agregat import load_beton_agregat
from .kayu_dan_plywood import load_kayu_plywood
from .dinding_dan_partisi import load_dinding_partisi
from .lantai_dan_keramik import load_lantai_keramik
from .atap_dan_genteng import load_atap_genteng
from .plafon_dan_rangka import load_plafon_rangka
from .cat_dan_pelapis import load_cat_pelapis
from .pipa_dan_fitting import load_pipa_fitting
from .kabel_dan_listrik import load_kabel_listrik
from .sanitair_dan_plumbing import load_sanitair_plumbing
from .material_khusus import load_material_khusus

def load_all_materials(kg):
    load_semen(kg)
    load_besi_baja(kg)
    load_beton_agregat(kg)
    load_kayu_plywood(kg)
    load_dinding_partisi(kg)
    load_lantai_keramik(kg)
    load_atap_genteng(kg)
    load_plafon_rangka(kg)
    load_cat_pelapis(kg)
    load_pipa_fitting(kg)
    load_kabel_listrik(kg)
    load_sanitair_plumbing(kg)
    load_material_khusus(kg)
    print(f"  🧱 TOTAL MATERIAL: {len(kg.materials)}")
