# FASTRA ACES-400 Quantity Compiler

Ringkasan: Pipeline komputasi deterministik yang menerjemahkan CCM menjadi BOQ sesuai ACES-400.

Status:
- Compliance test: 25/25 lulus (tests/test_compliance_aces400.py)
- Verifikasi regresi Fase 1-3: 500.197 relasi valid, 0 ID invalid
- Determinisme: boq_uuid dan trace_uuid di-hash dari input
- TraceLog: computation_steps sesuai 13.4
- Deduction: bukaan >0.5 m2, interseksi beam-column, wall adjacency dasar
- API: FastAPI dengan API key, rate limiter, payload limit, CORS, logging JSON

Arsitektur Pipeline:
1. Lexer
2. Parser
3. Geometry Builder
4. Topology Builder
5. Semantic Analyzer
6. Rule Validator
7. Quantity Engine
8. BOQ Builder

Cara Menjalankan:
- python -m pytest tests/test_compliance_aces400.py -v
- python run_fase4_demo.py
- python run_api.py

API:
- Header: x-api-key: dev-api-key-change-me
- Body: {"region":"JAKARTA","overhead_pct":10.0,"profit_pct":10.0,"ppn_pct":11.0,"pph_pct":3.0,"contingency_pct":5.0,"inflation_pct":3.5,"duration_months":12}

Keamanan:
- API key di-hash (env FASTRA_API_KEY)
- Rate limiter in-memory (10 req/menit)
- Payload max 1 MB
- CORS localhost

Keterbatasan:
- Geometri sintetis
- Rate limiter belum Redis
- Deduction wall-wall & slab-beam belum penuh
- generate_regional_prices belum tersedia

Tim FASTRA - 13 Agustus 2026
