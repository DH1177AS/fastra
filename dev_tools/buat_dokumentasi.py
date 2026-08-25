from pathlib import Path
from datetime import datetime

BASE = Path.cwd()

# README_COMPILER.md
readme = '''# FASTRA ACES-400 Quantity Compiler

## Ringkasan
Implementasi pipeline komputasi deterministik yang menerjemahkan Construction Canonical Model (CCM) menjadi Bill of Quantity (BOQ) sesuai standar **ACES-400**.

## Status
- **Compliance test:** 25/25 lulus (`tests/test_compliance_aces400.py`)
- **Verifikasi regresi Fase 1-3:** tetap hijau (`reset_and_test.py`)
- **Determinisme:** `boq_uuid` dan `trace_uuid` di-hash dari input; `project_uuid` API deterministik
- **TraceLog:** Menggunakan `computation_steps` sesuai §13.4
- **Deduction:** Bukaan >0.5 m², interseksi beam-column, wall adjacency dasar
- **API:** FastAPI dengan API key, rate limiter, payload limit, CORS, logging JSON

## Arsitektur Pipeline (8 Tahap)
1. **Lexer** (`lexer.py`) — Validasi CCM envelope & UUID
2. **Parser** (`parser.py`) — Deserialize entities, bangun object graph
3. **Geometry Builder** (`geometry_builder.py`) — Validasi geometri, gross quantity
4. **Topology Builder** (`topology_builder.py`) — Adjacency, deteksi koneksi
5. **Semantic Analyzer** (`semantic_analyzer.py`) — Validasi makna teknik
6. **Rule Validator** (`rule_validator.py`) — Aturan konstruksi SNI/AHSP
7. **Quantity Engine** (`quantity_engine.py`) — Deduction, interseksi, agregasi
8. **BOQ Builder** (`boq_builder.py`) — Mapping WorkItem, TraceLog, BOQ deterministik

## Cara Menjalankan
- Compliance Test: `python -m pytest tests/test_compliance_aces400.py -v`
- Demo Pipeline: `python run_fase4_demo.py`
- API Server: `python run_api.py`
- Swagger: `http://127.0.0.1:8000/docs`

## API Endpoint `/estimate-rab`
Header: `x-api-key: dev-api-key-change-me`  
Body: `{"region":"JAKARTA","overhead_pct":10.0,"profit_pct":10.0,"ppn_pct":11.0,"pph_pct":3.0,"contingency_pct":5.0,"inflation_pct":3.5,"duration_months":12}`

## Keamanan API
- API key di-hash (env `FASTRA_API_KEY`)
- Rate limiter in-memory (env `FASTRA_RATE_MAX`, `FASTRA_RATE_WINDOW`)
- Payload max 1 MB
- CORS configurable (`FASTRA_CORS_ORIGINS`)
- Logging JSON ke `api_audit.jsonl`

## Keterbatasan Saat Ini
- Geometri physical entities masih sintetis
- Rate limiter belum Redis
- Deduction wall-wall & slab-beam belum penuh
- `generate_regional_prices` belum tersedia

Dibuat oleh Tim FASTRA — 13 Agustus 2026
'''

# SESSION_HANDOVER.md
handover = f'''# SESSION_HANDOVER — {datetime.now():%d %B %Y}

## RINGKASAN PROYEK
FASTRA Construction Knowledge Platform.
Sesi ini menyelesaikan **Fase 4 (ACES-400 Quantity Compiler)**.

## STATUS AKHIR FASE 4
- Compliance test: **25/25 lulus** (`tests/test_compliance_aces400.py`)
- Pipeline 8 tahap berjalan end-to-end
- Deduction bukaan >0.5 m²
- Interseksi beam-column dihitung
- TraceLog sesuai §13.4 (`computation_steps`)
- BOQ deterministik (UUID dari hash input)
- API `/estimate-rab` dengan FastAPI + hardening
- Verifikasi regresi Fase 1-3: **500.197 relasi valid, 0 ID invalid**

## FILE UTAMA
| File | Fungsi |
|---|---|
| `fastra_core/compiler/compiler_pipeline.py` | Orchestrator 8 tahap |
| `fastra_core/compiler/quantity_engine.py` | Deduction & agregasi |
| `fastra_core/compiler/boq_builder.py` | BOQ + TraceLog |
| `fastra_core/compiler/trace.py` | TraceLog deterministik |
| `api_secure.py` | API FastAPI hardened |
| `tests/test_compliance_aces400.py` | 25 compliance test |
| `README_COMPILER.md` | Dokumentasi compiler |
| `reset_and_test.py` | Verifikasi Fase 1-3 |

## KEAMANAN API
- API key di-hash (default `dev-api-key-change-me`, env `FASTRA_API_KEY`)
- Rate limiter in-memory (10 req/menit per IP)
- Payload max 1 MB
- CORS hanya localhost
- Logging JSON `api_audit.jsonl`

## KETERBATASAN & LANGKAH SELANJUTNYA
- Geometri physical entities masih sintetis → perlu integrasi template gedung
- Rate limiter belum Redis → siapkan adapter untuk multi-worker
- Deduction wall-wall & slab-beam belum penuh
- `generate_regional_prices` belum tersedia

## CARA MENJALANKAN
```powershell
# Test compliance
python -m pytest tests/test_compliance_aces400.py -v

# Demo pipeline
python run_fase4_demo.py

# API
python run_api.py
