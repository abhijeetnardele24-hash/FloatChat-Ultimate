# FloatChat Power-Up Master Plan (Post-Phase-E)

Date: February 20, 2026
Author: Project planning update based on current docs and implemented scope

## 1. Why this plan exists

Current documentation indicates that the defined scope through Phase E is completed for the existing implementation baseline (routing, chat, RAG, auth, study workflows, export, CI, runbooks).  
This plan defines what to build next to make FloatChat significantly more powerful, impressive, and research-grade.

## 2. Source documents reviewed

- `floatchat-ultimate/README.md`
- `floatchat-ultimate/backend/README.md`
- `floatchat-docs/task.md`
- `floatchat-docs/implementation_plan.md`
- `floatchat-docs/project_structure.md`
- `floatchat-docs/tech_stack_guide.md`
- `floatchat-docs/ocean_study_super_project_plan.md`
- `floatchat-ultimate/docs/runbooks/production-deployment.md`
- `floatchat-ultimate/docs/runbooks/validation-and-ci.md`
- `floatchat-ultimate/docs/runbooks/rag-ingestion.md`

## 3. Strategic direction

FloatChat should evolve into a research copilot platform with:

1. Trustworthy scientific intelligence
2. Multi-dataset ocean data fusion
3. Real-time and predictive analysis
4. Collaboration and reproducibility by default
5. Production reliability and observability

## 4. High-impact capability upgrades

### A. Intelligence and AI (highest value)

1. Multi-agent orchestration layer
- Add orchestrator + specialist agents: SQL, domain expert, visualization, QA.
- Include chain-of-verification before final response.

2. Scientific answer reliability scoring
- Return confidence score, evidence coverage score, and contradiction warnings.
- Add "insufficient evidence" fallback instead of hallucinated answers.

3. Query planning with semantic intent graph
- Convert user requests into typed intents: explain, compare, detect anomaly, forecast, export.
- Use intent to choose best provider/tool path automatically.

4. Method-aware response templates
- Add response sections: "Method", "Data Source", "Limitations", "Next Checks".

### B. Data and ocean science depth

1. Data fusion layer
- Combine ARGO + BGC-ARGO + satellite + climate indices into a unified query surface.

2. Automated ingestion orchestration
- Move ingestion from manual scripts to scheduled workflows with retries and checkpoints.
- Add dead-letter and partial-failure recovery for files.

3. Data quality and lineage framework
- Quality score per profile, trace lineage from source file to answer payload.
- Expose lineage in API and study snapshots.

4. Time-series and anomaly pipelines
- Precompute seasonal baselines, anomalies, trend decomposition, and heatwave detection.

### C. Study tools and researcher productivity

1. Study versioning and reproducibility bundles
- Version each workspace state (notes, filters, queries, timeline, compare runs).
- One-click "repro package" export with metadata and citation block.

2. Team collaboration mode
- Shared workspaces, comments, review threads, role-based permissions.
- Activity timeline: who changed what and when.

3. Notebook and script interoperability
- Generate Python/R notebook templates from saved workspace snapshots.

4. Advanced compare lab
- Statistical tests, effect size summaries, and confidence intervals for region comparisons.

### D. Visualization and UX differentiation

1. 3D ocean scene mode
- Depth curtain, volumetric layers, trajectory animations, water-mass overlays.

2. Linked analysis workspace
- Brushing/selection in one chart updates all related views.

3. "Story mode" report builder
- Turn selected views + findings into publication-style narrative pages.

4. Accessibility + i18n completion
- Keyboard-first controls, contrast checks, translated UI string framework.

### E. Platform and production engineering

1. Full observability stack
- Request traces, provider latency, token usage, cache hit ratio, query failure diagnostics.

2. Security hardening
- MFA, SSO options, audit logging, row-level policy controls.

3. Performance program
- API p95 targets, DB query plans, background job throughput, frontend Core Web Vitals.

4. Developer platform APIs
- Public API keys/quotas, webhooks, SDKs, and API playground.

## 5. Prioritized roadmap (execution order)

## Phase P1 (0-6 weeks): Reliability + intelligence foundation

Goals:
- Make system trustworthy, measurable, and faster under load.

Deliverables:
1. Agent-ready intent router and query planner
2. Confidence/evidence scoring in chat responses
3. Full observability dashboard (API + LLM + ingestion)
4. Ingestion orchestration with job state persistence
5. Workspace versioning v1

Success metrics:
- Chat p95 latency under 4.0s for cached/general queries
- Provider failure auto-recovery over 98%
- Ingestion job restart success over 95%
- Zero critical errors in daily smoke checks for 14 days

## Phase P2 (6-16 weeks): Research workflow acceleration

Goals:
- Make FloatChat genuinely useful for daily researcher workflows.

Deliverables:
1. Shared workspaces with RBAC and activity feed
2. Advanced compare lab (stats + uncertainty)
3. Notebook export (Python/R) from snapshots
4. Linked visual analysis workspace
5. Story/report builder v1

Success metrics:
- Time-to-insight reduced by 40% (baseline user test)
- 70% of study sessions use saved or versioned workflows
- Report generation under 30 seconds for standard workspace

## Phase P3 (4-10 months): Multi-dataset and predictive intelligence

Goals:
- Move from descriptive to predictive and cross-source analysis.

Deliverables:
1. ARGO + BGC + satellite unified schema/query layer
2. Seasonal anomaly and trend forecasting modules
3. Event detection (marine heatwave, oxygen stress, bloom signals)
4. Model quality tracking and drift alerts

Success metrics:
- 3+ fused dataset workflows available in production
- Forecast MAE/MAPE targets defined and tracked per region
- Event detection precision/recall benchmarked and published internally

## Phase P4 (10-18 months): Platform ecosystem and autonomy

Goals:
- Transform FloatChat into a platform, not just an app.

Deliverables:
1. Plugin SDK and extension API
2. Public developer API + quotas + webhooks
3. Literature integration and citation graph assistance
4. Semi-autonomous research workflows with approval gates

Success metrics:
- External/internal plugin adoption (at least 10 active plugins)
- API usage by third-party scripts/notebooks
- At least 2 autonomous workflow templates with human approval controls

## 6. Technical architecture additions required

1. Workflow orchestrator
- Prefect or Dagster for ingestion and scheduled analytics.

2. Job queue and worker layer
- Celery/RQ with Redis or RabbitMQ for long-running workloads.

3. Time-series feature store
- Materialized tables/views for anomaly and forecast features.

4. Central telemetry store
- Prometheus + Grafana + structured logs + trace IDs end-to-end.

5. Policy and access engine
- RBAC + object-level access checks for workspace sharing.

## 7. Risk register and mitigations

1. LLM reliability risk
- Mitigation: response verification layer, evidence score, safe fallback templates.

2. Dataset ingestion instability
- Mitigation: checkpointed jobs, retries, checksum validation, dead-letter queue.

3. Cost creep from external providers
- Mitigation: Ollama-first routing, token budgets, provider quotas.

4. Product complexity overload
- Mitigation: phased release flags, strict acceptance criteria per phase.

## 8. Immediate next sprint plan (recommended)

Sprint 1 (2 weeks):
1. Implement intent router and response confidence schema.
2. Add provider/DB/ingestion latency dashboards and trace correlation IDs.
3. Finalize ingestion job persistence model.

Sprint 2 (2 weeks):
1. Workspace versioning and reproducibility export v1.
2. Advanced compare statistics (confidence intervals, significance tests).
3. Research report draft generator v1.

Sprint 3 (2 weeks):
1. Shared workspace RBAC base.
2. Notebook export templates.
3. Linked chart interactions in explorer + visualizations.

## 9. Definition of "more powerful" for FloatChat

FloatChat is considered next-level when:

1. It answers with evidence, confidence, and explicit limitations.
2. It supports end-to-end research lifecycle: ingest -> analyze -> compare -> report -> reproduce.
3. It handles multi-source ocean data, not only one dataset family.
4. It is stable and observable in production with measured SLOs.
5. Teams can collaborate safely with full history and permissions.

## 10. Final recommendation

Execute P1 immediately, then P2 without delay.  
P1 + P2 combined deliver the strongest jump in real user value and product impression while keeping engineering risk controlled.
