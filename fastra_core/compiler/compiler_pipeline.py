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
from fastra_core.compiler.ccm_validator import run_pipeline as validate_ccm_master
from fastra_core.digital_twin.snapshot import SnapshotStore
from fastra_core.digital_twin.serialization import entity_to_dict, to_serializable

class QuantityCompilerPipeline:
    def __init__(self, kg, generated_at: Optional[str] = None):
        self.kg = kg
        self.generated_at = generated_at or datetime.now(timezone.utc).isoformat()

    def compile(
        self,
        ccm_source,
        region: str = "JAKARTA",
        snapshot_store: Optional[SnapshotStore] = None,
        snapshot_name: Optional[str] = None,
        snapshot_type: str = "CHECKPOINT"
    ) -> Dict:
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
        result = {
            "compilation_status": "SUCCESS",
            "errors": [],
            "warnings": warnings,
            "boq": boq
        }
        # Capture snapshot jika diminta
        if snapshot_store is not None and snapshot_name is not None:
            snapshot_uuid = self._capture_snapshot(
                snapshot_store=snapshot_store,
                snapshot_name=snapshot_name,
                snapshot_type=snapshot_type,
                project_uuid=envelope.project_uuid,
                entities=entities,
                graph=graph,
                boq=boq
            )
            result["snapshot_uuid"] = snapshot_uuid
        return result

    def _capture_snapshot(
        self,
        snapshot_store: SnapshotStore,
        snapshot_name: str,
        snapshot_type: str,
        project_uuid: str,
        entities: Dict[str, Any],
        graph: Any,
        boq: Dict[str, Any]
    ) -> str:
        """Membuat snapshot dari state pipeline saat ini."""
        ccm_state = {
            "entities": {uid: entity_to_dict(entity) for uid, entity in entities.items()},
            "relationships": to_serializable(graph)
        }
        snapshot = snapshot_store.create_snapshot(
            project_uuid=project_uuid,
            snapshot_name=snapshot_name,
            snapshot_type=snapshot_type,
            ccm_state=ccm_state,
            boq_state=boq,
            timestamp=self.generated_at,
            description="Auto-captured by pipeline compile"
        )
        return snapshot.snapshot_uuid

    def validate_ccm(self, raw_text: str) -> Dict:
        """
        Validasi data CCM sesuai skema master CCM-MASTER-2026.V1.
        Mengembalikan ValidationReport, tidak mengubah pipeline costing.
        """
        try:
            return validate_ccm_master(raw_text)
        except Exception as e:
            return {"error": "VALIDATION_FAILED", "message": str(e)}

    def _fail(self, stage, errors, warnings):
        return {"compilation_status": "FAILED", "failed_stage": stage,
                "errors": errors, "warnings": warnings, "boq": None}
