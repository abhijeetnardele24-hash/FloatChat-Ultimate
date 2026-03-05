"""
World Ocean Database (WOD) API Router
Provides access to NOAA's World Ocean Database - the world's largest
collection of uniformly formatted, quality controlled ocean profile data.

Includes temperature, salinity, oxygen, nutrients, and more.
Free and open - no API key required for most data access via NCEI.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import httpx
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/wod", tags=["world-ocean-database"])

_TIMEOUT = httpx.Timeout(60.0, connect=15.0)

_WOD_NCEI = "https://www.ncei.noaa.gov/access/services/wod"


async def _get(path: str, params: Optional[Dict[str, Any]] = None) -> Any:
    """Make GET request to WOD/NCEI API."""
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            url = f"{_WOD_NCEI}{path}"
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPStatusError as exc:
        logger.error("WOD API error: %s", exc)
        raise HTTPException(status_code=502, detail=f"WOD API error: {exc}")
    except httpx.RequestError as exc:
        logger.error("WOD request failed: %s", exc)
        raise HTTPException(status_code=502, detail=f"WOD unreachable: {exc}")


async def _get_public(path: str, params: Optional[Dict[str, Any]] = None) -> Any:
    """Make GET request to public WOD endpoints."""
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            url = f"https://nodc.online/{path}"
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            if "json" in resp.headers.get("content-type", ""):
                return resp.json()
            return resp.text
    except httpx.RequestError as exc:
        logger.error("WOD public request failed: %s", exc)
        return {"error": str(exc)}


@router.get("/ping")
async def wod_ping():
    """Health check for World Ocean Database API."""
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
            resp = await client.get(
                "https://www.ncei.noaa.gov/products/world-ocean-database"
            )
            ok = resp.status_code == 200
            return {"ok": ok, "status_code": resp.status_code}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.get("/stations")
async def get_stations(
    lat_min: float = Query(-90, ge=-90, le=90),
    lat_max: float = Query(90, ge=-90, le=90),
    lon_min: float = Query(-180, ge=-180, le=180),
    lon_max: float = Query(180, ge=-180, le=180),
    depth_min: float = Query(0, ge=0, le=11000),
    depth_max: float = Query(1000, ge=0, le=11000),
    date_start: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_end: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(100, ge=1, le=1000),
):
    """
    Get oceanographic stations within a bounding box.

    Returns station locations and basic metadata.
    """
    params: Dict[str, Any] = {
        "bbox": f"{lon_min},{lat_min},{lon_max},{lat_max}",
        "depth": f"{depth_min},{depth_max}",
        "limit": limit,
    }
    if date_start:
        params["date"] = f"{date_start},{date_end}" if date_end else date_start

    data = await _get_public("/stations", params)
    return data


@router.get("/stations/{station_id}")
async def get_station_profile(
    station_id: str,
    depth_min: float = Query(0, ge=0),
    depth_max: float = Query(5000, ge=0, le=11000),
):
    """
    Get full profile data for a specific station.

    Returns all depth levels with measurements.
    """
    params = {
        "depth": f"{depth_min},{depth_max}",
    }
    data = await _get_public(f"/stations/{station_id}", params)
    return data


@router.get("/profiles")
async def get_profiles(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    radius: float = Query(100, ge=1, le=500, description="Search radius in km"),
    depth_min: float = Query(0, ge=0),
    depth_max: float = Query(2000, ge=0, le=11000),
    date_start: Optional[str] = Query(None),
    date_end: Optional[str] = Query(None),
    variables: Optional[str] = Query(
        None, description="Comma-separated: temperature, salinity, oxygen"
    ),
    limit: int = Query(50, ge=1, le=200),
):
    """
    Get ocean profiles near a specific location.

    Example: /profiles?lat=40&lon=-140&radius=100&variables=temperature,salinity
    """
    params: Dict[str, Any] = {
        "lat": lat,
        "lon": lon,
        "radius": radius,
        "depth": f"{depth_min},{depth_max}",
        "limit": limit,
    }
    if date_start:
        params["date"] = f"{date_start},{date_end}" if date_end else date_start
    if variables:
        params["variables"] = variables

    data = await _get_public("/profiles", params)
    return data


@router.get("/point")
async def get_point_data(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    depth: float = Query(0, ge=0, le=11000, description="Depth in meters"),
    date_start: str = Query(..., description="Start date (YYYY-MM-DD)"),
    date_end: str = Query(..., description="End date (YYYY-MM-DD)"),
    variables: Optional[str] = Query("temperature,salinity,oxygen"),
):
    """
    Get time series of ocean data at a specific point.

    Example: /point?lat=40&lon=-140&depth=0&date_start=2023-01-01&date_end=2023-12-31
    """
    params: Dict[str, Any] = {
        "lat": lat,
        "lon": lon,
        "depth": depth,
        "date": f"{date_start},{date_end}",
        "variables": variables,
    }
    data = await _get_public("/point", params)
    return data


@router.get("/climatology")
async def get_climatology(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    depth_min: float = Query(0, ge=0),
    depth_max: float = Query(1000, ge=0, le=11000),
):
    """
    Get climatological means (average values) at a location.

    Returns monthly averages for different depths.
    """
    params = {
        "lat": lat,
        "lon": lon,
        "depth": f"{depth_min},{depth_max}",
    }
    data = await _get_public("/climatology", params)
    return data


@router.get("/temperature")
async def get_temperature(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    date: str = Query(..., description="Date (YYYY-MM-DD)"),
    depth: float = Query(0, ge=0, le=11000),
):
    """
    Get temperature at a specific location, date, and depth.
    """
    params = {
        "lat": lat,
        "lon": lon,
        "depth": depth,
        "date": date,
    }
    data = await _get_public("/temperature", params)
    return data


@router.get("/salinity")
async def get_salinity(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    date: str = Query(..., description="Date (YYYY-MM-DD)"),
    depth: float = Query(0, ge=0, le=11000),
):
    """
    Get salinity at a specific location, date, and depth.
    """
    params = {
        "lat": lat,
        "lon": lon,
        "depth": depth,
        "date": date,
    }
    data = await _get_public("/salinity", params)
    return data


@router.get("/search")
async def search_wod(
    query: str = Query(..., description="Search query"),
    limit: int = Query(20, ge=1, le=100),
):
    """
    Search WOD datasets and variables.

    Example: /search?query=salinity&limit=20
    """
    params = {
        "q": query,
        "limit": limit,
    }
    data = await _get_public("/search", params)
    return data


@router.get("/regions")
async def get_ocean_regions():
    """
    Get list of ocean regions with available data.

    Returns region IDs and descriptions.
    """
    regions = [
        {"id": "atlantic", "name": "Atlantic Ocean"},
        {"id": "pacific", "name": "Pacific Ocean"},
        {"id": "indian", "name": "Indian Ocean"},
        {"id": "arctic", "name": "Arctic Ocean"},
        {"id": "southern", "name": "Southern Ocean"},
        {"id": "mediterranean", "name": "Mediterranean Sea"},
        {"id": "caribbean", "name": "Caribbean Sea"},
        {"id": "blacksea", "name": "Black Sea"},
    ]
    return {"regions": regions}


@router.get("/variables")
async def list_variables():
    """List available WOD measurement variables."""
    variables = [
        {"id": "temperature", "name": "Temperature", "unit": "°C"},
        {"id": "salinity", "name": "Salinity", "unit": "PSU"},
        {"id": "oxygen", "name": "Dissolved Oxygen", "unit": "ml/L"},
        {"id": "phosphate", "name": "Phosphate", "unit": "µmol/L"},
        {"id": "nitrate", "name": "Nitrate", "unit": "µmol/L"},
        {"id": "silicate", "name": "Silicate", "unit": "µmol/L"},
        {"id": "ph", "name": "pH", "unit": "scale"},
        {"id": "chlorophyll", "name": "Chlorophyll-a", "unit": "mg/m³"},
    ]
    return {"variables": variables}
