"""BGC-Argo profile filter API."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import text
from sqlalchemy.orm import Session

from core.db import build_engine, build_session_local, get_database_url

DATABASE_URL = get_database_url()
engine = build_engine(DATABASE_URL)
SessionLocal = build_session_local(engine)

router = APIRouter(prefix="/api/v1/bgc", tags=["bgc-argo"])


def _parse_iso_datetime(value: str, field_name: str) -> datetime:
    candidate = value.strip()
    try:
        return datetime.fromisoformat(candidate.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a valid ISO date/datetime string") from exc


class BBox(BaseModel):
    min_lon: float = Field(..., ge=-180, le=180)
    min_lat: float = Field(..., ge=-90, le=90)
    max_lon: float = Field(..., ge=-180, le=180)
    max_lat: float = Field(..., ge=-90, le=90)

    @model_validator(mode="after")
    def validate_bbox(self):
        if self.min_lon > self.max_lon:
            raise ValueError("bbox.min_lon must be <= bbox.max_lon")
        if self.min_lat > self.max_lat:
            raise ValueError("bbox.min_lat must be <= bbox.max_lat")
        return self


class BGCProfileFilter(BaseModel):
    bbox: Optional[BBox] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    wmo_numbers: Optional[list[str]] = None
    parameter: Optional[str] = Field(default=None, description="chlorophyll|nitrate|oxygen|ph")
    limit: int = Field(default=100, ge=1, le=5000)
    offset: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def validate_filters(self):
        if self.start_date and self.end_date:
            start = _parse_iso_datetime(self.start_date, "start_date")
            end = _parse_iso_datetime(self.end_date, "end_date")
            if start > end:
                raise ValueError("start_date must be <= end_date")

        if self.parameter is not None:
            normalized = self.parameter.strip().lower()
            if normalized not in {"chlorophyll", "nitrate", "oxygen", "ph"}:
                raise ValueError("parameter must be one of: chlorophyll, nitrate, oxygen, ph")
            self.parameter = normalized
        return self


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_bgc_table(db: Session) -> None:
    db.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS bgc_profiles (
                id BIGSERIAL PRIMARY KEY,
                wmo_number VARCHAR(32) NOT NULL,
                cycle_number INTEGER,
                profile_date TIMESTAMP,
                latitude DOUBLE PRECISION,
                longitude DOUBLE PRECISION,
                chlorophyll DOUBLE PRECISION,
                nitrate DOUBLE PRECISION,
                oxygen DOUBLE PRECISION,
                ph DOUBLE PRECISION,
                source_file VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
    )
    db.execute(text("CREATE INDEX IF NOT EXISTS idx_bgc_wmo_date ON bgc_profiles (wmo_number, profile_date DESC)"))
    db.execute(text("CREATE INDEX IF NOT EXISTS idx_bgc_geo ON bgc_profiles (latitude, longitude)"))
    db.commit()


def _to_iso(value: Any):
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


@router.post("/profiles/filter")
async def filter_bgc_profiles(
    payload: BGCProfileFilter,
    db: Session = Depends(get_db),
):
    ensure_bgc_table(db)
    params: Dict[str, Any] = {}
    query = """
        SELECT id, wmo_number, cycle_number, profile_date, latitude, longitude,
               chlorophyll, nitrate, oxygen, ph, source_file
        FROM bgc_profiles
        WHERE 1=1
    """
    if payload.bbox:
        query += " AND longitude BETWEEN :min_lon AND :max_lon AND latitude BETWEEN :min_lat AND :max_lat"
        params.update(
            {
                "min_lon": payload.bbox.min_lon,
                "max_lon": payload.bbox.max_lon,
                "min_lat": payload.bbox.min_lat,
                "max_lat": payload.bbox.max_lat,
            }
        )
    if payload.start_date:
        query += " AND profile_date >= :start_date"
        params["start_date"] = payload.start_date
    if payload.end_date:
        query += " AND profile_date <= :end_date"
        params["end_date"] = payload.end_date
    if payload.wmo_numbers:
        placeholders = ", ".join([f":wmo_{i}" for i in range(len(payload.wmo_numbers))])
        query += f" AND wmo_number IN ({placeholders})"
        for i, wmo in enumerate(payload.wmo_numbers):
            params[f"wmo_{i}"] = wmo
    if payload.parameter:
        query += f" AND {payload.parameter} IS NOT NULL"

    count_query = f"SELECT COUNT(*) FROM ({query}) AS filtered"
    total = int(db.execute(text(count_query), params).scalar() or 0)

    query += " ORDER BY profile_date DESC LIMIT :limit OFFSET :offset"
    params["limit"] = payload.limit
    params["offset"] = payload.offset

    rows = db.execute(text(query), params).fetchall()
    data = [
        {
            "id": row[0],
            "wmo_number": row[1],
            "cycle_number": row[2],
            "profile_date": _to_iso(row[3]),
            "latitude": row[4],
            "longitude": row[5],
            "chlorophyll": row[6],
            "nitrate": row[7],
            "oxygen": row[8],
            "ph": row[9],
            "source_file": row[10],
        }
        for row in rows
    ]
    return {"total": total, "limit": payload.limit, "offset": payload.offset, "data": data}


@router.get("/stats/summary")
async def bgc_summary(db: Session = Depends(get_db)):
    ensure_bgc_table(db)
    row = db.execute(
        text(
            """
            SELECT
                COUNT(*) AS total_profiles,
                COUNT(DISTINCT wmo_number) AS total_floats,
                AVG(chlorophyll) AS avg_chlorophyll,
                AVG(nitrate) AS avg_nitrate,
                AVG(oxygen) AS avg_oxygen,
                AVG(ph) AS avg_ph
            FROM bgc_profiles
            """
        )
    ).first()
    return {
        "total_profiles": int(row[0] or 0),
        "total_floats": int(row[1] or 0),
        "avg_chlorophyll": float(row[2]) if row[2] is not None else None,
        "avg_nitrate": float(row[3]) if row[3] is not None else None,
        "avg_oxygen": float(row[4]) if row[4] is not None else None,
        "avg_ph": float(row[5]) if row[5] is not None else None,
    }


@router.delete("/profiles")
async def clear_bgc_profiles(
    confirm: bool = Query(default=False, description="Set true to confirm deletion"),
    db: Session = Depends(get_db),
):
    ensure_bgc_table(db)
    if not confirm:
        return {"deleted": 0, "message": "Set confirm=true to delete BGC profiles."}
    result = db.execute(text("DELETE FROM bgc_profiles"))
    db.commit()
    return {"deleted": int(result.rowcount or 0)}
