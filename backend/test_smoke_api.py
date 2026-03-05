"""
Basic smoke test for core backend endpoints used in the Ollama + ARGO workflow.

Run:
    python test_smoke_api.py
"""

from __future__ import annotations

import sys
import requests

BASE_URL = "http://localhost:8000"
TIMEOUT_SECONDS = 10


def fail(message: str) -> None:
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def get_json(path: str) -> dict:
    url = f"{BASE_URL}{path}"
    response = requests.get(url, timeout=TIMEOUT_SECONDS)
    if response.status_code >= 400:
        fail(f"GET {path} returned HTTP {response.status_code}: {response.text[:200]}")
    try:
        return response.json()
    except Exception as exc:
        fail(f"GET {path} returned non-JSON response: {exc}")
    return {}


def post(path: str, payload: dict):
    url = f"{BASE_URL}{path}"
    response = requests.post(url, json=payload, timeout=TIMEOUT_SECONDS)
    if response.status_code >= 400:
        fail(f"POST {path} returned HTTP {response.status_code}: {response.text[:200]}")
    return response


def main() -> None:
    print("Running backend smoke checks...")

    health = get_json("/health")
    if health.get("status") != "healthy":
        fail(f"/health status not healthy: {health}")
    print(f"[OK] /health -> {health.get('status')}")

    providers = get_json("/api/chat/providers")
    if "providers" not in providers or "health" not in providers:
        fail(f"/api/chat/providers missing keys: {providers}")
    print(f"[OK] /api/chat/providers -> providers={providers.get('providers', [])}")

    argo_summary = get_json("/api/v1/argo/stats/summary")
    required_keys = {"total_floats", "active_floats", "total_profiles"}
    if not required_keys.issubset(argo_summary.keys()):
        fail(f"/api/v1/argo/stats/summary missing required keys: {argo_summary}")
    print(
        "[OK] /api/v1/argo/stats/summary -> "
        f"floats={argo_summary.get('total_floats')} profiles={argo_summary.get('total_profiles')}"
    )

    insights = get_json("/api/v1/tools/learn/insights")
    if not isinstance(insights, list):
        fail(f"/api/v1/tools/learn/insights expected list, got: {type(insights)}")
    print(f"[OK] /api/v1/tools/learn/insights -> {len(insights)} insight items")

    export_payload = {
        "bbox": {
            "min_lon": 30,
            "min_lat": -40,
            "max_lon": 120,
            "max_lat": 30,
        },
        "limit": 100,
        "offset": 0,
    }
    export_response = post("/api/v1/export/floats/csv?export_limit=100", export_payload)
    content_type = export_response.headers.get("content-type", "")
    if "text/csv" not in content_type:
        fail(f"/api/v1/export/floats/csv unexpected content-type: {content_type}")
    print("[OK] /api/v1/export/floats/csv -> csv stream")

    netcdf_payload = {
        "qc_max": 2,
        "limit": 100,
        "offset": 0,
    }
    netcdf_response = post("/api/v1/export/measurements/netcdf?export_limit=100", netcdf_payload)
    netcdf_type = netcdf_response.headers.get("content-type", "")
    if "application/x-netcdf" not in netcdf_type:
        fail(f"/api/v1/export/measurements/netcdf unexpected content-type: {netcdf_type}")
    print("[OK] /api/v1/export/measurements/netcdf -> netcdf stream")

    print("All smoke checks passed.")


if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.RequestException as exc:
        fail(f"Request failed: {exc}")
    except KeyboardInterrupt:
        print("Interrupted.")
        sys.exit(130)
