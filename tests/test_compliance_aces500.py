"""
ACES-500 Compliance Tests ? Cost Engine.
"""
import json
import uuid
from decimal import Decimal

import pytest

from fastra_core.knowledge.graph import KnowledgeGraph
from fastra_core.knowledge.nodes import MaterialNode, LaborNode, EquipmentNode, WorkItemNode
from fastra_core.knowledge.edges import MaterialRequirement, LaborRequirement, EquipmentRequirement, PriceRecord
from fastra_core.primitives.currency import Currency
from fastra_core.compiler.cost_engine import CostEngine


@pytest.fixture
def kg_minimal():
    kg = KnowledgeGraph()

    # Material
    kg.add_material(MaterialNode(id="mat-bata", name="Bata Merah", unit="buah", category="DINDING"))
    kg.add_material(MaterialNode(id="mat-semen", name="Semen", unit="sak", category="DINDING"))
    kg.add_material(MaterialNode(id="mat-pasir", name="Pasir", unit="m3", category="DINDING"))

    # Labor
    kg.add_labor(LaborNode(id="lab-pekerja", name="Pekerja", role="Pekerja", daily_rate=Currency(Decimal("120000"))))
    kg.add_labor(LaborNode(id="lab-tukang-batu", name="Tukang Batu", role="Tukang", daily_rate=Currency(Decimal("150000"))))

    # Equipment
    kg.add_equipment(EquipmentNode(id="eq-pump", name="Concrete Pump", unit="hari", rate_per_day=2500000))

    # Work Item
    kg.add_work_item(WorkItemNode(id="wi-bata", code="DIN.005", name="Pasangan Bata", unit="m2", sni_ref="SNI 6897:2008", category="DINDING"))
    kg.add_work_item(WorkItemNode(id="wi-cor", code="STR.029", name="Beton Cor", unit="m3", sni_ref="SNI 7394:2008", category="STRUKTUR"))

    # Requirements
    kg.add_material_requirement("wi-bata", MaterialRequirement(material_id="mat-bata", coefficient=70, waste_factor=1.05))
    kg.add_material_requirement("wi-bata", MaterialRequirement(material_id="mat-semen", coefficient=0.18, waste_factor=1.02))
    kg.add_material_requirement("wi-bata", MaterialRequirement(material_id="mat-pasir", coefficient=0.02, waste_factor=1.05))
    kg.add_labor_requirement("wi-bata", LaborRequirement(labor_id="lab-pekerja", coefficient=0.3))
    kg.add_labor_requirement("wi-bata", LaborRequirement(labor_id="lab-tukang-batu", coefficient=0.1))
    kg.add_equipment_requirement("wi-bata", EquipmentRequirement(equipment_id="eq-pump", coefficient=0.0))  # no cost

    # Prices
    kg.add_price("mat-bata", PriceRecord(material_id="mat-bata", price=850, region="JAKARTA", valid_from="2026-01-01", valid_until="2026-12-31", source="TEST"))
    kg.add_price("mat-semen", PriceRecord(material_id="mat-semen", price=63500, region="JAKARTA", valid_from="2026-01-01", valid_until="2026-12-31", source="TEST"))
    kg.add_price("mat-pasir", PriceRecord(material_id="mat-pasir", price=280000, region="JAKARTA", valid_from="2026-01-01", valid_until="2026-12-31", source="TEST"))
    return kg


def _make_boq():
    return {
        "project_uuid": str(uuid.uuid4()),
        "generated_at": "2026-08-20T00:00:00+00:00",
        "project_total": 0,
        "divisions": [
            {
                "division_code": "DIV-05",
                "division_name": "Pekerjaan Dinding",
                "items": [
                    {
                        "boq_item_uuid": "boq-item-001",
                        "item_code": "DIN.005",
                        "description": "Pasangan Bata",
                        "quantity": 43.51,
                        "unit": "m2",
                    }
                ]
            }
        ],
    }


def test_aces500_001_material_cost_calculation(kg_minimal):
    up = kg_minimal.get_unit_price("wi-bata", "JAKARTA")
    mat_cost = up["material_cost"]
    expected = (70 * 1.05 * 850) + (0.18 * 1.02 * 63500) + (0.02 * 1.05 * 280000)
    assert mat_cost == pytest.approx(round(expected, 2), 0.01)


def test_aces500_002_waste_factor_applied(kg_minimal):
    up = kg_minimal.get_unit_price("wi-bata", "JAKARTA")
    assert len(up["material_breakdown"]) == 3
    waste_bata = up["material_breakdown"][0]["waste_factor"]
    assert waste_bata == 1.05


def test_aces500_003_regional_price_lookup(kg_minimal):
    # Harga hanya tersedia untuk JAKARTA; region lain fallback ke harga pertama
    up = kg_minimal.get_unit_price("wi-bata", "BANDUNG")
    assert up["material_breakdown"][0]["price_source"].startswith("mat-bata/JAKARTA/")


def test_aces500_004_labor_cost_calculation(kg_minimal):
    up = kg_minimal.get_unit_price("wi-bata", "JAKARTA")
    expected = (0.3 * 120000) + (0.1 * 150000)
    assert up["labor_cost"] == pytest.approx(round(expected, 2), 0.01)


def test_aces500_006_equipment_cost_calculation(kg_minimal):
    # Tambah equipment requirement dengan koefisien > 0
    kg_minimal.add_equipment_requirement("wi-bata", EquipmentRequirement(equipment_id="eq-pump", coefficient=0.08))
    up = kg_minimal.get_unit_price("wi-bata", "JAKARTA")
    expected = 0.08 * 2500000
    assert up["equipment_cost"] == pytest.approx(round(expected, 2), 0.01)


def test_aces500_007_direct_cost_aggregator(kg_minimal):
    engine = CostEngine(kg_minimal)
    boq = _make_boq()
    rab = engine.generate_rab(boq, "JAKARTA")
    assert rab["direct_cost"] > 0


def test_aces500_008_overhead_percentage(kg_minimal):
    config = {"overhead_pct": 10.0}
    engine = CostEngine(kg_minimal, config)
    boq = _make_boq()
    rab = engine.generate_rab(boq, "JAKARTA")
    assert rab["overhead"] == pytest.approx(rab["direct_cost"] * 0.10, 0.01)


def test_aces500_009_profit_percentage(kg_minimal):
    config = {"profit_pct": 12.0}
    engine = CostEngine(kg_minimal, config)
    boq = _make_boq()
    rab = engine.generate_rab(boq, "JAKARTA")
    assert rab["profit"] == pytest.approx((rab["direct_cost"] + rab["overhead"]) * 0.12, 0.01)


def test_aces500_010_ppn_11_percent(kg_minimal):
    config = {"ppn_pct": 11.0}
    engine = CostEngine(kg_minimal, config)
    boq = _make_boq()
    rab = engine.generate_rab(boq, "JAKARTA")
    assert rab["ppn"] == pytest.approx(rab["dpp"] * 0.11, 0.01)


def test_aces500_012_contingency_percentage(kg_minimal):
    config = {"contingency_pct": 5.0}
    engine = CostEngine(kg_minimal, config)
    boq = _make_boq()
    rab = engine.generate_rab(boq, "JAKARTA")
    assert rab["contingency"] == pytest.approx(rab["direct_cost"] * 0.05, 0.01)


def test_aces500_013_escalation_compound(kg_minimal):
    config = {"inflation_pct": 3.5, "duration_months": 24}
    engine = CostEngine(kg_minimal, config)
    boq = _make_boq()
    rab = engine.generate_rab(boq, "JAKARTA")
    factor = (1 + 0.035) ** (24 / 12) - 1
    assert rab["escalation"] == pytest.approx(rab["dpp"] * factor, 0.01)


def test_aces500_019_determinism(kg_minimal):
    engine = CostEngine(kg_minimal)
    boq = _make_boq()
    r1 = engine.generate_rab(boq, "JAKARTA")
    r2 = engine.generate_rab(boq, "JAKARTA")
    r3 = engine.generate_rab(boq, "JAKARTA")
    assert json.dumps(r1, sort_keys=True, default=str) == json.dumps(r2, sort_keys=True, default=str) == json.dumps(r3, sort_keys=True, default=str)


def test_aces500_020_waste_factor_boundary(kg_minimal):
    with pytest.raises(ValueError):
        kg_minimal.add_material_requirement("wi-bata", MaterialRequirement(material_id="mat-bata", coefficient=1, waste_factor=1.5))
        kg_minimal.get_unit_price("wi-bata", "JAKARTA")


def test_aces500_021_price_validity_expired_rejected(kg_minimal):
    from fastra_core.knowledge.graph import KnowledgeGraph
    from fastra_core.knowledge.nodes import MaterialNode, LaborNode, WorkItemNode
    from fastra_core.knowledge.edges import MaterialRequirement, LaborRequirement, PriceRecord
    from fastra_core.primitives.currency import Currency
    from decimal import Decimal

    kg = KnowledgeGraph()
    kg.add_material(MaterialNode(id="mat-bata", name="Bata Merah", unit="buah", category="DINDING"))
    kg.add_labor(LaborNode(id="lab-pekerja", name="Pekerja", role="Pekerja", daily_rate=Currency(Decimal("120000"))))
    kg.add_work_item(WorkItemNode(id="wi-bata", code="DIN.005", name="Pasangan Bata", unit="m2", sni_ref="SNI 6897:2008", category="DINDING"))
    kg.add_material_requirement("wi-bata", MaterialRequirement(material_id="mat-bata", coefficient=1, waste_factor=1.0))
    kg.add_labor_requirement("wi-bata", LaborRequirement(labor_id="lab-pekerja", coefficient=0.0))
    kg.add_price("mat-bata", PriceRecord(material_id="mat-bata", price=999, region="JAKARTA", valid_from="2025-01-01", valid_until="2025-12-31", source="TEST"))
    up = kg.get_unit_price("wi-bata", "JAKARTA", price_date="2026-08-20")
    assert any(e["type"] == "expired_price" for e in up["errors"])


def test_aces500_023_audit_trail(kg_minimal):
    engine = CostEngine(kg_minimal)
    boq = _make_boq()
    rab = engine.generate_rab(boq, "JAKARTA")
    assert len(rab["traceability"]) == 1
    assert rab["traceability"][0]["audit_hash"]
    assert rab["traceability"][0]["ahs_reference"] == "SNI 6897:2008"

# ===== TAHAP A + B TESTS =====

def test_aces500_005_labor_regional(kg_minimal):
    """Upah regional: labor dengan region berbeda menghasilkan upah berbeda."""
    from decimal import Decimal
    # Tambah labor regional JAKARTA dan BANDUNG
    kg = KnowledgeGraph()
    kg.add_material(MaterialNode(id="mat-bata", name="Bata", unit="buah", category="DINDING"))
    kg.add_work_item(WorkItemNode(id="wi-bata", code="DIN.005", name="Pasangan Bata", unit="m2", sni_ref="SNI 6897:2008", category="DINDING"))
    kg.add_material_requirement("wi-bata", MaterialRequirement(material_id="mat-bata", coefficient=1, waste_factor=1.0))
    kg.add_labor(LaborNode(id="lab-pekerja", name="Pekerja", role="Pekerja", daily_rate=Currency(Decimal("120000")), region="JAKARTA"))
    kg.add_labor(LaborNode(id="lab-pekerja", name="Pekerja", role="Pekerja", daily_rate=Currency(Decimal("150000")), region="BANDUNG"))
    kg.add_labor_requirement("wi-bata", LaborRequirement(labor_id="lab-pekerja", coefficient=0.3))
    kg.add_price("mat-bata", PriceRecord(material_id="mat-bata", price=850, region="JAKARTA", valid_from="2026-01-01", valid_until="2026-12-31", source="TEST"))
    up_jkt = kg.get_unit_price("wi-bata", "JAKARTA")
    up_bdg = kg.get_unit_price("wi-bata", "BANDUNG")
    assert up_jkt["labor_breakdown"][0]["daily_rate"] == 120000
    assert up_bdg["labor_breakdown"][0]["daily_rate"] == 150000


def test_aces500_006b_equipment_cost_components(kg_minimal):
    """Equipment cost mencakup mobilization, operator, fuel."""
    kg = kg_minimal
    kg.equipment_requirements["wi-bata"] = []  # hapus requirement lama
    kg.add_equipment(EquipmentNode(id="eq-pump", name="Pump", unit="hari", rate_per_day=2500000,
                                   mobilization_cost=1000000, operator_cost_per_day=300000, fuel_cost_per_hour=50000))
    kg.add_equipment_requirement("wi-bata", EquipmentRequirement(equipment_id="eq-pump", coefficient=2))
    up = kg.get_unit_price("wi-bata", "JAKARTA")
    eq = up["equipment_breakdown"][0]
    assert eq["mobilization_cost"] == 1000000
    assert eq["operator_cost"] == 600000  # 2 * 300000
    assert eq["fuel_cost"] == 100000      # 2 * 50000
    assert eq["cost"] == 2*2500000 + 1000000 + 600000 + 100000


def test_aces500_012b_contingency_breakdown(kg_minimal):
    """Kontingensi terpisah menghasilkan breakdown."""
    config = {
        "design_contingency_pct": 2.0,
        "construction_contingency_pct": 3.0,
        "price_contingency_pct": 1.0,
    }
    engine = CostEngine(kg_minimal, config)
    boq = _make_boq()
    rab = engine.generate_rab(boq, "JAKARTA")
    assert rab["contingency_breakdown"]["design"] == round(rab["direct_cost"] * 0.02, 2)
    assert rab["contingency_breakdown"]["construction"] == round(rab["direct_cost"] * 0.03, 2)
    assert rab["contingency_breakdown"]["price"] == round(rab["direct_cost"] * 0.01, 2)


def test_aces500_012c_risk_contingency(kg_minimal):
    """Risk-based contingency dihitung dari probability x impact."""
    config = {
        "risk_register": [
            {"name": "cuaca", "probability": 0.1, "impact": 5000000},
            {"name": "desain", "probability": 0.05, "impact": 2000000},
        ]
    }
    engine = CostEngine(kg_minimal, config)
    boq = _make_boq()
    rab = engine.generate_rab(boq, "JAKARTA")
    expected_risk = 0.1*5000000 + 0.05*2000000
    assert rab["contingency_breakdown"]["risk"] == round(expected_risk, 2)


def test_aces500_013b_material_specific_escalation(kg_minimal):
    """Material dengan volatilitas menambah eskalasi."""
    from decimal import Decimal
    kg = KnowledgeGraph()
    kg.add_material(MaterialNode(id="mat-besi", name="Besi", unit="kg", category="STRUKTUR", volatility_factor=0.02))
    kg.add_work_item(WorkItemNode(id="wi-struktur", code="STR.029", name="Beton", unit="m3", category="STRUKTUR"))
    kg.add_material_requirement("wi-struktur", MaterialRequirement(material_id="mat-besi", coefficient=10, waste_factor=1.0))
    kg.add_price("mat-besi", PriceRecord(material_id="mat-besi", price=12000, region="JAKARTA", valid_from="2026-01-01", valid_until="2026-12-31", source="TEST"))
    engine = CostEngine(kg, {"inflation_pct": 3.5, "duration_months": 24})
    boq = {
        "project_uuid": str(uuid.uuid4()),
        "generated_at": "2026-08-20T00:00:00+00:00",
        "project_total": 0,
        "divisions": [{
            "division_code": "DIV-04",
            "division_name": "Struktur",
            "items": [{
                "boq_item_uuid": "boq-item-002",
                "item_code": "STR.029",
                "description": "Besi",
                "quantity": 10,
                "unit": "m3",
            }]
        }]
    }
    rab = engine.generate_rab(boq, "JAKARTA")
    assert rab["escalation"] > 0


def test_aces500_010b_ppn_pph_validation(kg_minimal):
    """PPN/PPh di luar batas harus ditolak."""
    with pytest.raises(ValueError):
        CostEngine(kg_minimal, {"ppn_pct": 25.0})
    with pytest.raises(ValueError):
        CostEngine(kg_minimal, {"pph_pct": 15.0})


def test_aces500_023b_computed_at_traceability(kg_minimal):
    """Traceability memiliki computed_at."""
    engine = CostEngine(kg_minimal)
    boq = _make_boq()
    rab = engine.generate_rab(boq, "JAKARTA")
    assert rab["traceability"][0]["computed_at"] == boq["generated_at"]

# ===== INTEGRASI DATA EXCEL =====
import os

@pytest.mark.skipif(not os.path.exists(r"D:\fastra_projects\Matriks_Manajemen_Risiko_Konstruksi_EMV.xlsx"), reason="File risiko tidak ada")
def test_aces500_024_integrasi_risk_register():
    from fastra_core.knowledge.graph import KnowledgeGraph
    from fastra_core.knowledge.integrasi_aces500 import integrasi_aces500
    kg = KnowledgeGraph()
    integrasi_aces500(kg)
    assert hasattr(kg, "risk_register")
    assert len(kg.risk_register) > 0
    assert kg.risk_register[0]["probability"] > 0

@pytest.mark.skipif(not os.path.exists(r"D:\fastra_projects\Sistem_Jadwal_KurvaS_dan_CashFlow.xlsx"), reason="File jadwal tidak ada")
def test_aces500_025_integrasi_schedule():
    from fastra_core.knowledge.graph import KnowledgeGraph
    from fastra_core.knowledge.integrasi_aces500 import integrasi_aces500
    kg = KnowledgeGraph()
    integrasi_aces500(kg)
    assert hasattr(kg, "schedule_weights")
    assert len(kg.schedule_weights) > 0

@pytest.mark.skipif(not os.path.exists(r"D:\fastra_projects\Multi_Template_RAB_Resmi_Generator.xlsx"), reason="File template tidak ada")
def test_aces500_026_integrasi_template():
    from fastra_core.knowledge.graph import KnowledgeGraph
    from fastra_core.knowledge.integrasi_aces500 import integrasi_aces500
    kg = KnowledgeGraph()
    integrasi_aces500(kg)
    assert hasattr(kg, "template_definitions")
    assert "PUPR Standard (AHSP)" in kg.template_definitions

def test_aces500_027_tax_rates_loaded():
    from fastra_core.knowledge.graph import KnowledgeGraph
    from fastra_core.knowledge.integrasi_aces500 import integrasi_aces500
    kg = KnowledgeGraph()
    integrasi_aces500(kg)
    assert hasattr(kg, "ppn_rate")
    assert hasattr(kg, "pph_rate")
    assert kg.ppn_rate > 0

# ===== VALUE ENGINEERING =====
import os

@pytest.mark.skipif(not os.path.exists(r"D:\fastra_projects\Alternatif_Material_Hemat.xlsx"), reason="File alternatif tidak ada")
def test_aces500_028_value_engineering_data_loaded():
    from fastra_core.knowledge.graph import KnowledgeGraph
    from fastra_core.knowledge.integrasi_aces500 import integrasi_aces500
    kg = KnowledgeGraph()
    integrasi_aces500(kg)
    assert hasattr(kg, "alternative_materials")
    assert len(kg.alternative_materials) > 0
    assert kg.alternative_materials[0]["original_id"]
    assert kg.alternative_materials[0]["alternative_id"]

def test_aces500_029_value_engineering_in_rab(kg_minimal):
    """Value engineering menampilkan potensi penghematan dari material alternatif."""
    # Setup alternatif manual untuk mat-bata
    kg_minimal.alternative_materials = [{
        "original_id": "mat-bata",
        "alternative_id": "mat-bata-alt",
        "original_price": 850,
        "alternative_price": 750,
        "status": "Lebih Hemat",
    }]
    config = {"include_value_engineering": True}
    engine = CostEngine(kg_minimal, config)
    boq = _make_boq()
    rab = engine.generate_rab(boq, "JAKARTA")
    assert "value_engineering" in rab
    assert len(rab["value_engineering"]) > 0
    ve = rab["value_engineering"][0]
    assert ve["material_id"] == "mat-bata"
    assert ve["alternative_id"] == "mat-bata-alt"
    assert ve["potential_saving"] > 0
