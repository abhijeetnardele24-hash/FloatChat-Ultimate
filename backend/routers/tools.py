"""
Research tools router:
- Ocean glossary
- Ocean calculators
- Learning insights generated from ARGO data
"""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from core.db import build_engine, build_session_local, get_database_url

try:
    import gsw as _gsw
except Exception:
    _gsw = None

DATABASE_URL = get_database_url()
engine = build_engine(DATABASE_URL)
SessionLocal = build_session_local(engine)

router = APIRouter(prefix="/api/v1/tools", tags=["tools"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class GlossaryItem(BaseModel):
    term: str
    category: str
    short_definition: str
    details: str
    units: Optional[str] = None


class PressureDepthRequest(BaseModel):
    depth_m: Optional[float] = Field(default=None, ge=0)
    pressure_dbar: Optional[float] = Field(default=None, ge=0)
    latitude: float = Field(default=0.0, ge=-90, le=90)


class PressureDepthResponse(BaseModel):
    depth_m: float
    pressure_dbar: float
    latitude: float


class LearningInsight(BaseModel):
    title: str
    detail: str
    metric: Optional[str] = None


class QuickStatsResponse(BaseModel):
    min_temperature: Optional[float] = None
    max_temperature: Optional[float] = None
    min_salinity: Optional[float] = None
    max_salinity: Optional[float] = None
    median_depth: Optional[float] = None
    latest_profile_date: Optional[str] = None


GLOSSARY: List[GlossaryItem] = [
    GlossaryItem(
        term="ARGO Float",
        category="Platform",
        short_definition="Autonomous float that drifts and profiles ocean properties.",
        details="ARGO floats cycle through descent, drift, and ascent phases, measuring temperature and salinity through the upper ocean.",
    ),
    GlossaryItem(
        term="Profile",
        category="Data",
        short_definition="A vertical measurement record from one float cycle.",
        details="Each profile captures pressure/depth-dependent measurements such as temperature and salinity from deep water to surface.",
    ),
    GlossaryItem(
        term="Temperature",
        category="Parameter",
        short_definition="In-situ seawater temperature measured by ARGO sensors.",
        details="Temperature is used to quantify thermal structure, stratification, and ocean heat content variations.",
        units="degC",
    ),
    GlossaryItem(
        term="Salinity",
        category="Parameter",
        short_definition="Concentration of dissolved salts in seawater.",
        details="Salinity controls seawater density and strongly influences circulation and water-mass identification.",
        units="PSU",
    ),
    GlossaryItem(
        term="Pressure",
        category="Parameter",
        short_definition="Hydrostatic pressure used as the native vertical axis.",
        details="Pressure is often converted to approximate depth for plotting and interpretation.",
        units="dbar",
    ),
    GlossaryItem(
        term="QC Flag",
        category="Quality",
        short_definition="Quality-control flag assigned to each observation.",
        details="Lower QC values generally indicate better data quality. Filters like QC <= 2 are commonly used for analysis.",
    ),
    GlossaryItem(
        term="Ocean Basin",
        category="Geography",
        short_definition="Large-scale ocean region label (e.g., Indian Ocean).",
        details="Basin grouping helps compare float density, temporal coverage, and hydrographic structure by region.",
    ),
    GlossaryItem(
        term="Data Mode",
        category="Quality",
        short_definition="Processing stage indicator for ARGO profile data.",
        details="Modes include real-time and delayed-mode products, where delayed mode is typically higher quality after expert review.",
    ),
]


def _to_iso(value: object) -> Optional[str]:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()  # type: ignore[no-any-return]
    return str(value)


@router.get("/glossary", response_model=List[GlossaryItem])
async def get_glossary(
    q: Optional[str] = Query(default=None, description="Case-insensitive term search"),
    limit: int = Query(default=50, ge=1, le=200),
):
    items = GLOSSARY
    if q:
        ql = q.strip().lower()
        items = [
            item
            for item in GLOSSARY
            if ql in item.term.lower() or ql in item.short_definition.lower() or ql in item.category.lower()
        ]
    return items[:limit]


@router.post("/calculate/pressure-depth", response_model=PressureDepthResponse)
async def calculate_pressure_depth(payload: PressureDepthRequest):
    if payload.depth_m is None and payload.pressure_dbar is None:
        raise HTTPException(status_code=400, detail="Provide either depth_m or pressure_dbar.")

    # Prefer TEOS-10 via gsw when available; otherwise use 1 dbar ~= 1 m fallback.
    if _gsw is not None:
        if payload.depth_m is not None:
            pressure = float(_gsw.p_from_z(-payload.depth_m, payload.latitude))
            return PressureDepthResponse(depth_m=payload.depth_m, pressure_dbar=pressure, latitude=payload.latitude)
        depth = float(-_gsw.z_from_p(payload.pressure_dbar or 0.0, payload.latitude))
        return PressureDepthResponse(depth_m=depth, pressure_dbar=payload.pressure_dbar or 0.0, latitude=payload.latitude)

    if payload.depth_m is not None:
        return PressureDepthResponse(
            depth_m=payload.depth_m,
            pressure_dbar=float(payload.depth_m),
            latitude=payload.latitude,
        )
    return PressureDepthResponse(
        depth_m=float(payload.pressure_dbar or 0.0),
        pressure_dbar=payload.pressure_dbar or 0.0,
        latitude=payload.latitude,
    )


@router.get("/learn/insights", response_model=List[LearningInsight])
async def get_learning_insights(db: Session = Depends(get_db)):
    total_floats = db.execute(text("SELECT COUNT(*) FROM argo_floats")).scalar() or 0
    active_floats = db.execute(text("SELECT COUNT(*) FROM argo_floats WHERE status = 'ACTIVE'")).scalar() or 0
    total_profiles = db.execute(text("SELECT COUNT(*) FROM argo_profiles")).scalar() or 0
    latest_profile = db.execute(text("SELECT MAX(profile_date) FROM argo_profiles")).scalar()
    avg_temp = db.execute(text("SELECT AVG(temperature) FROM argo_measurements WHERE temperature IS NOT NULL")).scalar()
    avg_sal = db.execute(text("SELECT AVG(salinity) FROM argo_measurements WHERE salinity IS NOT NULL")).scalar()

    top_basins = db.execute(
        text(
            """
            SELECT ocean_basin, COUNT(*) AS count
            FROM argo_floats
            WHERE ocean_basin IS NOT NULL
            GROUP BY ocean_basin
            ORDER BY count DESC
            LIMIT 3
            """
        )
    ).fetchall()

    basin_text = ", ".join([f"{row[0]} ({row[1]})" for row in top_basins]) if top_basins else "No basin data yet"

    return [
        LearningInsight(
            title="Network coverage snapshot",
            detail=f"The dataset currently tracks {total_floats} floats, with {active_floats} active floats available for current-ocean analysis.",
            metric=f"{active_floats}/{total_floats} active",
        ),
        LearningInsight(
            title="Sampling depth of evidence",
            detail=f"There are {total_profiles} historical profiles. More profiles improve confidence in trend and anomaly studies.",
            metric=f"{total_profiles} profiles",
        ),
        LearningInsight(
            title="Regional concentration",
            detail=f"Top basin distribution: {basin_text}. Compare basin concentration before interpreting global conclusions.",
        ),
        LearningInsight(
            title="Hydrographic baseline",
            detail=(
                f"Average measured temperature is {float(avg_temp):.2f} degC and average salinity is {float(avg_sal):.2f} PSU."
                if avg_temp is not None and avg_sal is not None
                else "Temperature/salinity averages are not yet available."
            ),
        ),
        LearningInsight(
            title="Most recent profile",
            detail=f"Latest profile timestamp: {_to_iso(latest_profile) or 'N/A'}. Use this for data recency checks.",
        ),
    ]


@router.get("/quick-stats", response_model=QuickStatsResponse)
async def get_quick_stats(db: Session = Depends(get_db)):
    row = db.execute(
        text(
            """
            SELECT
                MIN(temperature) AS min_temperature,
                MAX(temperature) AS max_temperature,
                MIN(salinity) AS min_salinity,
                MAX(salinity) AS max_salinity,
                percentile_cont(0.5) WITHIN GROUP (ORDER BY depth) AS median_depth
            FROM argo_measurements
            """
        )
    ).first()
    latest_profile = db.execute(text("SELECT MAX(profile_date) FROM argo_profiles")).scalar()

    return QuickStatsResponse(
        min_temperature=float(row[0]) if row and row[0] is not None else None,
        max_temperature=float(row[1]) if row and row[1] is not None else None,
        min_salinity=float(row[2]) if row and row[2] is not None else None,
        max_salinity=float(row[3]) if row and row[3] is not None else None,
        median_depth=float(row[4]) if row and row[4] is not None else None,
        latest_profile_date=_to_iso(latest_profile),
    )
