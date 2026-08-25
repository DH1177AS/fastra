"""
API AI Layer (ACES-700) Secure
JWT OAuth2 + RBAC, rate limiter, security headers, JSON logging, Master Security, dan API /v1.
"""
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field

from auth_secure import (
    create_access_token, get_current_user, require_role, verify_password,
    ROLE_ADMIN, ROLE_QS, ROLE_VIEWER, USERS_DB
)
from fastra_core.ai import (
    AIComponent, VisionResult, DrawingResult, DetectedElement, LLMResult,
    PredictionResult, Prediction, AIService, AIEventStore, DSLTranslator,
    PipelineBridge, SafetyFilter
)
from fastra_core.digital_twin.rate_limit import RateLimiter
from fastra_core.digital_twin.security import SecurityHeadersMiddleware, validate_env
from fastra_core.digital_twin.logging_config import setup_logging
from fastra_core.digital_twin.database_extended import ExtendedDigitalTwinDB
from fastra_core.security_master import MasterSecurity

setup_logging()
app = FastAPI(title="FASTRA AI Layer Secure API", version="1.0.0")
app.add_middleware(SecurityHeadersMiddleware)

env_errors = validate_env()
if os.getenv("FASTRA_ENV") == "production" and env_errors:
    raise RuntimeError(f"Missing environment variables: {env_errors}")

# DB AI
db = ExtendedDigitalTwinDB(os.getenv("FASTRA_DATABASE_URL", "sqlite:///./fastra_ai_secure.db"))
db.seed_default_users()

# Master Security
master_security = None
try:
    master_security = MasterSecurity()
except Exception as e:
    import logging
    logging.warning(f"Master Security not initialized: {e}")

# Rate limiter
rate_limiter = RateLimiter(
    redis_url=os.getenv("FASTRA_REDIS_URL"),
    limit=int(os.getenv("FASTRA_RATE_LIMIT", "60")),
    window_seconds=int(os.getenv("FASTRA_RATE_WINDOW", "60")),
)

# AI Service dengan DB
ai_service = AIService(AIEventStore(), db)
dsl_translator = DSLTranslator()
pipeline_bridge = PipelineBridge()
safety_filter = SafetyFilter()

# ---------- Pydantic Models ----------
class VisionRequest(BaseModel):
    model_version: str
    input_photos: List[str]
    estimations: Dict[str, Any]
    assumptions: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    suggested_actions: List[str] = Field(default_factory=list)

class DrawingRequest(BaseModel):
    model_version: str
    input_files: List[str]
    detected_elements: Dict[str, List[Dict[str, Any]]]
    detected_dimensions: Dict[str, Any]
    generated_ccm: Dict[str, Any] = Field(default_factory=dict)
    uncertainties: List[Dict[str, Any]] = Field(default_factory=list)

class LLMRequest(BaseModel):
    model_version: str
    input_text: str
    output_dsl: Optional[str] = None
    explanation: Optional[str] = None
    recommendations: List[str] = Field(default_factory=list)
    references: List[str] = Field(default_factory=list)

class PredictionRequest(BaseModel):
    model_version: str
    predictions: List[Dict[str, Any]]
    recommendations: List[str] = Field(default_factory=list)

class DSLTranslateRequest(BaseModel):
    text: str

class HumanReviewRequest(BaseModel):
    approved: bool
    modifications: List[str] = Field(default_factory=list)

# ---------- Rate Limit Dependency ----------
def rate_limit_dependency(request: Request):
    client_ip = request.client.host if request.client else "unknown"
    allowed, remaining, reset = rate_limiter.allow(f"{client_ip}:{request.url.path}")
    if not allowed:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    return {"remaining": remaining, "reset": reset}

# ---------- Router /v1 ----------
router = APIRouter(prefix="/v1")

@router.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = USERS_DB.get(form_data.username)
    if not user or not verify_password(form_data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = create_access_token(user["username"], user["role"])
    return {"access_token": token, "token_type": "bearer", "role": user["role"]}  # nosec B105

@router.post("/ai/vision", dependencies=[Depends(require_role(ROLE_ADMIN)), Depends(rate_limit_dependency)])
def process_vision(payload: VisionRequest):
    try:
        result = VisionResult(
            model_version=payload.model_version,
            input_photos=payload.input_photos,
            estimations=payload.estimations,
            assumptions=payload.assumptions,
            limitations=payload.limitations,
            suggested_actions=payload.suggested_actions,
        )
        return ai_service.process_vision(result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/ai/drawing", dependencies=[Depends(require_role(ROLE_QS)), Depends(rate_limit_dependency)])
def process_drawing(payload: DrawingRequest):
    try:
        detected = {}
        for element_type, elements in payload.detected_elements.items():
            detected[element_type] = [
                DetectedElement(
                    proposed_uuid=elem.get("proposed_uuid", ""),
                    type=elem.get("type", ""),
                    confidence=float(elem.get("confidence", 0.0)),
                    source=elem.get("source"),
                    properties=elem.get("properties", {}),
                )
                for elem in elements
            ]
        result = DrawingResult(
            model_version=payload.model_version,
            input_files=payload.input_files,
            detected_elements=detected,
            detected_dimensions=payload.detected_dimensions,
            generated_ccm=payload.generated_ccm,
            uncertainties=payload.uncertainties,
        )
        return ai_service.process_drawing(result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/ai/llm", dependencies=[Depends(require_role(ROLE_QS)), Depends(rate_limit_dependency)])
def process_llm(payload: LLMRequest):
    try:
        result = LLMResult(
            model_version=payload.model_version,
            input_text=payload.input_text,
            output_dsl=payload.output_dsl,
            explanation=payload.explanation,
            recommendations=payload.recommendations,
            references=payload.references,
        )
        return ai_service.process_llm(result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/ai/prediction", dependencies=[Depends(require_role(ROLE_QS)), Depends(rate_limit_dependency)])
def process_prediction(payload: PredictionRequest):
    try:
        predictions = [
            Prediction(
                type=item.get("type", ""),
                data=item.get("data", {}),
                confidence_interval=item.get("confidence_interval"),
                confidence_level=item.get("confidence_level"),
            )
            for item in payload.predictions
        ]
        result = PredictionResult(
            model_version=payload.model_version,
            predictions=predictions,
            recommendations=payload.recommendations,
        )
        return ai_service.process_prediction(result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/ai/translate", dependencies=[Depends(get_current_user), Depends(rate_limit_dependency)])
def translate_to_dsl(payload: DSLTranslateRequest):
    try:
        result = dsl_translator.translate(payload.text)
        return {
            "source_text": result.source_text,
            "dsl_text": result.dsl_text,
            "entities": result.entities,
            "needs_review": result.needs_review,
            "warnings": result.warnings,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/ai/review", dependencies=[Depends(require_role(ROLE_QS)), Depends(rate_limit_dependency)])
def human_review(payload: HumanReviewRequest, event_uuid: str):
    success = ai_service.record_human_review(event_uuid, payload.approved, payload.modifications)
    if not success:
        raise HTTPException(status_code=404, detail="AI event not found")
    return {"status": "recorded", "event_uuid": event_uuid, "approved": payload.approved}

@router.get("/ai/audit", dependencies=[Depends(get_current_user), Depends(rate_limit_dependency)])
def get_ai_audit():
    return {"events": ai_service.get_audit_events()}

# ---------- Master Security Endpoints ----------
@router.post("/master/verify")
def master_verify(password: str):
    if master_security is None:
        raise HTTPException(status_code=503, detail="Master Security not initialized")
    ok = master_security.verify_master(password)
    return {"valid": ok}

@router.post("/master/totp/verify")
def master_totp_verify(secret: str, code: str):
    if master_security is None:
        raise HTTPException(status_code=503, detail="Master Security not initialized")
    ok = master_security.verify_totp(secret, code)
    return {"valid": ok}

@router.get("/master/audit/integrity")
def master_audit_integrity():
    if master_security is None:
        raise HTTPException(status_code=503, detail="Master Security not initialized")
    return {"integrity": master_security.verify_audit_integrity()}

@router.get("/health")
def health():
    return {"status": "ok"}

app.include_router(router)
