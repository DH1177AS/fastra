"""
API FASTRA Secure - Hardened
Mode produksi: wajib CCM dari klien.
Mode demo: fallback ke data demo (hanya untuk pengembangan).
"""
import os
import sys
import time
import uuid
import logging
import json
import hashlib
from typing import Dict, Optional
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, Request, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator
import uvicorn

from fastra_core.knowledge.loader import create_fastra_knowledge_graph
from fastra_core.compiler.compiler_pipeline import QuantityCompilerPipeline
from fastra_core.compiler.cost_engine import CostEngine
from fastra_core.compiler.ccm_validator import run_pipeline as validate_ccm_master

# ---------- Config ----------
VALID_REGIONS = {
    "JAKARTA","SURABAYA","BANDUNG","SEMARANG","MEDAN","MAKASSAR",
    "YOGYAKARTA","DENPASAR","BALIKPAPAN","PALEMBANG","PEKANBARU",
    "BANJARMASIN","MANADO","PADANG","BOGOR","TANGERANG","BEKASI",
    "DEPOK","MALANG","SOLO"
}

API_KEY = os.getenv("FASTRA_API_KEY", "dev-api-key-change-me")
API_KEY_HASH = hashlib.sha256(API_KEY.encode()).hexdigest()

ALLOWED_ORIGINS = os.getenv("FASTRA_CORS_ORIGINS", "http://localhost,http://127.0.0.1").split(",")

# Mode: production = wajib CCM; demo = fallback data demo
FASTRA_MODE = os.getenv("FASTRA_MODE", "production").lower()

logging.basicConfig(filename="api_audit.jsonl", level=logging.INFO,
                    format='{"time":"%(asctime)s","level":"%(levelname)s","message":"%(message)s"}')

def create_api_kg():
    kg = create_fastra_knowledge_graph()
    if not hasattr(kg, 'physical_entities'):
        kg.physical_entities = {}
    if not hasattr(kg, 'relationships'):
        kg.relationships = []

    def ent(id, name, t, **kwargs):
        d = {'id': id, 'name': name, 'type': t, 'uuid': str(uuid.uuid4()),
             'entity_type': None, 'status': None}
        d.update(kwargs)
        return d

    kg.physical_entities['ph-001'] = ent('ph-001','Wall Demo 1','Wall')
    kg.physical_entities['ph-002'] = ent('ph-002','Column Demo 1','Column')
    kg.physical_entities['ph-003'] = ent('ph-003','Beam Demo 1','Beam')
    kg.physical_entities['ph-004'] = ent('ph-004','Slab Demo 1','Slab')
    kg.physical_entities['ph-005'] = ent('ph-005','Foundation Demo 1','Foundation')
    kg.physical_entities['ph-006'] = ent('ph-006','Roof Demo 1','Roof')
    kg.physical_entities['dr-001'] = ent('dr-001','Door Demo 1','Door', width=0.9, height=2.1, door_type='SINGLE', material='Kayu')
    kg.physical_entities['wd-001'] = ent('wd-001','Window Demo 1','Window', width=1.2, height=1.5, window_type='CASEMENT', sill_height=0.9, material='Aluminium')

    kg.relationships.append({"source":"ph-002","target":"ph-003","type":"SUPPORTS"})
    kg.relationships.append({"source":"ph-005","target":"ph-002","type":"SUPPORTS"})
    kg.relationships.append({"source":"ph-001","target":"ph-004","type":"SUPPORTS"})
    kg.relationships.append({"source":"ph-003","target":"ph-004","type":"SUPPORTS"})
    kg.relationships.append({"source":"ph-006","target":"ph-004","type":"SUPPORTS"})
    kg.relationships.append({"source":"ph-001","target":"dr-001","type":"HOSTS"})
    kg.relationships.append({"source":"ph-001","target":"wd-001","type":"HOSTS"})
    return kg

kg = create_api_kg()

app = FastAPI(title="FASTRA API Secure", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

RATE_MAX = int(os.getenv("FASTRA_RATE_MAX", "10"))
RATE_WINDOW = int(os.getenv("FASTRA_RATE_WINDOW", "60"))
REDIS_URL = os.getenv("FASTRA_REDIS_URL", None)



class RateLimiter:
    """Rate limiter dengan dua backend: in-memory (default) dan Redis-ready."""
    def __init__(self):
        self.backend = "memory"
        self.store: Dict[str, list] = {}
        if REDIS_URL:
            try:
                import redis
                self.redis_client = redis.Redis.from_url(REDIS_URL)
                self.backend = "redis"
                print(f"ÃƒÂ¢Ã…â€œÃ¢â‚¬Â¦ Rate limiter menggunakan Redis: {REDIS_URL}")
            except Exception as e:
                logging.warning(f"Redis tidak tersedia, fallback ke in-memory: {e}")
                self.backend = "memory"

    def is_allowed(self, key: str) -> bool:
        now = time.time()
        if self.backend == "redis":
            # Fixed window counter + TTL (atomic via INCR)
            bucket = int(now // RATE_WINDOW)
            redis_key = f"{key}:{bucket}"
            try:
                current = self.redis_client.incr(redis_key)
                if current == 1:
                    self.redis_client.expire(redis_key, RATE_WINDOW)
                return current <= RATE_MAX
            except Exception as e:
                logging.warning(f"Redis error, fallback ke memory: {e}")
                self.backend = "memory"
                self.store = {}
                reqs = [t for t in self.store.get(key, []) if now - t < RATE_WINDOW]
                if len(reqs) >= RATE_MAX:
                    return False
                reqs.append(now)
                self.store[key] = reqs
                return True
        else:
            reqs = [t for t in self.store.get(key, []) if now - t < RATE_WINDOW]
            if len(reqs) >= RATE_MAX:
                return False
            reqs.append(now)
            self.store[key] = reqs
            return True

limiter = RateLimiter()

@app.middleware("http")
async def security_middleware(request: Request, call_next):
    client = request.client.host if request.client else "unknown"
    if not limiter.is_allowed(client):
        logging.warning(f"Rate limit exceeded for {client}")
        return JSONResponse(status_code=429, content={"detail": "Too many requests"})

    if request.headers.get("content-length"):
        try:
            content_length = int(request.headers["content-length"])
            if content_length > 1_000_000:
                return JSONResponse(status_code=413, content={"detail": "Payload too large"})
        except ValueError:
            pass
    response = await call_next(request)
    return response

def verify_api_key(x_api_key: str = Header(None)):
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Missing API key")
    key_hash = hashlib.sha256(x_api_key.encode()).hexdigest()
    if key_hash != API_KEY_HASH:
        raise HTTPException(status_code=401, detail="Invalid API key")

class EstimateRequest(BaseModel):
    region: str = Field(..., json_schema_extra={"example": "JAKARTA"})
    overhead_pct: float = Field(10.0, ge=0, le=100)
    profit_pct: float = Field(10.0, ge=0, le=100)
    ppn_pct: float = Field(11.0, ge=0, le=100)
    pph_pct: float = Field(3.0, ge=0, le=100)
    contingency_pct: float = Field(5.0, ge=0, le=100)
    inflation_pct: float = Field(3.5, ge=0, le=100)
    duration_months: int = Field(12, ge=1, le=120)
    ccm: Optional[dict] = None  # CCM envelope dari klien
    contract_value: Optional[float] = Field(None, ge=0, description="Nilai kontrak aktual untuk SMKK (opsional)")
    include_smkk: bool = Field(False, description="Aktifkan perhitungan biaya SMKK")
    risk_level: Optional[str] = Field("KECIL", description="Tingkat risiko SMKK: KECIL/SEDANG/BESAR")

    @field_validator("region")
    def check_region(cls, v):
        v = v.upper().strip()
        if v not in VALID_REGIONS:
            raise ValueError(f"Invalid region. Valid: {sorted(VALID_REGIONS)}")
        return v

def build_ccm_from_physical(kg):
    """Fallback untuk mode demo: bangun CCM dari physical entities sintetis."""
    entities = []
    for pid, p in kg.physical_entities.items():
        t = p.get("type")
        if t == "Wall":
            entities.append({
                "uuid": p.get("uuid"),
                "entity_type": "Physical",
                "type": "Wall",
                "name": p.get("name", "Wall"),
                "geometry": {
                    "axis_line": {"points": [{"x":0,"y":0,"z":0},{"x":5,"y":0,"z":0}]},
                    "height": 3.5,
                    "thickness": 0.15
                },
                "construction_type": "BATA_MERAH",
                "openings": []
            })
        elif t == "Column":
            entities.append({
                "uuid": p.get("uuid"),
                "entity_type": "Physical",
                "type": "Column",
                "name": p.get("name", "Column"),
                "geometry": {"width": 0.3, "depth": 0.3, "height": 3.5}
            })
        elif t == "Beam":
            col_uuid = next(ep["uuid"] for ep in kg.physical_entities.values() if ep["type"] == "Column")
            entities.append({
                "uuid": p.get("uuid"),
                "entity_type": "Physical",
                "type": "Beam",
                "name": p.get("name", "Beam"),
                "geometry": {"width": 0.25, "depth": 0.4, "length": 5.0},
                "start_connection": col_uuid,
                "end_connection": col_uuid
            })
        elif t == "Slab":
            entities.append({
                "uuid": p.get("uuid"),
                "entity_type": "Physical",
                "type": "Slab",
                "name": p.get("name", "Slab"),
                "geometry": {
                    "boundary": {"points": [{"x":0,"y":0,"z":0},{"x":5,"y":0,"z":0},{"x":5,"y":4,"z":0},{"x":0,"y":4,"z":0},{"x":0,"y":0,"z":0}]},
                    "thickness": 0.12
                },
                "supports": ["ph-001", "ph-003", "ph-006"]
            })
        elif t == "Foundation":
            entities.append({
                "uuid": p.get("uuid"),
                "entity_type": "Physical",
                "type": "Foundation",
                "name": p.get("name", "Foundation"),
                "geometry": {
                    "footprint": {"points": [{"x":0,"y":0,"z":0},{"x":1,"y":0,"z":0},{"x":1,"y":1,"z":0},{"x":0,"y":1,"z":0},{"x":0,"y":0,"z":0}]},
                    "depth": 1.0
                },
                "foundation_type": "FOOTPLATE"
            })
        elif t == "Roof":
            entities.append({
                "uuid": p.get("uuid"),
                "entity_type": "Physical",
                "type": "Roof",
                "name": p.get("name", "Roof"),
                "geometry": {
                    "footprint": {"points": [{"x":0,"y":0,"z":0},{"x":5,"y":0,"z":0},{"x":5,"y":4,"z":0},{"x":0,"y":4,"z":0},{"x":0,"y":0,"z":0}]},
                    "slope": 30.0
                }
            })
        elif t == "Door":
            entities.append({
                "uuid": p.get("uuid"),
                "entity_type": "Physical",
                "type": "Door",
                "name": p.get("name", "Door"),
                "geometry": {"width": p.get("width", 0.9), "height": p.get("height", 2.1)},
                "door_type": p.get("door_type", "SINGLE"),
                "host_wall": None
            })
        elif t == "Window":
            entities.append({
                "uuid": p.get("uuid"),
                "entity_type": "Physical",
                "type": "Window",
                "name": p.get("name", "Window"),
                "geometry": {"width": p.get("width", 1.2), "height": p.get("height", 1.5), "sill_height": p.get("sill_height", 0.9)},
                "window_type": p.get("window_type", "CASEMENT"),
                "host_wall": None
            })
    project_uuid = hashlib.sha256(json.dumps(entities, sort_keys=True, default=str).encode()).hexdigest()
    return {
        "ccm_version": "1.0.0",
        "project_uuid": project_uuid,
        "entities": entities,
        "relationships": kg.relationships
    }

@app.post("/estimate-rab", dependencies=[Depends(verify_api_key)])
def estimate_rab(req: EstimateRequest, request: Request):
    try:
        # Mode produksi: CCM wajib
        if FASTRA_MODE == "production":
            if not req.ccm:
                return JSONResponse(
                    status_code=422,
                    content={
                        "status": "error",
                        "message": "CCM wajib diisi pada mode production. Kirim field 'ccm' berisi CCM envelope."
                    }
                )
            ccm = req.ccm
            if not isinstance(ccm, dict):
                return JSONResponse(status_code=422, content={"status": "error", "message": "Format CCM tidak valid"})
        else:
            # Mode demo: gunakan CCM dari request jika ada, jika tidak gunakan fallback
            ccm = req.ccm if req.ccm else build_ccm_from_physical(kg)

        # Determinisme: generated_at berasal dari hash CCM
        generated_at = hashlib.sha256(
            json.dumps(ccm, sort_keys=True, default=str).encode()
        ).hexdigest()
        pipeline = QuantityCompilerPipeline(kg, generated_at=generated_at)
        result = pipeline.compile(ccm, req.region)
        if result["compilation_status"] != "SUCCESS":
            logging.error(f"Compile failed: {result['errors']}")
            return JSONResponse(status_code=422, content=result)
        engine = CostEngine(kg, {
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
            "contract_value": req.contract_value,
        })
        rab = engine.generate_rab(result["boq"], req.region)
        logging.info(f"Estimate RAB for {req.region} success; client={request.client.host if request.client else 'unknown'}; api_key_hash={API_KEY_HASH[:8]}...")
        return {"status": "success", "boq": result["boq"], "rab": rab}
    except Exception as e:
        logging.exception("Internal error")
        return JSONResponse(status_code=500, content={"status":"error","message":"Internal server error"})

@app.get("/health")
def health():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}

@app.post("/validate-ccm")
async def validate_ccm_endpoint(request: Request):
    """Terima CCM mentah multi‑part, kembalikan ValidationReport."""
    try:
        raw = (await request.body()).decode("utf-8")
        report = validate_ccm_master(raw)
        return {"status": "validated", "report": report}
    except Exception as e:
        return JSONResponse(status_code=400, content={"status": "error", "message": str(e)})


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=False)
