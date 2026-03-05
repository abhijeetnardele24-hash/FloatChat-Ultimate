"""
GEBCO Bathymetry API Router
Provides access to General Bathymetric Chart of the Oceans (GEBCO) data.
GEBCO offers global bathymetric (ocean depth) data.

Free and open - no API key required.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import httpx
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/gebco", tags=["gebco-bathymetry"])

_TIMEOUT = httpx.Timeout(30.0, connect=10.0)

_GEBCO_BASE = "https://gebco.awi.de"


class BathymetryPoint(BaseModel):
    lon: float
    lat: float
    depth: float


async def _get(path: str, params: Optional[Dict[str, Any]] = None) -> Any:
    """Make GET request to GEBCO."""
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(f"{_GEBCO_BASE}{path}", params=params)
            resp.raise_for_status()
            return (
                resp.json()
                if "application/json" in resp.headers.get("content-type", "")
                else resp.text
            )
    except httpx.HTTPStatusError as exc:
        logger.error("GEBCO error: %s", exc)
        raise HTTPException(status_code=502, detail=f"GEBCO API error: {exc}")
    except httpx.RequestError as exc:
        logger.error("GEBCO request failed: %s", exc)
        raise HTTPException(status_code=502, detail=f"GEBCO unreachable: {exc}")


@router.get("/ping")
async def gebco_ping():
    """Health check for GEBCO."""
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
            resp = await client.get(f"{_GEBCO_BASE}/")
            ok = resp.status_code == 200
            return {"ok": ok, "status_code": resp.status_code}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.get("/elevation")
async def get_elevation(
    lat: float = Query(..., ge=-90, le=90, description="Latitude"),
    lon: float = Query(..., ge=-180, le=180, description="Longitude"),
):
    """
    Get elevation/bathymetry at a specific point.
    Returns depth (negative for below sea level).

    Example: /elevation?lat=0&lon=-140
    """
    params = {"lat": lat, "lon": lon}
    data = await _get("/api/elevation", params)
    return data


@router.get("/elevation/batch")
async def get_elevation_batch(
    points: str = Query(
        ..., description="Comma-separated lat,lon pairs: lat1,lon1;lat2,lon2;..."
    ),
):
    """
    Get elevation/bathymetry for multiple points.

    Example: /elevation/batch?points=0,-140;10,-120;20,-130
    """
    params = {"points": points}
    data = await _get("/api/elevation/batch", params)
    return data


@router.get("/dem")
async def get_dem(
    lat_min: float = Query(..., ge=-90, le=90),
    lat_max: float = Query(..., ge=-90, le=90),
    lon_min: float = Query(..., ge=-180, le=180),
    lon_max: float = Query(..., ge=-180, le=180),
    resolution: str = Query("1km", description="Resolution: 1km, 500m, 100m"),
):
    """
    Get digital elevation model (DEM) for a bounding box.

    Returns grid of elevations for the specified area.
    """
    params = {
        "lat_min": lat_min,
        "lat_max": lat_max,
        "lon_min": lon_min,
        "lon_max": lon_max,
        "resolution": resolution,
    }
    data = await _get("/api/dem", params)
    return data


@router.get("/tiles")
async def get_bathymetry_tile(
    z: int = Query(..., ge=0, le=10, description="Zoom level"),
    x: int = Query(..., ge=0, description="Tile X"),
    y: int = Query(..., ge=0, description="Tile Y"),
):
    """
    Get bathymetry tile (PNG image) for map visualization.

    Provides tiles compatible with standard web maps.
    """
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            url = f"{_GEBCO_BASE}/tiles/{z}/{x}/{y}.png"
            resp = await client.get(url)
            resp.raise_for_status()

            import base64

            img_b64 = base64.b64encode(resp.content).decode()
            return {
                "format": "png",
                "tile": f"data:image/png;base64,{img_b64}",
                "zoom": z,
                "x": x,
                "y": y,
            }
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=404, detail=f"Tile not found: {exc}")


@router.get("/contours")
async def get_contours(
    lat_min: float = Query(..., ge=-90, le=90),
    lat_max: float = Query(..., ge=-90, le=90),
    lon_min: float = Query(..., ge=-180, le=180),
    lon_max: float = Query(..., ge=-180, le=180),
    interval: int = Query(
        100, ge=10, le=1000, description="Contour interval in meters"
    ),
):
    """
    Get bathymetric contour lines for an area.

    Returns GeoJSON of depth contours.
    """
    params = {
        "lat_min": lat_min,
        "lat_max": lat_max,
        "lon_min": lon_min,
        "lon_max": lon_max,
        "interval": interval,
    }
    data = await _get("/api/contours", params)
    return data


@router.get("/region")
async def get_region_bathymetry(
    sw_lat: float = Query(..., ge=-90, le=90, description="Southwest latitude"),
    sw_lon: float = Query(..., ge=-180, le=180, description="Southwest longitude"),
    ne_lat: float = Query(..., ge=-90, le=90, description="Northeast latitude"),
    ne_lon: float = Query(..., ge=-180, le=180, description="Northeast longitude"),
    num_points: int = Query(50, ge=10, le=200, description="Number of points per side"),
):
    """
    Get bathymetry profile for a rectangular region.

    Returns grid of depths for the bounding box.
    """
    params = {
        "sw_lat": sw_lat,
        "sw_lon": sw_lon,
        "ne_lat": ne_lat,
        "ne_lon": ne_lon,
        "num_points": num_points,
    }
    data = await _get("/api/region", params)
    return data


@router.get("/transect")
async def get_transect(
    start_lat: float = Query(..., ge=-90, le=90),
    start_lon: float = Query(..., ge=-180, le=180),
    end_lat: float = Query(..., ge=-90, le=90),
    end_lon: float = Query(..., ge=-180, le=180),
    num_points: int = Query(100, ge=10, le=500),
):
    """
    Get bathymetry along a transect line between two points.

    Returns depth profile along the line.
    """
    params = {
        "start_lat": start_lat,
        "start_lon": start_lon,
        "end_lat": end_lat,
        "end_lon": end_lon,
        "num_points": num_points,
    }
    data = await _get("/api/transect", params)
    return data
