"""
Open-Meteo Marine API Router
Provides free marine weather data (waves, wind, temperature, etc.)
No API key required - completely free for non-commercial use.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import httpx
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/open-meteo-marine", tags=["open-meteo-marine"])

_TIMEOUT = httpx.Timeout(30.0, connect=10.0)
_BASE_URL = "https://marine-api.open-meteo.com/v1/marine"


class MarineDataPoint(BaseModel):
    time: Optional[str] = None
    wave_height: Optional[float] = None
    wave_direction: Optional[float] = None
    wave_period: Optional[float] = None
    wind_wave_height: Optional[float] = None
    swell_wave_height: Optional[float] = None
    swell_wave_direction: Optional[float] = None
    swell_wave_period: Optional[float] = None


class MarineForecastResponse(BaseModel):
    latitude: float
    longitude: float
    hourly: Dict[str, Any]
    daily: Optional[Dict[str, Any]] = None


async def _get(url: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Make GET request to Open-Meteo Marine API."""
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPStatusError as exc:
        logger.error("Open-Meteo Marine API error: %s", exc)
        raise HTTPException(
            status_code=502, detail=f"Open-Meteo Marine API error: {exc}"
        )
    except httpx.RequestError as exc:
        logger.error("Open-Meteo Marine request failed: %s", exc)
        raise HTTPException(
            status_code=502, detail=f"Open-Meteo Marine unreachable: {exc}"
        )


@router.get("/ping")
async def open_meteo_ping():
    """Health check for Open-Meteo Marine API."""
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
            resp = await client.get(
                _BASE_URL,
                params={"latitude": 0, "longitude": 0, "current": "wave_height"},
            )
            ok = resp.status_code == 200
            return {"ok": ok, "status_code": resp.status_code}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.get("/forecast")
async def get_marine_forecast(
    latitude: float = Query(..., ge=-90, le=90, description="Latitude"),
    longitude: float = Query(..., ge=-180, le=180, description="Longitude"),
    hourly: Optional[str] = Query(
        None,
        description="Comma-separated hourly variables (wave_height, wave_direction, wave_period, wind_wave_height, swell_wave_height, swell_wave_direction, swell_wave_period, sea_surface_temperature)",
    ),
    daily: Optional[str] = Query(None, description="Comma-separated daily variables"),
    timezone: str = Query("auto", description="Timezone (auto, UTC, etc.)"),
    forecast_days: int = Query(7, ge=1, le=16, description="Number of forecast days"),
):
    """
    Get marine forecast data for a location.

    Available hourly variables:
    - wave_height, wave_direction, wave_period
    - wind_wave_height, wind_wave_direction, wind_wave_period
    - swell_wave_height, swell_wave_direction, swell_wave_period
    - sea_surface_temperature

    Example: /forecast?latitude=40.7&-74.0&hourly=wave_height,wave_period,sea_surface_temperature
    """
    params: Dict[str, Any] = {
        "latitude": latitude,
        "longitude": longitude,
        "forecast_days": forecast_days,
        "timezone": timezone,
    }

    if hourly:
        params["hourly"] = hourly
    if daily:
        params["daily"] = daily

    data = await _get(_BASE_URL, params)
    return data


@router.get("/wave")
async def get_wave_data(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    forecast_days: int = Query(7, ge=1, le=16),
):
    """Get wave data specifically (height, direction, period)."""
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": "wave_height,wave_direction,wave_period,wind_wave_height,swell_wave_height,swell_wave_direction,swell_wave_period",
        "forecast_days": forecast_days,
        "timezone": "auto",
    }
    data = await _get(_BASE_URL, params)
    return data


@router.get("/sea-temperature")
async def get_sea_temperature(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    forecast_days: int = Query(7, ge=1, le=16),
):
    """Get sea surface temperature forecast."""
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": "sea_surface_temperature",
        "forecast_days": forecast_days,
        "timezone": "auto",
    }
    data = await _get(_BASE_URL, params)
    return data


@router.get("/wind-waves")
async def get_wind_waves(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    forecast_days: int = Query(7, ge=1, le=16),
):
    """Get wind wave data."""
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": "wind_wave_height,wind_wave_direction,wind_wave_period",
        "forecast_days": forecast_days,
        "timezone": "auto",
    }
    data = await _get(_BASE_URL, params)
    return data


@router.get("/swell")
async def get_swell_data(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    forecast_days: int = Query(7, ge=1, le=16),
):
    """Get swell wave data."""
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": "swell_wave_height,swell_wave_direction,swell_wave_period",
        "forecast_days": forecast_days,
        "timezone": "auto",
    }
    data = await _get(_BASE_URL, params)
    return data
