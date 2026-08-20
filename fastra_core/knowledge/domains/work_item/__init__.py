from .wi_pra_konstruksi import load_wi_pra_konstruksi
from .wi_struktur_bawah import load_wi_struktur_bawah
from .wi_struktur_atas import load_wi_struktur_atas
from .wi_atap import load_wi_atap
from .wi_dinding_kusen import load_wi_dinding_kusen
from .wi_finishing import load_wi_finishing
from .wi_elektrikal import load_wi_elektrikal
from .wi_plumbing import load_wi_plumbing
from .wi_interior import load_wi_interior
from .wi_taman import load_wi_taman
from .wi_kolam_renang import load_wi_kolam_renang
from .wi_jalan import load_wi_jalan
from .wi_jembatan import load_wi_jembatan
from .wi_irigasi import load_wi_irigasi
from .wi_trotoar import load_wi_trotoar
from .wi_dermaga import load_wi_dermaga
from .wi_terowongan import load_wi_terowongan
from .wi_olahraga import load_wi_olahraga
from .wi_pertanian import load_wi_pertanian
from .wi_lapangan_terbang import load_wi_lapangan_terbang
from .wi_rumah_sakit import load_wi_rumah_sakit
from .wi_sekolah import load_wi_sekolah
from .wi_gedung_pemerintah import load_wi_gedung_pemerintah
from .wi_gudang import load_wi_gudang
from .wi_pasar import load_wi_pasar
from .wi_gondola import load_wi_gondola
from .wi_kolam_ikan import load_wi_kolam_ikan
from .wi_dekorasi_luar import load_wi_dekorasi_luar
from .wi_komponen_mikro import load_wi_komponen_mikro
from .wi_pengujian_qc import load_wi_pengujian_qc
from .wi_pre_furnishing import load_wi_pre_furnishing
from .wi_serah_terima import load_wi_serah_terima
from .wi_tambahan_relasi import load_wi_tambahan_relasi

from .wi_auto_generated import load_wi_auto_generated

def load_all_work_items(kg):
    load_wi_pra_konstruksi(kg)
    load_wi_struktur_bawah(kg)
    load_wi_struktur_atas(kg)
    load_wi_atap(kg)
    load_wi_dinding_kusen(kg)
    load_wi_finishing(kg)
    load_wi_elektrikal(kg)
    load_wi_plumbing(kg)
    load_wi_interior(kg)
    load_wi_taman(kg)
    load_wi_kolam_renang(kg)
    load_wi_jalan(kg)
    load_wi_jembatan(kg)
    load_wi_irigasi(kg)
    load_wi_trotoar(kg)
    load_wi_dermaga(kg)
    load_wi_terowongan(kg)
    load_wi_olahraga(kg)
    load_wi_pertanian(kg)
    load_wi_lapangan_terbang(kg)
    load_wi_rumah_sakit(kg)
    load_wi_sekolah(kg)
    load_wi_gedung_pemerintah(kg)
    load_wi_gudang(kg)
    load_wi_pasar(kg)
    load_wi_gondola(kg)
    load_wi_kolam_ikan(kg)
    load_wi_dekorasi_luar(kg)
    load_wi_komponen_mikro(kg)
    load_wi_pengujian_qc(kg)
    load_wi_pre_furnishing(kg)
    load_wi_serah_terima(kg)
    load_wi_tambahan_relasi(kg)
    load_wi_auto_generated(kg)
    print(f"  📋 TOTAL ITEM PEKERJAAN: {len(kg.work_items)}")
