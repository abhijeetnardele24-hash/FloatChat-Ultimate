# FloatChat Ultimate Backend

FastAPI backend for FloatChat Ultimate ocean data workflows.

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.11+ (local development/tests)

### Start Services

```bash
docker-compose up -d
docker-compose logs -f backend
docker-compose down
```

### Access Points
- Backend API: `http://localhost:8000`
- API docs: `http://localhost:8000/docs`
- PostgreSQL: `localhost:5432`
- Redis: `localhost:6379`
- Ollama: `http://localhost:11434`
- Qdrant: `http://localhost:6333`

## API Endpoints

### Core
```bash
GET /health
GET /api/floats
GET /api/floats/{wmo_number}
GET /api/profiles
GET /api/stats
```

### Chat
```bash
POST /api/chat
GET /api/chat/providers
GET /api/admin/metrics/summary
GET /api/admin/metrics/slo
GET /api/admin/metrics/prometheus
# Optional header when ADMIN_API_KEY is set:
# X-Admin-Key: <your-admin-key>
```

`POST /api/chat` now also returns reliability metadata fields:
- `evidence_score`, `evidence_coverage_score`
- `method`, `data_source`, `limitations`, `next_checks`
- `reliability_warnings`

### ARGO v1 Filters
```bash
POST /api/v1/argo/floats/filter
POST /api/v1/argo/profiles/filter
POST /api/v1/argo/measurements/filter
GET  /api/v1/argo/stats/summary
GET  /api/v1/argo/ingestion/status
GET  /api/v1/argo/ingestion/jobs
POST /api/v1/argo/ingestion/run
```

### ArgoVis External (Optional)
```bash
GET /api/v1/argovis/ping
GET /api/v1/argovis/latest
GET /api/v1/argovis/region
GET /api/v1/argovis/profiles
GET /api/v1/argovis/profiles/{profile_id}
GET /api/v1/argovis/platforms
GET /api/v1/argovis/platforms/{platform_number}
GET /api/v1/argovis/vocabulary
```

### Tools and Export
```bash
GET  /api/v1/tools/glossary
POST /api/v1/tools/calculate/pressure-depth
GET  /api/v1/tools/learn/insights
GET  /api/v1/tools/quick-stats

POST /api/v1/export/floats/csv
POST /api/v1/export/profiles/csv
POST /api/v1/export/measurements/csv
POST /api/v1/export/measurements/netcdf
POST /api/v1/export/snapshot/json
```

### Auth (JWT)
```bash
POST /api/v1/auth/register
POST /api/v1/auth/login
GET  /api/v1/auth/me
```

### Study Workspaces
```bash
GET    /api/v1/study/workspaces
POST   /api/v1/study/workspaces
POST   /api/v1/study/workspaces/{workspace_id}/clone
PATCH  /api/v1/study/workspaces/{workspace_id}
DELETE /api/v1/study/workspaces/{workspace_id}
GET    /api/v1/study/workspaces/{workspace_id}/members
POST   /api/v1/study/workspaces/{workspace_id}/members
PATCH  /api/v1/study/workspaces/{workspace_id}/members/{member_user_id}
DELETE /api/v1/study/workspaces/{workspace_id}/members/{member_user_id}

GET    /api/v1/study/workspaces/{workspace_id}/notes
GET    /api/v1/study/workspaces/{workspace_id}/notes/search?q=...
POST   /api/v1/study/workspaces/{workspace_id}/notes
DELETE /api/v1/study/notes/{note_id}

GET    /api/v1/study/workspaces/{workspace_id}/queries
POST   /api/v1/study/workspaces/{workspace_id}/queries
GET    /api/v1/study/workspaces/{workspace_id}/snapshot
GET    /api/v1/study/workspaces/{workspace_id}/dashboard
POST   /api/v1/study/workspaces/{workspace_id}/versions
GET    /api/v1/study/workspaces/{workspace_id}/versions
GET    /api/v1/study/workspaces/{workspace_id}/versions/{version_id}
POST   /api/v1/study/workspaces/{workspace_id}/versions/{version_id}/restore
GET    /api/v1/study/workspaces/{workspace_id}/repro-package
GET    /api/v1/study/workspaces/{workspace_id}/notebook-template?language=python|r
POST   /api/v1/study/workspaces/{workspace_id}/repro-package/jobs
GET    /api/v1/study/workspaces/{workspace_id}/jobs
GET    /api/v1/study/workspaces/{workspace_id}/jobs/{job_id}

POST   /api/v1/study/compare/run
GET    /api/v1/study/compare/history
POST   /api/v1/study/timeline/profiles
GET    /api/v1/study/timeline/history
GET    /api/v1/study/workspaces/{workspace_id}/dashboard
GET    /api/v1/study/workspaces/{workspace_id}/notes/search?q=...
```

### BGC-Argo (Optional Dataset)
```bash
POST   /api/v1/bgc/profiles/filter
GET    /api/v1/bgc/stats/summary
DELETE /api/v1/bgc/profiles?confirm=true
```

## Local Development

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload --port 8000
```

Or use the local helper from project root:

```powershell
.\start-backend.ps1
```

## Ingestion Commands

### ARGO ingestion (Phase B)
```powershell
cd backend
python data_ingestion/argo_ingestion.py --region indian --max-profiles 500
python data_ingestion/argo_ingestion.py --region custom --bbox 30 -40 120 30 --max-profiles 1000
python data_ingestion/argo_ingestion.py --region global --index-limit 0 --max-profiles 0 --sleep-seconds 0.0
```

Notes:
- `--index-limit 0` means scan the full GDAC index.
- `--max-profiles 0` means process all matching files (large run, may take hours/days).

### RAG ingestion (Phase C)
```powershell
cd backend
python -m rag.ingest_corpus --recreate
```

### BGC ingestion (Phase E optional)
```powershell
cd backend
python data_ingestion/bgc_argo_ingestion.py --max-profiles 1000
python data_ingestion/bgc_argo_ingestion.py --bbox 30 -40 120 30 --start-date 2024-01-01 --end-date 2024-12-31 --max-profiles 2000
```

## Validation

```powershell
pytest -q backend/tests
```

CI workflow: `.github/workflows/ci.yml`

## Environment Variables

See `backend/.env.example`. Most important:
- `DATABASE_URL`
- `REDIS_URL`
- `OLLAMA_BASE_URL`, `OLLAMA_MODEL`
- `RAG_ENABLED`, `QDRANT_URL`, `QDRANT_COLLECTION`
- Optional: `OPENAI_API_KEY`, `OPENAI_MODEL`
- Optional: `GOOGLE_API_KEY`, `GEMINI_MODEL`
- Optional: `ARGOVIS_API_KEY`, `ARGOVIS_BASE_URL`
- `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`
- `RATE_LIMIT_ENABLED`, `RATE_LIMIT_REQUESTS`, `RATE_LIMIT_WINDOW_SECONDS`
- `CHAT_CACHE_TTL_SECONDS`, `CHAT_CACHE_MAX_ITEMS`, `CHAT_DATASET_CONTEXT_TTL_SECONDS`
- `CHAT_DATA_PROVIDER_ORDER`, `CHAT_GENERAL_PROVIDER_ORDER`, `CHAT_METRICS_MAXLEN`
- `OLLAMA_CONNECT_TIMEOUT_SECONDS`, `OLLAMA_READ_TIMEOUT_SECONDS`
- `OPENAI_TIMEOUT_SECONDS`, `GEMINI_TIMEOUT_SECONDS`
- Optional: `ADMIN_API_KEY` (protects `/api/admin/metrics/summary` with `X-Admin-Key`)
- Optional SLO thresholds: `SLO_CHAT_P95_MS`, `SLO_CHAT_SUCCESS_RATE_PERCENT`, `SLO_DB_PROBE_MS`

## Delivery Status (2026-02-10)

- Completed for current scope:
  - Multi-provider chat routing with RAG sources.
  - ARGO filter/export/tools APIs.
  - JWT auth and study workspace APIs.
  - Optional BGC-Argo ingestion and API surface.
  - CI and backend integration tests.
