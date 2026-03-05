from __future__ import annotations

import importlib
import sqlite3
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


def _seed_database(db_file: Path) -> None:
    conn = sqlite3.connect(str(db_file))
    cur = conn.cursor()
    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS argo_floats (
            id INTEGER PRIMARY KEY,
            wmo_number TEXT,
            platform_type TEXT,
            deployment_date TEXT,
            last_location_date TEXT,
            last_latitude REAL,
            last_longitude REAL,
            status TEXT,
            program TEXT,
            ocean_basin TEXT
        );

        CREATE TABLE IF NOT EXISTS argo_profiles (
            id INTEGER PRIMARY KEY,
            float_id INTEGER,
            wmo_number TEXT,
            cycle_number INTEGER,
            profile_date TEXT,
            latitude REAL,
            longitude REAL,
            position_qc TEXT,
            data_mode TEXT
        );

        CREATE TABLE IF NOT EXISTS argo_measurements (
            id INTEGER PRIMARY KEY,
            profile_id INTEGER,
            pressure REAL,
            depth REAL,
            temperature REAL,
            temperature_qc INTEGER,
            salinity REAL,
            salinity_qc INTEGER
        );

        CREATE TABLE IF NOT EXISTS argo_stats (
            total_floats INTEGER,
            active_floats INTEGER,
            inactive_floats INTEGER,
            total_profiles INTEGER,
            earliest_profile TEXT,
            latest_profile TEXT,
            ocean_basin_count INTEGER,
            total_measurements INTEGER,
            avg_temperature REAL,
            avg_salinity REAL
        );

        CREATE TABLE IF NOT EXISTS bgc_profiles (
            id INTEGER PRIMARY KEY,
            wmo_number TEXT NOT NULL,
            cycle_number INTEGER,
            profile_date TEXT,
            latitude REAL,
            longitude REAL,
            chlorophyll REAL,
            nitrate REAL,
            oxygen REAL,
            ph REAL,
            source_file TEXT
        );
        """
    )

    cur.execute("DELETE FROM argo_floats")
    cur.execute("DELETE FROM argo_profiles")
    cur.execute("DELETE FROM argo_measurements")
    cur.execute("DELETE FROM argo_stats")
    cur.execute("DELETE FROM bgc_profiles")

    cur.execute(
        """
        INSERT INTO argo_floats (
            id, wmo_number, platform_type, deployment_date, last_location_date,
            last_latitude, last_longitude, status, program, ocean_basin
        )
        VALUES (1, '2900001', 'APEX', '2024-01-01', '2024-01-11', -12.5, 67.2, 'ACTIVE', 'ARGO', 'Indian Ocean')
        """
    )
    cur.execute(
        """
        INSERT INTO argo_profiles (
            id, float_id, wmo_number, cycle_number, profile_date, latitude, longitude, position_qc, data_mode
        )
        VALUES (1, 1, '2900001', 1, '2024-01-11T00:00:00', -12.5, 67.2, '1', 'D')
        """
    )
    cur.execute(
        """
        INSERT INTO argo_measurements (
            id, profile_id, pressure, depth, temperature, temperature_qc, salinity, salinity_qc
        )
        VALUES (1, 1, 50.0, 50.0, 22.4, 1, 35.1, 1)
        """
    )
    cur.execute(
        """
        INSERT INTO argo_stats (
            total_floats, active_floats, inactive_floats, total_profiles,
            earliest_profile, latest_profile, ocean_basin_count, total_measurements, avg_temperature, avg_salinity
        )
        VALUES (1, 1, 0, 1, '2024-01-11T00:00:00', '2024-01-11T00:00:00', 1, 1, 22.4, 35.1)
        """
    )
    cur.execute(
        """
        INSERT INTO bgc_profiles (
            id, wmo_number, cycle_number, profile_date, latitude, longitude,
            chlorophyll, nitrate, oxygen, ph, source_file
        )
        VALUES (1, '2900001', 1, '2024-01-11T00:00:00', -12.5, 67.2, 0.55, 4.2, 190.0, 8.05, 'R2900001_001.nc')
        """
    )
    conn.commit()
    conn.close()


@pytest.fixture()
def client(tmp_path, monkeypatch):
    db_file = tmp_path / "integration.db"
    _seed_database(db_file)
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_file.as_posix()}")
    monkeypatch.setenv("ADMIN_API_KEY", "test-admin-key")

    import routers.argo_filter as argo_filter
    import routers.export as export_router
    import routers.tools as tools_router
    import llm.chat_service as chat_service
    import main as main_module

    importlib.reload(argo_filter)
    importlib.reload(export_router)
    importlib.reload(tools_router)
    importlib.reload(chat_service)
    main_module = importlib.reload(main_module)

    class StubChatService:
        def process_query(self, query, provider="auto"):
            return {
                "success": True,
                "response": f"stub response for {query}",
                "sql_query": None,
                "data": [],
                "row_count": 0,
                "source": provider if provider != "auto" else "openai",
                "query_type": "general" if "what is" in query.lower() else "data",
                "intent": "general_explanation" if "what is" in query.lower() else "data_lookup",
                "intent_confidence": 0.8,
                "confidence": 0.85,
                "evidence_score": 0.82,
                "evidence_coverage_score": 0.78,
                "method": "Stubbed method path for integration testing.",
                "data_source": ["argo_floats", "argo_profiles"],
                "limitations": ["Stub response for test validation."],
                "next_checks": ["Run real provider in e2e environment."],
                "reliability_warnings": [],
                "provider_metrics": [
                    {"provider": provider if provider != "auto" else "openai", "latency_ms": 10.2, "success": True}
                ],
                "sources": [
                    {
                        "title": "Argo Overview",
                        "source": "https://argo.ucsd.edu/",
                        "snippet": "Argo is a global profiling float network.",
                    }
                ],
                "cached": False,
            }

        def get_available_providers(self):
            return ["ollama", "openai"]

        def health_check(self):
            return {
                "ollama": {"available": True, "status": "healthy"},
                "openai": {"available": True, "status": "healthy"},
                "gemini": {"available": False, "status": "unavailable"},
                "rag": {"available": True, "status": "lexical"},
            }

    monkeypatch.setattr(chat_service, "HybridChatService", StubChatService)

    with TestClient(main_module.app) as test_client:
        yield test_client


def test_health_and_summary_routes(client: TestClient):
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "healthy"
    assert health.headers.get("x-request-id")

    summary = client.get("/api/v1/argo/stats/summary")
    assert summary.status_code == 200
    body = summary.json()
    assert body["total_floats"] == 1
    assert body["total_profiles"] == 1


def test_chat_providers_and_chat_response_with_sources(client: TestClient):
    providers = client.get("/api/chat/providers")
    assert providers.status_code == 200
    payload = providers.json()
    assert "openai" in payload["providers"]
    assert payload["health"]["rag"]["available"] is True

    chat = client.post("/api/chat", json={"message": "What is salinity?", "provider": "openai"})
    assert chat.status_code == 200
    result = chat.json()
    assert result["success"] is True
    assert result["source"] == "openai"
    assert result["sources"]
    assert result["sources"][0]["title"] == "Argo Overview"
    assert result["intent"] == "general_explanation"
    assert result["evidence_score"] >= 0.7
    assert result["evidence_coverage_score"] >= 0.7
    assert result["method"]
    assert result["data_source"]
    assert result["limitations"]
    assert result["next_checks"]
    assert result["provider_metrics"]


def test_invalid_provider_is_rejected(client: TestClient):
    response = client.post("/api/chat", json={"message": "hello", "provider": "invalid-provider"})
    assert response.status_code == 400
    assert "Invalid provider" in response.json()["detail"]


def test_tools_routes(client: TestClient):
    glossary = client.get("/api/v1/tools/glossary?limit=5")
    assert glossary.status_code == 200
    assert isinstance(glossary.json(), list)
    assert len(glossary.json()) <= 5

    insights = client.get("/api/v1/tools/learn/insights")
    assert insights.status_code == 200
    assert isinstance(insights.json(), list)
    assert len(insights.json()) >= 1


def test_auth_study_workspace_compare_timeline_flow(client: TestClient):
    register = client.post(
        "/api/v1/auth/register",
        json={
            "email": "researcher@example.com",
            "username": "researcher1",
            "password": "strong-pass-123",
            "full_name": "Ocean Researcher",
        },
    )
    assert register.status_code == 200
    register_body = register.json()
    token = register_body["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    me = client.get("/api/v1/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["username"] == "researcher1"

    workspace = client.post(
        "/api/v1/study/workspaces",
        json={"name": "Indian Ocean Study", "description": "Phase D flow"},
        headers=headers,
    )
    assert workspace.status_code == 200
    workspace_id = workspace.json()["id"]

    listed_workspaces = client.get("/api/v1/study/workspaces", headers=headers)
    assert listed_workspaces.status_code == 200
    assert any(ws["id"] == workspace_id for ws in listed_workspaces.json())

    note = client.post(
        f"/api/v1/study/workspaces/{workspace_id}/notes",
        json={"content": "QC <= 2 keeps high-confidence measurements."},
        headers=headers,
    )
    assert note.status_code == 200
    note_id = note.json()["id"]

    listed_notes = client.get(f"/api/v1/study/workspaces/{workspace_id}/notes", headers=headers)
    assert listed_notes.status_code == 200
    assert any(n["id"] == note_id for n in listed_notes.json())

    note_search = client.get(
        f"/api/v1/study/workspaces/{workspace_id}/notes/search?q=high-confidence",
        headers=headers,
    )
    assert note_search.status_code == 200
    assert any(n["id"] == note_id for n in note_search.json())

    saved_query = client.post(
        f"/api/v1/study/workspaces/{workspace_id}/queries",
        json={
            "name": "Indian QC filter",
            "query_payload": {"region": "indian", "qc_max": 2},
        },
        headers=headers,
    )
    assert saved_query.status_code == 200

    query_list = client.get(f"/api/v1/study/workspaces/{workspace_id}/queries", headers=headers)
    assert query_list.status_code == 200
    assert any(q["name"] == "Indian QC filter" for q in query_list.json())

    compare = client.post(
        "/api/v1/study/compare/run",
        json={
            "region_a": "indian",
            "region_b": "global",
            "bbox_a": {"min_lon": 30, "min_lat": -40, "max_lon": 120, "max_lat": 30},
            "workspace_id": workspace_id,
            "save_session": True,
        },
        headers=headers,
    )
    assert compare.status_code == 200
    compare_body = compare.json()
    assert compare_body["floats_a"] >= 1
    assert compare_body["delta_profiles"] >= 0
    assert "statistics" in compare_body
    assert "temperature" in compare_body["statistics"]
    assert "available" in compare_body["statistics"]["temperature"]

    compare_history = client.get(f"/api/v1/study/compare/history?workspace_id={workspace_id}", headers=headers)
    assert compare_history.status_code == 200
    assert len(compare_history.json()) >= 1

    timeline = client.post(
        "/api/v1/study/timeline/profiles",
        json={
            "bbox": {"min_lon": 30, "min_lat": -40, "max_lon": 120, "max_lat": 30},
            "workspace_id": workspace_id,
            "label": "Indian monthly timeline",
        },
        headers=headers,
    )
    assert timeline.status_code == 200
    assert timeline.json()["points"] >= 1

    timeline_history = client.get(f"/api/v1/study/timeline/history?workspace_id={workspace_id}", headers=headers)
    assert timeline_history.status_code == 200
    assert len(timeline_history.json()) >= 1

    dashboard = client.get(f"/api/v1/study/workspaces/{workspace_id}/dashboard", headers=headers)
    assert dashboard.status_code == 200
    dashboard_body = dashboard.json()
    assert dashboard_body["counts"]["notes"] >= 1
    assert dashboard_body["counts"]["saved_queries"] >= 1
    assert dashboard_body["counts"]["compare_sessions"] >= 1
    assert dashboard_body["counts"]["timeline_runs"] >= 1

    snapshot = client.get(f"/api/v1/study/workspaces/{workspace_id}/snapshot", headers=headers)
    assert snapshot.status_code == 200
    snapshot_body = snapshot.json()
    assert snapshot_body["workspace"]["id"] == workspace_id
    assert len(snapshot_body["notes"]) >= 1
    assert len(snapshot_body["saved_queries"]) >= 1
    assert len(snapshot_body["compare_history"]) >= 1
    assert len(snapshot_body["timeline_history"]) >= 1

    clone = client.post(
        f"/api/v1/study/workspaces/{workspace_id}/clone",
        json={
            "name": "Indian Ocean Study Copy",
            "include_notes": True,
            "include_queries": True,
        },
        headers=headers,
    )
    assert clone.status_code == 200
    clone_body = clone.json()
    cloned_workspace_id = clone_body["id"]
    assert clone_body["notes_cloned"] >= 1
    assert clone_body["queries_cloned"] >= 1

    clone_notes = client.get(f"/api/v1/study/workspaces/{cloned_workspace_id}/notes", headers=headers)
    assert clone_notes.status_code == 200
    assert len(clone_notes.json()) >= 1

    clone_queries = client.get(f"/api/v1/study/workspaces/{cloned_workspace_id}/queries", headers=headers)
    assert clone_queries.status_code == 200
    assert len(clone_queries.json()) >= 1

    create_version = client.post(
        f"/api/v1/study/workspaces/{workspace_id}/versions",
        json={
            "label": "Baseline v1",
            "include_notes": True,
            "include_queries": True,
            "include_compare_history": True,
            "include_timeline_history": True,
            "history_limit": 50,
        },
        headers=headers,
    )
    assert create_version.status_code == 200
    version_body = create_version.json()
    version_id = version_body["id"]
    assert version_body["counts"]["notes"] >= 1
    assert version_body["counts"]["saved_queries"] >= 1

    version_list = client.get(f"/api/v1/study/workspaces/{workspace_id}/versions?limit=10", headers=headers)
    assert version_list.status_code == 200
    assert any(version["id"] == version_id for version in version_list.json())

    version_detail = client.get(
        f"/api/v1/study/workspaces/{workspace_id}/versions/{version_id}",
        headers=headers,
    )
    assert version_detail.status_code == 200
    assert version_detail.json()["snapshot"]["workspace"]["id"] == workspace_id

    repro_package = client.get(
        f"/api/v1/study/workspaces/{workspace_id}/repro-package?version_id={version_id}",
        headers=headers,
    )
    assert repro_package.status_code == 200
    repro_body = repro_package.json()
    assert repro_body["metadata"]["workspace_id"] == workspace_id
    assert repro_body["metadata"]["counts"]["notes"] >= 1

    notebook_python = client.get(
        f"/api/v1/study/workspaces/{workspace_id}/notebook-template?language=python&version_id={version_id}",
        headers=headers,
    )
    assert notebook_python.status_code == 200
    notebook_python_body = notebook_python.json()
    assert notebook_python_body["format"] == "ipynb"
    assert notebook_python_body["filename"].endswith(".ipynb")

    notebook_r = client.get(
        f"/api/v1/study/workspaces/{workspace_id}/notebook-template?language=r",
        headers=headers,
    )
    assert notebook_r.status_code == 200
    notebook_r_body = notebook_r.json()
    assert notebook_r_body["format"] == "r_script"
    assert notebook_r_body["filename"].endswith(".R")

    restore_preview = client.post(
        f"/api/v1/study/workspaces/{workspace_id}/versions/{version_id}/restore",
        json={"dry_run": True},
        headers=headers,
    )
    assert restore_preview.status_code == 200
    assert restore_preview.json()["dry_run"] is True

    async_job = client.post(
        f"/api/v1/study/workspaces/{workspace_id}/repro-package/jobs",
        json={"version_id": version_id},
        headers=headers,
    )
    assert async_job.status_code == 200
    job_id = async_job.json()["id"]

    final_status = None
    for _ in range(15):
        job_state = client.get(f"/api/v1/study/workspaces/{workspace_id}/jobs/{job_id}", headers=headers)
        assert job_state.status_code == 200
        body = job_state.json()
        final_status = body["status"]
        if final_status in {"completed", "failed"}:
            break
        time.sleep(0.05)
    assert final_status in {"completed", "failed"}

    jobs_list = client.get(f"/api/v1/study/workspaces/{workspace_id}/jobs?limit=10", headers=headers)
    assert jobs_list.status_code == 200
    assert any(job["id"] == job_id for job in jobs_list.json())

    collaborator = client.post(
        "/api/v1/auth/register",
        json={
            "email": "collaborator@example.com",
            "username": "collab1",
            "password": "strong-pass-123",
            "full_name": "Collaborator User",
        },
    )
    assert collaborator.status_code == 200
    collaborator_token = collaborator.json()["access_token"]
    collaborator_headers = {"Authorization": f"Bearer {collaborator_token}"}

    add_member = client.post(
        f"/api/v1/study/workspaces/{workspace_id}/members",
        json={"user_identifier": "collab1", "role": "viewer"},
        headers=headers,
    )
    assert add_member.status_code == 200
    assert add_member.json()["role"] == "viewer"

    members = client.get(f"/api/v1/study/workspaces/{workspace_id}/members", headers=headers)
    assert members.status_code == 200
    assert any(member["user_id"] == add_member.json()["user_id"] for member in members.json())

    collab_workspaces = client.get("/api/v1/study/workspaces", headers=collaborator_headers)
    assert collab_workspaces.status_code == 200
    assert any(ws["id"] == workspace_id for ws in collab_workspaces.json())

    collab_note_forbidden = client.post(
        f"/api/v1/study/workspaces/{workspace_id}/notes",
        json={"content": "Viewer should not write."},
        headers=collaborator_headers,
    )
    assert collab_note_forbidden.status_code == 403

    promote_member = client.patch(
        f"/api/v1/study/workspaces/{workspace_id}/members/{add_member.json()['user_id']}",
        json={"role": "editor", "status": "active"},
        headers=headers,
    )
    assert promote_member.status_code == 200

    collab_note_ok = client.post(
        f"/api/v1/study/workspaces/{workspace_id}/notes",
        json={"content": "Editor can write now."},
        headers=collaborator_headers,
    )
    assert collab_note_ok.status_code == 200

    delete_note = client.delete(f"/api/v1/study/notes/{note_id}", headers=headers)
    assert delete_note.status_code == 200
    assert delete_note.json()["success"] is True


def test_bgc_routes(client: TestClient):
    summary = client.get("/api/v1/bgc/stats/summary")
    assert summary.status_code == 200
    assert summary.json()["total_profiles"] >= 1

    filtered = client.post(
        "/api/v1/bgc/profiles/filter",
        json={
            "bbox": {"min_lon": 30, "min_lat": -40, "max_lon": 120, "max_lat": 30},
            "parameter": "chlorophyll",
            "limit": 10,
            "offset": 0,
        },
    )
    assert filtered.status_code == 200
    body = filtered.json()
    assert body["total"] >= 1
    assert body["data"][0]["wmo_number"] == "2900001"

    dry_clear = client.delete("/api/v1/bgc/profiles")
    assert dry_clear.status_code == 200
    assert dry_clear.json()["deleted"] == 0

    clear = client.delete("/api/v1/bgc/profiles?confirm=true")
    assert clear.status_code == 200
    assert clear.json()["deleted"] >= 1


def test_argo_ingestion_status_and_dry_run(client: TestClient):
    status = client.get("/api/v1/argo/ingestion/status")
    assert status.status_code == 200
    body = status.json()
    assert "job" in body
    assert "jobs" in body
    assert body["dataset"]["total_floats"] >= 1

    jobs = client.get("/api/v1/argo/ingestion/jobs?limit=5")
    assert jobs.status_code == 200
    assert isinstance(jobs.json(), list)

    dry_run = client.post(
        "/api/v1/argo/ingestion/run",
        json={
            "region": "indian",
            "index_limit": 10,
            "max_profiles": 5,
            "dry_run": True,
        },
    )
    assert dry_run.status_code == 200
    dry_body = dry_run.json()
    assert dry_body["dry_run"] is True
    assert dry_body["config"]["region"] == "indian"


def test_chat_rejects_blank_message(client: TestClient):
    response = client.post("/api/chat", json={"message": "   ", "provider": "auto"})
    assert response.status_code == 400
    assert response.json()["detail"] == "Message is required"


def test_filter_validations_reject_invalid_ranges(client: TestClient):
    bad_bbox = client.post(
        "/api/v1/argo/floats/filter",
        json={
            "bbox": {"min_lon": 120, "min_lat": -40, "max_lon": 30, "max_lat": 30},
            "limit": 10,
            "offset": 0,
        },
    )
    assert bad_bbox.status_code == 422

    bad_bgc_date = client.post(
        "/api/v1/bgc/profiles/filter",
        json={
            "start_date": "2024-12-31T00:00:00",
            "end_date": "2024-01-01T00:00:00",
            "limit": 10,
            "offset": 0,
        },
    )
    assert bad_bgc_date.status_code == 422


def test_study_compare_rejects_invalid_date_range(client: TestClient):
    register = client.post(
        "/api/v1/auth/register",
        json={
            "email": "validator@example.com",
            "username": "validator1",
            "password": "strong-pass-123",
            "full_name": "Validation User",
        },
    )
    assert register.status_code == 200
    token = register.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post(
        "/api/v1/study/compare/run",
        json={
            "region_a": "indian",
            "region_b": "global",
            "start_date": "2024-12-31T00:00:00",
            "end_date": "2024-01-01T00:00:00",
        },
        headers=headers,
    )
    assert response.status_code == 422


def test_admin_metrics_summary(client: TestClient):
    chat = client.post("/api/chat", json={"message": "What is salinity?", "provider": "openai"})
    assert chat.status_code == 200

    metrics = client.get(
        "/api/admin/metrics/summary?window_minutes=60&include_recent_events=5",
        headers={"X-Admin-Key": "test-admin-key"},
    )
    assert metrics.status_code == 200
    body = metrics.json()
    assert body["chat"]["total_requests"] >= 1
    assert body["chat"]["cache_hit_rate"] is not None
    assert body["chat"]["latency_ms"]["avg"] is not None
    assert isinstance(body["chat"]["recent_events"], list)
    assert body["database"]["connected"] is True
    assert "ingestion" in body

    slo = client.get("/api/admin/metrics/slo?window_minutes=60", headers={"X-Admin-Key": "test-admin-key"})
    assert slo.status_code == 200
    assert "checks" in slo.json()

    prometheus = client.get("/api/admin/metrics/prometheus?window_minutes=60", headers={"X-Admin-Key": "test-admin-key"})
    assert prometheus.status_code == 200
    assert "floatchat_chat_requests_total" in prometheus.text


def test_admin_metrics_requires_key_when_enabled(client: TestClient):
    metrics = client.get("/api/admin/metrics/summary?window_minutes=60")
    assert metrics.status_code == 401
    slo = client.get("/api/admin/metrics/slo?window_minutes=60")
    assert slo.status_code == 401
    prometheus = client.get("/api/admin/metrics/prometheus?window_minutes=60")
    assert prometheus.status_code == 401
