from .tenaga_umum import load_tenaga_umum
from .tenaga_spesialis_batu import load_tenaga_spesialis_batu
from .tenaga_spesialis_kayu import load_tenaga_spesialis_kayu
from .tenaga_spesialis_besi import load_tenaga_spesialis_besi
from .tenaga_spesialis_listrik import load_tenaga_spesialis_listrik
from .tenaga_spesialis_plumbing import load_tenaga_spesialis_plumbing
from .tenaga_spesialis_cat import load_tenaga_spesialis_cat
from .tenaga_spesialis_atap import load_tenaga_spesialis_atap
from .operator_alat_berat import load_operator_alat_berat
from .tenaga_profesional import load_tenaga_profesional

def load_all_labors(kg):
    load_tenaga_umum(kg)
    load_tenaga_spesialis_batu(kg)
    load_tenaga_spesialis_kayu(kg)
    load_tenaga_spesialis_besi(kg)
    load_tenaga_spesialis_listrik(kg)
    load_tenaga_spesialis_plumbing(kg)
    load_tenaga_spesialis_cat(kg)
    load_tenaga_spesialis_atap(kg)
    load_operator_alat_berat(kg)
    load_tenaga_profesional(kg)
    print(f"  👷 TOTAL TENAGA KERJA: {len(kg.labors)}")
