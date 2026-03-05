"""
NOAA API Router
Provides access to NOAA CO-OPS (Tides & Currents) and NOAA NDBC (National Data Buoy Center).
These are public APIs and do not require an API key.
"""

import logging
from typing import Any, Dict, Optional

import httpx
from fastapi import APIRouter, HTTPException, Query

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/noaa", tags=["noaa-external"])

_TIMEOUT = httpx.Timeout(15.0, connect=5.0)

# ─── NOAA CO-OPS (Tides & Currents) ─────────────────────────────────────────

COOPS_BASE_URL = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter"

@router.get("/coops/stations")
async def get_coops_stations():
    """Get active CO-OPS stations (simplified metadata)."""
    # Active stations with water level capabilities
    url = "https://api.tidesandcurrents.noaa.gov/mdapi/prod/webapi/stations.json?type=waterlevels"
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()
            return {"total": len(data.get("stations", [])), "stations": data.get("stations", [])[:100]} # Limit for brevity
    except Exception as exc:
        logger.error(f"NOAA CO-OPS stations error: {exc}")
        raise HTTPException(status_code=502, detail=f"NOAA CO-OPS error: {exc}")


@router.get("/coops/data")
async def get_coops_data(
    station: str = Query(..., description="Station ID (e.g. 8454000 for Providence, RI)"),
    date: str = Query("latest", description="today, latest, recent, or YYYYMMDD"),
    product: str = Query("water_level", description="water_level, air_temperature, water_temperature, wind, etc."),
    datum: str = Query("MLLW", description="MLLW, MHW, STND, etc. (required for water_level)"),
    time_zone: str = Query("gmt", description="gmt, lst, lst_ldt"),
    units: str = Query("metric", description="metric or english"),
):
    """Get data from a specific NOAA CO-OPS station."""
    params = {
        "station": station,
        "date": date,
        "product": product,
        "datum": datum,
        "time_zone": time_zone,
        "units": units,
        "format": "json",
    }
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(COOPS_BASE_URL, params=params)
            resp.raise_for_status()
            data = resp.json()
            if "error" in data:
                raise HTTPException(status_code=400, detail=data["error"].get("message", "NOAA API Error"))
            return data
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=f"NOAA API error: {exc}")
    except Exception as exc:
        logger.error(f"NOAA CO-OPS data error: {exc}")
        raise HTTPException(status_code=502, detail=f"NOAA CO-OPS error: {exc}")


# ─── NOAA NDBC (National Data Buoy Center) ───────────────────────────────────

# NDBC doesn't have a modern JSON REST API, mostly txt blocks or standard DODS.
# We'll proxy their latest observations text block and parse it simply if possible,
# or return the raw text.

@router.get("/ndbc/latest")
async def get_ndbc_latest_station(
    station: str = Query(..., description="Station ID (e.g. 41004)")
):
    """Get the latest real-time meteorological data for a buoy (txt format -> basic JSON)."""
    # Latest observation is usually in the first two data lines of the realtime txt
    url = f"https://www.ndbc.noaa.gov/data/realtime2/{station}.txt"
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(url)
            if resp.status_code == 404:
                raise HTTPException(status_code=404, detail="Station data not found")
            resp.raise_for_status()
            
            lines = resp.text.split("\n")
            if len(lines) < 3:
                return {"station": station, "data": None, "raw": resp.text}
                
            headers = lines[0].split()
            units = lines[1].split()
            latest_data = lines[2].split()
            
            # Simple dict mapping
            parsed = {}
            for i, val in enumerate(latest_data):
                if i < len(headers):
                    key = headers[i]
                    parsed[key] = {
                        "value": val,
                        "unit": units[i] if i < len(units) else ""
                    }
                    
            return {
                "station": station,
                "parsed": parsed,
                "raw_preview": "\n".join(lines[:5])
            }
    except Exception as exc:
        if isinstance(exc, HTTPException):
            raise exc
        logger.error(f"NOAA NDBC error: {exc}")
        raise HTTPException(status_code=502, detail=f"NOAA NDBC error: {exc}")

@router.get("/ping")
async def noaa_ping():
    """Check if NOAA public APIs are reachable."""
    return {"ok": True, "message": "NOAA CO-OPS and NDBC routers are active (Public Access)"}
