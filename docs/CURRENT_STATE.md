# FloatChat — Current State Snapshot
## What Is Already Built (As of 2026-02-27)

**Purpose:** This document is the ground truth for any AI agent or developer picking up this project. Read this BEFORE writing any code. Do not re-implement what already exists.

---

## 1. Project Structure

```
Edi project/
├── floatchat-ultimate/          # Main application (Next.js + FastAPI)
│   ├── app/                     # Next.js 15 app directory (frontend)
│   │   ├── page.tsx             # Landing page
│   │   ├── layout.tsx           # Root layout (Inter font, dark theme)
│   │   ├── globals.css          # Global styles (ocean palette, glass morphism)
│   │   ├── dashboard/           # Dashboard page (ARGO stats, charts)
│   │   ├── chat/                # AI Chat interface
│   │   ├── explorer/            # ARGO Data Explorer (filter + table)
│   │   ├── visualizations/      # Charts (deployment trends, DAC dist., monthly profiles)
│   │   ├── tools/               # Research Tools (calculator, glossary, compare, timeline, workspace)
│   │   ├── admin/               # Admin stubs
│   │   ├── study/               # Study route stubs
│   │   └── test/                # Test route
│   ├── components/              # Shared React components
│   │   └── map/FloatMap.tsx     # Leaflet float map component
│   ├── lib/api-client.ts        # All frontend API calls (centralized)
│   ├── backend/                 # FastAPI Python backend
│   │   ├── main.py              # FastAPI app entry point, all routers wired
│   │   ├── main_local.py        # SQLite local dev variant
│   │   ├── core/
│   │   │   └── security.py      # JWT helpers (create_token, verify_token, hash/verify password)
│   │   ├── routers/
│   │   │   ├── argo_filter.py   # /api/v1/argo/* (floats, profiles, measurements, stats)
│   │   │   ├── auth.py          # /api/v1/auth/* (register, login, me)
│   │   │   ├── study.py         # /api/v1/study/* (workspaces, notes, queries, compare, timeline)
│   │   │   ├── export.py        # /api/v1/export/* (CSV, JSON, NetCDF exports)
│   │   │   ├── tools.py         # /api/v1/tools/* (glossary, calculator, insights, quickstats)
│   │   │   ├── bgc.py           # /api/v1/bgc/* (BGC-ARGO summary, filter)
│   │   │   ├── noaa.py          # /api/v1/noaa/* (NOAA integration stub)
│   │   │   ├── gebco.py         # /api/v1/gebco/* (bathymetry stub)
│   │   │   ├── cmems.py         # /api/v1/cmems/* (Copernicus Marine stub)
│   │   │   ├── erddap.py        # /api/v1/erddap/* stub
│   │   │   ├── argovis.py       # /api/v1/argovis/* stub
│   │   │   ├── obis.py          # /api/v1/obis/* stub
│   │   │   ├── ooi.py           # /api/v1/ooi/* stub
│   │   │   ├── onc.py           # /api/v1/onc/* stub
│   │   │   ├── gfw.py           # /api/v1/gfw/* stub
│   │   │   ├── ioos.py          # /api/v1/ioos/* stub
│   │   │   ├── icoads.py        # /api/v1/icoads/* stub
│   │   │   ├── wod.py           # /api/v1/wod/* stub
│   │   │   └── open_meteo_marine.py  # /api/v1/open-meteo-marine/* stub
│   │   ├── llm/
│   │   │   ├── chat_service.py  # Main chat orchestrator (provider routing, RAG trigger)
│   │   │   ├── ollama_engine.py # Ollama provider
│   │   │   ├── gemini_engine.py # Google Gemini provider
│   │   │   ├── groq_engine.py   # Groq provider
│   │   │   ├── openai_engine.py # OpenAI provider
│   │   │   └── sambanova_engine.py # SambaNova provider
│   │   ├── rag/
│   │   │   ├── retriever.py     # Vector (Qdrant) + lexical fallback retriever
│   │   │   ├── default_corpus.py # Static fallback corpus
│   │   │   ├── ingest_corpus.py # CLI for ingesting docs into Qdrant
│   │   │   └── corpus/          # Starter ocean science text files
│   │   ├── data_ingestion/
│   │   │   ├── argo_ingestion.py      # Full configurable ARGO pipeline (bbox, date, cache)
│   │   │   └── bgc_argo_ingestion.py  # BGC-ARGO ingestion script
│   │   ├── tests/               # pytest test suite
│   │   │   ├── test_api.py      # API integration tests
│   │   │   ├── test_chat.py     # Chat service routing/fallback tests
│   │   │   └── test_rag.py      # RAG lexical fallback tests
│   │   ├── init-db.sql          # Database schema (tables, indices)
│   │   ├── requirements.txt     # Python dependencies
│   │   └── .env.example         # Environment variable template
│   ├── docs/runbooks/
│   │   ├── production-deployment.md
│   │   ├── rag-ingestion.md
│   │   └── validation-and-ci.md
│   ├── .github/workflows/ci.yml # CI: frontend typecheck + backend tests
│   ├── docker-compose.yml       # PostgreSQL + Redis + Qdrant + Ollama
│   ├── next.config.ts           # Next.js config
│   ├── tailwind.config.ts       # Tailwind + ocean design tokens
│   └── package.json             # Node dependencies (pnpm)
├── floatchat-docs/              # Planning docs
│   ├── ENTERPRISE_PRD.md        # [NEW] Full enterprise product requirements
│   ├── ENTERPRISE_TODO.md       # [NEW] Actionable agent task list
│   ├── CURRENT_STATE.md         # [NEW] This file
│   ├── task.md                  # Original master task list (historical)
│   ├── implementation_plan.md   # Original implementation plan (historical)
│   ├── ocean_study_super_project_plan.md  # Extended plan with updates
│   ├── floatchat_power_up_master_plan_2026-02-20.md  # Post-Phase-E power-up plan
│   └── project_structure.md    # File-level structure guide
├── FloatChat_SRS_IEEE830.md     # IEEE 830 Software Requirements Specification
├── User_Classes_Table.txt       # User roles table
└── data/argo/                   # Local ARGO data cache directory
```

---

## 2. Completed Features (Phase A Through E)

### Authentication (Phase E)
- JWT-based registration and login (`/api/v1/auth/register`, `/api/v1/auth/login`, `/api/v1/auth/me`)
- bcrypt password hashing (cost factor 12)
- 24-hour JWT token expiration
- `core/security.py` — `create_access_token`, `verify_token`, `hash_password`, `verify_password`
- **NOT YET BUILT:** password reset, MFA, OAuth2/SSO

### ARGO Data (Phases A, B)
- ARGO float filter API: `/api/v1/argo/floats/filter` (bbox, date, QC, float_id)
- ARGO profile filter API: `/api/v1/argo/profiles/filter` (all above + depth/pressure)
- ARGO measurements filter API: `/api/v1/argo/measurements/filter`
- ARGO stats summary: `/api/v1/argo/stats/summary`
- All queries use parameterized SQL (no injection risk)
- Versioned routes under `/api/v1/`
- Ingestion pipeline: configurable CLI (bbox, date, index-limit, max-profiles, cache, timeout)
- BGC-ARGO ingestion script + `/api/v1/bgc/` router (summary, filter, clear)

### Multi-LLM Chat (Phase C)
- `/api/chat` endpoint with provider routing
- Providers: Ollama (local, default), Gemini (free tier key), Groq (free tier), OpenAI (optional), SambaNova (optional)
- Auto mode: tries providers in priority order
- RAG trigger: detects keywords (argo, ocean, temperature, salinity) → queries Qdrant or falls back to lexical search
- Source citations in responses (`sources` field in response)
- Query type classification (`query_type` field: data_query vs general)
- **NOT YET BUILT:** confidence scores, evidence coverage, "insufficient evidence" mode, graph-augmented reasoning

### RAG (Phase C)
- Qdrant vector database (Docker service in compose)
- Retriever: vector search first, lexical fallback if Qdrant unavailable
- Default corpus: ARGO documentation, oceanography primers
- Ingestion CLI: `backend/rag/ingest_corpus.py`
- **NOT YET BUILT:** knowledge graph integration, literature paper ingestion

### Study Workflow (Phase D, E)
- Workspaces: create, list, select active workspace
- Notes: create, list, delete (per workspace)
- Saved queries: save filter presets with name + parameters
- Compare mode: compare two ocean regions, save history
- Timeline runs: group profiles by month, visualize, save history
- **NOT YET BUILT:** workspace sharing, snapshot versioning, reproducibility bundles, comments/activity feed

### Data Export (Phase D)
- CSV export: floats, profiles, measurements
- JSON snapshot export (with citation metadata)
- NetCDF export for measurements (CF-conventions)
- Export includes "data_as_of" and basic citation text
- **NOT YET BUILT:** LaTeX export, full reproducibility ZIP bundle, figure export

### Research Tools (Phase D)
- Depth ↔ Pressure calculator (UNESCO formula, latitude-corrected)
- Ocean glossary (100+ terms, searchable)
- Learning insights (AI-generated from live ARGO data)
- Quick stats (median depth, temp range, salinity range)
- BGC summary panel
- Learning prompts (copyable research questions)
- Regional compare (Indian, Pacific, Atlantic, Global)
- Timeline playback (bar chart)
- **NOT YET BUILT:** flashcards, quizzes, learning progress, Socratic tutor mode

### Frontend (Phase D+)
- Landing page (hero, live stats, features, tech stack)
- Dashboard (ARGO stats cards, temperature anomaly chart, regional coverage, system status)
- Chat (multi-provider UI, markdown rendering, code highlighting, source citations)
- Explorer (filter form + map + results table + export buttons)
- Visualizations (KPI cards, float deployment trend, DAC distribution, monthly profile volume)
- Tools (workspace selector, calculator, glossary, compare, timeline, notes, learning prompts)
- Design system: Inter font, monochrome black/white, glass morphism, Framer Motion
- **NOT YET BUILT:** Research Library, Learning Hub, Report Builder, Knowledge Graph, 3D visualizations, Classroom, Developer API page

### Infrastructure
- Docker Compose: PostgreSQL + TimescaleDB, Redis, Qdrant, Ollama
- CI: `.github/workflows/ci.yml` — frontend typecheck + lint + backend pytest
- Runbooks: production deployment, RAG ingestion, validation/CI
- Tests: 10 backend tests covering API, chat routing, RAG fallback
- **NOT YET BUILT:** Prometheus metrics, Grafana dashboards, distributed tracing

---

## 3. Database Schema (Current)

Tables in `backend/init-db.sql`:

```
argo_floats       — float_id, platform_number, project_name, data_center, lon, lat, last_location_date
argo_profiles     — profile_id, float_id, cycle_number, date, lon, lat, pressure_dbar, temp, salinity, qc_flag
bgc_profiles      — BGC profile data (chlorophyll, dissolved_oxygen)
users             — id, username, email, password_hash, full_name, created_at
workspaces        — id, user_id, name, description, created_at
notes             — id, workspace_id, content, created_at
saved_queries     — id, workspace_id, name, query_payload (JSONB), created_at
compare_sessions  — id, workspace_id, region_a, region_b, result (JSONB), created_at
timeline_runs     — id, workspace_id, start_date, end_date, series (JSONB), created_at
```

**Not yet in schema (needed for enterprise features):**
- `password_reset_tokens` — for password reset flow
- `research_library` — saved academic papers
- `flashcards`, `quiz_results`, `learning_progress` — learning module
- `workspace_snapshots` — versioned workspace state
- `workspace_members` — RBAC collaboration
- `workspace_comments`, `workspace_activity`, `workspace_invitations` — collaboration
- `reports` — report builder
- `ocean_baselines`, `anomaly_events` — predictive analytics
- `api_keys`, `webhooks` — developer API
- `classrooms`, `assignments`, `submissions` — educator mode
- `audit_log` — security/compliance
- `mfa_settings` — TOTP MFA

---

## 4. Environment Variables (Current)

From `backend/.env.example`:

```bash
DATABASE_URL=postgresql://floatchat:dev_password@localhost:5432/floatchat
REDIS_URL=redis://localhost:6379
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=ocean_knowledge

OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3

GEMINI_API_KEY=           # optional - free tier available
OPENAI_API_KEY=           # optional
GROQ_API_KEY=             # optional - free tier available
SAMBANOVA_API_KEY=        # optional - free tier available

RAG_ENABLED=true
JWT_SECRET_KEY=           # REQUIRED - set strong secret
```

**New env vars needed (enterprise features):**
```bash
SMTP_HOST=                # for email (password reset)
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
SMTP_FROM=

GOOGLE_OAUTH_CLIENT_ID=   # for OAuth2 SSO
GOOGLE_OAUTH_CLIENT_SECRET=
GITHUB_OAUTH_CLIENT_ID=
GITHUB_OAUTH_CLIENT_SECRET=

SEMANTIC_SCHOLAR_API_KEY= # optional, improves rate limits

PROMETHEUS_ENABLED=true
```

---

## 5. API Endpoints (Current — All Working)

### Auth
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me` (requires JWT)

### ARGO Data
- `GET /api/v1/argo/floats/filter?bbox=&start_date=&end_date=&qc_max=&float_id=&limit=&offset=`
- `GET /api/v1/argo/profiles/filter?bbox=&start_date=&end_date=&min_depth=&max_depth=&qc_max=&float_id=&limit=&offset=`
- `GET /api/v1/argo/measurements/filter?profile_id=&min_depth=&max_depth=&qc_max=`
- `GET /api/v1/argo/stats/summary`

### Chat
- `POST /api/chat` (body: `{ "message": str, "provider": "auto|ollama|gemini|groq|openai" }`)
- `GET /api/chat/providers`

### Study (requires JWT)
- `POST /api/v1/study/workspaces`
- `GET /api/v1/study/workspaces`
- `POST /api/v1/study/workspaces/{id}/notes`
- `GET /api/v1/study/workspaces/{id}/notes`
- `DELETE /api/v1/study/workspaces/{id}/notes/{note_id}`
- `POST /api/v1/study/workspaces/{id}/queries`
- `GET /api/v1/study/workspaces/{id}/queries`
- `POST /api/v1/study/workspaces/{id}/compare`
- `GET /api/v1/study/workspaces/{id}/compare`
- `POST /api/v1/study/workspaces/{id}/timeline`
- `GET /api/v1/study/workspaces/{id}/timeline`

### Tools
- `GET /api/v1/tools/glossary?q=`
- `POST /api/v1/tools/calculator` (body: `{ "depth": float, "latitude": float }` or `{ "pressure": float, "latitude": float }`)
- `GET /api/v1/tools/learn/insights`
- `GET /api/v1/tools/quickstats`

### Export
- `GET /api/v1/export/floats/csv?...` (same filter params as argo_filter)
- `GET /api/v1/export/profiles/csv?...`
- `GET /api/v1/export/measurements/csv?...`
- `GET /api/v1/export/measurements/netcdf?...`
- `POST /api/v1/export/snapshot` (body: filter params → JSON snapshot with citation)

### BGC
- `GET /api/v1/bgc/summary`
- `GET /api/v1/bgc/profiles/filter?...`

### Other (stubs — exist but minimal/placeholder):
- `/api/v1/noaa/*`, `/api/v1/gebco/*`, `/api/v1/cmems/*`, `/api/v1/erddap/*`, `/api/v1/argovis/*`, `/api/v1/obis/*`, `/api/v1/ooi/*`, `/api/v1/onc/*`, `/api/v1/gfw/*`, `/api/v1/ioos/*`, `/api/v1/icoads/*`, `/api/v1/wod/*`, `/api/v1/open-meteo-marine/*`

---

## 6. Known Limitations & Technical Debt

1. **No confidence scoring in chat** — responses have no evidence quality indicators
2. **RAG corpus is minimal** — only starter files; needs enrichment from papers
3. **No background jobs** — all processing is synchronous; large exports block
4. **Test coverage ~40%** — needs to reach 70%+ target
5. **No password reset** — SRS TBD-2 still open
6. **No MFA** — SRS TBD-3 still open
7. **No OAuth/SSO** — SRS TBD-4 still open
8. **No email service** — SMTP not wired up
9. **No observability** — no Prometheus, no Grafana, no distributed tracing
10. **Study features browser-local only for guests** — saved presets fall back to localStorage, not DB, for unauthenticated users
11. **10 backend tests only** — covers basic paths but not edge cases
12. **No 3D visualizations** — charts are 2D Recharts/Chart.js only
13. **No literature integration** — no paper search, no citation management
14. **No learning features** — glossary is static, no flashcards, no quizzes, no progress tracking
15. **Multiple stub routers** — noaa, gebco, cmems etc. are wired but not implemented
16. **Database has no TimescaleDB** — `init-db.sql` doesn't call `create_hypertable` (original plan had it, current impl uses plain PostgreSQL)

---

## 7. How to Start the Application (NO DOCKER)

Docker is NOT used. All services run natively on Windows.

### Prerequisites (install these once)
1. **PostgreSQL 16** — https://www.postgresql.org/download/windows/
2. **Python 3.11+** — https://www.python.org/downloads/
3. **Node.js 20+** — https://nodejs.org/
4. **pnpm** — `npm install -g pnpm`

### One-time database setup
```sql
-- Run in pgAdmin or psql as postgres superuser
CREATE USER floatchat_user WITH PASSWORD '1234';
CREATE DATABASE floatchat OWNER floatchat_user;
GRANT ALL PRIVILEGES ON DATABASE floatchat TO floatchat_user;
```

```powershell
# Apply schema (from floatchat-ultimate folder)
psql -U floatchat_user -d floatchat -f backend/init-db.sql
```

### Start backend
```powershell
cd "C:\Users\Abhijeet Nardele\OneDrive\Desktop\Edi project\floatchat-ultimate"
pip install -r backend/requirements.txt
python -m uvicorn backend.main:app --reload --port 8000
```

### Start frontend
```powershell
cd "C:\Users\Abhijeet Nardele\OneDrive\Desktop\Edi project\floatchat-ultimate"
pnpm install
pnpm dev
```

### Ingest real ARGO data (ALL oceans, 5 years)
```powershell
# Start small to validate (2000 profiles, global, from 2024)
python backend\data_ingestion\argo_ingestion.py --region global --start-date 2024-01-01 --max-profiles 2000 --cache-dir backend\data\argo

# Full 5-year global run (run after small test succeeds)
python backend\data_ingestion\argo_ingestion.py --region global --start-date 2021-01-01 --max-profiles 50000 --index-limit 200000 --cache-dir backend\data\argo --sleep-seconds 0.05
```

**See `floatchat-docs/DATA_INGESTION_GUIDE.md` for full step-by-step checklist.**

Access:
- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`

---

## 8. Validation Commands

```bash
# TypeScript check (from floatchat-ultimate/)
pnpm exec tsc --noEmit

# ESLint
pnpm exec eslint app lib components --max-warnings 0

# Backend tests
pytest -q backend/tests

# Smoke test (requires running backend)
python backend/test_smoke_api.py
```

---

*This document reflects the state as of 2026-02-27 (end of Phase E).*  
*Next planned work: See `ENTERPRISE_TODO.md` Sprint 1.*
