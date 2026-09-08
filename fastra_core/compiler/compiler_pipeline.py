# fastra_core\compiler\compiler_pipeline.py

from __future__ import annotations

import enum
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from fastra_core.compiler.boq_builder import BOQBuilder
from fastra_core.compiler.ccm_validator import validate_ccm_master
from fastra_core.compiler.geometry_builder import GeometryBuilder
from fastra_core.compiler.lexer import Lexer
from fastra_core.compiler.parser import Parser
from fastra_core.compiler.quantity_engine import QuantityEngine
from fastra_core.compiler.rule_validator import RuleValidator
from fastra_core.compiler.semantic_analyzer import SemanticAnalyzer
from fastra_core.compiler.topology_builder import TopologyBuilder
from fastra_core.compiler.utils import entity_to_dict, to_serializable

logger = logging.getLogger(__name__)


class CompilationStatus(str, enum.Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class SnapshotType(str, enum.Enum):
    CHECKPOINT = "CHECKPOINT"
    BASELINE = "BASELINE"
    REVISION = "REVISION"


class PipelineStage(str, enum.Enum):
    LEXER = "LEXER"
    PARSER = "PARSER"
    GEOMETRY_BUILDER = "GEOMETRY_BUILDER"
    TOPOLOGY_BUILDER = "TOPOLOGY_BUILDER"
    SEMANTIC_ANALYZER = "SEMANTIC_ANALYZER"
    RULE_VALIDATOR = "RULE_VALIDATOR"
    QUANTITY_GENERATOR = "QUANTITY_GENERATOR"
    BOQ_GENERATOR = "BOQ_GENERATOR"


# ---------------------------------------------------------------------------
# Inbound DTOs – Pydantic Strict Gateway & Validation Matrix (Fail-Fast)
# ---------------------------------------------------------------------------
class PipelineErrorDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, strict=True)

    error_code: str = Field(..., min_length=2, max_length=16, pattern=r"^[A-Z0-9_\-]+$")
    message: str = Field(..., min_length=5, max_length=512)
    entity_uuid: Optional[str] = Field(default=None, max_length=64)

class PipelineWarningDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, strict=True)

    warning_code: str = Field(..., min_length=2, max_length=16, pattern=r"^[A-Z0-9_\-]+$")
    message: str = Field(..., min_length=5, max_length=512)
    entity_uuid: Optional[str] = Field(default=None, max_length=64)

class PipelineCompilePayloadDTO(BaseModel):
   
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, strict=True)

    region: str = Field(
        default="JAKARTA",
        min_length=2,
        max_length=64,
        pattern=r"^[A-Za-z0-9_\-\s]+$",
    )
    snapshot_name: Optional[str] = Field(default=None, min_length=2, max_length=128)
    snapshot_type: SnapshotType = Field(default=SnapshotType.CHECKPOINT)


class PipelineCompilationResultDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    compilation_status: str = Field(..., min_length=1, max_length=32)
    failed_stage: Optional[str] = Field(default=None, min_length=1, max_length=64)
    errors: List[PipelineErrorDTO] = Field(default_factory=list, max_length=1000)
    warnings: List[PipelineWarningDTO] = Field(default_factory=list, max_length=5000)
    boq: Optional[Dict[str, Any]] = None
    snapshot_uuid: Optional[str] = Field(
        default=None,
        min_length=36,
        max_length=36,
        pattern=r"^[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$",
    )


# ---------------------------------------------------------------------------
# Domain Models & Core Pipeline Orchestrator
# ---------------------------------------------------------------------------
class QuantityCompilerPipeline:
    
    def __init__(self, knowledge_graph: Any, generated_at: Optional[str] = None) -> None:
        self._kg = knowledge_graph
        self._generated_at = generated_at or datetime.now(timezone.utc).isoformat()

    def compile(
        self,
        ccm_source: Any,
        region: str = "JAKARTA",
        snapshot_store: Optional[Any] = None,
        snapshot_name: Optional[str] = None,
        snapshot_type: str = "CHECKPOINT",
    ) -> Dict[str, Any]:
        
        try:
            param_dto = PipelineCompilePayloadDTO(
                region=region,
                snapshot_name=snapshot_name,
                snapshot_type=SnapshotType(snapshot_type),
            )
        except ValueError as exc:
            return self._fail(
                stage=PipelineStage.LEXER,
                errors=[{"error_code": "LEX_001", "message": f"Parameter pipeline tidak valid: {exc}"}],
                warnings=[],
            )
       
        lexer = Lexer()
        try:
            envelope = lexer.load(ccm_source)
        except Exception as exc:
            logger.exception("Lexer stage gagal")
            return self._fail(
                PipelineStage.LEXER,
                [{"error_code": "LEX_002", "message": f"Lexer error: {exc}"}],
                [],
            )
        if getattr(lexer, "errors", None):
            return self._fail(PipelineStage.LEXER, lexer.errors, getattr(lexer, "warnings", []))
        if envelope is None:
            return self._fail(
                PipelineStage.LEXER,
                [{"error_code": "LEX_002", "message": "Bundel data CCM Envelope terdeteksi Null."}],
                [],
            )
        
        parser = Parser()
        try:
            entities, graph = parser.parse(envelope)
        except Exception as exc:
            logger.exception("Parser stage gagal")
            return self._fail(
                PipelineStage.PARSER,
                [{"error_code": "PAR_001", "message": f"Parser error: {exc}"}],
                [],
            )
        if getattr(parser, "errors", None):
            return self._fail(PipelineStage.PARSER, parser.errors, getattr(parser, "warnings", []))
      
        geom = GeometryBuilder()
        try:
            geom_errors = geom.validate(entities)
        except Exception as exc:
            logger.exception("Geometry Builder stage gagal")
            return self._fail(
                PipelineStage.GEOMETRY_BUILDER,
                [{"error_code": "GEO_003", "message": f"Geometry error: {exc}"}],
                [],
            )
        if geom_errors:
            return self._fail(PipelineStage.GEOMETRY_BUILDER, geom_errors, getattr(geom, "warnings", []))
       
        topo = TopologyBuilder()
        try:
            adjacency, topo_warnings = topo.build(entities, graph)
        except Exception as exc:
            logger.exception("Topology Builder stage gagal")
            return self._fail(
                PipelineStage.TOPOLOGY_BUILDER,
                [{"error_code": "TOP_001", "message": f"Topology error: {exc}"}],
                [],
            )
       
        sem = SemanticAnalyzer()
        try:
            sem_errors, sem_warnings = sem.analyze(entities, adjacency)
        except Exception as exc:
            logger.exception("Semantic Analyzer stage gagal")
            return self._fail(
                PipelineStage.SEMANTIC_ANALYZER,
                [{"error_code": "SEM_001", "message": f"Semantic error: {exc}"}],
                [],
            )
        if sem_errors:
            return self._fail(PipelineStage.SEMANTIC_ANALYZER, sem_errors, sem_warnings)
       
        rule = RuleValidator()
        try:
            rule_errors, rule_warnings = rule.validate(entities, adjacency)
        except Exception as exc:
            logger.exception("Rule Validator stage gagal")
            return self._fail(
                PipelineStage.RULE_VALIDATOR,
                [{"error_code": "RUL_001", "message": f"Rule validator error: {exc}"}],
                [],
            )
        if rule_errors:
            return self._fail(PipelineStage.RULE_VALIDATOR, rule_errors, rule_warnings)
        
        qty = QuantityEngine()
        try:
            quantities = qty.process(entities, adjacency)
        except Exception as exc:
            logger.exception("Quantity Engine stage gagal")
            return self._fail(
                PipelineStage.QUANTITY_GENERATOR,
                [{"error_code": "QTO_002", "message": f"Quantity engine error: {exc}"}],
                [],
            )
        if not quantities:
            return self._fail(
                PipelineStage.QUANTITY_GENERATOR,
                [{"error_code": "QTO_001", "message": "Tidak ada kuantitas volume bersih yang valid."}],
                [],
            )
      
        boq_builder = BOQBuilder(self._kg, generated_at=self._generated_at)
        try:
            boq = boq_builder.build_boq({
                "quantities": quantities,
                "region": param_dto.region,
                "project_uuid": getattr(envelope, "project_uuid", "00000000-0000-4000-8000-000000000000"),
            })
        except Exception as exc:
            logger.exception("BOQ Builder stage gagal")
            return self._fail(
                PipelineStage.BOQ_GENERATOR,
                [{"error_code": "BOQ_001", "message": f"BOQ builder error: {exc}"}],
                [],
            )
       
        compiled_warnings = []
        for warn_list in (topo_warnings, sem_warnings, rule_warnings, getattr(qty, "warnings", [])):
            if warn_list:
                compiled_warnings.extend(warn_list)
       
        normalized_warnings = []
        for w in compiled_warnings:
            try:
                normalized_warnings.append(PipelineWarningDTO.model_validate(w).model_dump())
            except Exception:
                logger.warning("Warning dengan format tidak valid diabaikan: %s", w)

        result_payload = {
            "compilation_status": CompilationStatus.SUCCESS.value,
            "errors": [],
            "warnings": normalized_warnings,
            "boq": boq,
        }
        
        if snapshot_store is not None and param_dto.snapshot_name is not None:
            try:
                snapshot_uuid = self._capture_snapshot(
                    snapshot_store=snapshot_store,
                    snapshot_name=param_dto.snapshot_name,
                    snapshot_type=param_dto.snapshot_type.value,
                    project_uuid=getattr(envelope, "project_uuid", "00000000-0000-4000-8000-000000000000"),
                    entities=entities,
                    graph=graph,
                    boq=boq,
                )
                result_payload["snapshot_uuid"] = snapshot_uuid
            except Exception as exc:
                logger.exception("Gagal menyimpan snapshot")
               
                result_payload["warnings"].append(
                    PipelineWarningDTO(
                        warning_code="SNAP_001",
                        message=f"Snapshot gagal dibuat: {exc}",
                    ).model_dump()
                )
       
        try:
            validated_result = PipelineCompilationResultDTO.model_validate(result_payload)
        except Exception as exc:
            logger.exception("Hasil pipeline tidak lolos validasi hilir")
            return self._fail(
                PipelineStage.BOQ_GENERATOR,
                [{"error_code": "OUT_001", "message": f"Output pipeline tidak valid: {exc}"}],
                [],
            )

        return validated_result.model_dump(exclude_none=True)

    def _capture_snapshot(
        self,
        snapshot_store: Any,
        snapshot_name: str,
        snapshot_type: str,
        project_uuid: str,
        entities: Dict[str, Any],
        graph: Any,
        boq: Dict[str, Any],
    ) -> str:
             
        if isinstance(entities, dict):
            entity_dict = {uid: entity_to_dict(entity) for uid, entity in entities.items()}
        else:
            entity_dict = {getattr(e, "uuid", str(i)): entity_to_dict(e) for i, e in enumerate(entities)}

        ccm_state = {
            "entities": entity_dict,
            "relationships": to_serializable(graph),
        }

        snapshot = snapshot_store.create_snapshot(
            project_uuid=project_uuid,
            snapshot_name=snapshot_name,
            snapshot_type=snapshot_type,
            ccm_state=ccm_state,
            boq_state=boq,
            timestamp=self._generated_at,
            description="Otomatis direkam oleh QuantityCompilerPipeline",
        )
        return str(getattr(snapshot, "snapshot_uuid", ""))

    def validate_ccm_master(self, raw_text: str) -> Dict[str, Any]:
       
        try:
            return validate_ccm_master(raw_text)
        except Exception as exc:
            logger.exception("Validasi CCM master gagal")
            return {
                "validation_status": "VALIDATION_FAILED",
                "message": f"Elemen dokumen melanggar aturan skema master: {exc}",
            }

    def _fail(
        self,
        stage: PipelineStage,
        errors: List[Dict[str, Any]],
        warnings: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
       
        fail_payload = {
            "compilation_status": CompilationStatus.FAILED.value,
            "failed_stage": stage.value,
            "errors": [],
            "warnings": [],
            "boq": None,
        }
       
        for e in errors:
            try:
                fail_payload["errors"].append(PipelineErrorDTO.model_validate(e).model_dump())
            except Exception:
                logger.warning("Error dengan format tidak valid diabaikan: %s", e)
       
        for w in warnings:
            try:
                fail_payload["warnings"].append(PipelineWarningDTO.model_validate(w).model_dump())
            except Exception:
                logger.warning("Warning dengan format tidak valid diabaikan: %s", w)

        try:
            return PipelineCompilationResultDTO.model_validate(fail_payload).model_dump(exclude_none=True)
        except Exception as exc:
            logger.critical("Gagal membuat DTO kegagalan: %s", exc)
           
            return {
                "compilation_status": "FAILED",
                "failed_stage": stage.value,
                "errors": [],
                "warnings": [],
                "boq": None,
            }