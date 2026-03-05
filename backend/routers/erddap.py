"""
ERDDAP External API Router
Proxies requests to ERDDAP data servers for oceanographic data.
ERDDAP provides access to thousands of ocean and atmospheric datasets.

No API key required for most public datasets.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import httpx
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/erddap", tags=["erddap-external"])

_TIMEOUT = httpx.Timeout(60.0, connect=15.0)

_ERDDAP_SERVERS = {
    "oceanobservatories": "https://erddap.dataexplorer.oceanobservatories.org/erddap",
    "noaa-pmel": "https://data.pmel.noaa.gov/pmel/erddap",
    "noaa-ncei": "https://www.ncei.noaa.gov/erddap",
}


class DatasetInfo(BaseModel):
    dataset_id: str
    title: Optional[str] = None
    institution: Optional[str] = None
    summary: Optional[str] = None


async def _get(url: str, params: Optional[Dict[str, Any]] = None) -> Any:
    """Make GET request to ERDDAP server."""
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            content_type = resp.headers.get("content-type", "")
            if "application/json" in content_type:
                return resp.json()
            return resp.text
    except httpx.HTTPStatusError as exc:
        logger.error("ERDDAP error: %s", exc)
        raise HTTPException(status_code=502, detail=f"ERDDAP API error: {exc}")
    except httpx.RequestError as exc:
        logger.error("ERDDAP request failed: %s", exc)
        raise HTTPException(status_code=502, detail=f"ERDDAP unreachable: {exc}")


@router.get("/ping")
async def erddap_ping(
    server: str = Query(
        "oceanobservatories",
        description="ERDDAP server: oceanobservatories, noaa-pmel, noaa-ncei",
    ),
):
    """Health check for ERDDAP servers."""
    base_url = _ERDDAP_SERVERS.get(server, _ERDDAP_SERVERS["oceanobservatories"])
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
            resp = await client.get(f"{base_url}/version")
            ok = resp.status_code == 200
            return {
                "ok": ok,
                "server": server,
                "version": resp.text.strip() if ok else None,
            }
    except Exception as e:
        return {"ok": False, "server": server, "error": str(e)}


@router.get("/servers")
async def list_erddap_servers():
    """List available ERDDAP servers."""
    return {"servers": _ERDDAP_SERVERS}


@router.get("/datasets")
async def list_datasets(
    server: str = Query("oceanobservatories", description="ERDDAP server"),
    search_for: Optional[str] = Query(None, description="Search term"),
    page: int = Query(1, ge=1, description="Page number"),
    items_per_page: int = Query(100, ge=1, le=1000),
):
    """
    List available datasets on an ERDDAP server.

    Search for datasets by term, e.g., "temperature", "salinity", "argo".
    """
    base_url = _ERDDAP_SERVERS.get(server, _ERDDAP_SERVERS["oceanobservatories"])
    params = {
        "page": page,
        "itemsPerPage": items_per_page,
        "protocol": "tabledap,griddap",
    }
    if search_for:
        params["searchFor"] = search_for

    url = f"{base_url}/search/index.csv"
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()

            lines = resp.text.strip().split("\n")
            if len(lines) < 2:
                return {"datasets": [], "total": 0}

            headers = lines[0].split(",")
            datasets = []
            for line in lines[1:]:
                if line.strip():
                    values = line.split(",")
                    if len(values) >= 2:
                        datasets.append(
                            {
                                "dataset_id": values[0],
                                "title": values[1] if len(values) > 1 else None,
                            }
                        )

            return {
                "server": server,
                "datasets": datasets[:items_per_page],
                "total": len(datasets),
                "search_for": search_for,
            }
    except Exception as e:
        raise HTTPException(
            status_code=502, detail=f"Failed to list datasets: {str(e)}"
        )


@router.get("/dataset-info")
async def get_dataset_info(
    dataset_id: str,
    server: str = Query("oceanobservatories", description="ERDDAP server"),
):
    """Get detailed information about a specific dataset."""
    base_url = _ERDDAP_SERVERS.get(server, _ERDDAP_SERVERS["oceanobservatories"])
    url = f"{base_url}/info/{dataset_id}/index.csv"

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(url)
            resp.raise_for_status()

            lines = resp.text.strip().split("\n")
            if len(lines) < 2:
                return {"error": "No info available"}

            info = {}
            for line in lines[1:]:
                if line.strip():
                    parts = line.split(",")
                    if len(parts) >= 2:
                        info[parts[0]] = parts[1]

            return {"dataset_id": dataset_id, "server": server, "info": info}
    except httpx.HTTPStatusError:
        return {"error": f"Dataset {dataset_id} not found on {server}"}
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/data")
async def get_erddap_data(
    dataset_id: str,
    variables: Optional[str] = Query(None, description="Comma-separated variables"),
    latitude: Optional[float] = Query(None, ge=-90, le=90),
    longitude: Optional[float] = Query(None, ge=-180, le=180),
    depth: Optional[float] = Query(None, ge=0, le=11000),
    time_start: Optional[str] = Query(None, description="Start time (ISO 8601)"),
    time_end: Optional[str] = Query(None, description="End time (ISO 8601)"),
    server: str = Query("oceanobservatories", description="ERDDAP server"),
    format: str = Query("json", description="Output format: json, csv, nc"),
    limit: int = Query(1000, ge=1, le=10000),
):
    """
    Fetch data from an ERDDAP dataset.

    Example: /data?dataset_id=erdGAtempDay&variables=time,latitude,longitude,temperature&latitude=0&longitude=-140&time_start=2024-01-01&time_end=2024-12-31
    """
    base_url = _ERDDAP_SERVERS.get(server, _ERDDAP_SERVERS["oceanobservatories"])

    ext = "json" if format == "json" else format
    url = f"{base_url}/tabledap/{dataset_id}.{ext}"

    params: Dict[str, Any] = {}

    if variables:
        params["variables"] = variables

    constraints = []
    if latitude is not None:
        constraints.append(f"latitude>={latitude}")
    if longitude is not None:
        constraints.append(f"longitude>={longitude}")
    if depth is not None:
        constraints.append(f"depth>={depth}")
    if time_start:
        constraints.append(f"time>={time_start}")
    if time_end:
        constraints.append(f"time<={time_end}")

    if constraints:
        params[".constraint"] = constraints

    params["limit"] = min(limit, 10000)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()

            if format == "json":
                return resp.json()
            elif format == "csv":
                return {"format": "csv", "data": resp.text}
            else:
                return {"format": format, "data": "binary data (not shown)"}
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=502, detail=f"ERDDAP data fetch error: {exc}")
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/search")
async def erddap_global_search(
    query: str = Query(..., description="Search query"),
    server: str = Query("oceanobservatories", description="ERDDAP server"),
    limit: int = Query(20, ge=1, le=100),
):
    """
    Search for datasets across ERDDAP.

    Example: /search?query=sea+surface+temperature
    """
    base_url = _ERDDAP_SERVERS.get(server, _ERDDAP_SERVERS["oceanobservatories"])
    params = {
        "searchFor": query,
        "page": 1,
        "itemsPerPage": limit,
    }

    url = f"{base_url}/search/index.csv"

    try:
        data = await _get(url, params)

        if isinstance(data, str):
            lines = data.strip().split("\n")
            results = []
            for line in lines[1:]:
                if line.strip():
                    parts = line.split(",")
                    if len(parts) >= 2:
                        results.append(
                            {
                                "dataset_id": parts[0],
                                "title": parts[1] if len(parts) > 1 else "Unknown",
                            }
                        )
            return {"query": query, "results": results, "count": len(results)}

        return {"query": query, "results": [], "error": "Unexpected response"}
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/popular")
async def get_popular_datasets(
    server: str = Query("oceanobservatories", description="ERDDAP server"),
    category: str = Query(
        "temperature",
        description="Category: temperature, salinity, chlorophyll, currents",
    ),
):
    """Get popular/common ocean datasets."""
    base_url = _ERDDAP_SERVERS.get(server, _ERDDAP_SERVERS["oceanobservatories"])

    popular_datasets = {
        "temperature": [
            {
                "id": "erdGAtempDay",
                "title": "Global Area Foundation Sea Surface Temperature",
            },
            {"id": "jplMURSST", "title": "Multi-scale Ultra-high Resolution SST"},
        ],
        "salinity": [
            {"id": "esaCoraSeasurfaceSalinity", "title": "Sea Surface Salinity"},
        ],
        "chlorophyll": [
            {"id": "erdMBchla8day", "title": "Chlorophyll-a, OCI algorithm"},
        ],
        "currents": [
            {"id": "usfDaacCurrents", "title": "Ocean Surface Currents"},
        ],
    }

    datasets = popular_datasets.get(category, popular_datasets["temperature"])
    return {"category": category, "server": server, "datasets": datasets}
