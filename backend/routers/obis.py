"""
OBIS API Router
Provides access to the Ocean Biodiversity Information System.
This is a public API and does not require an API key.
"""

import logging
from typing import Any, Dict, Optional

import httpx
from fastapi import APIRouter, HTTPException, Query

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/obis", tags=["obis-external"])

_TIMEOUT = httpx.Timeout(20.0, connect=5.0)

OBIS_BASE_URL = "https://api.obis.org/v3"

@router.get("/occurrence")
async def get_obis_occurrence(
    scientificname: Optional[str] = Query(None, description="Scientific name of species (e.g. 'Delphinidae')"),
    geometry: Optional[str] = Query(None, description="WKT geometry string (e.g. 'POLYGON((...))')"),
    startdate: Optional[str] = Query(None, description="Start date YYYY-MM-DD"),
    enddate: Optional[str] = Query(None, description="End date YYYY-MM-DD"),
    size: int = Query(50, description="Number of results (pageSize)"),
):
    """Fetch species occurrences from OBIS."""
    params: Dict[str, Any] = {"size": size}
    if scientificname:
        params["scientificname"] = scientificname
    if geometry:
        params["geometry"] = geometry
    if startdate:
        params["startdate"] = startdate
    if enddate:
        params["enddate"] = enddate
        
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(f"{OBIS_BASE_URL}/occurrence", params=params)
            resp.raise_for_status()
            data = resp.json()
            return {"total": data.get("total", 0), "results": data.get("results", [])}
    except Exception as exc:
        logger.error(f"OBIS occurrence error: {exc}")
        raise HTTPException(status_code=502, detail=f"OBIS API error: {exc}")

@router.get("/taxon/{scientificname}")
async def get_obis_taxon(scientificname: str):
    """Get taxonomic information for a species."""
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(f"{OBIS_BASE_URL}/taxon/{scientificname}")
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.error(f"OBIS taxon error: {exc}")
        raise HTTPException(status_code=502, detail=f"OBIS API error: {exc}")

@router.get("/ping")
async def obis_ping():
    """Check if OBIS public API is reachable."""
    return {"ok": True, "message": "OBIS router is active (Public Access)"}
