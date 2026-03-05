"""
Copernicus Marine Service (CMEMS) External API Router
Proxies requests to the Copernicus Marine Data Store (MDS) APIs.

Auth: uses Basic Auth with CMEMS_USERNAME and CMEMS_PASSWORD env vars.
"""

import os
import logging
from typing import Any, Dict, Optional

import httpx
from fastapi import APIRouter, HTTPException, Query

logger = logging.getLogger(__name__)

CMEMS_USERNAME = os.getenv("CMEMS_USERNAME", "")
CMEMS_PASSWORD = os.getenv("CMEMS_PASSWORD", "")
CMEMS_BASE_URL = os.getenv("CMEMS_BASE_URL", "https://wmts.marine.copernicus.eu/teroWmts")

router = APIRouter(prefix="/api/v1/cmems", tags=["cmems-external"])

_TIMEOUT = httpx.Timeout(20.0, connect=5.0)


async def _get(path: str, params: Optional[Dict[str, Any]] = None, use_auth: bool = False) -> Any:
    url = f"{CMEMS_BASE_URL}{path}"
    auth = (CMEMS_USERNAME, CMEMS_PASSWORD) if use_auth and CMEMS_USERNAME and CMEMS_PASSWORD else None

    # Using standard async HTTP client
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT, auth=auth) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            
            # Identify if the response is JSON or XML/capabilities
            content_type = resp.headers.get("content-type", "")
            if "application/json" in content_type:
                return resp.json()
            else:
                return resp.text
    except httpx.HTTPStatusError as exc:
        code = exc.response.status_code
        detail = exc.response.text[:300] if exc.response.text else str(exc)
        logger.error("CMEMS request to %s returned %d: %s", path, code, detail)
        # Authentication error
        if code in (401, 403):
            raise HTTPException(status_code=401, detail="CMEMS Authentication failed. Check CMEMS_USERNAME and CMEMS_PASSWORD.")
        raise HTTPException(status_code=502, detail=f"CMEMS API error ({code}): {detail}")
    except httpx.RequestError as exc:
        logger.error("CMEMS request to %s failed: %s", path, exc)
        raise HTTPException(status_code=502, detail=f"CMEMS unreachable: {exc}")


@router.get("/ping")
async def cmems_ping():
    """Quick health check to see if credentials are provided."""
    has_creds = bool((CMEMS_USERNAME or "").strip() and (CMEMS_PASSWORD or "").strip())
    
    # Simple check without hitting a heavy endpoint
    return {
        "ok": True, 
        "has_credentials": has_creds,
        "username": CMEMS_USERNAME if CMEMS_USERNAME else None,
        "message": "Copernicus router is active. Credentials " + ("found" if has_creds else "missing")
    }


@router.get("/wmts/capabilities")
async def get_wmts_capabilities():
    """Get the WMTS GetCapabilities XML document for ocean map tiles."""
    params = {
        "service": "WMTS",
        "request": "GetCapabilities",
    }
    # This endpoint is usually open to get catalog metadata
    xml_data = await _get("/", params=params)
    return {"raw_xml_length": len(xml_data) if isinstance(xml_data, str) else 0}


@router.get("/catalogue/search")
async def search_catalogue(
    query: str = Query("temperature", description="Search term for ocean products"),
):
    """Search the Copernicus marine data catalogue (using marine.copernicus.eu public search)"""
    search_url = "https://catalogue.marine.copernicus.eu/api/v2/products"
    params = {
        "searchText": query,
        "size": 10
    }
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(search_url, params=params)
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        logger.error(f"CMEMS catalogue search failed: {e}")
        raise HTTPException(status_code=502, detail=f"CMEMS catalogue unreachable: {e}")
