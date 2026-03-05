# FloatChat Enterprise PRD
## Product Requirements Document — Enterprise-Grade Ocean Research Platform

**Document Version:** 2.0  
**Date:** 2026-02-27  
**Status:** Active Planning  
**Based on:** Research gap analysis, IEEE 830 SRS, current implementation (Phases A–E complete), web research on 2025–2026 enterprise science platforms  

---

## 1. Executive Summary

FloatChat has completed its foundational phases (A through E): ARGO ingestion, multi-provider LLM chat, RAG, JWT auth, workspaces, notes, exports, BGC-ARGO, and CI/CD. The platform works.

**The gap:** It is a tool, not a research platform. Students and researchers using it today encounter the same friction that enterprise platforms like Hub Ocean, Pangeo, and OceanAI have identified and started solving: no research workflow intelligence, no paper integration, no reproducibility guarantees, no collaborative knowledge building, no learning scaffolding, and no scientific output generation.

This PRD defines the next evolution: **FloatChat Enterprise Research Platform** — a full-cycle scientific workspace where students and researchers go from question to published-quality insight without leaving the platform.

---

## 2. Problem Statement — The Gaps

### 2.1 Identified from Research Paper / Platform Analysis (2025–2026)

| Gap Category | Specific Gap | Evidence Source |
|---|---|---|
| **AI Trustworthiness** | Chat responses have no confidence score, no evidence coverage, no "I don't know" fallback | Power-up plan, OceanAI research |
| **Knowledge Integration** | No connection between ocean data and scientific literature (papers, methods, citations) | Semantic Scholar, OKG-LLM research |
| **Reproducibility** | No reproducibility bundles; researchers can't re-run an analysis from saved state | Bibal et al. 2025, Power-up plan |
| **Learning Scaffolding** | No guided learning, flashcards, adaptive quizzes from ocean data | NotebookLM, 2025 student platform trends |
| **Collaborative Research** | No shared workspaces, no team annotations, no review threads | Power-up plan Phase P2 |
| **Scientific Output** | No report/paper draft generation; no LaTeX/Word export | Task.md Phase 3 item 23 |
| **Literature Bridge** | No connection to Semantic Scholar, arXiv, or DOI resolver for paper context | 2025 research platform research |
| **Graph Reasoning** | Only flat RAG (keyword/vector); no knowledge graph for multi-hop ocean reasoning | GraphRAG, OKG-LLM |
| **Multi-Dataset Fusion** | BGC-ARGO added but satellite, climate indices, glider data not unified | Hub Ocean, Pangeo comparison |
| **Predictive Analytics** | No forecasting, no anomaly detection pipelines, no marine heatwave alerts | Task.md Phase 3 item 22 |
| **Notebook Interop** | No Jupyter/R notebook generation from saved workspace snapshots | Power-up plan Phase P2 |
| **Data Governance** | No data lineage, no quality scores per profile, no provenance in responses | Hub Ocean RBAC, 2026 enterprise stack |
| **Deep Ocean Blind Spot** | Only surface-weighted data; no 2000m+ deep-ocean interpolation | 2025–2026 gap analysis |
| **Real-time Alerts** | No event-driven alerts (marine heatwave, oxygen stress, bloom detection) | Power-up plan Phase P3 |
| **3D Visualization** | No 3D ocean depth scenes, trajectory animations, volumetric layers | Power-up plan Phase P1 |
| **MFA / SSO** | Only JWT password auth; no MFA, no institutional SSO | SRS TBD-3, TBD-4 |
| **Mobile / PWA** | No offline mode, no mobile-first layouts for fieldwork | SRS TBD-11 |
| **API for Developers** | No public API keys, no webhooks, no Python/R SDK | Task.md Phase 3 item 25 |

### 2.2 What Students and Researchers Actually Need (Derived)

A graduate student using FloatChat today must:
1. Query ARGO data (works)
2. Get an AI answer (works, but no confidence/source quality)
3. Manually go to Google Scholar to find related papers
4. Manually write their notes linking data to literature
5. Export CSV and manually write the methods section
6. Share findings by copy-pasting to colleagues
7. Reproduce the analysis by hand later

**Every step after step 2 is a gap.** Enterprise research platforms close these gaps.

---

## 3. Vision Statement

> FloatChat Enterprise transforms from a smart data tool into the **complete scientific workspace** for ocean science students and researchers — where data querying, literature integration, collaborative analysis, AI-assisted writing, and reproducible publication happen in one place, at zero mandatory cost.

---

## 4. User Personas (Expanded)

### P1: Graduate Researcher (Primary)
- Running thesis research on Indian Ocean temperature anomalies
- Needs: data + papers together, reproducible snapshots, citation export, advisor sharing
- Current pain: switches between 5 tools (ARGO portal, Google Scholar, Jupyter, Word, Slack)

### P2: Undergraduate Student (Primary)
- Taking Physical Oceanography course
- Needs: guided learning, glossary, quizzes, "explain this to me" AI tutor mode
- Current pain: data too technical, no learning pathway, no feedback on understanding

### P3: Educator / Professor (Secondary)
- Teaching ocean science, assigning student projects
- Needs: classroom management, assignment creation, student progress tracking, curated datasets
- Current pain: no LMS integration, no way to create guided exercises on real data

### P4: Data Scientist / Oceanographer (Secondary)
- Running production analysis pipelines
- Needs: Python SDK, API keys, notebook generation, webhook for pipeline integration
- Current pain: must scrape APIs manually; no programmatic access to FloatChat's derived insights

### P5: Citizen Scientist (Tertiary)
- Interested in ocean health and climate
- Needs: simple dashboard, AI explanations without jargon, shareable visuals
- Current pain: jargon-heavy UI, no story-mode narrative

---

## 5. Strategic Feature Tiers

### TIER 1 — Critical Enterprise Research Features (Next 0–8 weeks)
*These unlock FloatChat from "tool" to "research platform" immediately.*

### TIER 2 — Research Acceleration Features (8–20 weeks)
*These make FloatChat genuinely superior to alternatives for daily use.*

### TIER 3 — Platform Ecosystem Features (20–40 weeks)
*These make FloatChat a platform others build on.*

---

## 6. Feature Requirements

---

### FEATURE 1: Scientific Answer Reliability Engine (TIER 1)
**ID:** ENT-001  
**Priority:** CRITICAL  
**User need:** Researchers cannot trust AI answers without evidence and confidence scores.

**Requirements:**
- REQ-ENT-001-1: Every chat response MUST include a `confidence_score` (0.0–1.0) based on evidence coverage
- REQ-ENT-001-2: Responses MUST include an `evidence_sources` array listing: source name, relevance score, snippet
- REQ-ENT-001-3: When confidence < 0.4, system MUST respond with "Insufficient evidence" template instead of generating an answer
- REQ-ENT-001-4: Response MUST include a "Limitations" section for data-grounded answers
- REQ-ENT-001-5: Response MUST include a "Method" field explaining how the answer was derived
- REQ-ENT-001-6: Chain-of-verification layer MUST check the generated answer against source evidence before returning
- REQ-ENT-001-7: UI MUST display confidence badge (color-coded: green ≥0.7, yellow 0.4–0.7, red <0.4)

**Technical approach:** Add `AnswerVerifier` class in backend; post-process LLM output against retrieved RAG docs; return structured `ScientificResponse` schema.

---

### FEATURE 2: Literature Integration Module (TIER 1)
**ID:** ENT-002  
**Priority:** CRITICAL  
**User need:** Researchers need papers linked to data queries; students need related reading.

**Requirements:**
- REQ-ENT-002-1: System MUST integrate Semantic Scholar public API (free, no key required for basic access)
- REQ-ENT-002-2: Every significant chat response about an oceanographic topic MUST include "Related Papers" section (top 3–5)
- REQ-ENT-002-3: Papers MUST be linked by: topic similarity, DOI, citation count, publication year
- REQ-ENT-002-4: User MUST be able to "Add to Research Library" any suggested paper (saved to workspace)
- REQ-ENT-002-5: System MUST support paper recommendation seeding (positive/negative paper IDs for SPECTER2 similarity)
- REQ-ENT-002-6: Research Library page MUST show: title, authors, abstract, citation count, year, DOI link
- REQ-ENT-002-7: System SHOULD generate "how this paper relates to your query" one-line summary
- REQ-ENT-002-8: Citation export MUST support BibTeX, APA, and MLA formats

**Technical approach:** New `/api/v1/literature/` router; Semantic Scholar Recommendations API; store in `research_library` table; RAG corpus auto-enrichment from user-added papers.

---

### FEATURE 3: Adaptive Learning Module (TIER 1)
**ID:** ENT-003  
**Priority:** HIGH  
**User need:** Students need guided learning, not just data access. Current glossary/calculator is passive.

**Requirements:**
- REQ-ENT-003-1: System MUST provide "Learning Mode" toggle in chat that activates Socratic tutor behavior
- REQ-ENT-003-2: In Learning Mode, AI MUST ask guiding questions rather than giving direct answers
- REQ-ENT-003-3: System MUST auto-generate flashcards from any chat response or data query result
- REQ-ENT-003-4: Flashcards MUST include: question, answer, source citation, difficulty level
- REQ-ENT-003-5: System MUST provide spaced repetition scheduling for flashcard review (Leitner box algorithm)
- REQ-ENT-003-6: System MUST generate quizzes (MCQ) from glossary terms, recent chat topics, and data insights
- REQ-ENT-003-7: Quizzes MUST show score, correct answers with explanations, and suggested further reading
- REQ-ENT-003-8: System MUST track learning progress per user: topics covered, quiz scores, flashcards reviewed
- REQ-ENT-003-9: Learning progress MUST be visible in user profile/workspace dashboard
- REQ-ENT-003-10: System MUST provide "Concept Map" view showing relationships between learned topics

**Technical approach:** New `/api/v1/learn/` router; flashcard generation from LLM with Pydantic schema; progress tracking in `learning_progress` table; concept map from topic entity graph.

---

### FEATURE 4: Reproducibility & Citation Bundle (TIER 1)
**ID:** ENT-004  
**Priority:** HIGH  
**User need:** Researchers need to reproduce analyses and cite the platform correctly.

**Requirements:**
- REQ-ENT-004-1: System MUST support "Snapshot" versioning of workspace state (filters, notes, queries, compare runs, timeline)
- REQ-ENT-004-2: Each snapshot MUST record: timestamp, user, filter parameters, data version, LLM provider used, sources cited
- REQ-ENT-004-3: User MUST be able to export a "Reproducibility Bundle" as ZIP containing: README.md, data_params.json, chat_transcript.md, citations.bib, python_notebook.ipynb
- REQ-ENT-004-4: Python notebook MUST contain working code to reproduce the data fetch and analysis
- REQ-ENT-004-5: System MUST auto-generate a "Suggested Citation" for the platform in APA format
- REQ-ENT-004-6: Every export (CSV, NetCDF, JSON) MUST include metadata header: data_as_of, filter_params, citation_text, data_source
- REQ-ENT-004-7: Snapshots MUST be immutable once saved (append-only versioning)
- REQ-ENT-004-8: System SHOULD generate a DOI-ready dataset description for depositing to Zenodo

**Technical approach:** `snapshots` table with JSONB version state; ZIP generation endpoint; Jupyter notebook templating with nbformat; citation formatter service.

---

### FEATURE 5: Collaborative Workspace (TIER 2)
**ID:** ENT-005  
**Priority:** HIGH  
**User need:** Research teams need to share findings, comment, and co-analyze.

**Requirements:**
- REQ-ENT-005-1: Workspace owner MUST be able to invite collaborators by email
- REQ-ENT-005-2: Roles MUST include: Owner, Collaborator (read+write), Viewer (read-only)
- REQ-ENT-005-3: Collaborators MUST be able to add comments/threads on: notes, saved queries, compare sessions, timeline runs
- REQ-ENT-005-4: System MUST maintain activity feed: "User X added a note", "User Y ran compare", timestamps
- REQ-ENT-005-5: System MUST show presence indicators (who is currently viewing the workspace)
- REQ-ENT-005-6: All workspace mutations MUST be tracked with user_id and timestamp (audit log)
- REQ-ENT-005-7: Owner MUST be able to "publish" a workspace as read-only public shareable URL
- REQ-ENT-005-8: System SHOULD support @mention notifications in comments

**Technical approach:** `workspace_members` table; `comments` table with polymorphic target; `activity_log` table; presence via Redis pub/sub; public workspace token URL.

---

### FEATURE 6: Scientific Report Builder (TIER 2)
**ID:** ENT-006  
**Priority:** HIGH  
**User need:** Researchers need to generate draft paper sections, not just export data.

**Requirements:**
- REQ-ENT-006-1: User MUST be able to select workspace artifacts (notes, compare runs, chat responses, visualizations) and generate a structured report
- REQ-ENT-006-2: Report MUST include sections: Abstract, Introduction (from notes), Data & Methods (from filter params), Results (from data + AI), Discussion (from AI reasoning), References (from literature library)
- REQ-ENT-006-3: Report MUST be exportable as: Markdown, Word (.docx), PDF
- REQ-ENT-006-4: System MUST support LaTeX template export for journal submission
- REQ-ENT-006-5: All figures in the report MUST be exportable as high-resolution PNG/SVG
- REQ-ENT-006-6: Report generation MUST complete within 60 seconds for standard workspace (up to 20 artifacts)
- REQ-ENT-006-7: Generated report MUST include proper citations for all data sources and related papers
- REQ-ENT-006-8: User MUST be able to edit the generated report inline before export

**Technical approach:** Report assembly service combining workspace artifacts; LLM for prose generation per section; `python-docx` for Word export; `WeasyPrint` or `reportlab` for PDF; LaTeX Jinja2 templates.

---

### FEATURE 7: Knowledge Graph for Ocean Science (TIER 2)
**ID:** ENT-007  
**Priority:** MEDIUM  
**User need:** Multi-hop reasoning ("How does ENSO affect Indian Ocean salinity patterns?") requires graph reasoning.

**Requirements:**
- REQ-ENT-007-1: System MUST maintain an Ocean Knowledge Graph (OKG) with entity types: Region, Current, Phenomenon, Parameter, Float, Species, Event
- REQ-ENT-007-2: Graph MUST support relationships: influenced_by, located_in, adjacent_to, measures, causes, correlates_with
- REQ-ENT-007-3: Chat queries MUST use graph traversal for multi-hop reasoning before LLM generation
- REQ-ENT-007-4: UI MUST provide "Concept Explorer" view: interactive graph of how ocean concepts connect
- REQ-ENT-007-5: Graph MUST be populated from: ARGO metadata, curated ocean science ontologies, user-added papers
- REQ-ENT-007-6: User MUST be able to add new entities/relationships to the graph from their research
- REQ-ENT-007-7: Graph queries MUST return traversal path (chain of reasoning) alongside the answer

**Technical approach:** NetworkX for graph structure (free, in-memory for MVP); entity extraction from corpus using LLM; SPARQL-style query layer; D3.js force-directed visualization.

---

### FEATURE 8: Predictive Analytics & Event Detection (TIER 2)
**ID:** ENT-008  
**Priority:** MEDIUM  
**User need:** Researchers need forecasting and anomaly detection, not just historical data browsing.

**Requirements:**
- REQ-ENT-008-1: System MUST compute and store seasonal baselines per ocean region (monthly mean T, S by region/depth)
- REQ-ENT-008-2: System MUST compute anomaly scores (z-score vs baseline) for all new profile ingestions
- REQ-ENT-008-3: System MUST detect marine heatwave events (T > baseline + 3σ for consecutive profiles)
- REQ-ENT-008-4: System MUST detect potential oxygen stress events (DO below threshold in BGC profiles)
- REQ-ENT-008-5: Alert events MUST be stored and surfaced in a "Events Feed" on the dashboard
- REQ-ENT-008-6: System MUST provide trend decomposition (seasonal + trend + residual) for selected regions
- REQ-ENT-008-7: System SHOULD provide 14-day temperature forecast using Prophet or ARIMA for active float positions
- REQ-ENT-008-8: All predictions MUST include uncertainty bounds (95% confidence interval)
- REQ-ENT-008-9: Alert subscriptions MUST allow email/webhook notification when threshold exceeded

**Technical approach:** Precomputed baseline tables in PostgreSQL; statsmodels/Prophet for forecasting; background Celery/RQ worker for anomaly detection after ingestion; alert_events table with webhook dispatch.

---

### FEATURE 9: Notebook & Script Interoperability (TIER 2)
**ID:** ENT-009  
**Priority:** MEDIUM  
**User need:** Data scientists and researchers need to take FloatChat analyses into their own Python/R workflows.

**Requirements:**
- REQ-ENT-009-1: System MUST generate a runnable Jupyter notebook from any saved workspace snapshot
- REQ-ENT-009-2: Notebook MUST include: argopy data fetch code, filter parameters as variables, basic visualization cells, citation cell
- REQ-ENT-009-3: System MUST generate equivalent R script (using `argo` or `oce` package patterns)
- REQ-ENT-009-4: Generated code MUST be tested/validated (basic syntax check) before download
- REQ-ENT-009-5: System MUST provide a Python SDK (installable via pip) with: ArgoClient, ChatClient, WorkspaceClient
- REQ-ENT-009-6: Python SDK MUST support: data fetching, chat queries, workspace CRUD, snapshot export
- REQ-ENT-009-7: SDK MUST be documented with type hints and docstrings
- REQ-ENT-009-8: System MUST provide an API Playground (web UI) for testing all endpoints with live responses

**Technical approach:** nbformat for notebook generation; Jinja2 R script templates; SDK as `floatchat-sdk` Python package; Swagger UI already exists, enhance with live playground.

---

### FEATURE 10: 3D Ocean Visualization (TIER 2)
**ID:** ENT-010  
**Priority:** MEDIUM  
**User need:** Current 2D charts are insufficient for depth-profile and trajectory analysis that researchers need.

**Requirements:**
- REQ-ENT-010-1: System MUST provide 3D depth curtain visualization (temperature/salinity vs depth across float track)
- REQ-ENT-010-2: System MUST provide float trajectory animation (time-lapse of float movement)
- REQ-ENT-010-3: System MUST provide vertical profile comparison (multiple floats overlaid in 3D)
- REQ-ENT-010-4: 3D visualizations MUST be interactive (rotate, zoom, select depth range)
- REQ-ENT-010-5: System MUST provide Hovmöller diagram (longitude/latitude vs time, color = T or S)
- REQ-ENT-010-6: System MUST provide T-S diagram (Temperature-Salinity scatter with water mass overlays)
- REQ-ENT-010-7: All 3D visualizations MUST be exportable as high-resolution images

**Technical approach:** Three.js + React Three Fiber for 3D; Plotly.js for Hovmöller and T-S diagrams; data streamed from existing filter API.

---

### FEATURE 11: Multi-Dataset Fusion Layer (TIER 3)
**ID:** ENT-011  
**Priority:** MEDIUM  
**User need:** Real ocean research requires combining ARGO with satellite SST, climate indices, and bathymetry.

**Requirements:**
- REQ-ENT-011-1: System MUST integrate GEBCO bathymetry (already has router) into depth-aware visualizations
- REQ-ENT-011-2: System MUST integrate NOAA SST (already has router) as an overlay on ARGO float maps
- REQ-ENT-011-3: System MUST expose ENSO index (ONI) and IOD index as query-able parameters
- REQ-ENT-011-4: System MUST provide unified query endpoint that joins ARGO + satellite + climate index data
- REQ-ENT-011-5: Chat MUST be able to answer questions fusing multi-dataset context ("Is this anomaly correlated with El Niño?")
- REQ-ENT-011-6: Multi-dataset query MUST return provenance metadata per data source

**Technical approach:** The existing routers (noaa, gebco, cmems, open_meteo_marine, etc.) exist — wire them into a unified fusion query layer with JOIN logic.

---

### FEATURE 12: Educator / Classroom Mode (TIER 3)
**ID:** ENT-012  
**Priority:** MEDIUM  
**User need:** Professors need to use FloatChat as a teaching tool with assignments and tracking.

**Requirements:**
- REQ-ENT-012-1: System MUST support "Classroom" role that groups students under an instructor
- REQ-ENT-012-2: Instructor MUST be able to create "Assignments" with: ocean data task, due date, required deliverable (workspace snapshot)
- REQ-ENT-012-3: Students MUST be able to submit workspace snapshots as assignment completions
- REQ-ENT-012-4: Instructor MUST see per-student: quiz scores, learning progress, submitted assignments
- REQ-ENT-012-5: System MUST support LTI 1.3 Deep Linking for Canvas/Moodle integration
- REQ-ENT-012-6: System MUST provide pre-built "Ocean Science Exercises" library (10+ exercises using real ARGO data)
- REQ-ENT-012-7: Each exercise MUST have: learning objectives, step-by-step guide, answer key (instructor-only)

**Technical approach:** `classrooms` + `assignments` + `submissions` tables; LTI 1.3 library integration; exercise library as curated JSON.

---

### FEATURE 13: Public Developer API (TIER 3)
**ID:** ENT-013  
**Priority:** LOW-MEDIUM  
**User need:** Researchers and institutions want programmatic access to FloatChat data and AI.

**Requirements:**
- REQ-ENT-013-1: System MUST support API key generation per user (beyond JWT session tokens)
- REQ-ENT-013-2: API keys MUST have configurable rate limits: free (60 req/hr), researcher (600 req/hr), institution (6000 req/hr)
- REQ-ENT-013-3: System MUST provide webhook registration for: new data ingestion, alert events, workspace changes
- REQ-ENT-013-4: API documentation portal MUST be separate from backend Swagger UI
- REQ-ENT-013-5: System MUST track API usage per key: requests, data volume, error rates
- REQ-ENT-013-6: System SHOULD provide a Python package `floatchat-sdk` on PyPI

---

### FEATURE 14: Security & Compliance Hardening (TIER 1)
**ID:** ENT-014  
**Priority:** HIGH  
**User need:** Institutional researchers need MFA, SSO, and audit trails.

**Requirements:**
- REQ-ENT-014-1: System MUST support TOTP-based MFA (Google Authenticator compatible)
- REQ-ENT-014-2: System MUST support OAuth2/OIDC SSO (Google, GitHub, institutional providers)
- REQ-ENT-014-3: System MUST maintain audit log: all authentication events, workspace changes, data exports, admin actions
- REQ-ENT-014-4: Audit log MUST be tamper-evident (append-only, hash-chained)
- REQ-ENT-014-5: System MUST enforce GDPR: data export (all user data), data deletion (right to erasure)
- REQ-ENT-014-6: Admin dashboard MUST show: active users, API usage, error rates, storage consumed
- REQ-ENT-014-7: Password reset via email MUST be implemented (currently TBD-2 in SRS)

---

### FEATURE 15: PWA & Mobile Optimization (TIER 3)
**ID:** ENT-015  
**Priority:** LOW  
**User need:** Field researchers and students need offline access to their saved data and notes.

**Requirements:**
- REQ-ENT-015-1: System MUST be installable as PWA (Progressive Web App) with offline capability
- REQ-ENT-015-2: Offline mode MUST support: viewing cached dashboard, reading saved notes, browsing research library
- REQ-ENT-015-3: Mobile layouts MUST be optimized for portrait phone view
- REQ-ENT-015-4: Touch gestures MUST work on 3D visualizations (pinch-to-zoom, drag-to-rotate)

---

## 7. Non-Functional Requirements (Enterprise Grade)

### 7.1 Observability
- NFR-OBS-1: ALL API requests MUST include distributed trace ID (correlation ID header)
- NFR-OBS-2: System MUST expose Prometheus metrics endpoint: request rate, p50/p95 latency, error rate, LLM token usage, cache hit ratio
- NFR-OBS-3: Grafana dashboard MUST be provisioned via Docker Compose for local and production
- NFR-OBS-4: LLM provider latency MUST be tracked per provider (ollama, gemini, groq, openai, sambanova)
- NFR-OBS-5: Ingestion pipeline MUST report: files processed, rows inserted, errors, duration

### 7.2 Performance
- NFR-PERF-1: Chat p95 latency MUST be under 4.0s for cached/general queries
- NFR-PERF-2: Reproducibility bundle generation MUST complete within 30 seconds
- NFR-PERF-3: Report draft generation MUST complete within 60 seconds
- NFR-PERF-4: Knowledge graph traversal MUST return in under 500ms for 5-hop queries
- NFR-PERF-5: 3D visualization render MUST be interactive within 3 seconds for 10,000 points

### 7.3 Reliability
- NFR-REL-1: Provider failure auto-recovery rate MUST exceed 98%
- NFR-REL-2: Ingestion job restart success MUST exceed 95%
- NFR-REL-3: Zero critical errors in daily smoke checks for 14 consecutive days before any release

### 7.4 Scalability
- NFR-SCALE-1: System MUST support 1000 concurrent users
- NFR-SCALE-2: Knowledge graph MUST support up to 100,000 entity nodes without degradation
- NFR-SCALE-3: Snapshot storage MUST support up to 1,000 snapshots per workspace

### 7.5 Data Quality
- NFR-DQ-1: Every ARGO profile MUST have a computed `data_quality_score` (0.0–1.0) based on QC flags and coverage
- NFR-DQ-2: Data lineage MUST be traceable: source file → ingestion run → DB row → API response → chat answer
- NFR-DQ-3: Stale data indicators MUST appear in UI when ARGO data is >48 hours old

---

## 8. Success Metrics (KPIs)

| Metric | Current | Target (6 months) | Target (12 months) |
|---|---|---|---|
| Chat responses with confidence score | 0% | 100% | 100% |
| Responses with literature links | 0% | 70% | 90% |
| Reproducibility bundle downloads | 0 | 50/month | 500/month |
| Active research libraries (saved papers) | 0 | 200 | 2000 |
| Time-to-first-insight (new user) | >30 min | <10 min | <5 min |
| Student flashcards created | 0 | 500/month | 5000/month |
| Collaborative workspaces | 0 | 50 | 500 |
| Report drafts generated | 0 | 20/month | 200/month |
| API keys issued | 0 | 100 | 1000 |
| Test coverage (backend) | ~40% | 70% | 80% |

---

## 9. Architecture Additions Required

```
Current Stack (Phases A–E):
  Next.js → FastAPI → PostgreSQL + Redis + Qdrant
  Multi-LLM: Ollama, Gemini, Groq, SambaNova, OpenAI
  RAG: Qdrant vector + lexical fallback
  Auth: JWT
  Study: workspaces, notes, queries, compare, timeline
  Export: CSV, JSON, NetCDF
  BGC-ARGO, 10+ data source routers

New Components Required:
  1. Semantic Scholar API client         (ENT-002: literature)
  2. NetworkX knowledge graph            (ENT-007: graph reasoning)
  3. Answer verifier service             (ENT-001: reliability)
  4. Learning progress store             (ENT-003: flashcards/quizzes)
  5. Snapshot versioning engine          (ENT-004: reproducibility)
  6. nbformat notebook generator         (ENT-004, ENT-009)
  7. Report assembly service             (ENT-006: report builder)
  8. python-docx + PDF renderer          (ENT-006: export)
  9. Celery/RQ worker + Redis queue      (ENT-008: background jobs)
  10. Baseline + anomaly precomputation  (ENT-008: predictive)
  11. Prophet/statsmodels forecasting    (ENT-008)
  12. Three.js 3D visualization layer    (ENT-010)
  13. Prometheus + Grafana stack         (NFR-OBS)
  14. MFA / OAuth2 OIDC layer            (ENT-014)
  15. Collaboration tables + activity    (ENT-005)
  16. Classroom + assignment tables      (ENT-012)
  17. API key management                 (ENT-013)
  18. Audit log (hash-chained)           (ENT-014)
  19. PWA service worker                 (ENT-015)
  20. floatchat-sdk Python package       (ENT-009, ENT-013)
```

---

## 10. Implementation Roadmap

### Sprint 1 (Weeks 1–2): Trust & Reliability
- ENT-001: Scientific answer reliability engine
- ENT-014: Password reset (TBD-2 from SRS), MFA TOTP
- NFR-OBS: Prometheus metrics + trace IDs

### Sprint 2 (Weeks 3–4): Literature Bridge
- ENT-002: Semantic Scholar integration + Research Library UI
- ENT-004: Workspace snapshot versioning + basic reproducibility bundle

### Sprint 3 (Weeks 5–6): Learning Platform
- ENT-003: Adaptive learning module (flashcards, quizzes, learning mode)
- ENT-003: Learning progress tracking and concept map

### Sprint 4 (Weeks 7–8): Collaboration
- ENT-005: Shared workspaces (invite, roles, comments, activity feed)
- ENT-005: Public shareable workspace URLs

### Sprint 5 (Weeks 9–12): Output Generation
- ENT-006: Report builder (Markdown + Word + PDF export)
- ENT-009: Jupyter notebook + R script generation from snapshots

### Sprint 6 (Weeks 13–16): Intelligence Upgrade
- ENT-007: Ocean Knowledge Graph (entities, relationships, concept explorer)
- ENT-008: Seasonal baselines + anomaly detection + marine heatwave events

### Sprint 7 (Weeks 17–20): Visualization & Fusion
- ENT-010: 3D visualization (depth curtain, trajectory, T-S diagram)
- ENT-011: Multi-dataset fusion layer (ARGO + NOAA SST + climate indices)

### Sprint 8 (Weeks 21–24): Platform APIs
- ENT-009: Python SDK (`floatchat-sdk`)
- ENT-013: Public API keys + rate limits + webhooks

### Sprint 9 (Weeks 25–32): Educator & Enterprise
- ENT-012: Classroom mode (assignments, submissions, LTI 1.3)
- ENT-014: OAuth2/OIDC SSO + audit log hardening
- ENT-015: PWA + mobile optimization

---

## 11. Open Questions / TBD

1. Should the knowledge graph use NetworkX (in-memory, simpler) or Neo4j (persistent, scalable)?
2. Should report PDF use WeasyPrint (pure Python) or headless Chrome?
3. Should forecasting use Prophet (Facebook, interpretable) or LSTM (more accurate for ocean data)?
4. What journal citation format should be default for the LaTeX template?
5. Should classroom mode integrate with specific LMS (Canvas first) or be standalone?
6. Should the Python SDK be published to PyPI under the `floatchat` namespace?

---

*Document maintained in: `floatchat-docs/ENTERPRISE_PRD.md`*  
*Next review: After Sprint 2 completion*  
*Owner: Project Engineering Team*
