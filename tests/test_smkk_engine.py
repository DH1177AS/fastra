
"""
Unit test untuk SMKK Engine.
"""
import pytest
from fastra_core.compiler.smkk_engine import calculate_smkk, RISK_LEVELS

def test_smkk_risk_kecil():
    r = calculate_smkk("KECIL", 1_000_000_000)
    assert r["total_smkk"] > 0
    assert len(r["components"]) == 9
    assert all(c["status"] in ("APPROVED_QS_EXTERNAL", "APPROVED_DENGAN_ASUMSI_PROYEK", "PERLU_KUOTASI_VENDOR") for c in r["components"])

def test_smkk_risk_sedang():
    r = calculate_smkk("SEDANG", 2_000_000_000, worker_count=50, duration_months=12)
    assert r["total_smkk"] > 0

def test_smkk_risk_invalid():
    with pytest.raises(ValueError):
        calculate_smkk("SANGAT_BESAR", 1_000_000_000)

def test_smkk_fallback_file_missing(monkeypatch):
    """Saat file SMKK_Calibration.xlsx tidak ada, engine memakai fallback default."""
    import fastra_core.compiler.smkk_engine as sm
    monkeypatch.setattr(sm, "SMKK_FILE", r"D:\fastra_projects\NONEXISTENT.xlsx")
    r = sm.calculate_smkk("KECIL", 1_000_000_000)
    assert r["total_smkk"] > 0
    assert len(r["components"]) == 9
