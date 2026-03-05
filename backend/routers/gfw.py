"""
Global Fishing Watch API Router
Provides access to global fishing vessel tracking and fishing effort data.
Free for research and non-commercial use - requires free API key registration.

Register at: https://globalfishingwatch.org/our-apis/
"""

from __future__ import annotations

import os
import logging
from typing import Any, Dict, List, Optional

import httpx
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/gfw", tags=["global-fishing-watch"])

_TIMEOUT = httpx.Timeout(30.0, connect=10.0)
_GFW_BASE = "https://gateway.api.globalfishingwatch.org"


def _headers() -> Dict[str, str]:
    h: Dict[str, str] = {"Content-Type": "application/json"}
    key = (os.getenv("GFW_API_KEY") or "").strip()
    if key:
        h["Authorization"] = f"Bearer {key}"
    return h


async def _get(path: str, params: Optional[Dict[str, Any]] = None) -> Any:
    """Make GET request to Global Fishing Watch API."""
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            url = f"{_GFW_BASE}{path}"
            resp = await client.get(url, params=params, headers=_headers())
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPStatusError as exc:
        logger.error("GFW API error: %s", exc)
        raise HTTPException(status_code=502, detail=f"GFW API error: {exc}")
    except httpx.RequestError as exc:
        logger.error("GFW request failed: %s", exc)
        raise HTTPException(status_code=502, detail=f"GFW unreachable: {exc}")


async def _post(path: str, data: Dict[str, Any]) -> Any:
    """Make POST request to Global Fishing Watch API."""
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            url = f"{_GFW_BASE}{path}"
            resp = await client.post(url, json=data, headers=_headers())
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPStatusError as exc:
        logger.error("GFW API error: %s", exc)
        raise HTTPException(status_code=502, detail=f"GFW API error: {exc}")
    except httpx.RequestError as exc:
        logger.error("GFW request failed: %s", exc)
        raise HTTPException(status_code=502, detail=f"GFW unreachable: {exc}")


@router.get("/ping")
async def gfw_ping():
    """Health check for Global Fishing Watch API."""
    has_key = bool((os.getenv("GFW_API_KEY") or "").strip())
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
            url = f"{_GFW_BASE}/v3/datasets"
            resp = await client.get(url, headers=_headers())
            ok = resp.status_code == 200
            return {
                "ok": ok,
                "status_code": resp.status_code,
                "has_api_key": has_key,
            }
    except Exception as e:
        return {"ok": False, "has_api_key": has_key, "error": str(e)}


@router.get("/datasets")
async def list_datasets(
    limit: int = Query(20, ge=1, le=100),
):
    """
    List available Global Fishing Watch datasets.

    Requires GFW_API_KEY environment variable.
    """
    data = await _get("/v3/datasets", {"limit": limit})
    return data


@router.get("/datasets/{dataset_id}")
async def get_dataset_info(
    dataset_id: str,
):
    """Get information about a specific dataset."""
    data = await _get(f"/v3/datasets/{dataset_id}")
    return data


@router.get("/fishing-effort")
async def get_fishing_effort(
    dataset: str = Query("public-fishing-effort:v1", description="Dataset ID"),
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    vessel_ids: Optional[str] = Query(None, description="Comma-separated vessel IDs"),
    region_id: Optional[str] = Query(None, description="Region ID"),
    spatial_resolution: str = Query(
        "1deg", description="Spatial resolution: 1deg, 0.25deg"
    ),
    temporal_resolution: str = Query(
        "monthly", description="Temporal resolution: daily, monthly, yearly"
    ),
):
    """
    Get fishing effort data for a time period and area.

    Example: /fishing-effort?start_date=2024-01&end_date=2024-12&spatial_resolution=1deg&temporal_resolution=monthly
    """
    params: Dict[str, Any] = {
        "dataset": dataset,
        "startDate": start_date,
        "endDate": end_date,
        "spatialResolution": spatial_resolution,
        "temporalResolution": temporal_resolution,
    }

    if vessel_ids:
        params["vesselIds"] = vessel_ids
    if region_id:
        params["regionId"] = region_id

    data = await _get("/v3/fishing-effort", params)
    return data


@router.get("/vessels/search")
async def search_vessels(
    query: str = Query(..., description="Search query (vessel name, IMO, MMSI)"),
    limit: int = Query(10, ge=1, le=50),
):
    """
    Search for vessels by name, IMO number, or MMSI.

    Example: /vessels/search?query=ocean&limit=10
    """
    params = {
        "query": query,
        "limit": limit,
    }
    data = await _get("/v3/vessels/search", params)
    return data


@router.get("/vessels/{vessel_id}")
async def get_vessel_info(
    vessel_id: str,
):
    """Get detailed information about a vessel."""
    data = await _get(f"/v3/vessels/{vessel_id}")
    return data


@router.get("/vessels/{vessel_id}/tracks")
async def get_vessel_tracks(
    vessel_id: str,
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
):
    """
    Get vessel track/positions for a time period.

    Example: /vessels/123/tracks?start_date=2024-01-01&end_date=2024-01-31
    """
    params = {
        "startDate": start_date,
        "endDate": end_date,
    }
    data = await _get(f"/v3/vessels/{vessel_id}/tracks", params)
    return data


@router.get("/vessel-events")
async def get_vessel_events(
    vessel_id: str,
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    event_type: Optional[str] = Query(
        None, description="Event type: fishing, port_visit, encounter"
    ),
):
    """
    Get vessel events (fishing, port visits, encounters).
    """
    params: Dict[str, Any] = {
        "startDate": start_date,
        "endDate": end_date,
    }
    if event_type:
        params["eventType"] = event_type

    data = await _get(f"/v3/vessels/{vessel_id}/events", params)
    return data


@router.get("/regions")
async def list_regions(
    dataset: str = Query("public-fishing-effort:v1"),
    limit: int = Query(50, ge=1, le=200),
):
    """
    List available fishing regions.
    """
    params = {
        "dataset": dataset,
        "limit": limit,
    }
    data = await _get("/v3/regions", params)
    return data


@router.get("/heatmap")
async def get_heatmap(
    dataset: str = Query("public-fishing-effort:v1"),
    start_date: str = Query(...),
    end_date: str = Query(...),
    zoom: int = Query(3, ge=1, le=10),
):
    """
    Get fishing effort heatmap tile data.

    Returns GeoJSON heatmap for visualization.
    """
    params = {
        "dataset": dataset,
        "startDate": start_date,
        "endDate": end_date,
        "zoom": zoom,
    }
    data = await _get("/v3/heatmap", params)
    return data
