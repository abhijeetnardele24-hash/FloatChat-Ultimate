"""
ArgoVis External API Router
Proxies requests to the ArgoVis REST API (https://argovis-api.colorado.edu)
and returns ocean data (Argo profiles, platform metadata, grids).

Auth: uses x-argokey header from ARGOVIS_API_KEY env var.
"""

from __future__ import annotations

import os
import logging
from typing import Any, Dict, List, Optional

import httpx
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/argovis", tags=["argovis-external"])

_TIMEOUT = httpx.Timeout(30.0, connect=10.0)


# ─── Helpers ────────────────────────────────────────────────────────────────

def _headers() -> Dict[str, str]:
    h: Dict[str, str] = {"Accept": "application/json"}
    key = (os.getenv("ARGOVIS_API_KEY") or "").strip()
    if key:
        h["x-argokey"] = key
    return h


async def _get(path: str, params: Optional[Dict[str, Any]] = None) -> Any:
    """GET request to ArgoVis API with error handling. Returns parsed JSON or raw text."""
    base_url = (os.getenv("ARGOVIS_BASE_URL") or "https://argovis-api.colorado.edu").strip().rstrip("/")
    url = f"{base_url}{path}"
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(url, params=params, headers=_headers())
            resp.raise_for_status()
            content_type = resp.headers.get("content-type", "")
            # Return raw text if not JSON (e.g. ArgoVis /ping returns plain text)
            if not resp.content:
                return None
            if "application/json" in content_type:
                return resp.json()
            # Try JSON parse anyway, fall back to text
            try:
                return resp.json()
            except Exception:
                return resp.text
    except httpx.HTTPStatusError as exc:
        code = exc.response.status_code
        detail = exc.response.text[:300] if exc.response.text else str(exc)
        logger.error("ArgoVis %s returned %d: %s", path, code, detail)
        raise HTTPException(status_code=502, detail=f"ArgoVis API error ({code}): {detail}")
    except httpx.RequestError as exc:
        logger.error("ArgoVis request to %s failed: %s", path, exc)
        raise HTTPException(status_code=502, detail=f"ArgoVis unreachable: {exc}")


# ─── Response models ────────────────────────────────────────────────────────

class ArgoVisProfile(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    basin: Optional[int] = None
    data_center: Optional[str] = None
    date: Optional[str] = None
    date_added: Optional[str] = None
    lat: Optional[float] = Field(None, alias="geolocation_lat")
    lon: Optional[float] = Field(None, alias="geolocation_lon")
    platform_number: Optional[str] = None
    cycle_number: Optional[int] = None
    source: Optional[List[Dict[str, Any]]] = None
    data: Optional[List[List[Any]]] = None
    data_keys: Optional[List[str]] = None


class ArgoVisPlatform(BaseModel):
    platform_number: Optional[str] = None
    date_updated_argovis: Optional[str] = None
    most_recent_date: Optional[str] = None
    most_recent_date_added: Optional[str] = None
    cycle_number: Optional[int] = None


class ArgoVisSearchResponse(BaseModel):
    profiles: List[Dict[str, Any]] = []
    total: int = 0


# ─── Endpoints ──────────────────────────────────────────────────────────────

@router.get("/ping")
async def argovis_ping():
    """Quick health check – verify ArgoVis key is accepted."""
    has_key = bool((os.getenv("ARGOVIS_API_KEY") or "").strip())
    base_url = (os.getenv("ARGOVIS_BASE_URL") or "https://argovis-api.colorado.edu").strip().rstrip("/")
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
            resp = await client.get(f"{base_url}/ping", headers=_headers())
            ok = resp.status_code == 200
            return {
                "ok": ok,
                "status_code": resp.status_code,
                "argovis_response": resp.text[:200] if resp.text else None,
                "has_key": has_key,
                "base_url": base_url,
            }
    except httpx.RequestError as exc:
        return {"ok": False, "error": str(exc), "has_key": has_key}


@router.get("/profiles")
async def search_profiles(
    startDate: Optional[str] = Query(None, description="ISO date, e.g. 2024-01-01T00:00:00Z"),
    endDate: Optional[str] = Query(None, description="ISO date"),
    polygon: Optional[str] = Query(None, description="GeoJSON polygon as string, e.g. [[-180,-90],[180,-90],[180,90],[-180,90],[-180,-90]]"),
    box: Optional[str] = Query(None, description="[[sw_lon,sw_lat],[ne_lon,ne_lat]]"),
    center: Optional[str] = Query(None, description="[lon,lat]"),
    radius: Optional[float] = Query(None, description="Radius in km (with center)"),
    platform: Optional[str] = Query(None, description="WMO platform number"),
    source: Optional[str] = Query(None, description="Source filter, e.g. argo_core"),
    data: Optional[str] = Query(None, description="Comma-separated var names to include, e.g. pres,temp,psal"),
    compression: Optional[str] = Query("minimal", description="minimal or full"),
    limit: int = Query(50, ge=1, le=1000),
):
    """
    Search ArgoVis profiles with spatial, temporal, and platform filters.
    Returns profile metadata and optionally measurement data.
    """
    params: Dict[str, Any] = {"compression": compression}
    if startDate:
        params["startDate"] = startDate
    if endDate:
        params["endDate"] = endDate
    if polygon:
        params["polygon"] = polygon
    if box:
        params["box"] = box
    if center:
        params["center"] = center
    if radius is not None:
        params["radius"] = radius
    if platform:
        params["platform"] = platform
    if source:
        params["source"] = source
    if data:
        params["data"] = data

    raw = await _get("/argo", params=params)
    profiles = raw if isinstance(raw, list) else []
    return {
        "total": len(profiles),
        "limit": limit,
        "data": profiles[:limit],
    }


@router.get("/profiles/{profile_id}")
async def get_profile(profile_id: str, data: Optional[str] = Query(None)):
    """Get a single ArgoVis profile by its ID."""
    params: Dict[str, Any] = {}
    if data:
        params["data"] = data
    result = await _get(f"/argo/{profile_id}", params=params)
    if isinstance(result, list) and len(result) > 0:
        return result[0]
    return result


@router.get("/platforms")
async def list_platforms():
    """
    List known Argo platforms (floats) from ArgoVis vocabulary.
    """
    data = await _get("/argo/vocabulary", params={"parameter": "platform"})
    platforms = data if isinstance(data, list) else []
    return {"total": len(platforms), "data": platforms}


@router.get("/platforms/{platform_number}")
async def get_platform_profiles(
    platform_number: str,
    startDate: Optional[str] = Query(None),
    endDate: Optional[str] = Query(None),
    data: Optional[str] = Query(None),
    compression: Optional[str] = Query("minimal"),
):
    """Get all profiles for a specific platform/float."""
    params: Dict[str, Any] = {"platform": platform_number, "compression": compression}
    if startDate:
        params["startDate"] = startDate
    if endDate:
        params["endDate"] = endDate
    if data:
        params["data"] = data

    raw = await _get("/argo", params=params)
    profiles = raw if isinstance(raw, list) else []
    return {"platform": platform_number, "total": len(profiles), "data": profiles}


@router.get("/vocabulary")
async def get_vocabulary(
    parameter: str = Query("data_keys", description="Vocabulary parameter: platform, data_keys, source, etc."),
):
    """Get ArgoVis vocabulary/metadata (available platforms, data keys, sources)."""
    data = await _get("/argo/vocabulary", params={"parameter": parameter})
    return {"parameter": parameter, "data": data}


@router.get("/latest")
async def latest_profiles(
    limit: int = Query(20, ge=1, le=200),
):
    """
    Get the most recent Argo profiles globally.
    Useful for populating visualizations with fresh data.
    """
    from datetime import datetime, timedelta
    end = datetime.utcnow()
    start = end - timedelta(days=7)
    params = {
        "startDate": start.strftime("%Y-%m-%dT00:00:00Z"),
        "endDate": end.strftime("%Y-%m-%dT23:59:59Z"),
        "compression": "minimal",
        "source": "argo_core",
    }
    raw = await _get("/argo", params=params)
    profiles = raw if isinstance(raw, list) else []
    return {"total": len(profiles), "limit": limit, "data": profiles[:limit]}


@router.get("/region")
async def profiles_by_region(
    sw_lon: float = Query(..., ge=-180, le=180),
    sw_lat: float = Query(..., ge=-90, le=90),
    ne_lon: float = Query(..., ge=-180, le=180),
    ne_lat: float = Query(..., ge=-90, le=90),
    startDate: Optional[str] = Query(None),
    endDate: Optional[str] = Query(None),
    data: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
):
    """
    Get profiles within a bounding box.
    Great for the Explorer map and regional visualizations.
    """
    box = f"[[{sw_lon},{sw_lat}],[{ne_lon},{ne_lat}]]"
    params: Dict[str, Any] = {"box": box, "compression": "minimal", "source": "argo_core"}
    if startDate:
        params["startDate"] = startDate
    if endDate:
        params["endDate"] = endDate
    if data:
        params["data"] = data

    raw = await _get("/argo", params=params)
    profiles = raw if isinstance(raw, list) else []
    return {"total": len(profiles), "limit": limit, "data": profiles[:limit]}
