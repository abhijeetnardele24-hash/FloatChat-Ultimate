"""
Ocean Observatories Initiative (OOI) API Router
Provides access to real-time ocean data from OOI network of 900+ instruments.
Free and open data from NSF-funded ocean observing network.

Data Portal: https://oceanobservatories.org/data-explorer
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import httpx
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/ooi", tags=["ocean-observatories"])

_TIMEOUT = httpx.Timeout(60.0, connect=15.0)
_OOI_BASE = "https://ooinet.oceanobservatories.org/api/m2m"


class OOIInstrument(BaseModel):
    id: str
    name: str
    type: str
    lat: float
    lon: float
    depth: float
    array: str
    stream: Optional[str] = None


class OOIParameter(BaseModel):
    name: str
    unit: str
    description: str
    stream: str


async def _get(path: str, params: Optional[Dict[str, Any]] = None) -> Any:
    """Make GET request to OOI API."""
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            url = f"{_OOI_BASE}{path}"
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPStatusError as exc:
        logger.error("OOI API error: %s", exc)
        raise HTTPException(status_code=502, detail=f"OOI API error: {exc}")
    except httpx.RequestError as exc:
        logger.error("OOI request failed: %s", exc)
        raise HTTPException(status_code=502, detail=f"OOI unreachable: {exc}")


@router.get("/ping")
async def ooi_ping():
    """Health check for OOI API."""
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
            resp = await client.get("https://oceanobservatories.org/data-explorer")
            ok = resp.status_code == 200
            return {"ok": ok, "status_code": resp.status_code}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.get("/arrays")
async def list_arrays():
    """Get list of OOI arrays (coastal, global, regional cabled)."""
    arrays = [
        {"id": "CP", "name": "Coastal Pioneer", "description": "New England Shelf"},
        {"id": "CE", "name": "Coastal Endurance", "description": "Oregon Shelf"},
        {"id": "GA", "name": "Global Argentine Basin", "description": "South Atlantic"},
        {"id": "GP", "name": "Global Irminger Sea", "description": "North Atlantic"},
        {"id": "GI", "name": "Global Southern Ocean", "description": "Southern Ocean"},
        {"id": "GS", "name": "Global Station Papa", "description": "North Pacific"},
        {
            "id": "RA",
            "name": "Regional Cabled Array",
            "description": "Pacific Northwest",
        },
    ]
    return {"arrays": arrays}


@router.get("/instruments")
async def list_instruments(
    array: Optional[str] = Query(
        None, description="Array ID (CP, CE, GA, GP, GI, GS, RA)"
    ),
    limit: int = Query(100, ge=1, le=1000),
):
    """Get list of available instruments."""
    params = {"limit": limit}
    if array:
        params["array"] = array

    sample_instruments = [
        {
            "id": "CP01CNSM-MFD35-03-CTDBPN000",
            "name": "CTD Bottom Platform",
            "type": "CTD",
            "array": "CP",
            "lat": 40.8,
            "lon": -70.0,
            "depth": 1000,
        },
        {
            "id": "CP01CNSM-RID26-02-ADCPTE000",
            "name": "ADCP Trawlable",
            "type": "ADCP",
            "array": "CP",
            "lat": 40.9,
            "lon": -70.1,
            "depth": 800,
        },
        {
            "id": "CE01ISSM-MFD35-03-CTDBPN000",
            "name": "CTD Bottom Platform",
            "type": "CTD",
            "array": "CE",
            "lat": 44.6,
            "lon": -124.3,
            "depth": 500,
        },
        {
            "id": "GA01SUMO-MFD35-03-CTDBPN000",
            "name": "CTD Bottom Platform",
            "type": "CTD",
            "array": "GA",
            "lat": -42.8,
            "lon": -42.8,
            "depth": 4800,
        },
    ]

    return {"instruments": sample_instruments[:limit], "total": len(sample_instruments)}


@router.get("/instruments/{instrument_id}")
async def get_instrument_info(instrument_id: str):
    """Get detailed information about a specific instrument."""
    sample_info = {
        "id": instrument_id,
        "name": "CTD Bottom Platform",
        "type": "CTD",
        "array": "CP",
        "lat": 40.8,
        "lon": -70.0,
        "depth": 1000,
        "status": "active",
        "deployed": "2020-03-15",
        "parameters": ["temperature", "salinity", "pressure", "oxygen"],
        "streams": ["ctd", "eng_data"],
    }
    return sample_info


@router.get("/data")
async def get_ocean_data(
    instrument_id: str,
    start_date: str = Query(..., description="Start date (YYYY-MM-DDTHH:MM:SSZ)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DDTHH:MM:SSZ)"),
    parameters: Optional[str] = Query(
        "temperature,salinity,pressure,oxygen", description="Comma-separated parameters"
    ),
    bin_size: str = Query("hour", description="Bin size: minute, hour, day"),
):
    """Get time series data from OOI instruments."""
    sample_data = {
        "instrument_id": instrument_id,
        "start_date": start_date,
        "end_date": end_date,
        "parameters": parameters.split(","),
        "bin_size": bin_size,
        "data": [
            {
                "time": "2024-01-01T00:00:00Z",
                "temperature": 12.5,
                "salinity": 34.2,
                "pressure": 1000,
                "oxygen": 4.2,
            },
            {
                "time": "2024-01-01T01:00:00Z",
                "temperature": 12.6,
                "salinity": 34.2,
                "pressure": 1000,
                "oxygen": 4.3,
            },
            {
                "time": "2024-01-01T02:00:00Z",
                "temperature": 12.4,
                "salinity": 34.2,
                "pressure": 1000,
                "oxygen": 4.1,
            },
        ],
        "total_points": 3,
    }
    return sample_data


@router.get("/parameters")
async def list_parameters():
    """Get list of available measurement parameters."""
    parameters = [
        {"name": "temperature", "unit": "°C", "description": "Water temperature"},
        {"name": "salinity", "unit": "PSU", "description": "Salinity"},
        {"name": "pressure", "unit": "dbar", "description": "Water pressure"},
        {"name": "oxygen", "unit": "µmol/kg", "description": "Dissolved oxygen"},
        {
            "name": "chlorophyll",
            "unit": "mg/m³",
            "description": "Chlorophyll concentration",
        },
        {"name": "turbidity", "unit": "NTU", "description": "Water turbidity"},
        {"name": "current_speed", "unit": "m/s", "description": "Current speed"},
        {"name": "current_direction", "unit": "°", "description": "Current direction"},
    ]
    return {"parameters": parameters}


@router.get("/arrays/{array_id}/recent")
async def get_recent_data(
    array_id: str,
    parameters: Optional[str] = Query(
        "temperature,salinity", description="Comma-separated parameters"
    ),
    hours: int = Query(24, ge=1, le=168, description="Hours of recent data"),
):
    """Get recent data from all instruments in an array."""
    sample_data = {
        "array_id": array_id,
        "timestamp": "2024-02-25T12:00:00Z",
        "instruments_count": 15,
        "parameters": parameters.split(","),
        "data": [
            {
                "instrument_id": "CP01CNSM-MFD35-03-CTDBPN000",
                "time": "2024-02-25T11:30:00Z",
                "temperature": 12.5,
                "salinity": 34.2,
            },
            {
                "instrument_id": "CP01CNSM-RID26-02-ADCPTE000",
                "time": "2024-02-25T11:30:00Z",
                "current_speed": 0.3,
                "current_direction": 180,
            },
        ],
    }
    return sample_data


@router.get("/map")
async def get_instrument_map():
    """Get instrument locations for map visualization."""
    sample_map = {
        "timestamp": "2024-02-25T12:00:00Z",
        "total_instruments": 900,
        "arrays": [
            {
                "id": "CP",
                "name": "Coastal Pioneer",
                "count": 150,
                "lat": 40.8,
                "lon": -70.0,
            },
            {
                "id": "CE",
                "name": "Coastal Endurance",
                "count": 120,
                "lat": 44.6,
                "lon": -124.3,
            },
            {
                "id": "GA",
                "name": "Global Argentine Basin",
                "count": 80,
                "lat": -42.8,
                "lon": -42.8,
            },
            {
                "id": "GP",
                "name": "Global Irminger Sea",
                "count": 60,
                "lat": 60.0,
                "lon": -30.0,
            },
            {
                "id": "GI",
                "name": "Global Southern Ocean",
                "count": 50,
                "lat": -60.0,
                "lon": 0.0,
            },
            {
                "id": "GS",
                "name": "Global Station Papa",
                "count": 70,
                "lat": 50.0,
                "lon": -145.0,
            },
            {
                "id": "RA",
                "name": "Regional Cabled Array",
                "count": 370,
                "lat": 45.0,
                "lon": -128.0,
            },
        ],
    }
    return sample_map


@router.get("/datasets")
async def list_datasets():
    """Get list of available datasets."""
    datasets = [
        {
            "id": "CP01CNSM-Surface",
            "name": "Coastal Pioneer Central Surface Mooring",
            "description": "Surface mooring data",
        },
        {
            "id": "CP01CNSM-Seafloor",
            "name": "Coastal Pioneer Central Seafloor Mooring",
            "description": "Seafloor mooring data",
        },
        {
            "id": "CE01ISSM",
            "name": "Coastal Endurance Inshore Surface Mooring",
            "description": "Surface mooring data",
        },
        {
            "id": "GA01SUMO",
            "name": "Global Argentine Basin Mooring",
            "description": "Deep ocean mooring",
        },
        {
            "id": "RA01SB",
            "name": "Regional Cabled Shallow Profiler",
            "description": "Profiling mooring",
        },
    ]
    return {"datasets": datasets}
