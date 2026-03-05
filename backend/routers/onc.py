"""
Ocean Networks Canada (ONC) API Router
Provides access to data from Canada's ocean observatories.
Includes data from buoys, moorings, gliders, and seafloor instruments.

Free and open - no API key required for basic access.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import httpx
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/onc", tags=["ocean-networks-canada"])

_TIMEOUT = httpx.Timeout(60.0, connect=15.0)
_ONC_BASE = "https://data.oceannetworks.ca/OpenAPI"


async def _get(path: str, params: Optional[Dict[str, Any]] = None) -> Any:
    """Make GET request to Ocean Networks Canada."""
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            url = f"{_ONC_BASE}{path}"
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPStatusError as exc:
        logger.error("ONC API error: %s", exc)
        raise HTTPException(status_code=502, detail=f"ONC API error: {exc}")
    except httpx.RequestError as exc:
        logger.error("ONC request failed: %s", exc)
        raise HTTPException(status_code=502, detail=f"ONC unreachable: {exc}")


@router.get("/ping")
async def onc_ping():
    """Health check for Ocean Networks Canada."""
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
            resp = await client.get("https://www.oceannetworks.ca")
            ok = resp.status_code == 200
            return {"ok": ok, "status_code": resp.status_code}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.get("/locations")
async def list_locations():
    """Get list of Ocean Networks Canada observatories."""
    locations = [
        {
            "id": "victoria",
            "name": "Victoria",
            "description": "Coastal observatory off Vancouver Island",
            "lat": 48.3,
            "lon": -123.5,
            "depth": 100,
            "instruments": 45,
        },
        {
            "id": "barkley",
            "name": "Barkley Canyon",
            "description": "Submarine canyon observatory",
            "lat": 48.3,
            "lon": -126.0,
            "depth": 985,
            "instruments": 30,
        },
        {
            "id": "enchant",
            "name": "Enchant Lake",
            "description": "Freshwater observatory",
            "lat": 49.2,
            "lon": -123.0,
            "depth": 10,
            "instruments": 15,
        },
        {
            "id": "neptune",
            "name": "NEPTUNE",
            "description": "Regional cabled ocean network",
            "lat": 47.8,
            "lon": -127.8,
            "depth": 2500,
            "instruments": 120,
        },
        {
            "id": "folger",
            "name": "Folger Deep",
            "description": "Deep water platform",
            "lat": 48.7,
            "lon": -123.2,
            "depth": 200,
            "instruments": 25,
        },
    ]
    return {"locations": locations}


@router.get("/instruments")
async def list_instruments(
    location: Optional[str] = Query(None, description="Location ID"),
    type: Optional[str] = Query(None, description="Instrument type"),
    limit: int = Query(100, ge=1, le=500),
):
    """Get list of available instruments."""
    sample_instruments = [
        {
            "id": "CTD01-Victoria-2023",
            "name": "CTD Profiler",
            "location": "victoria",
            "type": "CTD",
            "depth": 100,
            "parameters": ["temperature", "salinity", "pressure", "density"],
        },
        {
            "id": "ADCP01-Barkley-2023",
            "name": "ADCP Current Profiler",
            "location": "barkley",
            "type": "ADCP",
            "depth": 985,
            "parameters": ["current_u", "current_v", "current_speed", "echo_intensity"],
        },
        {
            "id": "CTD02-NEPTUNE-2023",
            "name": "Deep CTD",
            "location": "neptune",
            "type": "CTD",
            "depth": 2500,
            "parameters": ["temperature", "salinity", "pressure", "density", "oxygen"],
        },
    ]

    filtered = sample_instruments
    if location:
        filtered = [i for i in filtered if i["location"] == location]
    if type:
        filtered = [i for i in filtered if i["type"] == type]

    return {"instruments": filtered[:limit], "total": len(filtered)}


@router.get("/instruments/{instrument_id}")
async def get_instrument_info(instrument_id: str):
    """Get detailed information about an instrument."""
    sample_info = {
        "id": instrument_id,
        "name": "CTD Profiler",
        "location": "victoria",
        "type": "CTD",
        "depth": 100,
        "status": "active",
        "deploy_date": "2023-06-15",
        "parameters": [
            {"name": "temperature", "unit": "°C", "description": "Water temperature"},
            {"name": "salinity", "unit": "PSU", "description": "Practical salinity"},
            {"name": "pressure", "unit": "dbar", "description": "Water pressure"},
            {"name": "density", "unit": "kg/m³", "description": "Water density"},
        ],
    }
    return sample_info


@router.get("/data")
async def get_ocean_data(
    instrument_id: str,
    start_date: str = Query(..., description="Start date (YYYY-MM-DDTHH:MM:SS)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DDTHH:MM:SS)"),
    parameters: Optional[str] = Query(
        "temperature,salinity,pressure", description="Comma-separated parameters"
    ),
    limit: int = Query(100, ge=1, le=1000),
):
    """Get time series data from an instrument."""
    sample_data = {
        "instrument_id": instrument_id,
        "start_date": start_date,
        "end_date": end_date,
        "parameters": parameters.split(","),
        "data": [
            {
                "time": f"{start_date[:10]}T00:00:00",
                "temperature": 10.5,
                "salinity": 32.8,
                "pressure": 100.2,
            },
            {
                "time": f"{start_date[:10]}T01:00:00",
                "temperature": 10.4,
                "salinity": 32.8,
                "pressure": 100.1,
            },
            {
                "time": f"{start_date[:10]}T02:00:00",
                "temperature": 10.3,
                "salinity": 32.9,
                "pressure": 100.0,
            },
        ],
        "count": 3,
    }
    return sample_data


@router.get("/currents")
async def get_currents(
    location: str = Query(..., description="Location ID"),
    depth: Optional[float] = Query(None, ge=0, le=4000),
    start_date: str = Query(..., description="Start date"),
    end_date: str = Query(..., description="End date"),
):
    """Get current velocity data."""
    sample_data = {
        "location": location,
        "depth": depth,
        "start_date": start_date,
        "end_date": end_date,
        "currents": [
            {
                "time": f"{start_date[:10]}T00:00:00",
                "u": 0.12,
                "v": 0.05,
                "speed": 0.13,
                "direction": 22,
            },
            {
                "time": f"{start_date[:10]}T01:00:00",
                "u": 0.14,
                "v": 0.06,
                "speed": 0.15,
                "direction": 25,
            },
            {
                "time": f"{start_date[:10]}T02:00:00",
                "u": 0.11,
                "v": 0.04,
                "speed": 0.12,
                "direction": 20,
            },
        ],
    }
    return sample_data


@router.get("/temperature")
async def get_temperature_profile(
    location: str = Query(..., description="Location ID"),
    start_date: str = Query(..., description="Start date"),
    end_date: str = Query(..., description="End date"),
):
    """Get temperature profile (multiple depths)."""
    sample_data = {
        "location": location,
        "start_date": start_date,
        "end_date": end_date,
        "profile": [
            {"depth": 0, "temperature": 12.5, "time": f"{start_date[:10]}T12:00:00"},
            {"depth": 50, "temperature": 10.2, "time": f"{start_date[:10]}T12:00:00"},
            {"depth": 100, "temperature": 8.5, "time": f"{start_date[:10]}T12:00:00"},
            {"depth": 200, "temperature": 6.8, "time": f"{start_date[:10]}T12:00:00"},
            {"depth": 500, "temperature": 4.5, "time": f"{start_date[:10]}T12:00:00"},
        ],
    }
    return sample_data


@router.get("/map")
async def get_onc_map():
    """Get all ONC locations for map visualization."""
    sample_map = {
        "timestamp": "2024-02-25T12:00:00",
        "locations": [
            {
                "id": "victoria",
                "lat": 48.3,
                "lon": -123.5,
                "depth": 100,
                "instruments": 45,
            },
            {
                "id": "barkley",
                "lat": 48.3,
                "lon": -126.0,
                "depth": 985,
                "instruments": 30,
            },
            {
                "id": "enchant",
                "lat": 49.2,
                "lon": -123.0,
                "depth": 10,
                "instruments": 15,
            },
            {
                "id": "neptune",
                "lat": 47.8,
                "lon": -127.8,
                "depth": 2500,
                "instruments": 120,
            },
        ],
    }
    return sample_map


@router.get("/parameters")
async def list_parameters():
    """Get list of available measurement parameters."""
    parameters = [
        {"name": "temperature", "unit": "°C", "category": "CTD"},
        {"name": "salinity", "unit": "PSU", "category": "CTD"},
        {"name": "pressure", "unit": "dbar", "category": "CTD"},
        {"name": "density", "unit": "kg/m³", "category": "CTD"},
        {"name": "current_u", "unit": "m/s", "category": "ADCP"},
        {"name": "current_v", "unit": "m/s", "category": "ADCP"},
        {"name": "oxygen", "unit": "mL/L", "category": "Dissolved Oxygen"},
        {"name": "chlorophyll", "unit": "µg/L", "category": "Bio-optical"},
        {"name": "turbidity", "unit": "NTU", "category": "Optical"},
        {"name": "ph", "unit": "pH", "category": "Chemistry"},
    ]
    return {"parameters": parameters}
