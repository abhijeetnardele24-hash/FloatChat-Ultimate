                                                                            # FloatChat Ultimate

AI-powered ocean data platform for ARGO research workflows with multi-provider chat, filtering, export, and study tooling.

                                                                              Project Status (2026-02-10)

### Phase Completion for Current Scope
- Phase A: Completed
  - Parameterized query paths in backend API routes.
  - Versioned ARGO filter routes and secure query handling.
- Phase B: Completed
  - ARGO ingestion and filter-driven explorer workflow.
- Phase C: Completed
  - Optional OpenAI provider path plus Ollama/Gemini routing.
  - RAG retriever with Qdrant vector mode and lexical fallback.
  - Source citations in conceptual chat responses.
- Phase D and D+: Completed
  - Export APIs and tools page (calculator, glossary, quick stats).
  - JWT auth, workspaces, notes, saved queries, compare mode, timeline playback.
  - Polished UI across main pages with shared design language and motion.
- Phase E (current implementation scope): Completed
  - Optional BGC-Argo ingestion/API path.
  - CI and integration tests.
  - Production deployment and runbook documentation.

## Quick Start

### Prerequisites
- Docker Desktop
- Node.js 20+ and pnpm
- Python 3.11+ (for backend tests/scripts)

### Start Stack

```powershell
.\start.ps1
```

or

```bash
chmod +x start.sh
./start.sh
```

### Access Points
- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`

## Core Features

- ARGO filtering APIs (`/api/v1/argo/*`) with bbox/date/depth/QC filters.
- Multi-provider chat (`ollama`, optional `openai`, optional `gemini`) via `/api/chat`.
- RAG support with source snippets for conceptual queries.
- Export endpoints for CSV/NetCDF/JSON snapshots.
- Study workflow APIs:
  - Auth (`/api/v1/auth/*`)
  - Workspaces, notes, saved queries, compare runs, timeline runs (`/api/v1/study/*`)
- Optional BGC-Argo dataset API (`/api/v1/bgc/*`).

## Validation Commands

From project root:

```bash
pnpm exec tsc --noEmit
pnpm exec eslint app lib components --max-warnings 0
pytest -q backend/tests
```

## CI

- Workflow: `.github/workflows/ci.yml`
- Jobs:
  - Frontend typecheck and lint
  - Backend integration tests

## Key Docs

- Backend guide: `backend/README.md`
- Production runbook: `docs/runbooks/production-deployment.md`
- RAG ingestion runbook: `docs/runbooks/rag-ingestion.md`
- Validation/CI runbook: `docs/runbooks/validation-and-ci.md`

## Zero-Cost Mode

The platform runs fully in free/open mode with:
- Ollama as default LLM
- PostgreSQL + Redis + Qdrant (self-hosted/open-source)
- Optional OpenAI/Gemini only when user-provided keys are configured
