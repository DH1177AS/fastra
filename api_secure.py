"""
API FASTRA Secure - Hardened
Mode produksi: wajib CCM dari klien.
Mode demo: fallback ke data demo (hanya untuk pengembangan).
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import uvicorn
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from fastra_core.compiler.ccm_validator import run_pipeline as validate_ccm_master
from fastra_core.compiler.compiler_pipeline import QuantityCompilerPipeline
from fastra_core.compiler.cost_engine import CostEngine
from fastra_core.knowledge.loader import create_fastra_knowledge_graph

# ------------------------------------------------------------------------------
# Logging Configuration
# ------------------------------------------------------------------------------
logger = logging.getLogger("fastra_core.api_secure")
logging.basicConfig(
    filename="api_audit.jsonl",
    level=logging.INFO,
    format='{"time":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","message":"%(message)s"}',
)

# ------------------------------------------------------------------------------
# Configuration (Environment)
# ------------------------------------------------------------------------------
VALID_REGIONS = frozenset({
    "JAKARTA", "SURABAYA", "BANDUNG", "SEMARANG", "MEDAN", "MAKASSAR",
    "YOGYAKARTA", "DENPASAR", "BALIKPAPAN", "PALEMBANG", "PEKANBARU",
    "BANJARMASIN", "MANADO", "PADANG", "BOGOR", "TANGERANG", "BEKASI",
    "DEPOK", "MALANG", "SOLO",
})

API_KEY = os.getenv("FASTRA_API_KEY", "dev-api-key-change-me")
API_KEY_HASH = hashlib.sha256(API_KEY.encode("utf-8")).hexdigest()

ALLOWED_ORIGINS = (
    origin.strip()
    for origin in os.getenv("FASTRA_CORS_ORIGINS", "http://localhost,http://127.0.0.1").split(",")
    if origin.strip()
)

FASTRA_MODE = os.getenv("FASTRA_MODE", "production").strip().lower()
if FASTRA_MODE not in {"production", "demo"}:
    raise ValueError("FASTRA_MODE must be either 'production' or 'demo'")

RATE_MAX = int(os.getenv("FASTRA_RATE_MAX", "10"))
RATE_WINDOW = int(os.getenv("FASTRA_RATE_WINDOW", "60"))
REDIS_URL = os.getenv("FASTRA_REDIS_URL")

# ------------------------------------------------------------------------------
# Knowledge Graph Initialization & Demo Data
# ------------------------------------------------------------------------------
def _create_api_kg():
    kg = create_fastra_knowledge_graph()
    if not hasattr(kg, "physical_entities"):
        kg.physical_entities = {}
    if not hasattr(kg, "relationships"):
        kg.relationships = []

    def _make_entity(id_: str, name: str, type_: str, **kwargs) -> Dict[str, Any]:
        return {
            "id": id_,
            "name": name,
            "type": type_,
            "uuid": str(uuid.uuid4()),
            "entity_type": None,
            "status": None,
            **kwargs,
        }

    kg.physical_entities["ph-001"] = _make_entity("ph-001", "Wall Demo 1", "Wall")
    kg.physical_entities["ph-002"] = _make_entity("ph-002", "Column Demo 1", "Column")
    kg.physical_entities["ph-003"] = _make_entity("ph-003", "Beam Demo 1", "Beam")
    kg.physical_entities["ph-004"] = _make_entity("ph-004", "Slab Demo 1", "Slab")
    kg.physical_entities["ph-005"] = _make_entity("ph-005", "Foundation Demo 1", "Foundation")
    kg.physical_entities["ph-006"] = _make_entity("ph-006", "Roof Demo 1", "Roof")
    kg.physical_entities["dr-001"] = _make_entity(
        "dr-001", "Door Demo 1", "Door", width=0.9, height=2.1, door_type="SINGLE", material="Kayu"
    )
    kg.physical_entities["wd-001"] = _make_entity(
        "wd-001", "Window Demo 1", "Window", width=1.2, height=1.5,
        window_type="CASEMENT", sill_height=0.9, material="Aluminium"
    )

    kg.relationships.extend([
        {"source": "ph-002", "target": "ph-003", "type": "SUPPORTS"},
        {"source": "ph-005", "target": "ph-002", "type": "SUPPORTS"},
        {"source": "ph-001", "target": "ph-004", "type": "SUPPORTS"},
        {"source": "ph-003", "target": "ph-004", "type": "SUPPORTS"},
        {"source": "ph-006", "target": "ph-004", "type": "SUPPORTS"},
        {"source": "ph-001", "target": "dr-001", "type": "HOSTS"},
        {"source": "ph-001", "target": "wd-001", "type": "HOSTS"},
    ])
    return kg

kg = _create_api_kg()

# ------------------------------------------------------------------------------
# Rate Limiter (In-Memory / Redis)
# ------------------------------------------------------------------------------
class RateLimiter:
    def __init__(self, redis_url: Optional[str] = None):
        self.redis_client = None
        self.store: Dict[str, List[float]] = {}
        if redis_url:
            try:
                import redis
                self.redis_client = redis.Redis.from_url(redis_url)
                self.redis_client.ping()
                logger.info("Rate limiter menggunakan Redis: %s", redis_url)
            except Exception as exc:
                logger.warning("Redis tidak tersedia, fallback ke in-memory: %s", exc)
                self.redis_client = None

    def _memory_is_allowed(self, key: str, now: float) -> bool:
        reqs = [t for t in self.store.get(key, []) if now - t < RATE_WINDOW]
        if len(reqs) >= RATE_MAX:
            return False
        reqs.append(now)
        self.store[key] = reqs
        return True

    def _redis_is_allowed(self, key: str, now: float) -> bool:
        bucket = int(now // RATE_WINDOW)
        redis_key = f"{key}:{bucket}"
        try:
            current = self.redis_client.incr(redis_key)
            if current == 1:
                self.redis_client.expire(redis_key, RATE_WINDOW)
            return current <= RATE_MAX
        except Exception as exc:
            logger.warning("Redis error, fallback ke memory: %s", exc)
            return self._memory_is_allowed(key, now)

    def is_allowed(self, key: str) -> bool:
        now = time.time()
        if self.redis_client is not None:
            return self._redis_is_allowed(key, now)
        return self._memory_is_allowed(key, now)

    def is_allowed(self, key: str) -> bool:
        now = time.time()
        if self.redis_client is not None:
            return self._redis_is_allowed(key, now)
        return self._memory_is_allowed(key, now)

limiter = RateLimiter(REDIS_URL)

# ------------------------------------------------------------------------------
# API Key Verification (Constant-Time)
# ------------------------------------------------------------------------------
def verify_api_key(x_api_key: str = Header(None)) -> None:
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Missing API key")
    # Gunakan hmac.compare_digest untuk perbandingan aman
    if not hmac.compare_digest(
        hashlib.sha256(x_api_key.encode("utf-8")).hexdigest(),
        API_KEY_HASH,
    ):
        raise HTTPException(status_code=401, detail="Invalid API key")

# ------------------------------------------------------------------------------
# Pydantic DTO (Strict)
# ------------------------------------------------------------------------------
class StrictBaseModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        strict=True,
        frozen=True,
        allow_inf_nan=False,
        populate_by_name=False,
        arbitrary_types_allowed=False,
    )

class EstimateRequest(StrictBaseModel):
    region: str = Field(..., description="Kota lokasi proyek")
    overhead_pct: float = Field(10.0, ge=0, le=100)
    profit_pct: float = Field(10.0, ge=0, le=100)
    ppn_pct: float = Field(11.0, ge=0, le=100)
    pph_pct: float = Field(3.0, ge=0, le=100)
    contingency_pct: float = Field(5.0, ge=0, le=100)
    inflation_pct: float = Field(3.5, ge=0, le=100)
    duration_months: int = Field(12, ge=1, le=120)
    ccm: Optional[Dict[str, Any]] = None
    contract_value: Optional[Decimal] = Field(None, ge=0, description="Nilai kontrak aktual untuk SMKK (opsional)")
    include_smkk: bool = Field(False, description="Aktifkan perhitungan biaya SMKK")
    risk_level: Optional[str] = Field("KECIL", description="Tingkat risiko SMKK: KECIL/SEDANG/BESAR")

    @field_validator("region")
    @classmethod
    def _validate_region(cls, v: str) -> str:
        v = v.upper().strip()
        if v not in VALID_REGIONS:
            raise ValueError(f"Invalid region. Valid: {sorted(VALID_REGIONS)}")
        return v

    @field_validator("risk_level")
    @classmethod
    def _validate_risk_level(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.upper().strip()
        if v not in {"KECIL", "SEDANG", "BESAR"}:
            raise ValueError("risk_level must be one of: KECIL, SEDANG, BESAR")
        return v

    @field_validator("contract_value", mode="before")
    @classmethod
    def _convert_contract_value_to_decimal(cls, v: Any) -> Any:
        if v is None or isinstance(v, Decimal):
            return v
        if isinstance(v, (int, float, str)):
            try:
                # Bersihkan simbol mata uang sederhana
                if isinstance(v, str):
                    v = v.replace("Rp", "").replace("IDR", "").strip()
                dec = Decimal(str(v))
                if not dec.is_finite():
                    raise ValueError("contract_value must be finite")
                return dec
            except (InvalidOperation, ValueError) as exc:
                raise ValueError("invalid contract_value") from exc
        raise TypeError("contract_value must be numeric")

    @model_validator(mode="after")
    def _validate_contract_value_required_for_smkk(self):
        if self.include_smkk and self.contract_value is None:
            raise ValueError("contract_value is required when include_smkk=True")
        return self

# ------------------------------------------------------------------------------
# Helper: Build CCM from physical entities (demo mode only)
# ------------------------------------------------------------------------------
def _build_ccm_from_physical(kg) -> Dict[str, Any]:
    entities = []
    for pid, p in kg.physical_entities.items():
        t = p.get("type")
        base = {
            "uuid": p.get("uuid"),
            "entity_type": "Physical",
            "type": t,
            "name": p.get("name", t),
        }
        if t == "Wall":
            base["geometry"] = {
                "axis_line": {"points": [{"x": 0, "y": 0, "z": 0}, {"x": 5, "y": 0, "z": 0}]},
                "height": 3.5,
                "thickness": 0.15,
            }
            base["construction_type"] = "BATA_MERAH"
            base["openings"] = []
        elif t == "Column":
            base["geometry"] = {"width": 0.3, "depth": 0.3, "height": 3.5}
        elif t == "Beam":
            col_uuid = next(
                ep["uuid"] for ep in kg.physical_entities.values() if ep["type"] == "Column"
            )
            base["geometry"] = {"width": 0.25, "depth": 0.4, "length": 5.0}
            base["start_connection"] = col_uuid
            base["end_connection"] = col_uuid
        elif t == "Slab":
            base["geometry"] = {
                "boundary": {
                    "points": [
                        {"x": 0, "y": 0, "z": 0},
                        {"x": 5, "y": 0, "z": 0},
                        {"x": 5, "y": 4, "z": 0},
                        {"x": 0, "y": 4, "z": 0},
                        {"x": 0, "y": 0, "z": 0},
                    ]
                },
                "thickness": 0.12,
            }
            base["supports"] = ["ph-001", "ph-003", "ph-006"]
        elif t == "Foundation":
            base["geometry"] = {
                "footprint": {
                    "points": [
                        {"x": 0, "y": 0, "z": 0},
                        {"x": 1, "y": 0, "z": 0},
                        {"x": 1, "y": 1, "z": 0},
                        {"x": 0, "y": 1, "z": 0},
                        {"x": 0, "y": 0, "z": 0},
                    ]
                },
                "depth": 1.0,
            }
            base["foundation_type"] = "FOOTPLATE"
        elif t == "Roof":
            base["geometry"] = {
                "footprint": {
                    "points": [
                        {"x": 0, "y": 0, "z": 0},
                        {"x": 5, "y": 0, "z": 0},
                        {"x": 5, "y": 4, "z": 0},
                        {"x": 0, "y": 4, "z": 0},
                        {"x": 0, "y": 0, "z": 0},
                    ]
                },
                "slope": 30.0,
            }
        elif t == "Door":
            base["geometry"] = {"width": p.get("width", 0.9), "height": p.get("height", 2.1)}
            base["door_type"] = p.get("door_type", "SINGLE")
            base["host_wall"] = None
        elif t == "Window":
            base["geometry"] = {
                "width": p.get("width", 1.2),
                "height": p.get("height", 1.5),
                "sill_height": p.get("sill_height", 0.9),
            }
            base["window_type"] = p.get("window_type", "CASEMENT")
            base["host_wall"] = None
        else:
            continue
        entities.append(base)

    project_uuid = hashlib.sha256(
        json.dumps(entities, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()
    return {
        "ccm_version": "1.0.0",
        "project_uuid": project_uuid,
        "entities": entities,
        "relationships": kg.relationships,
    }

# ------------------------------------------------------------------------------
# FastAPI Application
# ------------------------------------------------------------------------------
app = FastAPI(title="FASTRA API Secure", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

@app.middleware("http")
async def security_middleware(request: Request, call_next):
    client = request.client.host if request.client else "unknown"
    if not limiter.is_allowed(client):
        logger.warning("Rate limit exceeded for %s", client)
        return JSONResponse(status_code=429, content={"detail": "Too many requests"})

    content_length = request.headers.get("content-length")
    if content_length:
        try:
            if int(content_length) > 1_000_000:
                return JSONResponse(status_code=413, content={"detail": "Payload too large"})
        except ValueError:
            logger.debug("Invalid content-length header ignored")
    response = await call_next(request)
    return response

# ------------------------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------------------------
@app.post("/estimate-rab", dependencies=[Depends(verify_api_key)])
def estimate_rab(req: EstimateRequest, request: Request):
    try:
        if FASTRA_MODE == "production":
            if not req.ccm:
                return JSONResponse(
                    status_code=422,
                    content={
                        "status": "error",
                        "message": "CCM wajib diisi pada mode production. Kirim field 'ccm' berisi CCM envelope."
                    },
                )
            ccm = req.ccm
            if not isinstance(ccm, dict):
                return JSONResponse(status_code=422, content={"status": "error", "message": "Format CCM tidak valid"})
        else:  # demo
            ccm = req.ccm if req.ccm else _build_ccm_from_physical(kg)

        generated_at = hashlib.sha256(
            json.dumps(ccm, sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()

        pipeline = QuantityCompilerPipeline(kg, generated_at=generated_at)
        result = pipeline.compile(ccm, req.region)
        if result["compilation_status"] != "SUCCESS":
            logger.error("Compile failed: %s", result.get("errors"))
            return JSONResponse(status_code=422, content=result)

        engine = CostEngine(
            kg,
            {
                "overhead_pct": req.overhead_pct,
                "profit_pct": req.profit_pct,
                "ppn_pct": req.ppn_pct,
                "pph_pct": req.pph_pct,
                "contingency_pct": req.contingency_pct,
                "inflation_pct": req.inflation_pct,
                "duration_months": req.duration_months,
                "location_factor": 1.0,
                "include_smkk": req.include_smkk,
                "risk_level": req.risk_level,
                "contract_value": float(req.contract_value) if req.contract_value else None,
            },
        )
        rab = engine.generate_rab(result["boq"], req.region)
        logger.info(
            "Estimate RAB for %s success; client=%s; api_key_hash=%s",
            req.region,
            request.client.host if request.client else "unknown",
            API_KEY_HASH[:8],
        )
        return {"status": "success", "boq": result["boq"], "rab": rab}
    except Exception as exc:
        logger.exception("Internal error: %s", exc)
        return JSONResponse(status_code=500, content={"status": "error", "message": "Internal server error"})

@app.get("/health")
def health():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}

@app.post("/validate-ccm")
async def validate_ccm_endpoint(request: Request):
    try:
        raw = (await request.body()).decode("utf-8")
        report = validate_ccm_master(raw)
        return {"status": "validated", "report": report}
    except Exception as exc:
        logger.error("CCM validation error: %s", exc)
        return JSONResponse(status_code=400, content={"status": "error", "message": str(exc)})

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=False)