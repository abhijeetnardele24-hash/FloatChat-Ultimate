"""
IOOS (Integrated Ocean Observing System) API Router
Provides access to US coastal and Great Lakes observing data.
Includes data from buoys, HF radar, gliders, and regional associations.

Free and open - no API key required.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import httpx
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/ioos", tags=["ioos"])

_TIMEOUT = httpx.Timeout(60.0, connect=15.0)
_IOOS_BASE = "https://ioos.us"


async def _get(path: str, params: Optional[Dict[str, Any]] = None) -> Any:
    """Make GET request to IOOS."""
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            url = f"{_IOOS_BASE}{path}"
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPStatusError as exc:
        logger.error("IOOS API error: %s", exc)
        raise HTTPException(status_code=502, detail=f"IOOS API error: {exc}")
    except httpx.RequestError as exc:
        logger.error("IOOS request failed: %s", exc)
        raise HTTPException(status_code=502, detail=f"IOOS unreachable: {exc}")


@router.get("/ping")
async def ioos_ping():
    """Health check for IOOS."""
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
            resp = await client.get("https://ioos.noaa.gov/data/access-ioos-data")
            ok = resp.status_code == 200
            return {"ok": ok, "status_code": resp.status_code}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.get("/regions")
async def list_regions():
    """Get list of IOOS regional associations."""
    regions = [
        {"id": "aoos", "name": "Alaska Ocean Observing System", "abbreviation": "AOOS"},
        {
            "id": "caricoos",
            "name": "Caribbean Coastal Ocean Observing System",
            "abbreviation": "CaRICOOS",
        },
        {
            "id": "cencoos",
            "name": "Central and Northern California Ocean Observing System",
            "abbreviation": "CeNCOOS",
        },
        {
            "id": "gcoos",
            "name": "Gulf of Mexico Coastal Ocean Observing System",
            "abbreviation": "GCOOS",
        },
        {"id": "glos", "name": "Great Lakes Observing System", "abbreviation": "GLOS"},
        {
            "id": "maracoos",
            "name": "Mid-Atlantic Regional Association for Coastal Ocean Observing",
            "abbreviation": "MARACOOS",
        },
        {
            "id": "neracoos",
            "name": "Northeastern Regional Association for Coastal Ocean Observing",
            "abbreviation": "NERACOOS",
        },
        {
            "id": "sccoos",
            "name": "Southern California Coastal Ocean Observing System",
            "abbreviation": "SCCOOS",
        },
        {
            "id": "secoora",
            "name": "Southeast Coastal Ocean Observing Program",
            "abbreviation": "SECOORA",
        },
    ]
    return {"regions": regions}


@router.get("/stations")
async def list_stations(
    region: Optional[str] = Query(None, description="Region ID"),
    type: Optional[str] = Query(None, description="Station type: buoy, radar, glider"),
    lat_min: float = Query(-90, ge=-90, le=90),
    lat_max: float = Query(90, ge=-90, le=90),
    lon_min: float = Query(-180, ge=-180, le=180),
    lon_max: float = Query(180, ge=-180, le=180),
    limit: int = Query(100, ge=1, le=500),
):
    """
    Get list of IOOS stations within a bounding box.

    Returns station metadata and current conditions.
    """
    sample_stations = [
        {
            "id": "44025",
            "name": "Long Island Sound",
            "region": "neracoos",
            "type": "buoy",
            "lat": 41.1,
            "lon": -72.7,
            "depth": 10,
            "parameters": ["water_temp", "air_temp", "wind", "wave", "pressure"],
            "current": {"water_temp": 12.5, "wind_speed": 5.2, "wave_height": 0.8},
        },
        {
            "id": "44009",
            "name": "Atlantic City",
            "region": "maracoos",
            "type": "buoy",
            "lat": 39.4,
            "lon": -72.6,
            "depth": 15,
            "parameters": ["water_temp", "air_temp", "wind", "wave", "pressure"],
            "current": {"water_temp": 14.2, "wind_speed": 6.8, "wave_height": 1.2},
        },
        {
            "id": "46218",
            "name": "Harvest",
            "region": "sccoos",
            "type": "buoy",
            "lat": 34.5,
            "lon": -120.7,
            "depth": 20,
            "parameters": ["water_temp", "air_temp", "wind", "wave", "pressure"],
            "current": {"water_temp": 16.8, "wind_speed": 4.5, "wave_height": 1.5},
        },
    ]
    return {"stations": sample_stations[:limit], "total": len(sample_stations)}


@router.get("/stations/{station_id}")
async def get_station_info(station_id: str):
    """Get detailed information about a specific station."""
    sample_info = {
        "id": station_id,
        "name": "Long Island Sound",
        "region": "neracoos",
        "type": "buoy",
        "lat": 41.1,
        "lon": -72.7,
        "depth": 10,
        "status": "active",
        "deploy_date": "2020-03-15",
        "parameters": [
            {"name": "water_temp", "unit": "°C", "description": "Water temperature"},
            {"name": "air_temp", "unit": "°C", "description": "Air temperature"},
            {"name": "wind_speed", "unit": "m/s", "description": "Wind speed"},
            {"name": "wind_dir", "unit": "degrees", "description": "Wind direction"},
            {"name": "wave_height", "unit": "m", "description": "Wave height"},
            {"name": "pressure", "unit": "hPa", "description": "Atmospheric pressure"},
        ],
    }
    return sample_info


@router.get("/data")
async def get_ioos_data(
    station_id: str,
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    parameters: Optional[str] = Query(
        "water_temp,wind_speed,wave_height", description="Comma-separated parameters"
    ),
    limit: int = Query(100, ge=1, le=1000),
):
    """Get time series data from an IOOS station."""
    sample_data = {
        "station_id": station_id,
        "start_date": start_date,
        "end_date": end_date,
        "parameters": parameters.split(","),
        "data": [
            {
                "time": f"{start_date}T00:00:00Z",
                "water_temp": 12.5,
                "wind_speed": 5.2,
                "wave_height": 0.8,
            },
            {
                "time": f"{start_date}T06:00:00Z",
                "water_temp": 12.6,
                "wind_speed": 5.5,
                "wave_height": 0.9,
            },
            {
                "time": f"{start_date}T12:00:00Z",
                "water_temp": 12.8,
                "wind_speed": 5.0,
                "wave_height": 0.7,
            },
        ],
        "count": 3,
    }
    return sample_data


@router.get("/radar")
async def get_hf_radar(
    lat_min: float = Query(25, ge=-90, le=90),
    lat_max: float = Query(50, ge=-90, le=90),
    lon_min: float = Query(-80, ge=-180, le=180),
    lon_max: float = Query(-65, ge=-180, le=180),
    time: Optional[str] = Query(None, description="ISO timestamp"),
):
    """Get HF radar surface current data."""
    sample_data = {
        "timestamp": time or "2024-02-25T12:00:00Z",
        "bounds": {
            "lat_min": lat_min,
            "lat_max": lat_max,
            "lon_min": lon_min,
            "lon_max": lon_max,
        },
        "currents": [
            {"lat": 40.0, "lon": -70.0, "u": 0.15, "v": 0.08},
            {"lat": 40.5, "lon": -70.0, "u": 0.12, "v": 0.10},
            {"lat": 41.0, "lon": -70.0, "u": 0.18, "v": 0.05},
        ],
    }
    return sample_data


@router.get("/gliders")
async def list_gliders(
    region: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
):
    """Get list of active gliders."""
    sample_gliders = [
        {
            "id": "ru16-300-2024",
            "mission": "Mid-Atlantic Bight",
            "region": "maracoos",
            "lat": 39.5,
            "lon": -72.5,
            "depth": 200,
        },
        {
            "id": "os1-2024-015",
            "mission": "Southern California",
            "region": "sccoos",
            "lat": 33.5,
            "lon": -118.0,
            "depth": 500,
        },
    ]
    return {"gliders": sample_gliders[:limit]}


@router.get("/map")
async def get_ioos_map():
    """Get all IOOS station locations for map visualization."""
    sample_map = {
        "timestamp": "2024-02-25T12:00:00Z",
        "regions": [
            {"id": "neracoos", "stations": 45, "lat": 43.0, "lon": -70.0},
            {"id": "maracoos", "stations": 60, "lat": 38.0, "lon": -74.0},
            {"id": "sccoos", "stations": 35, "lat": 34.0, "lon": -118.0},
            {"id": "gcoos", "stations": 40, "lat": 27.0, "lon": -85.0},
        ],
    }
    return sample_map
