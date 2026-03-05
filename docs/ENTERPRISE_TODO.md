# FloatChat Enterprise — Master TODO & Agent Task List

**Document Version:** 1.0  
**Date:** 2026-02-27  
**Purpose:** Actionable task list for AI coding agents and developers. Read ENTERPRISE_PRD.md and CURRENT_STATE.md first before executing any task.  
**Rule:** Never start a task without reading the referenced files. Mark tasks `[x]` when done. Update the "Current Sprint" section to track active work.

---

## How to Use This Document

1. Read `CURRENT_STATE.md` to understand what is already built.
2. Read `ENTERPRISE_PRD.md` to understand the full requirements for each feature.
3. Pick the current sprint tasks below and work top-to-bottom.
4. Each task references: which files to read, what to build, what files to create/modify.
5. Mark `[x]` when complete. Add sub-tasks discovered during implementation.

---

## SPRINT 0 — Foundation (Must Complete Before ANY Other Sprint)

**Goal:** Get real data into the database, remove Docker dependency, fix broken schema.  
**Files to read first:** `DATA_INGESTION_GUIDE.md`, `backend/data_ingestion/argo_ingestion.py`, `backend/init-db.sql`

> **This sprint is the blocker for everything else. The app currently has 3 fake floats and zero real profiles. No enterprise feature makes sense without real global ARGO data.**

### S0-T1: Remove Docker — Native PostgreSQL Setup

- [ ] **S0-T1-1** Install PostgreSQL 16 natively on Windows (https://www.postgresql.org/download/windows/)
- [ ] **S0-T1-2** Create DB user + database:
  ```sql
  CREATE USER floatchat_user WITH PASSWORD '1234';
  CREATE DATABASE floatchat OWNER floatchat_user;
  GRANT ALL PRIVILEGES ON DATABASE floatchat TO floatchat_user;
  ```
- [ ] **S0-T1-3** Update `backend/init-db.sql` — remove ALL timescaledb/postgis extensions:
  - Remove: `CREATE EXTENSION IF NOT EXISTS timescaledb;`
  - Remove: `CREATE EXTENSION IF NOT EXISTS postgis;`
  - Remove: `SELECT create_hypertable(...);`
  - Remove: `CREATE INDEX ... USING GIST (ST_MakePoint(...));`
  - Replace with plain: `CREATE INDEX idx_profile_lat_lon ON argo_profiles (latitude, longitude);`
  - Replace with plain: `CREATE INDEX idx_float_lat_lon ON argo_floats (last_latitude, last_longitude);`
- [ ] **S0-T1-4** Apply schema: `psql -U floatchat_user -d floatchat -f backend/init-db.sql`
- [ ] **S0-T1-5** Verify DB works: `python backend/test_smoke_api.py` — health endpoint should say `database: connected`
- [ ] **S0-T1-6** Update `backend/.env`:
  ```env
  DATABASE_URL=postgresql+psycopg2://floatchat_user:1234@localhost:5432/floatchat
  GROQ_API_KEY=gsk_****************************  # Add your real key in backend/.env only
  GROQ_MODEL=llama-3.3-70b-versatile
  GOOGLE_API_KEY=    # add Gemini key here
  ```
- [ ] **S0-T1-7** Remove `docker-compose.yml` Redis/Qdrant/TimescaleDB services from startup docs (keep file but note they are optional for dev)
- [ ] **S0-T1-8** Update `CURRENT_STATE.md` to confirm no-Docker path is validated

### S0-T2: Fix `argo_ingestion.py` — All Oceans + Correct Ocean Basin

- [ ] **S0-T2-1** Read `backend/data_ingestion/argo_ingestion.py` in full (line 1–514)
- [ ] **S0-T2-2** Add `OCEAN_CODE_MAP` constant at top of file:
  ```python
  OCEAN_CODE_MAP = {
      "I": "Indian Ocean",
      "P": "Pacific Ocean",
      "A": "Atlantic Ocean",
      "S": "Southern Ocean",
      "M": "Mediterranean Sea",
      "N": "Arctic Ocean",
      "T": "N Atlantic Subpolar",
  }
  ```
- [ ] **S0-T2-3** In `fetch_float_index()` — pass `item["ocean"]` in the returned dict (it's already parsed as `values[4]` — just ensure it flows through)
- [ ] **S0-T2-4** In `insert_float()` — change signature to accept `ocean_code: str = None` parameter
- [ ] **S0-T2-5** In `insert_float()` — replace hardcoded `"Indian Ocean"` with:
  ```python
  "ocean_basin": OCEAN_CODE_MAP.get(ocean_code or "", "Unknown Ocean"),
  ```
- [ ] **S0-T2-6** In `insert_profile()` — pass `ocean_code=profile_data.get("ocean_code")` to `insert_float()`
- [ ] **S0-T2-7** In `parse_netcdf_profile()` — note: ocean_code comes from the index, not from NetCDF. The index `item["ocean"]` must be threaded into the profile dict during `run_ingestion()`:
  ```python
  profile_data = self.parse_netcdf_profile(local_file)
  if profile_data:
      profile_data["ocean_code"] = item.get("ocean", "")
  ```
- [ ] **S0-T2-8** Test the fix: run a small ingestion with `--region global --max-profiles 10` and verify `SELECT DISTINCT ocean_basin FROM argo_floats` shows multiple oceans, not just `"Unknown"`

### S0-T3: Run Initial Global Ingestion (Last 5 Years)

- [ ] **S0-T3-1** Create cache directory: `mkdir backend\data\argo`
- [ ] **S0-T3-2** Run small validation batch (2000 profiles, 2024+, all oceans):
  ```powershell
  python backend\data_ingestion\argo_ingestion.py --region global --start-date 2024-01-01 --max-profiles 2000 --index-limit 20000 --cache-dir backend\data\argo --sleep-seconds 0.1
  ```
- [ ] **S0-T3-3** Verify: `GET http://localhost:8000/api/stats` — `total_floats > 100`, `total_profiles > 500`
- [ ] **S0-T3-4** Verify: `GET http://localhost:8000/api/floats?limit=5` — shows multiple `ocean_basin` values (Indian, Pacific, Atlantic, Southern)
- [ ] **S0-T3-5** Once small batch works — run full 5-year global ingestion (leave running overnight):
  ```powershell
  python backend\data_ingestion\argo_ingestion.py --region global --start-date 2021-01-01 --end-date 2026-02-27 --max-profiles 50000 --index-limit 200000 --cache-dir backend\data\argo --sleep-seconds 0.05
  ```
- [ ] **S0-T3-6** After completion — update `CURRENT_STATE.md` with actual counts: floats ingested, profiles ingested, measurements ingested, oceans covered, date range

### S0-T4: Verify Chat Works with Real Data

- [ ] **S0-T4-1** Start backend: `python -m uvicorn backend.main:app --reload --port 8000`
- [ ] **S0-T4-2** Test chat with data query:
  ```bash
  curl -X POST http://localhost:8000/api/chat -H "Content-Type: application/json" -d "{\"message\": \"How many floats are in each ocean basin?\"}"
  ```
  Expected: returns real SQL + real counts from database
- [ ] **S0-T4-3** Test chat with general query:
  ```bash
  curl -X POST http://localhost:8000/api/chat -H "Content-Type: application/json" -d "{\"message\": \"What is a T-S diagram and why is it useful?\", \"provider\": \"groq\"}"
  ```
  Expected: Groq answers with oceanographic explanation
- [ ] **S0-T4-4** Add GOOGLE_API_KEY to `.env` and test Gemini:
  ```bash
  curl -X POST http://localhost:8000/api/chat -H "Content-Type: application/json" -d "{\"message\": \"What is the Indian Ocean Dipole?\", \"provider\": \"gemini\"}"
  ```
- [ ] **S0-T4-5** Open frontend `http://localhost:3000/dashboard` — verify stats cards show real numbers

### S0-T5: Build Missing Core Visualizations (NetCDF → Chart)

These are the charts that are **the entire point of the project** — T/S vs depth from real profiles:

- [ ] **S0-T5-1** Add new backend endpoint `GET /api/v1/argo/profiles/{profile_id}/measurements`:
  - Returns `[{pressure, depth, temperature, salinity, temp_qc, salinity_qc}]` for one profile
  - Add to `backend/routers/argo_filter.py`
- [ ] **S0-T5-2** Add new backend endpoint `GET /api/v1/argo/floats/{wmo_number}/track`:
  - Returns ordered list of `[{cycle_number, profile_date, latitude, longitude}]` for float's full track
  - Add to `backend/routers/argo_filter.py`
- [ ] **S0-T5-3** Create `components/charts/DepthProfileChart.tsx`:
  - X-axis: Temperature (°C) OR Salinity (PSU) — toggle
  - Y-axis: Pressure/Depth (inverted — surface at top, deep at bottom)
  - One line per profile, multiple profiles overlay-able
  - Data source: `GET /api/v1/argo/profiles/{id}/measurements`
  - Library: Recharts LineChart (already in project)
- [ ] **S0-T5-4** Create `components/charts/TSDiagram.tsx`:
  - X-axis: Salinity (PSU)
  - Y-axis: Temperature (°C)
  - Each point = one depth level
  - Color = depth (colorscale: surface blue → deep red)
  - Points from same profile connect with lines
  - Data source: same measurements endpoint
  - Library: Recharts ScatterChart
- [ ] **S0-T5-5** Create `components/charts/FloatTrackMap.tsx`:
  - Extends existing `components/map/FloatMap.tsx`
  - Shows polyline of float's position over time
  - Clickable points → show cycle number + date tooltip
  - Data source: `GET /api/v1/argo/floats/{wmo}/track`
- [ ] **S0-T5-6** Create `app/profile/[id]/page.tsx` — Profile Detail page:
  - Shows: profile metadata (float, date, lat, lon, ocean)
  - Shows: DepthProfileChart (temperature + salinity on same chart)
  - Shows: TSDiagram for this profile
  - Shows: FloatTrackMap showing the parent float's full history
  - Download buttons: CSV, NetCDF for this profile
- [ ] **S0-T5-7** Update `app/explorer/page.tsx` — make each profile row in table clickable → goes to `/profile/[id]`
- [ ] **S0-T5-8** Test: navigate to a real profile detail page and verify all 3 charts render with real data

---

## Current Sprint: Sprint 1 — Trust & Reliability

**Goal:** Make chat responses scientifically trustworthy and add security hardening.  
**Files to read first:** `backend/llm/chat_service.py`, `backend/rag/retriever.py`, `backend/routers/auth.py`

### S1-T1: Scientific Answer Reliability Engine (ENT-001)

- [ ] **S1-T1-1** Read `backend/llm/chat_service.py` in full
- [ ] **S1-T1-2** Read `backend/rag/retriever.py` in full
- [ ] **S1-T1-3** Create `backend/services/answer_verifier.py`
  - Input: LLM response text + RAG source snippets
  - Output: `VerifiedAnswer` Pydantic model with fields: `text`, `confidence_score` (0.0–1.0), `evidence_sources` (list), `method`, `limitations`, `is_sufficient_evidence` (bool)
  - Confidence scoring logic: ratio of response claims covered by retrieved sources
  - If `confidence_score < 0.4`: return structured "insufficient evidence" template, do not call LLM
- [ ] **S1-T1-4** Add `VerifiedAnswer` Pydantic schema to `backend/core/schemas.py` (or create it)
- [ ] **S1-T1-5** Wire `answer_verifier.py` into `chat_service.py` — call it after LLM response and before returning
- [ ] **S1-T1-6** Add `/api/chat` response field: `confidence_score`, `evidence_sources`, `method`, `limitations`
- [ ] **S1-T1-7** Update frontend `app/chat/page.tsx`:
  - Display confidence badge (green/yellow/red pill) below assistant message
  - Expand "Evidence" collapsible section showing sources
  - Display "Method" and "Limitations" in expandable info panel
- [ ] **S1-T1-8** Add unit test `backend/tests/test_answer_verifier.py` covering: high confidence case, low confidence case, no evidence case
- [ ] **S1-T1-9** Verify: run `pytest -q backend/tests`, check no regressions

### S1-T2: Prometheus Observability (NFR-OBS)

- [ ] **S1-T2-1** Read `backend/main.py` and `docker-compose.yml`
- [ ] **S1-T2-2** Add `prometheus-fastapi-instrumentator` to `backend/requirements.txt`
- [ ] **S1-T2-3** Wire metrics endpoint `/metrics` in `backend/main.py` (Prometheus scrape target)
- [ ] **S1-T2-4** Add custom metrics:
  - `floatchat_chat_requests_total` (counter, labels: provider, query_type)
  - `floatchat_chat_latency_seconds` (histogram, labels: provider)
  - `floatchat_llm_tokens_total` (counter, labels: provider)
  - `floatchat_rag_hits_total` (counter, labels: result=hit/miss)
  - `floatchat_ingestion_profiles_total` (counter)
- [ ] **S1-T2-5** Add correlation ID middleware (UUID per request, returned in `X-Request-ID` header)
- [ ] **S1-T2-6** Add `prometheus` and `grafana` services to `docker-compose.yml`
- [ ] **S1-T2-7** Create `docker/grafana/dashboards/floatchat.json` — basic Grafana dashboard JSON with: request rate, p95 latency, error rate, LLM provider breakdown panels
- [ ] **S1-T2-8** Test: start stack, curl `/metrics`, verify metrics appear; check Grafana at port 3001

### S1-T3: Password Reset via Email (SRS TBD-2, ENT-014)

- [ ] **S1-T3-1** Read `backend/routers/auth.py` in full
- [ ] **S1-T3-2** Add `password_reset_tokens` table migration to `backend/init-db.sql`:
  - `id`, `user_id` (FK), `token` (UUID), `expires_at`, `used` (bool), `created_at`
- [ ] **S1-T3-3** Add endpoint `POST /api/v1/auth/forgot-password` — accepts email, generates token, sends email (or logs token if SMTP not configured)
- [ ] **S1-T3-4** Add endpoint `POST /api/v1/auth/reset-password` — accepts token + new password, validates, updates hash
- [ ] **S1-T3-5** Add simple email service wrapper `backend/services/email_service.py` — uses SMTP env vars, falls back to console log if SMTP not configured
- [ ] **S1-T3-6** Add frontend password reset flow: "Forgot password?" link on login form → email form → success message
- [ ] **S1-T3-7** Add test: `backend/tests/test_auth_reset.py`

### S1-T4: TOTP MFA (ENT-014)

- [ ] **S1-T4-1** Add `pyotp` and `qrcode` to `backend/requirements.txt`
- [ ] **S1-T4-2** Add `mfa_secret` column to users table (nullable, encrypted at rest)
- [ ] **S1-T4-3** Add endpoint `POST /api/v1/auth/mfa/setup` — generates TOTP secret, returns QR code URL
- [ ] **S1-T4-4** Add endpoint `POST /api/v1/auth/mfa/verify` — verifies TOTP code, enables MFA on account
- [ ] **S1-T4-5** Add endpoint `POST /api/v1/auth/mfa/disable` — requires current TOTP code to disable
- [ ] **S1-T4-6** Update login flow: if user has MFA enabled, require TOTP code after password check
- [ ] **S1-T4-7** Add frontend MFA setup UI in user settings page (QR code display, verification input)
- [ ] **S1-T4-8** Add test: `backend/tests/test_mfa.py`

---

## Sprint 2 — Literature Bridge

**Goal:** Connect ARGO data queries to scientific papers; enable research library.  
**Files to read first:** `backend/routers/study.py`, `lib/api-client.ts`, `app/tools/page.tsx`

### S2-T1: Semantic Scholar Literature API (ENT-002)

- [ ] **S2-T1-1** Create `backend/services/literature_service.py`
  - `search_papers(query: str, limit: int) -> list[Paper]` — calls Semantic Scholar Graph API
  - `get_recommendations(positive_ids: list, negative_ids: list) -> list[Paper]` — uses Recommendations API
  - `get_paper_details(paper_id: str) -> Paper` — fetches full metadata + abstract
  - `format_citation(paper: Paper, style: str) -> str` — APA, BibTeX, MLA
- [ ] **S2-T1-2** Add `research_library` table to `backend/init-db.sql`:
  - `id`, `workspace_id` (FK), `user_id` (FK), `paper_id` (Semantic Scholar ID), `title`, `authors` (JSONB), `abstract`, `year`, `doi`, `citation_count`, `relevance_note` (user text), `created_at`
- [ ] **S2-T1-3** Create `backend/routers/literature.py`:
  - `GET /api/v1/literature/search?q=...` — search papers
  - `GET /api/v1/literature/related?topic=...` — topic-based suggestions
  - `POST /api/v1/literature/library` — save paper to workspace library
  - `GET /api/v1/literature/library/{workspace_id}` — list saved papers
  - `DELETE /api/v1/literature/library/{paper_id}` — remove from library
  - `GET /api/v1/literature/cite/{paper_id}?style=apa|bibtex|mla` — formatted citation
- [ ] **S2-T1-4** Wire literature router into `backend/main.py`
- [ ] **S2-T1-5** Update `/api/chat` to append "Related Papers" to general-question responses (call `literature_service.search_papers` with extracted topic)
- [ ] **S2-T1-6** Add frontend `app/library/page.tsx` — Research Library page:
  - Paper cards with: title, authors, year, abstract excerpt, citation count, DOI link
  - "Copy Citation" dropdown (APA / BibTeX / MLA)
  - "Remove from library" button
  - Search/filter within saved library
- [ ] **S2-T1-7** Update chat UI to show "Related Papers" section when `related_papers` in response
- [ ] **S2-T1-8** Add to navigation sidebar
- [ ] **S2-T1-9** Add tests: `backend/tests/test_literature.py`

### S2-T2: Workspace Snapshot Versioning (ENT-004)

- [ ] **S2-T2-1** Read `backend/routers/study.py` in full
- [ ] **S2-T2-2** Add `workspace_snapshots` table to `backend/init-db.sql`:
  - `id`, `workspace_id` (FK), `user_id` (FK), `version` (int, auto-increment per workspace), `label` (user text), `state` (JSONB: filters, notes, queries, compare_ids, timeline_ids, chat_excerpts), `llm_provider`, `argo_data_as_of`, `created_at`
  - Constraint: snapshots are immutable (no UPDATE allowed — enforce in trigger or app layer)
- [ ] **S2-T2-3** Add endpoints in `backend/routers/study.py`:
  - `POST /api/v1/study/workspaces/{id}/snapshots` — create snapshot of current workspace state
  - `GET /api/v1/study/workspaces/{id}/snapshots` — list all snapshots
  - `GET /api/v1/study/workspaces/{id}/snapshots/{version}` — get specific snapshot
- [ ] **S2-T2-4** Create `backend/services/reproducibility_service.py`:
  - `generate_repro_bundle(snapshot_id) -> bytes (ZIP)` — assembles:
    - `README.md` (what the snapshot contains, how to reproduce)
    - `data_params.json` (filter parameters used)
    - `chat_transcript.md` (key chat exchanges)
    - `citations.bib` (all literature from workspace library)
    - `notebook.ipynb` (generated Jupyter notebook with argopy code)
  - `generate_citation(snapshot) -> str` — APA citation for the dataset snapshot
- [ ] **S2-T2-5** Add endpoint `GET /api/v1/study/workspaces/{id}/snapshots/{version}/bundle` — returns ZIP download
- [ ] **S2-T2-6** Update frontend `app/tools/page.tsx`:
  - Add "Save Snapshot" button with label input
  - Show snapshot history list (version, label, date)
  - "Download Bundle" button per snapshot
  - "Restore" button to reload snapshot state into current workspace
- [ ] **S2-T2-7** Add `nbformat` to `backend/requirements.txt`
- [ ] **S2-T2-8** Create `backend/services/notebook_generator.py`:
  - `generate_jupyter_notebook(snapshot) -> dict (nbformat)` — produces notebook with:
    - Cell 0: markdown header + citation
    - Cell 1: pip install argopy block
    - Cell 2: data fetch code with snapshot filter parameters
    - Cell 3: basic matplotlib/plotly visualization
- [ ] **S2-T2-9** Add tests: `backend/tests/test_snapshots.py`, `backend/tests/test_repro_bundle.py`

---

## Sprint 3 — Learning Platform

**Goal:** Build adaptive learning features for students.  
**Files to read first:** `backend/routers/tools.py`, `app/tools/page.tsx`

### S3-T1: Flashcard & Quiz System (ENT-003)

- [ ] **S3-T1-1** Add tables to `backend/init-db.sql`:
  - `flashcards`: `id`, `user_id`, `workspace_id`, `front` (question), `back` (answer), `source_citation`, `difficulty` (1–5), `topic`, `created_at`
  - `quiz_results`: `id`, `user_id`, `quiz_topic`, `score`, `total_questions`, `answers` (JSONB), `created_at`
  - `learning_progress`: `id`, `user_id`, `topic`, `mastery_level` (0.0–1.0), `flashcards_reviewed`, `quizzes_passed`, `last_activity`
- [ ] **S3-T1-2** Create `backend/services/learning_service.py`:
  - `generate_flashcards_from_response(chat_response: str, topic: str) -> list[Flashcard]` — LLM call with structured output
  - `generate_quiz(topic: str, num_questions: int) -> list[QuizQuestion]` — MCQ from glossary + topic
  - `get_next_flashcard(user_id: int) -> Flashcard` — Leitner box spaced repetition scheduling
  - `update_mastery(user_id: int, topic: str, correct: bool)` — update mastery score
- [ ] **S3-T1-3** Create `backend/routers/learn.py`:
  - `POST /api/v1/learn/flashcards/generate` — from chat response text, generate flashcards
  - `GET /api/v1/learn/flashcards` — list user's flashcards (filterable by topic)
  - `POST /api/v1/learn/flashcards/{id}/review` — record review result (easy/hard/again)
  - `GET /api/v1/learn/flashcards/next` — get next card due for review
  - `POST /api/v1/learn/quiz/generate` — generate quiz for a topic
  - `POST /api/v1/learn/quiz/submit` — submit answers, get scored result
  - `GET /api/v1/learn/progress` — get user's learning progress across topics
- [ ] **S3-T1-4** Wire learn router into `backend/main.py`
- [ ] **S3-T1-5** Update chat response — add "Generate Flashcards" button on each assistant message
- [ ] **S3-T1-6** Create `app/learn/page.tsx` — Learning Hub page:
  - Flashcard deck view (flip animation)
  - "Review Due Cards" button (spaced repetition)
  - Quiz mode UI (MCQ with progress bar)
  - Progress dashboard: mastery per topic, heatmap of review activity
- [ ] **S3-T1-7** Add "Learning Mode" toggle in chat — activates Socratic prompt behavior
- [ ] **S3-T1-8** Add to navigation
- [ ] **S3-T1-9** Add tests: `backend/tests/test_learning_service.py`

---

## Sprint 4 — Collaboration

**Goal:** Enable team research across shared workspaces.  
**Files to read first:** `backend/routers/study.py`, `backend/routers/auth.py`

### S4-T1: Shared Workspace with RBAC (ENT-005)

- [ ] **S4-T1-1** Add tables to `backend/init-db.sql`:
  - `workspace_members`: `workspace_id` (FK), `user_id` (FK), `role` (owner/collaborator/viewer), `invited_by`, `joined_at`
  - `workspace_comments`: `id`, `workspace_id`, `user_id`, `target_type` (note/query/compare/timeline), `target_id`, `text`, `created_at`
  - `workspace_activity`: `id`, `workspace_id`, `user_id`, `action`, `details` (JSONB), `created_at`
  - `workspace_invitations`: `id`, `workspace_id`, `email`, `role`, `token` (UUID), `expires_at`, `accepted`
- [ ] **S4-T1-2** Add invite endpoints to `backend/routers/study.py`:
  - `POST /api/v1/study/workspaces/{id}/invite` — send invitation (email + role)
  - `GET /api/v1/study/workspaces/accept-invite/{token}` — accept invitation
  - `GET /api/v1/study/workspaces/{id}/members` — list members
  - `DELETE /api/v1/study/workspaces/{id}/members/{user_id}` — remove member
- [ ] **S4-T1-3** Add comment endpoints:
  - `POST /api/v1/study/comments` — create comment on artifact
  - `GET /api/v1/study/comments?workspace_id=&target_type=&target_id=` — list comments
  - `DELETE /api/v1/study/comments/{id}` — delete comment (own only)
- [ ] **S4-T1-4** Add activity feed endpoint: `GET /api/v1/study/workspaces/{id}/activity`
- [ ] **S4-T1-5** Add RBAC middleware: collaborator role check on mutation endpoints
- [ ] **S4-T1-6** Add public workspace URL: `POST /api/v1/study/workspaces/{id}/publish` — returns read-only token; `GET /api/v1/public/workspace/{token}` — unauthenticated read-only view
- [ ] **S4-T1-7** Update frontend `app/tools/page.tsx` workspace section:
  - Member list with role badges
  - "Invite" button + email input
  - Activity feed panel (recent actions)
  - Comment threads on notes/queries
  - "Share" button → public URL copy
- [ ] **S4-T1-8** Add tests: `backend/tests/test_collaboration.py`

---

## Sprint 5 — Scientific Report Builder

**Goal:** Generate publication-quality research drafts from workspace content.  
**Files to read first:** `backend/services/reproducibility_service.py` (created in S2), `backend/services/notebook_generator.py`

### S5-T1: Report Assembly Service (ENT-006)

- [ ] **S5-T1-1** Add `python-docx`, `weasyprint` (or `reportlab`) to `backend/requirements.txt`
- [ ] **S5-T1-2** Create `backend/services/report_service.py`:
  - `generate_report(workspace_id: int, artifact_ids: list, style: str) -> ReportDraft`
  - Report sections: Abstract, Introduction, Data & Methods, Results, Discussion, References
  - Each section generated by LLM prompt with relevant workspace content as context
  - Citations auto-inserted from research library
  - Figures referenced from export endpoint URLs
- [ ] **S5-T1-3** Create `backend/routers/report.py`:
  - `POST /api/v1/report/generate` — initiate report generation (async background job)
  - `GET /api/v1/report/{job_id}/status` — check generation status
  - `GET /api/v1/report/{report_id}/download?format=md|docx|pdf|latex` — download in format
  - `GET /api/v1/report/{report_id}` — get report JSON (for in-browser editing)
  - `PUT /api/v1/report/{report_id}/section/{section}` — update a section
- [ ] **S5-T1-4** Add `reports` table: `id`, `workspace_id`, `user_id`, `job_id`, `status`, `sections` (JSONB), `created_at`, `updated_at`
- [ ] **S5-T1-5** Wire report router into `backend/main.py`
- [ ] **S5-T1-6** Add background job worker (use `concurrent.futures` or `celery` depending on scope):
  - Process report generation asynchronously
  - Update `status` field: pending → generating → ready → error
- [ ] **S5-T1-7** Create `app/report/page.tsx` — Report Builder page:
  - Workspace artifact selector (checkboxes: notes, queries, compare, timeline, chat excerpts)
  - Style selector: "Research Paper", "Technical Report", "Summary Brief"
  - Generate button → loading state → preview
  - Inline editor for each section (markdown)
  - Export buttons: Download MD, Download Word, Download PDF, Download LaTeX
- [ ] **S5-T1-8** Add high-res figure export endpoint `GET /api/v1/export/figure/{type}?params=...`
- [ ] **S5-T1-9** Add tests: `backend/tests/test_report_service.py`

### S5-T2: R Script Generation (ENT-009)

- [ ] **S5-T2-1** Update `backend/services/notebook_generator.py`:
  - Add `generate_r_script(snapshot) -> str` — produces R code using `oce` + `ggplot2` patterns
  - Template covers: data download via argoFloats/rerddap, basic T-S plot, map of float positions
- [ ] **S5-T2-2** Add endpoint `GET /api/v1/study/workspaces/{id}/snapshots/{version}/rscript` — returns R script download

---

## Sprint 6 — Intelligence Upgrade

**Goal:** Add graph reasoning and predictive analytics.  
**Files to read first:** `backend/rag/retriever.py`, `backend/routers/argo_filter.py`, `backend/data_ingestion/`

### S6-T1: Ocean Knowledge Graph (ENT-007)

- [ ] **S6-T1-1** Add `networkx` to `backend/requirements.txt`
- [ ] **S6-T1-2** Create `backend/knowledge/graph.py`:
  - `OceanKnowledgeGraph` class wrapping NetworkX DiGraph
  - Entity types: Region, Current, Phenomenon, Parameter, Float, Event, Species
  - Relationships: influenced_by, located_in, adjacent_to, measures, causes, correlates_with
  - Methods: `add_entity`, `add_relationship`, `traverse(start, max_hops)`, `query(question) -> Path`
  - Persistence: serialize to/from JSON file (load on startup)
- [ ] **S6-T1-3** Create `backend/knowledge/seed_graph.py` — seed script populating:
  - Major ocean regions (Indian, Pacific, Atlantic, Southern, Arctic)
  - Major currents (AMOC, Kuroshio, Agulhas, etc.)
  - Key phenomena (ENSO, IOD, AMO, Monsoon)
  - BGC parameters (chlorophyll, oxygen, nitrate, pH)
  - ARGO measurement parameters (temperature, salinity, pressure)
- [ ] **S6-T1-4** Wire graph into chat — pre-query graph for relevant entity context; include traversal path in response
- [ ] **S6-T1-5** Add endpoint `GET /api/v1/knowledge/graph` — return graph JSON (nodes + edges) for visualization
- [ ] **S6-T1-6** Add endpoint `POST /api/v1/knowledge/graph/entity` — add custom entity
- [ ] **S6-T1-7** Create frontend `app/knowledge/page.tsx` — Concept Explorer:
  - D3.js force-directed graph visualization
  - Click node → show entity info panel
  - Search bar to find entities
  - "Add Entity" form for user-contributed knowledge

### S6-T2: Anomaly Detection & Predictive Analytics (ENT-008)

- [ ] **S6-T2-1** Add tables to `backend/init-db.sql`:
  - `ocean_baselines`: `region`, `month`, `depth_range`, `mean_temp`, `std_temp`, `mean_sal`, `std_sal`, `sample_count`, `computed_at`
  - `anomaly_events`: `id`, `event_type` (heatwave/oxygen_stress/bloom), `region`, `detected_at`, `severity`, `details` (JSONB), `float_ids` (JSONB array), `acknowledged`
- [ ] **S6-T2-2** Create `backend/services/analytics_service.py`:
  - `compute_baselines(region: str)` — compute monthly mean/std from historical profiles in DB
  - `detect_anomalies(profiles: list)` — z-score vs baseline, flag if > 2σ
  - `detect_marine_heatwave(region: str, window_days: int)` — sustained temperature anomaly detection
  - `detect_oxygen_stress(bgc_profiles: list)` — DO below threshold
- [ ] **S6-T2-3** Add `statsmodels` to `backend/requirements.txt`
- [ ] **S6-T2-4** Create `backend/services/forecast_service.py`:
  - `forecast_temperature(float_id: int, days_ahead: int) -> Forecast` — Prophet/ARIMA on float's history
  - Returns: forecast values + upper/lower 95% CI bounds per day
- [ ] **S6-T2-5** Create `backend/routers/analytics.py`:
  - `GET /api/v1/analytics/baselines?region=&month=` — get baseline stats
  - `GET /api/v1/analytics/anomalies?region=&severity=` — list detected events
  - `POST /api/v1/analytics/compute-baselines` — trigger baseline recomputation (admin)
  - `GET /api/v1/analytics/forecast/{float_id}?days=14` — get temperature forecast
  - `GET /api/v1/analytics/events-feed` — dashboard events feed
- [ ] **S6-T2-6** Wire analytics router into `backend/main.py`
- [ ] **S6-T2-7** Update `app/dashboard/page.tsx`:
  - Add "Events Feed" panel (marine heatwaves, anomalies detected)
  - Add "Forecast" section for selected region
- [ ] **S6-T2-8** Add tests: `backend/tests/test_analytics_service.py`

---

## Sprint 7 — 3D Visualization & Multi-Dataset Fusion

**Goal:** Add 3D ocean visualizations and unify data sources.  
**Files to read first:** `app/visualizations/page.tsx`, `backend/routers/noaa.py`, `backend/routers/gebco.py`

### S7-T1: 3D Ocean Visualizations (ENT-010)

- [ ] **S7-T1-1** Add to `floatchat-ultimate/package.json`: `three`, `@react-three/fiber`, `@react-three/drei`
- [ ] **S7-T1-2** Create `components/3d/DepthCurtain.tsx` — temperature/salinity vs depth along float track
- [ ] **S7-T1-3** Create `components/3d/FloatTrajectory.tsx` — animated float position over time (play/pause/scrub)
- [ ] **S7-T1-4** Create `components/charts/HovmollerDiagram.tsx` — Plotly heatmap, longitude/time x-axis, color = T or S
- [ ] **S7-T1-5** Create `components/charts/TSdiagram.tsx` — T-S scatter plot with water mass polygon overlays (North Atlantic, Mediterranean, etc.)
- [ ] **S7-T1-6** Update `app/visualizations/page.tsx` — add tabs for 3D views, Hovmöller, T-S diagram
- [ ] **S7-T1-7** Add high-resolution export button to each 3D/chart component (PNG/SVG download)

### S7-T2: Multi-Dataset Fusion Layer (ENT-011)

- [ ] **S7-T2-1** Read all existing routers: `backend/routers/noaa.py`, `gebco.py`, `cmems.py`, `open_meteo_marine.py`
- [ ] **S7-T2-2** Create `backend/routers/fusion.py`:
  - `GET /api/v1/fusion/query` — accepts bbox + date range, returns merged: ARGO profiles + NOAA SST at location + GEBCO depth + climate index value
  - `GET /api/v1/fusion/climate-index?index=enso|iod&date_range=` — ENSO/IOD indices for correlation
- [ ] **S7-T2-3** Update chat service — when query mentions multi-dataset keywords (El Niño, SST, climate, heatwave), route to fusion query
- [ ] **S7-T2-4** Update dashboard to show SST overlay option on float map
- [ ] **S7-T2-5** Add tests: `backend/tests/test_fusion.py`

---

## Sprint 8 — Platform APIs

**Goal:** Enable developer access to FloatChat data and AI.  
**Files to read first:** `backend/core/security.py`, `backend/routers/auth.py`

### S8-T1: Python SDK (ENT-009)

- [ ] **S8-T1-1** Create `floatchat-sdk/` directory at project root
- [ ] **S8-T1-2** Create `floatchat-sdk/floatchat/__init__.py` — package init
- [ ] **S8-T1-3** Create `floatchat-sdk/floatchat/client.py` — `FloatChatClient` class:
  - `ArgoClient.filter(bbox, date_range, depth_range, qc_level)`
  - `ChatClient.ask(question, provider='auto')`
  - `WorkspaceClient.create(name)`, `.get_snapshots()`, `.export_bundle(version)`
  - `LiteratureClient.search(query)`, `.save_to_library(paper_id)`
- [ ] **S8-T1-4** Create `floatchat-sdk/pyproject.toml` — package metadata
- [ ] **S8-T1-5** Create `floatchat-sdk/README.md` — SDK quick-start guide
- [ ] **S8-T1-6** Create `floatchat-sdk/examples/` — 3 example notebooks

### S8-T2: API Keys & Webhooks (ENT-013)

- [ ] **S8-T2-1** Add `api_keys` table: `id`, `user_id`, `key_hash` (SHA-256 of key), `label`, `tier` (free/researcher/institution), `requests_per_hour`, `created_at`, `last_used`, `revoked`
- [ ] **S8-T2-2** Add `webhooks` table: `id`, `user_id`, `url`, `events` (JSONB array), `secret`, `active`, `created_at`
- [ ] **S8-T2-3** Add endpoints in new `backend/routers/developer.py`:
  - `POST /api/v1/developer/keys` — create API key
  - `GET /api/v1/developer/keys` — list keys
  - `DELETE /api/v1/developer/keys/{id}` — revoke key
  - `POST /api/v1/developer/webhooks` — register webhook
  - `GET /api/v1/developer/webhooks` — list webhooks
  - `GET /api/v1/developer/usage` — API usage stats
- [ ] **S8-T2-4** Add API key auth middleware — `X-API-Key` header as alternative to JWT
- [ ] **S8-T2-5** Implement webhook dispatch: after ingestion, after anomaly event, after workspace mutation
- [ ] **S8-T2-6** Create `app/developer/page.tsx` — API Keys & Webhooks management page

---

## Sprint 9 — Educator & Enterprise

**Goal:** Classroom tools, SSO, and mobile.

### S9-T1: Classroom Mode (ENT-012)

- [ ] **S9-T1-1** Add tables: `classrooms`, `assignments`, `submissions`, `classroom_members`
- [ ] **S9-T1-2** Create `backend/routers/classroom.py` — full CRUD for classrooms, assignments, submissions
- [ ] **S9-T1-3** Create `app/classroom/page.tsx` — instructor view + student view
- [ ] **S9-T1-4** Add pre-built Ocean Science Exercises JSON (10 exercises with real ARGO data)
- [ ] **S9-T1-5** LTI 1.3 basic integration (optional, research library only if time permits)

### S9-T2: OAuth2 / OIDC SSO (ENT-014)

- [ ] **S9-T2-1** Add `authlib` to `backend/requirements.txt`
- [ ] **S9-T2-2** Add OAuth2 Google provider: `GET /api/v1/auth/oauth/google`, callback handling, token exchange
- [ ] **S9-T2-3** Add OAuth2 GitHub provider: same pattern
- [ ] **S9-T2-4** Update frontend login page to show "Sign in with Google" and "Sign in with GitHub" buttons

### S9-T3: Audit Log (ENT-014)

- [ ] **S9-T3-1** Add `audit_log` table: `id`, `user_id`, `action`, `resource_type`, `resource_id`, `ip_address`, `user_agent`, `details` (JSONB), `created_at`, `prev_hash` (for tamper-evidence)
- [ ] **S9-T3-2** Add audit middleware that logs all authenticated mutations
- [ ] **S9-T3-3** Add admin endpoint `GET /api/v1/admin/audit-log` (admin role only)

### S9-T4: PWA & Mobile (ENT-015)

- [ ] **S9-T4-1** Add `next-pwa` to `package.json`
- [ ] **S9-T4-2** Configure service worker in `next.config.ts`
- [ ] **S9-T4-3** Add `public/manifest.json` — PWA manifest
- [ ] **S9-T4-4** Add offline fallback page `app/offline/page.tsx`
- [ ] **S9-T4-5** Review and fix all pages for mobile portrait viewport (320px–480px)

---

## Continuous / Ongoing Tasks

### Testing
- [ ] Maintain backend test coverage ≥ 70% at all times
- [ ] After each sprint, run `pytest -q backend/tests` — zero failures before merge
- [ ] After each sprint, run `pnpm exec tsc --noEmit` — zero TypeScript errors
- [ ] After each sprint, run `pnpm exec eslint app lib components --max-warnings 0` — clean lint
- [ ] Perform manual smoke test of critical path: login → filter → chat → export → snapshot

### Documentation
- [ ] Update `CURRENT_STATE.md` after each sprint with completed features
- [ ] Update `backend/README.md` with new environment variables added
- [ ] Update `docs/runbooks/` with new runbooks for: anomaly detection, report generation, classroom setup
- [ ] Keep `ENTERPRISE_TODO.md` (this file) updated — check off completed tasks

### Performance
- [ ] After Sprint 6: run load test (k6 or locust) against /api/chat — target p95 < 4s
- [ ] After Sprint 7: profile 3D visualization rendering with 10k data points
- [ ] After Sprint 8: verify API key rate limiting under load

### Security
- [ ] Run OWASP dependency check after each sprint
- [ ] Review all new endpoints for missing auth — all mutation endpoints MUST require JWT or API key
- [ ] Verify no secrets in any new committed files

---

## Backlog (Future Sprints, Not Yet Scheduled)

- [ ] Polar Argo data integration (under-ice sampling gap from 2026 research)
- [ ] Deep Ocean (>2000m) GNN interpolation (SeaCast-style gap filling)
- [ ] Real-time BGC-QC agent (Agentic Data Steward pattern)
- [ ] ARCO/Zarr format support for cloud-native data access
- [ ] argopy integration as primary data fetcher (replaces custom ARGO pipeline)
- [ ] Sound speed profile calculator (ocean acoustics tool)
- [ ] Tide prediction tool (harmonic analysis)
- [ ] OBIS biodiversity data integration (species + ARGO overlay)
- [ ] OOI real-time sensor stream integration
- [ ] Kubernetes Helm charts for cloud deployment
- [ ] Admin monitoring dashboard (system health, user stats)
- [ ] Custom branding for institutional deployments
- [ ] Citation network visualization (paper citation graph from Research Library)
- [ ] Audio overview generation (NotebookLM-style podcast from workspace)
- [ ] Multilingual UI (i18n framework + at least French and Chinese)
- [ ] WCAG 2.1 AA full accessibility audit and remediation
- [ ] Model Context Protocol (MCP) server for LLM desktop tool integration

---

## Quick Reference: Key Files Per Feature

| Feature | Backend Files | Frontend Files |
|---|---|---|
| ENT-001 Answer Reliability | `services/answer_verifier.py`, `llm/chat_service.py` | `app/chat/page.tsx` |
| ENT-002 Literature | `services/literature_service.py`, `routers/literature.py` | `app/library/page.tsx` |
| ENT-003 Learning | `services/learning_service.py`, `routers/learn.py` | `app/learn/page.tsx` |
| ENT-004 Reproducibility | `services/reproducibility_service.py`, `services/notebook_generator.py` | `app/tools/page.tsx` |
| ENT-005 Collaboration | `routers/study.py` (extend) | `app/tools/page.tsx` (extend) |
| ENT-006 Report Builder | `services/report_service.py`, `routers/report.py` | `app/report/page.tsx` |
| ENT-007 Knowledge Graph | `knowledge/graph.py`, `knowledge/seed_graph.py` | `app/knowledge/page.tsx` |
| ENT-008 Predictive | `services/analytics_service.py`, `services/forecast_service.py`, `routers/analytics.py` | `app/dashboard/page.tsx` (extend) |
| ENT-009 SDK | `floatchat-sdk/` (new package) | `app/developer/page.tsx` |
| ENT-010 3D Viz | — | `components/3d/`, `app/visualizations/page.tsx` (extend) |
| ENT-011 Fusion | `routers/fusion.py` | `app/visualizations/page.tsx` (extend) |
| ENT-012 Classroom | `routers/classroom.py` | `app/classroom/page.tsx` |
| ENT-013 API Keys | `routers/developer.py` | `app/developer/page.tsx` |
| ENT-014 Security | `routers/auth.py` (extend), `core/security.py` (extend) | `app/settings/page.tsx` |
| ENT-015 PWA | — | `next.config.ts`, `public/manifest.json` |
| NFR-OBS | `main.py` (extend), `docker-compose.yml` | — |

---

*Last updated: 2026-02-27*  
*Read alongside: `ENTERPRISE_PRD.md`, `CURRENT_STATE.md`*
