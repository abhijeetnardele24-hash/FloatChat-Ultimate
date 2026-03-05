"""
ARGO Data Filter API Router
Provides comprehensive filtering for ARGO floats, profiles, and measurements
"""

from fastapi import APIRouter, Depends, Query, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel, Field, model_validator
from typing import Optional, List
from datetime import datetime, timezone
from threading import Lock
import os
import json
import uuid

from core.db import build_engine, build_session_local, get_database_url

# Database configuration
DATABASE_URL = get_database_url()
engine = build_engine(DATABASE_URL)
SessionLocal = build_session_local(engine)

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

router = APIRouter(prefix="/api/v1/argo", tags=["argo-filter"])
_ingestion_state_lock = Lock()
_ingestion_state = {
    "running": False,
    "status": "idle",
    "started_at": None,
    "finished_at": None,
    "request": None,
    "summary": None,
    "error": None,
}
_INGESTION_JOB_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS argo_ingestion_jobs (
    id VARCHAR(64) PRIMARY KEY,
    status VARCHAR(20) NOT NULL,
    request_payload TEXT,
    summary_payload TEXT,
    error TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    finished_at TIMESTAMP
)
"""


def _to_iso(value):
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _parse_iso_datetime(value: str, field_name: str) -> datetime:
    candidate = value.strip()
    try:
        return datetime.fromisoformat(candidate.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a valid ISO date/datetime string") from exc

# ============================================
# Pydantic Models
# ============================================

class BBox(BaseModel):
    """Bounding box for spatial filtering"""
    min_lon: float = Field(..., ge=-180, le=180, description="Minimum longitude")
    min_lat: float = Field(..., ge=-90, le=90, description="Minimum latitude")
    max_lon: float = Field(..., ge=-180, le=180, description="Maximum longitude")
    max_lat: float = Field(..., ge=-90, le=90, description="Maximum latitude")

    @model_validator(mode="after")
    def validate_bbox(self):
        if self.min_lon > self.max_lon:
            raise ValueError("bbox.min_lon must be <= bbox.max_lon")
        if self.min_lat > self.max_lat:
            raise ValueError("bbox.min_lat must be <= bbox.max_lat")
        return self

class FloatFilter(BaseModel):
    """Filter parameters for ARGO floats"""
    bbox: Optional[BBox] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    status: Optional[str] = Field(None, description="ACTIVE or INACTIVE")
    ocean_basin: Optional[str] = None
    wmo_numbers: Optional[List[str]] = None
    limit: int = Field(100, ge=1, le=1000)
    offset: int = Field(0, ge=0)

    @model_validator(mode="after")
    def validate_date_range(self):
        if self.start_date and self.end_date:
            start = _parse_iso_datetime(self.start_date, "start_date")
            end = _parse_iso_datetime(self.end_date, "end_date")
            if start > end:
                raise ValueError("start_date must be <= end_date")
        return self

class ProfileFilter(BaseModel):
    """Filter parameters for ARGO profiles"""
    bbox: Optional[BBox] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    wmo_numbers: Optional[List[str]] = None
    min_depth: Optional[float] = Field(None, ge=0)
    max_depth: Optional[float] = Field(None, ge=0)
    data_mode: Optional[str] = Field(None, description="R, A, or D")
    limit: int = Field(100, ge=1, le=1000)
    offset: int = Field(0, ge=0)

    @model_validator(mode="after")
    def validate_filters(self):
        if self.start_date and self.end_date:
            start = _parse_iso_datetime(self.start_date, "start_date")
            end = _parse_iso_datetime(self.end_date, "end_date")
            if start > end:
                raise ValueError("start_date must be <= end_date")
        if self.min_depth is not None and self.max_depth is not None and self.min_depth > self.max_depth:
            raise ValueError("min_depth must be <= max_depth")
        return self

class MeasurementFilter(BaseModel):
    """Filter parameters for measurements"""
    profile_ids: Optional[List[int]] = None
    wmo_number: Optional[str] = None
    min_depth: Optional[float] = Field(None, ge=0)
    max_depth: Optional[float] = Field(None, ge=0)
    min_temperature: Optional[float] = None
    max_temperature: Optional[float] = None
    min_salinity: Optional[float] = None
    max_salinity: Optional[float] = None
    qc_max: int = Field(2, ge=0, le=9, description="Maximum QC flag (0-9)")
    limit: int = Field(1000, ge=1, le=10000)
    offset: int = Field(0, ge=0)

    @model_validator(mode="after")
    def validate_ranges(self):
        if self.min_depth is not None and self.max_depth is not None and self.min_depth > self.max_depth:
            raise ValueError("min_depth must be <= max_depth")
        if (
            self.min_temperature is not None
            and self.max_temperature is not None
            and self.min_temperature > self.max_temperature
        ):
            raise ValueError("min_temperature must be <= max_temperature")
        if self.min_salinity is not None and self.max_salinity is not None and self.min_salinity > self.max_salinity:
            raise ValueError("min_salinity must be <= max_salinity")
        return self


class IngestionRunRequest(BaseModel):
    region: str = Field(default="indian")
    bbox: Optional[BBox] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    index_limit: int = Field(default=5000, ge=0, le=1_000_000)
    max_profiles: int = Field(default=500, ge=0, le=1_000_000)
    cache_dir: Optional[str] = None
    request_timeout: int = Field(default=60, ge=5, le=600)
    sleep_seconds: float = Field(default=0.1, ge=0.0, le=5.0)
    force_redownload: bool = False
    dry_run: bool = False

    @model_validator(mode="after")
    def validate_request(self):
        normalized_region = self.region.strip().lower()
        if normalized_region not in {"indian", "global", "custom"}:
            raise ValueError("region must be one of: indian, global, custom")
        if normalized_region == "custom" and self.bbox is None:
            raise ValueError("bbox is required when region=custom")
        self.region = normalized_region

        if self.start_date and self.end_date:
            start = _parse_iso_datetime(self.start_date, "start_date")
            end = _parse_iso_datetime(self.end_date, "end_date")
            if start > end:
                raise ValueError("start_date must be <= end_date")
        return self


def _parse_optional_yyyy_mm_dd(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    candidate = value.strip()
    for fmt in ("%Y-%m-%d",):
        try:
            return datetime.strptime(candidate[:10], fmt)
        except ValueError:
            continue
    return _parse_iso_datetime(candidate, "date")


def _ensure_ingestion_job_table(db: Session) -> None:
    db.execute(text(_INGESTION_JOB_TABLE_SQL))
    db.commit()


def _job_row_to_payload(row) -> dict:
    request_payload = {}
    summary_payload = {}
    try:
        request_payload = json.loads(row.get("request_payload") or "{}")
    except Exception:
        request_payload = {}
    try:
        summary_payload = json.loads(row.get("summary_payload") or "{}")
    except Exception:
        summary_payload = {}
    return {
        "id": row.get("id"),
        "status": row.get("status"),
        "request": request_payload,
        "summary": summary_payload,
        "error": row.get("error"),
        "created_at": _to_iso(row.get("created_at")),
        "started_at": _to_iso(row.get("started_at")),
        "finished_at": _to_iso(row.get("finished_at")),
    }


def _get_recent_ingestion_jobs(db: Session, limit: int = 20) -> List[dict]:
    _ensure_ingestion_job_table(db)
    rows = db.execute(
        text(
            """
            SELECT id, status, request_payload, summary_payload, error, created_at, started_at, finished_at
            FROM argo_ingestion_jobs
            ORDER BY created_at DESC
            LIMIT :limit
            """
        ),
        {"limit": max(1, limit)},
    ).mappings().all()
    return [_job_row_to_payload(row) for row in rows]


def _create_ingestion_job(db: Session, request_payload: dict, status: str = "running") -> str:
    _ensure_ingestion_job_table(db)
    job_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    db.execute(
        text(
            """
            INSERT INTO argo_ingestion_jobs (id, status, request_payload, created_at, started_at)
            VALUES (:id, :status, :request_payload, :created_at, :started_at)
            """
        ),
        {
            "id": job_id,
            "status": status,
            "request_payload": json.dumps(request_payload, ensure_ascii=True),
            "created_at": now,
            "started_at": now if status == "running" else None,
        },
    )
    db.commit()
    return job_id


def _update_ingestion_job(job_id: str, status: str, summary: Optional[dict] = None, error: Optional[str] = None) -> None:
    db = SessionLocal()
    try:
        _ensure_ingestion_job_table(db)
        params = {
            "id": job_id,
            "status": status,
            "summary_payload": json.dumps(summary or {}, ensure_ascii=True),
            "error": error,
            "finished_at": datetime.now(timezone.utc) if status in {"completed", "failed"} else None,
        }
        db.execute(
            text(
                """
                UPDATE argo_ingestion_jobs
                SET
                    status = :status,
                    summary_payload = :summary_payload,
                    error = :error,
                    finished_at = :finished_at
                WHERE id = :id
                """
            ),
            params,
        )
        db.commit()
    finally:
        db.close()


def _ingestion_dataset_summary(db: Session) -> dict:
    try:
        total_floats = int(db.execute(text("SELECT COUNT(*) FROM argo_floats")).scalar() or 0)
        total_profiles = int(db.execute(text("SELECT COUNT(*) FROM argo_profiles")).scalar() or 0)
        total_measurements = int(db.execute(text("SELECT COUNT(*) FROM argo_measurements")).scalar() or 0)
        latest_profile = db.execute(text("SELECT MAX(profile_date) FROM argo_profiles")).scalar()
        return {
            "total_floats": total_floats,
            "total_profiles": total_profiles,
            "total_measurements": total_measurements,
            "latest_profile": _to_iso(latest_profile),
        }
    except Exception as exc:
        return {"error": str(exc)}


def _build_ingestion_config(payload: IngestionRunRequest):
    from data_ingestion.argo_ingestion import IngestionConfig

    bbox = None
    if payload.bbox:
        bbox = (
            payload.bbox.min_lon,
            payload.bbox.min_lat,
            payload.bbox.max_lon,
            payload.bbox.max_lat,
        )

    return IngestionConfig(
        region=payload.region,
        bbox=bbox,
        start_date=_parse_optional_yyyy_mm_dd(payload.start_date),
        end_date=_parse_optional_yyyy_mm_dd(payload.end_date),
        index_limit=payload.index_limit if payload.index_limit > 0 else None,
        max_profiles=payload.max_profiles if payload.max_profiles > 0 else None,
        cache_dir=payload.cache_dir or os.getenv("ARGO_CACHE_DIR", "./data/argo"),
        request_timeout=payload.request_timeout,
        sleep_seconds=payload.sleep_seconds,
        force_redownload=payload.force_redownload,
    )


def _run_ingestion_job(job_id: str, payload_dict: dict) -> None:
    from data_ingestion.argo_ingestion import ArgoDataIngestion

    payload = IngestionRunRequest(**payload_dict)
    try:
        config = _build_ingestion_config(payload)
        ingestion = ArgoDataIngestion(config)
        summary = ingestion.run_ingestion()
        _update_ingestion_job(job_id=job_id, status="completed", summary=summary, error=None)
        with _ingestion_state_lock:
            _ingestion_state.update(
                {
                    "running": False,
                    "status": "completed",
                    "finished_at": datetime.now(timezone.utc).isoformat(),
                    "summary": summary,
                    "error": None,
                    "job_id": job_id,
                }
            )
    except Exception as exc:
        _update_ingestion_job(job_id=job_id, status="failed", summary=None, error=str(exc))
        with _ingestion_state_lock:
            _ingestion_state.update(
                {
                    "running": False,
                    "status": "failed",
                    "finished_at": datetime.now(timezone.utc).isoformat(),
                    "error": str(exc),
                    "job_id": job_id,
                }
            )

# ============================================
# API Endpoints
# ============================================

@router.post("/floats/filter")
async def filter_floats(filter_params: FloatFilter, db: Session = Depends(get_db)):
    """
    Filter ARGO floats by bbox, date, status, and other criteria
    
    Returns:
        - total: Total count matching filter
        - limit: Requested limit
        - offset: Requested offset
        - data: List of floats
    """
    query = """
        SELECT 
            id, wmo_number, platform_type, deployment_date,
            last_latitude, last_longitude, last_location_date,
            status, ocean_basin, program
        FROM argo_floats
        WHERE 1=1
    """
    params = {}
    
    # Bbox filter using PostGIS
    if filter_params.bbox:
        query += """
            AND location IS NOT NULL
            AND ST_Within(
                location::geometry,
                ST_MakeEnvelope(:min_lon, :min_lat, :max_lon, :max_lat, 4326)
            )
        """
        params.update({
            "min_lon": filter_params.bbox.min_lon,
            "min_lat": filter_params.bbox.min_lat,
            "max_lon": filter_params.bbox.max_lon,
            "max_lat": filter_params.bbox.max_lat
        })
    
    # Date filter
    if filter_params.start_date:
        query += " AND last_location_date >= :start_date"
        params["start_date"] = filter_params.start_date
    
    if filter_params.end_date:
        query += " AND last_location_date <= :end_date"
        params["end_date"] = filter_params.end_date
    
    # Status filter
    if filter_params.status:
        query += " AND status = :status"
        params["status"] = filter_params.status
    
    # Ocean basin filter
    if filter_params.ocean_basin:
        query += " AND ocean_basin = :ocean_basin"
        params["ocean_basin"] = filter_params.ocean_basin
    
    # WMO numbers filter
    if filter_params.wmo_numbers:
        placeholders = ", ".join([f":wmo_{i}" for i in range(len(filter_params.wmo_numbers))])
        query += f" AND wmo_number IN ({placeholders})"
        for i, wmo in enumerate(filter_params.wmo_numbers):
            params[f"wmo_{i}"] = wmo
    
    # Get total count
    count_query = f"SELECT COUNT(*) FROM ({query}) AS filtered"
    total = db.execute(text(count_query), params).scalar()
    
    # Add pagination
    query += " ORDER BY last_location_date DESC LIMIT :limit OFFSET :offset"
    params["limit"] = filter_params.limit
    params["offset"] = filter_params.offset
    
    # Execute query
    result = db.execute(text(query), params)
    
    floats = []
    for row in result:
        floats.append({
            "id": row[0],
            "wmo_number": row[1],
            "platform_type": row[2],
            "deployment_date": row[3].isoformat() if row[3] else None,
            "last_latitude": row[4],
            "last_longitude": row[5],
            "last_location_date": row[6].isoformat() if row[6] else None,
            "status": row[7],
            "ocean_basin": row[8],
            "program": row[9]
        })
    
    return {
        "total": total,
        "limit": filter_params.limit,
        "offset": filter_params.offset,
        "data": floats
    }

@router.post("/profiles/filter")
async def filter_profiles(filter_params: ProfileFilter, db: Session = Depends(get_db)):
    """
    Filter ARGO profiles by bbox, date, depth, and other criteria
    """
    query = """
        SELECT 
            p.id, p.wmo_number, p.cycle_number, p.profile_date,
            p.latitude, p.longitude, p.position_qc, p.data_mode,
            f.platform_type, f.status, f.ocean_basin
        FROM argo_profiles p
        JOIN argo_floats f ON p.float_id = f.id
        WHERE 1=1
    """
    params = {}
    
    # Bbox filter
    if filter_params.bbox:
        query += """
            AND p.location IS NOT NULL
            AND ST_Within(
                p.location::geometry,
                ST_MakeEnvelope(:min_lon, :min_lat, :max_lon, :max_lat, 4326)
            )
        """
        params.update({
            "min_lon": filter_params.bbox.min_lon,
            "min_lat": filter_params.bbox.min_lat,
            "max_lon": filter_params.bbox.max_lon,
            "max_lat": filter_params.bbox.max_lat
        })
    
    # Date filter
    if filter_params.start_date:
        query += " AND p.profile_date >= :start_date"
        params["start_date"] = filter_params.start_date
    
    if filter_params.end_date:
        query += " AND p.profile_date <= :end_date"
        params["end_date"] = filter_params.end_date
    
    # WMO filter
    if filter_params.wmo_numbers:
        placeholders = ", ".join([f":wmo_{i}" for i in range(len(filter_params.wmo_numbers))])
        query += f" AND p.wmo_number IN ({placeholders})"
        for i, wmo in enumerate(filter_params.wmo_numbers):
            params[f"wmo_{i}"] = wmo
    
    # Data mode filter
    if filter_params.data_mode:
        query += " AND p.data_mode = :data_mode"
        params["data_mode"] = filter_params.data_mode
    
    # Depth filter (requires join with measurements)
    if filter_params.min_depth is not None or filter_params.max_depth is not None:
        query += """
            AND EXISTS (
                SELECT 1 FROM argo_measurements m
                WHERE m.profile_id = p.id
        """
        if filter_params.min_depth is not None:
            query += " AND m.depth >= :min_depth"
            params["min_depth"] = filter_params.min_depth
        if filter_params.max_depth is not None:
            query += " AND m.depth <= :max_depth"
            params["max_depth"] = filter_params.max_depth
        query += ")"
    
    # Get total count
    count_query = f"SELECT COUNT(*) FROM ({query}) AS filtered"
    total = db.execute(text(count_query), params).scalar()
    
    # Add pagination
    query += " ORDER BY p.profile_date DESC LIMIT :limit OFFSET :offset"
    params["limit"] = filter_params.limit
    params["offset"] = filter_params.offset
    
    # Execute query
    result = db.execute(text(query), params)
    
    profiles = []
    for row in result:
        profiles.append({
            "id": row[0],
            "wmo_number": row[1],
            "cycle_number": row[2],
            "profile_date": row[3].isoformat() if row[3] else None,
            "latitude": row[4],
            "longitude": row[5],
            "position_qc": row[6],
            "data_mode": row[7],
            "platform_type": row[8],
            "status": row[9],
            "ocean_basin": row[10]
        })
    
    return {
        "total": total,
        "limit": filter_params.limit,
        "offset": filter_params.offset,
        "data": profiles
    }

@router.post("/measurements/filter")
async def filter_measurements(filter_params: MeasurementFilter, db: Session = Depends(get_db)):
    """
    Filter measurements by depth, temperature, salinity, and QC flags
    """
    query = """
        SELECT 
            m.id, m.profile_id, m.pressure, m.depth,
            m.temperature, m.temperature_qc,
            m.salinity, m.salinity_qc
        FROM argo_measurements m
        WHERE 1=1
    """
    params = {}
    
    # Profile IDs filter
    if filter_params.profile_ids:
        placeholders = ", ".join([f":pid_{i}" for i in range(len(filter_params.profile_ids))])
        query += f" AND m.profile_id IN ({placeholders})"
        for i, pid in enumerate(filter_params.profile_ids):
            params[f"pid_{i}"] = pid
    
    # WMO filter (requires join)
    if filter_params.wmo_number:
        query = query.replace("FROM argo_measurements m", 
                             "FROM argo_measurements m JOIN argo_profiles p ON m.profile_id = p.id")
        query += " AND p.wmo_number = :wmo_number"
        params["wmo_number"] = filter_params.wmo_number
    
    # Depth filter
    if filter_params.min_depth is not None:
        query += " AND m.depth >= :min_depth"
        params["min_depth"] = filter_params.min_depth
    
    if filter_params.max_depth is not None:
        query += " AND m.depth <= :max_depth"
        params["max_depth"] = filter_params.max_depth
    
    # Temperature filter
    if filter_params.min_temperature is not None:
        query += " AND m.temperature >= :min_temperature"
        params["min_temperature"] = filter_params.min_temperature
    
    if filter_params.max_temperature is not None:
        query += " AND m.temperature <= :max_temperature"
        params["max_temperature"] = filter_params.max_temperature
    
    # Salinity filter
    if filter_params.min_salinity is not None:
        query += " AND m.salinity >= :min_salinity"
        params["min_salinity"] = filter_params.min_salinity
    
    if filter_params.max_salinity is not None:
        query += " AND m.salinity <= :max_salinity"
        params["max_salinity"] = filter_params.max_salinity
    
    # QC filter
    query += " AND (m.temperature_qc <= :qc_max OR m.salinity_qc <= :qc_max)"
    params["qc_max"] = filter_params.qc_max
    
    # Get total count
    count_query = f"SELECT COUNT(*) FROM ({query}) AS filtered"
    total = db.execute(text(count_query), params).scalar()
    
    # Add pagination
    query += " ORDER BY m.depth LIMIT :limit OFFSET :offset"
    params["limit"] = filter_params.limit
    params["offset"] = filter_params.offset
    
    # Execute query
    result = db.execute(text(query), params)
    
    measurements = []
    for row in result:
        measurements.append({
            "id": row[0],
            "profile_id": row[1],
            "pressure": row[2],
            "depth": row[3],
            "temperature": row[4],
            "temperature_qc": row[5],
            "salinity": row[6],
            "salinity_qc": row[7]
        })
    
    return {
        "total": total,
        "limit": filter_params.limit,
        "offset": filter_params.offset,
        "data": measurements
    }

@router.get("/stats/summary")
async def get_summary_stats(db: Session = Depends(get_db)):
    """
    Get summary statistics from materialized view
    """
    try:
        result = db.execute(text("SELECT * FROM argo_stats")).first()
        
        if not result:
            return {
                "total_floats": 0,
                "active_floats": 0,
                "inactive_floats": 0,
                "total_profiles": 0,
                "total_measurements": 0
            }
        
        return {
            "total_floats": result[0] or 0,
            "active_floats": result[1] or 0,
            "inactive_floats": result[2] or 0,
            "total_profiles": result[3] or 0,
            "earliest_profile": _to_iso(result[4]),
            "latest_profile": _to_iso(result[5]),
            "ocean_basin_count": result[6] or 0,
            "total_measurements": result[7] or 0,
            "avg_temperature": float(result[8]) if result[8] else None,
            "avg_salinity": float(result[9]) if result[9] else None
        }
    except Exception as e:
        # Fallback to direct query if materialized view doesn't exist
        raise HTTPException(status_code=500, detail=f"Stats query failed: {str(e)}")

@router.post("/stats/refresh")
async def refresh_stats(db: Session = Depends(get_db)):
    """
    Refresh materialized views (admin endpoint)
    """
    try:
        db.execute(text("SELECT refresh_argo_stats()"))
        db.commit()
        return {"message": "Statistics refreshed successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Refresh failed: {str(e)}")


@router.get("/ingestion/status")
async def ingestion_status(db: Session = Depends(get_db)):
    jobs = _get_recent_ingestion_jobs(db, limit=5)
    with _ingestion_state_lock:
        state = dict(_ingestion_state)
    return {
        "job": state,
        "latest_job": jobs[0] if jobs else None,
        "jobs": jobs,
        "dataset": _ingestion_dataset_summary(db),
    }


@router.get("/ingestion/jobs")
async def ingestion_jobs(limit: int = Query(default=20, ge=1, le=200), db: Session = Depends(get_db)):
    return _get_recent_ingestion_jobs(db, limit=limit)


@router.post("/ingestion/run")
async def ingestion_run(
    payload: IngestionRunRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    config = _build_ingestion_config(payload)
    config_preview = {
        "region": config.region,
        "bbox": list(config.bbox) if config.bbox else None,
        "start_date": config.start_date.isoformat() if config.start_date else None,
        "end_date": config.end_date.isoformat() if config.end_date else None,
        "index_limit": config.index_limit,
        "max_profiles": config.max_profiles,
        "cache_dir": config.cache_dir,
        "request_timeout": config.request_timeout,
        "sleep_seconds": config.sleep_seconds,
        "force_redownload": config.force_redownload,
    }

    if payload.dry_run:
        return {
            "accepted": False,
            "dry_run": True,
            "config": config_preview,
        }

    with _ingestion_state_lock:
        if _ingestion_state.get("running"):
            raise HTTPException(status_code=409, detail="An ingestion job is already running")
        job_id = _create_ingestion_job(db, request_payload=config_preview, status="running")
        _ingestion_state.update(
            {
                "running": True,
                "status": "running",
                "started_at": datetime.now(timezone.utc).isoformat(),
                "finished_at": None,
                "request": config_preview,
                "summary": None,
                "error": None,
                "job_id": job_id,
            }
        )

    background_tasks.add_task(_run_ingestion_job, job_id, payload.model_dump())
    return {
        "accepted": True,
        "dry_run": False,
        "status": "running",
        "job_id": job_id,
        "config": config_preview,
    }
