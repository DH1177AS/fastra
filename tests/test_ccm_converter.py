
"""
Test konversi CCM master -> internal FASTRA + compile pipeline.
"""
import json
import sys
import os
from pathlib import Path

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastra_core.compiler.ccm_converter import convert_master_to_internal
from fastra_core.compiler.compiler_pipeline import QuantityCompilerPipeline
from fastra_core.knowledge.loader import create_fastra_knowledge_graph


def _load_demo_master():
    path = Path("tests/fixtures/ccm_demo_complete.json")
    data = json.loads(path.read_text(encoding="utf-8"))
    return data["ConstructionCanonicalModel"]


def test_convert_master_to_internal_entities():
    master = _load_demo_master()
    internal = convert_master_to_internal(master)
    assert internal["ccm_version"] == "1.0.0"
    assert len(internal["entities"]) > 0
    assert len(internal["relationships"]) > 0
    types = {e["type"] for e in internal["entities"]}
    assert "Room" in types
    assert "Wall" in types
    assert "Column" in types
    assert "Beam" in types
    assert "Slab" in types

def test_compile_internal_from_demo():
    master = _load_demo_master()
    internal = convert_master_to_internal(master)
    kg = create_fastra_knowledge_graph()
    pipeline = QuantityCompilerPipeline(kg, generated_at="2026-08-21T00:00:00+00:00")
    result = pipeline.compile(internal, "JAKARTA")
    assert result["compilation_status"] == "SUCCESS"
    assert result["boq"] is not None
    assert result["boq"]["total_items"] > 0
