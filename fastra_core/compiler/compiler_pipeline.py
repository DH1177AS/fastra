
"""
ACES-400 Full Compliance Pipeline - deterministik
"""
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from fastra_core.compiler.lexer import Lexer
from fastra_core.compiler.parser import Parser
from fastra_core.compiler.geometry_builder import GeometryBuilder
from fastra_core.compiler.topology_builder import TopologyBuilder
from fastra_core.compiler.semantic_analyzer import SemanticAnalyzer
from fastra_core.compiler.rule_validator import RuleValidator
from fastra_core.compiler.quantity_engine import QuantityEngine
from fastra_core.compiler.boq_builder import BOQBuilder

class QuantityCompilerPipeline:
    def __init__(self, kg, generated_at: Optional[str] = None):
        self.kg = kg
        self.generated_at = generated_at or datetime.now(timezone.utc).isoformat()

    def compile(self, ccm_source, region: str = "JAKARTA") -> Dict:
        # Stage 1
        lexer = Lexer()
        envelope = lexer.load(ccm_source)
        if lexer.errors:
            return self._fail("LEXER", lexer.errors, lexer.warnings)
        # Stage 2
        parser = Parser()
        if envelope is None:
            return self._fail("LEXER", [{"error_code":"LEX-002","message":"CCM envelope is None"}], [])
        entities, graph = parser.parse(envelope)
        if parser.errors:
            return self._fail("PARSER", parser.errors, parser.warnings)
        # Stage 3
        geom = GeometryBuilder()
        geom_errors = geom.validate(entities)
        if geom_errors:
            return self._fail("GEOMETRY_BUILDER", geom_errors, geom.warnings)
        # Stage 4
        topo = TopologyBuilder()
        adjacency, topo_warnings = topo.build(entities, graph)
        # Stage 5
        sem = SemanticAnalyzer()
        sem_errors, sem_warnings = sem.analyze(entities, adjacency)
        if sem_errors:
            return self._fail("SEMANTIC_ANALYZER", sem_errors, sem_warnings)
        # Stage 6
        rule = RuleValidator()
        rule_errors, rule_warnings = rule.validate(entities, adjacency)
        if rule_errors:
            return self._fail("RULE_VALIDATOR", rule_errors, rule_warnings)
        # Stage 7
        qty = QuantityEngine()
        quantities = qty.process(entities, adjacency)
        if not quantities:
            return self._fail("QUANTITY_GENERATOR", [{"error_code":"QTO-001","message":"No quantities"}], [])
        # Stage 8
        boq_builder = BOQBuilder(self.kg, generated_at=self.generated_at)
        boq = boq_builder.build(quantities, region, envelope.project_uuid)
        warnings = topo_warnings + sem_warnings + rule_warnings + qty.warnings
        return {
            "compilation_status": "SUCCESS",
            "errors": [],
            "warnings": warnings,
            "boq": boq
        }

    def _fail(self, stage, errors, warnings):
        return {"compilation_status": "FAILED", "failed_stage": stage,
                "errors": errors, "warnings": warnings, "boq": None}
