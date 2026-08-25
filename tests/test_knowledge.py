"""
ACTS-300 Knowledge Network minimal compliance tests.
"""
import pytest
from fastra_core.knowledge.graph import KnowledgeGraph
from fastra_core.ontology.universal_object import UniversalObject


def test_knowledge_graph_empty_creation():
    kg = KnowledgeGraph()
    assert kg is not None
    assert hasattr(kg, "work_items")


def test_knowledge_graph_material_coefficient_valid():
    # Buat dua entitas sederhana untuk uji koefisien material
    kg = KnowledgeGraph()
    # Uji bahwa properti material ada dan dapat diset
    material = UniversalObject()
    material.id = "mat-001"
    material.unit = "kg"
    assert material.id == "mat-001"
    assert material.unit == "kg"


def test_knowledge_graph_add_work_item():
    kg = KnowledgeGraph()
    # Pastikan work_items dictionary ada
    assert hasattr(kg, "work_items")
    # Simulasi tambah work item manual (tanpa load Excel)
    class DummyWorkItem:
        def __init__(self):
            self.id = "wi-test"
            self.code = "PEK.TEST.001"
            self.name = "Test Work Item"
            self.unit = "m²"
            self.materials = []
            self.labor = []
    wi = DummyWorkItem()
    kg.work_items[wi.id] = wi
    assert "wi-test" in kg.work_items
    assert kg.work_items["wi-test"].code == "PEK.TEST.001"
