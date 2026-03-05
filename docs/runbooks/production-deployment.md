# FloatChat Production Deployment Runbook

This runbook documents a zero-cost-friendly deployment path with optional OpenAI usage.

## 1. Scope

- Backend API: FastAPI (`backend/main.py`)
- Frontend: Next.js app
- Data services: PostgreSQL, Redis, Ollama, optional Qdrant
- LLM providers:
  - Required for free mode: `ollama`
  - Optional paid mode: `openai` (user key), optional `gemini`

## 2. Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for operational scripts/tests)
- Node.js 20+ and pnpm (for frontend checks/build)
- Host with persistent disk for PostgreSQL and model/cache volumes

## 3. Environment Configuration

Use `backend/.env.example` as template. Minimum production variables:

- `DATABASE_URL`
- `REDIS_URL`
- `OLLAMA_BASE_URL`
- `OLLAMA_MODEL`
- `QDRANT_URL` (if vector RAG is enabled)
- `QDRANT_COLLECTION` (default: `ocean_knowledge`)
- `RAG_ENABLED=true`
- Optional: `OPENAI_API_KEY`, `OPENAI_MODEL`
- Optional: `GOOGLE_API_KEY`, `GEMINI_MODEL`
- Optional: `ARGOVIS_API_KEY`, `ARGOVIS_BASE_URL`

Recommended:

- Keep OpenAI/Gemini keys empty for strict zero-cost operation.
- Set provider policy in UI/process docs: `auto` or `ollama` default.

## 4. Deployment Steps

1. Pull latest code.
2. Build and start services:

```bash
docker-compose up -d --build
```

3. Verify service health:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/api/chat/providers
curl http://localhost:8000/api/v1/argo/stats/summary
```

4. If RAG vector mode is required, ingest corpus:

```bash
cd backend
python -m rag.ingest_corpus --recreate
```

Optional large ARGO ingestion (full/global):

```bash
cd backend
python data_ingestion/argo_ingestion.py --region global --index-limit 0 --max-profiles 0 --sleep-seconds 0.0
```

5. Start frontend (if not containerized in your environment):

```bash
pnpm install
pnpm run build
pnpm run start
```

## 5. Post-Deploy Validation

Run backend integration tests:

```bash
pytest -q backend/tests
```

Smoke-check key endpoints:

- `/health`
- `/api/chat/providers` (confirm `openai` appears only when key exists)
- `/api/chat` with `provider=auto` and a general question
- `/api/v1/export/*` for CSV/NetCDF
- `/api/v1/auth/register` + `/api/v1/auth/login` + `/api/v1/auth/me`
- `/api/v1/study/workspaces` and `/api/v1/study/compare/history`
- `/api/v1/bgc/stats/summary`

## 6. Failure Handling

- If OpenAI fails or key expires:
  - Keep platform operational with `ollama` and RAG lexical mode.
- If Qdrant is unavailable:
  - RAG retriever falls back to lexical corpus mode.
- If Ollama is unavailable:
  - Use `openai`/`gemini` (if configured) for general answers.

## 7. Rollback

1. Deploy previous git tag/commit.
2. Restart stack:

```bash
docker-compose up -d --build
```

3. Re-run post-deploy validation checks.

## 8. Operations Checklist

- Daily:
  - Check `/health` and `/api/chat/providers`.
- Weekly:
  - Run backend tests and lint/type checks.
- After dependency upgrades:
  - Re-run CI-equivalent checks and ingestion script once.
