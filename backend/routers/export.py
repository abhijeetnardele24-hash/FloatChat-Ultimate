"""
Export router for filtered ARGO data.
Provides CSV/JSON exports with reproducibility metadata.
"""

from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

import numpy as np
import xarray as xr
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from core.db import build_engine, build_session_local, get_database_url
from .argo_filter import FloatFilter, MeasurementFilter, ProfileFilter

DATABASE_URL = get_database_url()
engine = build_engine(DATABASE_URL)
SessionLocal = build_session_local(engine)

router = APIRouter(prefix="/api/v1/export", tags=["export"])


class ExportSnapshotRequest(BaseModel):
    float_filter: FloatFilter
    profile_filter: ProfileFilter
    measurement_filter: MeasurementFilter


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _in_clause(prefix: str, values: List[Any], params: Dict[str, Any]) -> str:
    placeholders = []
    for i, value in enumerate(values):
        key = f"{prefix}_{i}"
        placeholders.append(f":{key}")
        params[key] = value
    return ", ".join(placeholders)


def _serializable(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def _rows_to_csv(rows: List[Dict[str, Any]]) -> str:
    if not rows:
        return ""
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    for row in rows:
        writer.writerow({k: _serializable(v) for k, v in row.items()})
    return output.getvalue()


def _build_citation(resource: str, row_count: int) -> str:
    timestamp = datetime.now(timezone.utc).isoformat()
    return (
        "FloatChat Ultimate export; "
        f"resource={resource}; rows={row_count}; exported_at={timestamp}; "
        "source=ARGO + platform filters"
    )


def _build_float_query(filter_params: FloatFilter) -> Tuple[str, Dict[str, Any]]:
    query = """
        SELECT
            id, wmo_number, platform_type, deployment_date, last_location_date,
            last_latitude, last_longitude, status, program, ocean_basin
        FROM argo_floats
        WHERE 1=1
    """
    params: Dict[str, Any] = {}

    if filter_params.bbox:
        query += " AND last_longitude BETWEEN :min_lon AND :max_lon AND last_latitude BETWEEN :min_lat AND :max_lat"
        params.update(
            {
                "min_lon": filter_params.bbox.min_lon,
                "max_lon": filter_params.bbox.max_lon,
                "min_lat": filter_params.bbox.min_lat,
                "max_lat": filter_params.bbox.max_lat,
            }
        )
    if filter_params.start_date:
        query += " AND last_location_date >= :start_date"
        params["start_date"] = filter_params.start_date
    if filter_params.end_date:
        query += " AND last_location_date <= :end_date"
        params["end_date"] = filter_params.end_date
    if filter_params.status:
        query += " AND status = :status"
        params["status"] = filter_params.status
    if filter_params.ocean_basin:
        query += " AND ocean_basin = :ocean_basin"
        params["ocean_basin"] = filter_params.ocean_basin
    if filter_params.wmo_numbers:
        clause = _in_clause("wmo", filter_params.wmo_numbers, params)
        query += f" AND wmo_number IN ({clause})"

    return query, params


def _build_profile_query(filter_params: ProfileFilter) -> Tuple[str, Dict[str, Any]]:
    query = """
        SELECT
            p.id, p.wmo_number, p.cycle_number, p.profile_date, p.latitude, p.longitude,
            p.position_qc, p.data_mode, f.platform_type, f.status, f.ocean_basin
        FROM argo_profiles p
        JOIN argo_floats f ON p.float_id = f.id
        WHERE 1=1
    """
    params: Dict[str, Any] = {}

    if filter_params.bbox:
        query += " AND p.longitude BETWEEN :min_lon AND :max_lon AND p.latitude BETWEEN :min_lat AND :max_lat"
        params.update(
            {
                "min_lon": filter_params.bbox.min_lon,
                "max_lon": filter_params.bbox.max_lon,
                "min_lat": filter_params.bbox.min_lat,
                "max_lat": filter_params.bbox.max_lat,
            }
        )
    if filter_params.start_date:
        query += " AND p.profile_date >= :start_date"
        params["start_date"] = filter_params.start_date
    if filter_params.end_date:
        query += " AND p.profile_date <= :end_date"
        params["end_date"] = filter_params.end_date
    if filter_params.wmo_numbers:
        clause = _in_clause("wmo", filter_params.wmo_numbers, params)
        query += f" AND p.wmo_number IN ({clause})"
    if filter_params.data_mode:
        query += " AND p.data_mode = :data_mode"
        params["data_mode"] = filter_params.data_mode
    if filter_params.min_depth is not None or filter_params.max_depth is not None:
        query += " AND EXISTS (SELECT 1 FROM argo_measurements m WHERE m.profile_id = p.id"
        if filter_params.min_depth is not None:
            query += " AND m.depth >= :min_depth"
            params["min_depth"] = filter_params.min_depth
        if filter_params.max_depth is not None:
            query += " AND m.depth <= :max_depth"
            params["max_depth"] = filter_params.max_depth
        query += ")"

    return query, params


def _build_measurements_query(filter_params: MeasurementFilter) -> Tuple[str, Dict[str, Any]]:
    query = """
        SELECT
            m.id, m.profile_id, p.wmo_number, p.profile_date,
            m.pressure, m.depth, m.temperature, m.temperature_qc, m.salinity, m.salinity_qc
        FROM argo_measurements m
        JOIN argo_profiles p ON m.profile_id = p.id
        WHERE 1=1
    """
    params: Dict[str, Any] = {}

    if filter_params.profile_ids:
        clause = _in_clause("pid", filter_params.profile_ids, params)
        query += f" AND m.profile_id IN ({clause})"
    if filter_params.wmo_number:
        query += " AND p.wmo_number = :wmo_number"
        params["wmo_number"] = filter_params.wmo_number
    if filter_params.min_depth is not None:
        query += " AND m.depth >= :min_depth"
        params["min_depth"] = filter_params.min_depth
    if filter_params.max_depth is not None:
        query += " AND m.depth <= :max_depth"
        params["max_depth"] = filter_params.max_depth
    if filter_params.min_temperature is not None:
        query += " AND m.temperature >= :min_temperature"
        params["min_temperature"] = filter_params.min_temperature
    if filter_params.max_temperature is not None:
        query += " AND m.temperature <= :max_temperature"
        params["max_temperature"] = filter_params.max_temperature
    if filter_params.min_salinity is not None:
        query += " AND m.salinity >= :min_salinity"
        params["min_salinity"] = filter_params.min_salinity
    if filter_params.max_salinity is not None:
        query += " AND m.salinity <= :max_salinity"
        params["max_salinity"] = filter_params.max_salinity

    query += " AND (m.temperature_qc <= :qc_max OR m.salinity_qc <= :qc_max)"
    params["qc_max"] = filter_params.qc_max
    return query, params


def _download_headers(filename: str, citation: str) -> Dict[str, str]:
    return {
        "Content-Disposition": f'attachment; filename="{filename}"',
        "X-Suggested-Citation": citation,
        "Cache-Control": "no-store",
    }


def _measurements_to_netcdf_bytes(rows: List[Dict[str, Any]]) -> bytes:
    obs = len(rows)
    if obs == 0:
        ds = xr.Dataset(
            data_vars={
                "pressure": ("obs", np.array([], dtype=np.float64)),
                "depth": ("obs", np.array([], dtype=np.float64)),
                "temperature": ("obs", np.array([], dtype=np.float64)),
                "salinity": ("obs", np.array([], dtype=np.float64)),
                "temperature_qc": ("obs", np.array([], dtype=np.int32)),
                "salinity_qc": ("obs", np.array([], dtype=np.int32)),
            },
            coords={"obs": np.array([], dtype=np.int32)},
        )
        ds.attrs["title"] = "FloatChat measurements export"
        ds.attrs["source"] = "ARGO + FloatChat filters"
        return ds.to_netcdf()

    def arr(name: str, dtype, default=np.nan):
        values = []
        for row in rows:
            val = row.get(name, default)
            if val is None:
                val = default
            values.append(val)
        return np.array(values, dtype=dtype)

    wmo = np.array([str(row.get("wmo_number", "")) for row in rows], dtype="U32")
    profile_date = np.array([str(row.get("profile_date", "")) for row in rows], dtype="U32")

    ds = xr.Dataset(
        data_vars={
            "pressure": ("obs", arr("pressure", np.float64)),
            "depth": ("obs", arr("depth", np.float64)),
            "temperature": ("obs", arr("temperature", np.float64)),
            "salinity": ("obs", arr("salinity", np.float64)),
            "temperature_qc": ("obs", arr("temperature_qc", np.int32, default=-1)),
            "salinity_qc": ("obs", arr("salinity_qc", np.int32, default=-1)),
            "profile_id": ("obs", arr("profile_id", np.int64, default=-1)),
            "wmo_number": ("obs", wmo),
            "profile_date": ("obs", profile_date),
        },
        coords={"obs": np.arange(obs, dtype=np.int32)},
    )
    ds.attrs["title"] = "FloatChat measurements export"
    ds.attrs["source"] = "ARGO + FloatChat filters"
    ds.attrs["conventions"] = "CF-1.8 (partial)"
    return ds.to_netcdf()


@router.post("/floats/csv")
async def export_floats_csv(
    filter_params: FloatFilter,
    db: Session = Depends(get_db),
    export_limit: int = Query(default=10000, ge=1, le=50000),
):
    query, params = _build_float_query(filter_params)
    query += " ORDER BY last_location_date DESC NULLS LAST LIMIT :export_limit"
    params["export_limit"] = export_limit

    rows = [dict(row) for row in db.execute(text(query), params).mappings().all()]
    csv_body = _rows_to_csv(rows)
    citation = _build_citation("floats_csv", len(rows))
    filename = f"argo_floats_export_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv"
    return StreamingResponse(
        iter([csv_body]),
        media_type="text/csv",
        headers=_download_headers(filename, citation),
    )


@router.post("/profiles/csv")
async def export_profiles_csv(
    filter_params: ProfileFilter,
    db: Session = Depends(get_db),
    export_limit: int = Query(default=20000, ge=1, le=50000),
):
    query, params = _build_profile_query(filter_params)
    query += " ORDER BY p.profile_date DESC LIMIT :export_limit"
    params["export_limit"] = export_limit

    rows = [dict(row) for row in db.execute(text(query), params).mappings().all()]
    csv_body = _rows_to_csv(rows)
    citation = _build_citation("profiles_csv", len(rows))
    filename = f"argo_profiles_export_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv"
    return StreamingResponse(
        iter([csv_body]),
        media_type="text/csv",
        headers=_download_headers(filename, citation),
    )


@router.post("/measurements/csv")
async def export_measurements_csv(
    filter_params: MeasurementFilter,
    db: Session = Depends(get_db),
    export_limit: int = Query(default=50000, ge=1, le=100000),
):
    query, params = _build_measurements_query(filter_params)
    query += " ORDER BY m.depth ASC NULLS LAST LIMIT :export_limit"
    params["export_limit"] = export_limit

    rows = [dict(row) for row in db.execute(text(query), params).mappings().all()]
    csv_body = _rows_to_csv(rows)
    citation = _build_citation("measurements_csv", len(rows))
    filename = f"argo_measurements_export_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv"
    return StreamingResponse(
        iter([csv_body]),
        media_type="text/csv",
        headers=_download_headers(filename, citation),
    )


@router.post("/measurements/netcdf")
async def export_measurements_netcdf(
    filter_params: MeasurementFilter,
    db: Session = Depends(get_db),
    export_limit: int = Query(default=50000, ge=1, le=150000),
):
    query, params = _build_measurements_query(filter_params)
    query += " ORDER BY m.depth ASC NULLS LAST LIMIT :export_limit"
    params["export_limit"] = export_limit

    rows = [dict(row) for row in db.execute(text(query), params).mappings().all()]
    nc_bytes = _measurements_to_netcdf_bytes(rows)
    citation = _build_citation("measurements_netcdf", len(rows))
    filename = f"argo_measurements_export_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.nc"
    return StreamingResponse(
        iter([nc_bytes]),
        media_type="application/x-netcdf",
        headers=_download_headers(filename, citation),
    )


@router.post("/snapshot/json")
async def export_snapshot_json(
    payload: ExportSnapshotRequest,
    db: Session = Depends(get_db),
    export_limit_each: int = Query(default=10000, ge=1, le=50000),
):
    floats_query, floats_params = _build_float_query(payload.float_filter)
    floats_query += " ORDER BY last_location_date DESC NULLS LAST LIMIT :export_limit"
    floats_params["export_limit"] = export_limit_each
    floats_rows = [dict(row) for row in db.execute(text(floats_query), floats_params).mappings().all()]

    profiles_query, profiles_params = _build_profile_query(payload.profile_filter)
    profiles_query += " ORDER BY p.profile_date DESC LIMIT :export_limit"
    profiles_params["export_limit"] = export_limit_each
    profiles_rows = [dict(row) for row in db.execute(text(profiles_query), profiles_params).mappings().all()]

    measurements_query, measurements_params = _build_measurements_query(payload.measurement_filter)
    measurements_query += " ORDER BY m.depth ASC NULLS LAST LIMIT :export_limit"
    measurements_params["export_limit"] = export_limit_each
    measurements_rows = [dict(row) for row in db.execute(text(measurements_query), measurements_params).mappings().all()]

    citation = _build_citation(
        "snapshot_json",
        len(floats_rows) + len(profiles_rows) + len(measurements_rows),
    )
    body = {
        "metadata": {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "citation": citation,
            "counts": {
                "floats": len(floats_rows),
                "profiles": len(profiles_rows),
                "measurements": len(measurements_rows),
            },
        },
        "data": {
            "floats": [{k: _serializable(v) for k, v in row.items()} for row in floats_rows],
            "profiles": [{k: _serializable(v) for k, v in row.items()} for row in profiles_rows],
            "measurements": [{k: _serializable(v) for k, v in row.items()} for row in measurements_rows],
        },
    }
    payload_str = json.dumps(body, ensure_ascii=True)
    filename = f"argo_snapshot_export_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
    return StreamingResponse(
        iter([payload_str]),
        media_type="application/json",
        headers=_download_headers(filename, citation),
    )
