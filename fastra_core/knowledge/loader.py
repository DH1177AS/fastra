"""
FASTRA Construction Knowledge Platform - Orchestrator
"""
import logging
import re
import pandas as pd
from datetime import datetime
from fastra_core.knowledge.edges import PriceRecord

logger = logging.getLogger("fastra.knowledge")

def _slugify(text):
    text = str(text).lower().strip()
    text = re.sub(r'[^a-z0-9\s]', '', text)
    text = re.sub(r'\s+', '-', text)
    return text[:60]

def _load_prices_from_excel(kg):
    """Muat harga material dari Excel dan indeks regional."""
    regional_multipliers = {
        "DKI Jakarta": 1.0, "Surabaya": 0.98, "Bandung": 0.95,
        "Semarang": 0.93, "Surakarta (Solo)": 0.92, "Palembang": 1.05,
        "Medan": 1.08, "Denpasar": 1.1, "Makassar": 1.12,
        "Balikpapan": 1.2, "IKN": 1.35, "Morowali/Halmahera": 1.25,
        "Jayapura/Sorong": 1.45, "Wamena": 1.85, "Batam": 1.03,
        "Yogyakarta": 0.96, "Cirebon": 0.94, "Serang (Banten)": 0.97,
        "Bandar Lampung": 1.02, "Pontianak": 1.15, "Pekanbaru": 1.1,
        "Padang": 1.08,
    }
    try:
        df_mat = pd.read_excel(
            r"d:\fastra_projects\Database_Material_Bangunan.xlsx",
            sheet_name="Database Material"
        )
        new_prices = 0
        for _, row in df_mat.iterrows():
            kat_slug = _slugify(str(row.get('Kategori', '')))
            merek_slug = _slugify(str(row.get('Merek / Brand', '')))
            tipe_slug = _slugify(str(row.get('Tipe / Grade', '')))
            ukuran_slug = _slugify(str(row.get('Spesifikasi / Ukuran', '')))
            mat_id = f"mat-{kat_slug}-{merek_slug}-{tipe_slug}-{ukuran_slug}"[:120]
            harga_str = str(row.get('Harga Estimasi (Rp)', '0')).replace('Rp', '').replace('.', '').replace(',', '').strip()
            try:
                harga_excel = float(harga_str)
            except ValueError:
                continue
            if mat_id in kg.materials:
                if mat_id not in kg.prices:
                    kg.prices[mat_id] = []
                for region, multiplier in regional_multipliers.items():
                    kg.add_price(
                        mat_id,
                        PriceRecord(
                            material_id=mat_id,
                            price=harga_excel * multiplier,
                            region=region,
                            valid_from=datetime(2024, 1, 1),
                            valid_until=datetime(2026, 12, 31),
                            supplier_id="excel",
                            source=f"Excel ({row.get('Merek / Brand', '')})"
                        )
                    )
                    new_prices += 1
        logger.info(f"Harga material dimuat: {new_prices} record")
    except Exception as e:
        logger.warning(f"Harga material gagal dimuat: {e}")

    try:
        df_reg = pd.read_excel(
            r"d:\fastra_projects\Database Referensi Indeks Regional.xlsx",
            skiprows=1
        )
        df_reg.columns = ['no', 'kota', 'indeks', 'deskripsi']
        for _, row in df_reg.iterrows():
            if pd.isna(row.get('kota')):
                continue
            try:
                kota = str(row['kota']).strip()
                indeks = float(row['indeks'])
                regional_multipliers[kota] = indeks
            except (ValueError, TypeError):
                continue
        logger.info(f"Indeks regional dimuat: {len(regional_multipliers)} kota")
    except Exception as e:
        logger.warning(f"Indeks regional gagal dimuat: {e}")

    # Simpan region list di KG
    if not hasattr(kg, 'regions'):
        kg.regions = {}
    kg.regions = regional_multipliers

def create_fastra_knowledge_graph():
    from fastra_core.knowledge.graph import KnowledgeGraph
    kg = KnowledgeGraph()

    # MATERIALS (Domain + Excel)
    try:
        from fastra_core.knowledge.domains.material import load_all_materials
        load_all_materials(kg)
    except Exception as e:
        logger.error(f"Material domain: {e}")

    try:
        from import_material_excel import import_materials_from_excel
        import_materials_from_excel(kg)
    except Exception as e:
        logger.warning(f"Excel material skipped: {e}")

    # LABOR (Excel - WAJIB)
    try:
        from import_tenaga_excel import import_tenaga_from_excel
        import_tenaga_from_excel(kg)
    except Exception as e:
        logger.critical(f"Excel labor GAGAL: {e}")
        raise RuntimeError("Tenaga kerja dari Excel wajib dimuat.")

    # WORK ITEMS
    try:
        from fastra_core.knowledge.domains.work_item import load_all_work_items
        load_all_work_items(kg)
    except Exception as e:
        logger.error(f"Work Item: {e}")

    # RELASI SNI
    try:
        from integrasi_relasi_sni import integrasikan_relasi_sni
        integrasikan_relasi_sni(kg)
        logger.info("Relasi SNI berhasil diintegrasikan.")
    except Exception as e:
        logger.warning(f"Relasi SNI skipped: {e}")

    # EQUIPMENT
    try:
        from import_equipment_excel import import_equipment_from_excel
        import_equipment_from_excel(kg)
    except Exception as e:
        logger.warning(f"Equipment skipped: {e}")

    # INTEGRASI DATA ACES-500 (pajak, risiko, jadwal, template)
    try:
        from fastra_core.knowledge.integrasi_aces500 import integrasi_aces500
        integrasi_aces500(kg)
    except Exception as e:
        logger.warning(f"Integrasi ACES-500 skipped: {e}")

    # LOAD SEGMENT CALIBRATION (AHSP per segmen)
    try:
        from fastra_core.knowledge.segment_calibration import load_segment_calibration
        load_segment_calibration(kg)
        logger.info("Segment calibration dimuat.")
    except Exception as e:
        logger.warning(f"Segment calibration skipped: {e}")

    # HARGA REGIONAL & MATERIAL
    _load_prices_from_excel(kg)
    logger.info("Knowledge Graph selesai dibuat.")
        
    return kg
