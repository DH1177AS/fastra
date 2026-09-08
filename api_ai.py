# fastra_core/api_ai.py

"""
API AI Layer (ACES-700) Secure
JWT OAuth2 + RBAC, rate limiter, security headers, JSON logging, Master Security, dan API /v1.
"""

from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv
from fastapi import APIRouter, Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    UUID4,
    field_validator,
    model_validator,
)

from auth_secure import (
    ROLE_ADMIN,
    ROLE_QS,
    ROLE_VIEWER,
    USERS_DB,
    create_access_token,
    get_current_user,
    require_role,
    verify_password,
)
from fastra_core.ai import (
    AIComponent,
    AIEventStore,
    AIService,
    DSLTranslator,
    DetectedElement,
    DrawingResult,
    LLMResult,
    PipelineBridge,
    Prediction,
    PredictionResult,
    SafetyFilter,
    VisionResult,
)
from fastra_core.digital_twin.database_extended import ExtendedDigitalTwinDB
from fastra_core.digital_twin.logging_config import setup_logging
from fastra_core.digital_twin.rate_limit import RateLimiter
from fastra_core.digital_twin.security import (
    SecurityHeadersMiddleware,
    validate_env,
)
from fastra_core.security_master import MasterSecurity

load_dotenv()
setup_logging()

logger = logging.getLogger("fastra_core.api_ai")
TOKEN_TYPE_BEARER = "bearer"  # nosec B105

app = FastAPI(title="FASTRA AI Layer Secure API", version="1.0.0")

# ------------------------------------------------------------------------------
# CORS & Security Middleware
# ------------------------------------------------------------------------------
cors_origins = os.getenv("FASTRA_CORS_ORIGINS", "http://localhost:8080,http://127.0.0.1:8080").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SecurityHeadersMiddleware)

# ------------------------------------------------------------------------------
# Environment validation
# ------------------------------------------------------------------------------
env_errors = validate_env()
if env_errors:
    if os.getenv("FASTRA_ENV", "").strip().lower() == "production":
        raise RuntimeError(f"Missing environment variables: {env_errors}")
    else:
        logger.warning("Environment validation issues (non-production): %s", env_errors)

# ------------------------------------------------------------------------------
# Database & core services
# ------------------------------------------------------------------------------
db = ExtendedDigitalTwinDB(
    os.getenv("FASTRA_DATABASE_URL", "sqlite:///./fastra_ai_secure.db")
)
db.seed_default_users()

master_security: Optional[MasterSecurity] = None
try:
    master_security = MasterSecurity.initialize_master_subsystem()
    logger.info("MasterSecurity initialized successfully")
except Exception as exc:
    logger.error("Master Security initialization failed: %s", exc, exc_info=True)

rate_limiter = RateLimiter(
    redis_url=os.getenv("FASTRA_REDIS_URL"),
    limit=int(os.getenv("FASTRA_RATE_LIMIT", "60")),
    window_seconds=int(os.getenv("FASTRA_RATE_WINDOW", "60")),
)

ai_service = AIService(AIEventStore(), db)
dsl_translator = DSLTranslator()
pipeline_bridge = PipelineBridge()
safety_filter = SafetyFilter()

# ------------------------------------------------------------------------------
# 1. LAYER DTO & PYDANTIC VALIDATOR (STRICT)
# ------------------------------------------------------------------------------


class StrictBaseModel(BaseModel):
    """Base class untuk semua DTO dengan strict mode dan anti‑coercion."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        strict=True,
        frozen=True,
        allow_inf_nan=False,
        populate_by_name=False,
        arbitrary_types_allowed=False,
    )


class VisionRequest(StrictBaseModel):
    model_version: str = Field(..., min_length=1, max_length=50)
    input_photos: List[str] = Field(..., min_length=1)
    estimations: Dict[str, Any]
    assumptions: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    suggested_actions: List[str] = Field(default_factory=list)

    @field_validator("input_photos")
    @classmethod
    def _validate_photo_paths(cls, value: List[str]) -> List[str]:
        if not value:
            raise ValueError("input_photos_cannot_be_empty")
        for path in value:
            if not isinstance(path, str) or not path.strip():
                raise ValueError("invalid_photo_path_string")
        return value


class DrawingRequest(StrictBaseModel):
    model_version: str = Field(..., min_length=1, max_length=50)
    input_files: List[str] = Field(..., min_length=1)
    detected_elements: Dict[str, List[Dict[str, Any]]]
    detected_dimensions: Dict[str, Any]
    generated_ccm: Dict[str, Any] = Field(default_factory=dict)
    uncertainties: List[Dict[str, Any]] = Field(default_factory=list)

    @field_validator("input_files")
    @classmethod
    def _validate_file_paths(cls, value: List[str]) -> List[str]:
        if not value:
            raise ValueError("input_files_cannot_be_empty")
        for path in value:
            if not isinstance(path, str) or not path.strip():
                raise ValueError("invalid_file_path_string")
        return value


class LLMRequest(StrictBaseModel):
    model_version: str = Field(..., min_length=1, max_length=50)
    input_text: str = Field(..., min_length=1, max_length=10000)
    output_dsl: Optional[str] = Field(default=None, max_length=10000)
    explanation: Optional[str] = Field(default=None, max_length=5000)
    recommendations: List[str] = Field(default_factory=list)
    references: List[str] = Field(default_factory=list)

    @field_validator("input_text")
    @classmethod
    def _validate_input_text_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("input_text_must_not_be_blank")
        return value


class PredictionRequest(StrictBaseModel):
    model_version: str = Field(..., min_length=1, max_length=50)
    predictions: List[Dict[str, Any]] = Field(..., min_length=1)
    recommendations: List[str] = Field(default_factory=list)

    @field_validator("predictions")
    @classmethod
    def _validate_predictions_structure(
        cls, value: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        if not value:
            raise ValueError("predictions_list_cannot_be_empty")
        for idx, pred in enumerate(value):
            if not isinstance(pred, dict):
                raise ValueError(f"prediction_{idx}_must_be_object")
            if not isinstance(pred.get("type", ""), str) or not pred.get("type", "").strip():
                raise ValueError(f"prediction_{idx}_type_required")
            if "data" not in pred or not isinstance(pred["data"], dict):
                raise ValueError(f"prediction_{idx}_data_required")
        return value


class DSLTranslateRequest(StrictBaseModel):
    text: str = Field(..., min_length=1, max_length=5000)

    @field_validator("text")
    @classmethod
    def _validate_text_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("text_must_not_be_blank")
        return value


class HumanReviewRequest(StrictBaseModel):
    approved: bool
    modifications: List[str] = Field(default_factory=list)


class MasterVerifyRequest(StrictBaseModel):
    password: str = Field(..., min_length=1, max_length=512)


class TOTPVerifyRequest(StrictBaseModel):
    secret: str = Field(..., min_length=1, max_length=128)
    code: str = Field(..., min_length=6, max_length=8)


# ------------------------------------------------------------------------------
# 2. LAYER DOMAIN MODEL & SERIALIZERS
# ------------------------------------------------------------------------------


class TokenAuthDomain:
    """Model domain murni untuk token otentikasi AI Layer."""

    def __init__(self, access_token: str, token_type: str, role: str) -> None:
        self.access_token = access_token
        self.token_type = token_type
        self.role = role

    def to_transport_record(self) -> Dict[str, str]:
        return {
            "access_token": self.access_token,
            "token_type": self.token_type,
            "role": self.role,
        }


class AIServiceResultDomain:
    """
    Model representasi bisnis murni untuk membungkus keluaran hasil komputasi dari AIService.
    Mencegah kebocoran data mentah engine AI internal ke client.
    """

    def __init__(self, raw_result: Any) -> None:
        self.model_version: str = getattr(raw_result, "model_version", "")
        self.input_photos: List[str] = getattr(raw_result, "input_photos", [])
        self.input_files: List[str] = getattr(raw_result, "input_files", [])
        self.estimations: Dict[str, Any] = getattr(raw_result, "estimations", {})
        self.assumptions: List[str] = getattr(raw_result, "assumptions", [])
        self.limitations: List[str] = getattr(raw_result, "limitations", [])
        self.suggested_actions: List[str] = getattr(raw_result, "suggested_actions", [])
        self.detected_elements: Dict[str, Any] = getattr(raw_result, "detected_elements", {})
        self.detected_dimensions: Dict[str, Any] = getattr(raw_result, "detected_dimensions", {})
        self.generated_ccm: Dict[str, Any] = getattr(raw_result, "generated_ccm", {})
        self.uncertainties: List[Any] = getattr(raw_result, "uncertainties", [])
        self.input_text: str = getattr(raw_result, "input_text", "")
        self.output_dsl: str = getattr(raw_result, "output_dsl", "")
        self.explanation: str = getattr(raw_result, "explanation", "")
        self.recommendations: List[str] = getattr(raw_result, "recommendations", [])
        self.references: List[str] = getattr(raw_result, "references", [])
        self.predictions: List[Any] = getattr(raw_result, "predictions", [])

    def serialize_vision_output(self) -> Dict[str, Any]:
        return {
            "model_version": self.model_version,
            "input_photos": self.input_photos,
            "estimations": self.estimations,
            "assumptions": self.assumptions,
            "limitations": self.limitations,
            "suggested_actions": self.suggested_actions,
        }

    def serialize_drawing_output(self) -> Dict[str, Any]:
        serialized_elements: Dict[str, List[Dict[str, Any]]] = {}
        for element_type, elements in self.detected_elements.items():
            serialized_elements[element_type] = []
            for elem in elements:
                serialized_elements[element_type].append(
                    {
                        "proposed_uuid": getattr(elem, "proposed_uuid", ""),
                        "type": getattr(elem, "type", ""),
                        "confidence": float(getattr(elem, "confidence", 0.0)),
                        "source": getattr(elem, "source", None),
                        "properties": getattr(elem, "properties", {}),
                    }
                )
        return {
            "model_version": self.model_version,
            "input_files": self.input_files,
            "detected_elements": serialized_elements,
            "detected_dimensions": self.detected_dimensions,
            "generated_ccm": self.generated_ccm,
            "uncertainties": self.uncertainties,
        }

    def serialize_llm_output(self) -> Dict[str, Any]:
        return {
            "model_version": self.model_version,
            "input_text": self.input_text,
            "output_dsl": self.output_dsl,
            "explanation": self.explanation,
            "recommendations": self.recommendations,
            "references": self.references,
        }

    def serialize_prediction_output(self) -> Dict[str, Any]:
        return {
            "model_version": self.model_version,
            "predictions": [
                {
                    "type": getattr(pred, "type", ""),
                    "data": getattr(pred, "data", {}),
                    "confidence_interval": getattr(pred, "confidence_interval", None),
                    "confidence_level": getattr(pred, "confidence_level", None),
                }
                for pred in self.predictions
            ],
            "recommendations": self.recommendations,
        }


class DSLTranslationDomain:
    """Model representasi bisnis murni hasil komputasi DSL Translator."""

    def __init__(self, translation_result: Any) -> None:
        self.source_text: str = getattr(translation_result, "source_text", "")
        self.dsl_text: str = getattr(translation_result, "dsl_text", "")
        self.entities: List[Any] = getattr(translation_result, "entities", [])
        self.needs_review: bool = bool(getattr(translation_result, "needs_review", False))
        self.warnings: List[str] = getattr(translation_result, "warnings", [])

    def serialize(self) -> Dict[str, Any]:
        return {
            "source_text": self.source_text,
            "dsl_text": self.dsl_text,
            "entities": self.entities,
            "needs_review": self.needs_review,
            "warnings": self.warnings,
        }


class AIAuditTrailDomain:
    """Model koleksi domain murni untuk audit log aktivitas komputasi AI."""

    def __init__(self, raw_events: List[Any]) -> None:
        self.raw_events = raw_events

    def serialize(self) -> Dict[str, List[Dict[str, Any]]]:
        serialized_events: List[Dict[str, Any]] = []
        for event in self.raw_events:
            if hasattr(event, "to_dict"):
                serialized_events.append(event.to_dict())
            elif hasattr(event, "model_dump"):
                serialized_events.append(event.model_dump())
            else:
                serialized_events.append(
                    {
                        "event_uuid": getattr(event, "event_uuid", ""),
                        "event_type": getattr(event, "event_type", ""),
                        "timestamp": getattr(event, "timestamp", ""),
                        "metadata": getattr(event, "metadata", {}),
                    }
                )
        return {"events": serialized_events}


# ------------------------------------------------------------------------------
# 3. INTERCEPTOR & DEPENDENCY LAYER
# ------------------------------------------------------------------------------


def _parse_uuid(value: str, field_name: str) -> uuid.UUID:
    """Parse dan validasi UUID, raise HTTPException 400 jika gagal."""
    try:
        return uuid.UUID(value)
    except (ValueError, TypeError, AttributeError) as exc:
        logger.debug("Invalid UUID for %s: %s", field_name, value)
        raise HTTPException(
            status_code=400, detail=f"invalid_{field_name}_uuid_format"
        ) from exc


def rate_limit_dependency(request: Request) -> Dict[str, int]:
    client_ip = request.client.host if request.client else "unknown"
    allowed, remaining, reset = rate_limiter.allow(
        f"{client_ip}:{request.url.path}"
    )
    if not allowed:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    return {"remaining": remaining, "reset": reset}


# ------------------------------------------------------------------------------
# 4. ROUTER V1 & CONTROLLER ENDPOINTS
# ------------------------------------------------------------------------------

router = APIRouter(prefix="/v1")


@router.post("/token", response_model=Dict[str, str])
def login_v1(form_data: OAuth2PasswordRequestForm = Depends()) -> Dict[str, str]:
    user = USERS_DB.get(form_data.username)
    if not user or not verify_password(
        form_data.password, user.get("password_hash", "")
    ):
        logger.warning("Failed login attempt for user: %s", form_data.username)
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = create_access_token(
        user.get("username", ""), user.get("role", "")
    )
    auth_domain = TokenAuthDomain(
        access_token=token,
        token_type=TOKEN_TYPE_BEARER,
        role=user.get("role", ""),
    )
    logger.info("User %s logged in successfully", user.get("username", ""))
    return auth_domain.to_transport_record()


@router.post(
    "/ai/vision",
    response_model=Dict[str, Any],
    dependencies=[Depends(require_role(ROLE_ADMIN)), Depends(rate_limit_dependency)],
)
def process_vision(payload: VisionRequest) -> Dict[str, Any]:
    try:
        result = VisionResult(
            model_version=payload.model_version,
            input_photos=payload.input_photos,
            estimations=payload.estimations,
            assumptions=payload.assumptions,
            limitations=payload.limitations,
            suggested_actions=payload.suggested_actions,
        )
        service_output = ai_service.process_vision(result)
        return {
            "result_uuid": service_output["result_uuid"],
            "event_uuid": service_output.get("event_uuid"),
            "verification": service_output.get("verification"),
            "model_version": result.model_version,
            "input_photos": list(result.input_photos),
            "estimations": result.estimations,
            "assumptions": list(result.assumptions),
            "limitations": list(result.limitations),
            "suggested_actions": list(result.suggested_actions),
        }
    except Exception as exc:
        logger.exception("Error in /ai/vision: %s", exc)
        raise HTTPException(status_code=400, detail="vision_processing_failed") from exc

@router.post(
    "/ai/drawing",
    response_model=Dict[str, Any],
    dependencies=[Depends(require_role(ROLE_QS)), Depends(rate_limit_dependency)],
)
def process_drawing(payload: DrawingRequest) -> Dict[str, Any]:
    try:
        detected: Dict[str, List[DetectedElement]] = {}
        for element_type, elements in payload.detected_elements.items():
            element_list: List[DetectedElement] = []
            for idx, elem in enumerate(elements):
                raw_uuid = elem.get("proposed_uuid", "")
                if raw_uuid:
                    try:
                        uuid.UUID(str(raw_uuid))
                    except (ValueError, TypeError, AttributeError) as exc:
                        raise ValueError(
                            f"invalid_proposed_uuid_format_at_index_{idx}"
                        ) from exc

                element_list.append(
                    DetectedElement(
                        proposed_uuid=str(raw_uuid),
                        type=str(elem.get("type", "")),
                        confidence=float(elem.get("confidence", 0.0)),
                        source=elem.get("source"),
                        properties=elem.get("properties", {}),
                    )
                )
            detected[str(element_type)] = element_list

        result = DrawingResult(
            model_version=payload.model_version,
            input_files=payload.input_files,
            detected_elements=detected,
            detected_dimensions=payload.detected_dimensions,
            generated_ccm=payload.generated_ccm,
            uncertainties=payload.uncertainties,
        )
        service_output = ai_service.process_drawing(result)
        domain_output = AIServiceResultDomain(service_output)
        return domain_output.serialize_drawing_output()
    except Exception as exc:
        logger.exception("Error in /ai/drawing: %s", exc)
        raise HTTPException(status_code=400, detail="drawing_processing_failed") from exc


@router.post(
    "/ai/llm",
    response_model=Dict[str, Any],
    dependencies=[Depends(require_role(ROLE_QS)), Depends(rate_limit_dependency)],
)
def process_llm(payload: LLMRequest) -> Dict[str, Any]:
    try:
        result = LLMResult(
            model_version=payload.model_version,
            input_text=payload.input_text,
            output_dsl=payload.output_dsl,
            explanation=payload.explanation,
            recommendations=payload.recommendations,
            references=payload.references,
        )
        service_output = ai_service.process_llm(result)
        domain_output = AIServiceResultDomain(service_output)
        return domain_output.serialize_llm_output()
    except Exception as exc:
        logger.exception("Error in /ai/llm: %s", exc)
        raise HTTPException(status_code=400, detail="llm_processing_failed") from exc


@router.post(
    "/ai/prediction",
    response_model=Dict[str, Any],
    dependencies=[Depends(require_role(ROLE_QS)), Depends(rate_limit_dependency)],
)
def process_prediction(payload: PredictionRequest) -> Dict[str, Any]:
    try:
        predictions: List[Prediction] = []
        for idx, item in enumerate(payload.predictions):
            prediction = Prediction(
                type=str(item["type"]),
                data=dict(item["data"]),
                confidence_interval=item.get("confidence_interval"),
                confidence_level=item.get("confidence_level"),
            )
            predictions.append(prediction)

        result = PredictionResult(
            model_version=payload.model_version,
            predictions=predictions,
            recommendations=payload.recommendations,
        )
        service_output = ai_service.process_prediction(result)
        domain_output = AIServiceResultDomain(service_output)
        return domain_output.serialize_prediction_output()
    except Exception as exc:
        logger.exception("Error in /ai/prediction: %s", exc)
        raise HTTPException(
            status_code=400, detail="prediction_processing_failed"
        ) from exc


@router.post(
    "/ai/translate",
    response_model=Dict[str, Any],
    dependencies=[Depends(get_current_user), Depends(rate_limit_dependency)],
)
def translate_to_dsl(payload: DSLTranslateRequest) -> Dict[str, Any]:
    try:
        result = dsl_translator.translate(payload.text)
        translation_domain = DSLTranslationDomain(result)
        return translation_domain.serialize()
    except Exception as exc:
        logger.exception("Error in /ai/translate: %s", exc)
        raise HTTPException(status_code=400, detail="translation_failed") from exc


@router.post(
    "/ai/review",
    response_model=Dict[str, Any],
    dependencies=[Depends(require_role(ROLE_QS)), Depends(rate_limit_dependency)],
)
def human_review(
    payload: HumanReviewRequest,
    event_uuid: str,
) -> Dict[str, Any]:
    validated_event_uuid = _parse_uuid(event_uuid, "event")
    success = ai_service.record_human_review(
        str(validated_event_uuid),
        payload.approved,
        payload.modifications,
    )
    if not success:
        raise HTTPException(status_code=404, detail="AI event not found")
    return {
        "status": "recorded",
        "event_uuid": str(validated_event_uuid),
        "approved": payload.approved,
    }


@router.get(
    "/ai/audit",
    response_model=Dict[str, List[Dict[str, Any]]],
    dependencies=[Depends(get_current_user), Depends(rate_limit_dependency)],
)
def get_ai_audit() -> Dict[str, List[Dict[str, Any]]]:
    events = ai_service.get_audit_events()
    audit_domain = AIAuditTrailDomain(events)
    return audit_domain.serialize()


# ------------------------------------------------------------------------------
# 7. MASTER SECURITY ENDPOINTS
# ------------------------------------------------------------------------------


@router.post(
    "/master/verify",
    response_model=Dict[str, bool],
    dependencies=[Depends(rate_limit_dependency)],
)
def master_verify(payload: MasterVerifyRequest) -> Dict[str, bool]:
    if master_security is None:
        raise HTTPException(status_code=503, detail="Master Security not initialized")
    ok = master_security.verify_master(payload.password)
    return {"valid": ok}


@router.post(
    "/master/totp/verify",
    response_model=Dict[str, bool],
    dependencies=[Depends(rate_limit_dependency)],
)
def master_totp_verify(payload: TOTPVerifyRequest) -> Dict[str, bool]:
    if master_security is None:
        raise HTTPException(status_code=503, detail="Master Security not initialized")
    ok = master_security.verify_totp(payload.secret, payload.code)
    return {"valid": ok}


@router.get(
    "/master/audit/integrity",
    response_model=Dict[str, Any],
    dependencies=[Depends(require_role(ROLE_ADMIN)), Depends(rate_limit_dependency)],
)
def master_audit_integrity() -> Dict[str, Any]:
    if master_security is None:
        raise HTTPException(status_code=503, detail="Master Security not initialized")
    return {"integrity": master_security.verify_audit_integrity()}


@router.get("/health", response_model=Dict[str, str])
def health() -> Dict[str, str]:
    return {"status": "ok"}


app.include_router(router)




