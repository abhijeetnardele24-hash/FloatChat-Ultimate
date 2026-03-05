import os
from threading import Lock
from collections import deque

from fastapi import FastAPI, HTTPException, Depends, Header, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from sqlalchemy import text
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional, Literal
import logging
from datetime import datetime, timezone
import time
from core.db import build_engine, build_session_local, get_database_url
from core.middleware import RequestContextRateLimitMiddleware
import psycopg2

# Import direct data module
from direct_data import get_argo_stats, get_float_details

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration (SQLAlchemy needs "postgresql", not "postgres")
DATABASE_URL = get_database_url()
engine = build_engine(DATABASE_URL)
SessionLocal = build_session_local(engine)

# FastAPI app
app = FastAPI(
    title="FloatChat Ultimate API",
    description="AI-Powered Ocean Data Platform API",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add direct data endpoint
@app.get("/api/direct/argo/stats")
async def get_direct_argo_stats():
    """Get ARGO statistics directly - bypasses database connection issues"""
    return get_argo_stats()

@app.get("/api/direct/argo/float/{wmo_number}")
async def get_direct_float_details(wmo_number: str):
    """Get float details directly - bypasses database connection issues"""
    return get_float_details(wmo_number)

@app.get("/api/v1/argo/profiles")
async def get_argo_profiles(limit: int = 100):
    """Get ARGO profiles with real data"""
    try:
        conn = psycopg2.connect(
            host="localhost",
            port="5432",
            database="floatchat",
            user="floatchat_user",
            password="1234"
        )
        cursor = conn.cursor()
        
        # Get profiles with their measurements
        cursor.execute("""
            SELECT 
                p.id as profile_id,
                p.cycle_number,
                p.profile_date,
                p.latitude,
                p.longitude,
                f.wmo_number,
                f.ocean_basin,
                f.platform_type,
                m.pressure,
                m.temperature,
                m.salinity,
                m.temperature_qc,
                m.salinity_qc
            FROM argo_profiles p
            JOIN argo_floats f ON p.float_id = f.id
            LEFT JOIN argo_measurements m ON p.id = m.profile_id
            ORDER BY p.profile_date DESC, p.cycle_number DESC
            LIMIT %s
        """, (limit,))
        
        rows = cursor.fetchall()
        
        # Group measurements by profile
        profile_data = {}
        for row in rows:
            profile_id = row[0]
            if profile_id not in profile_data:
                profile_data[profile_id] = {
                    'profile_id': profile_id,
                    'cycle_number': row[1],
                    'profile_date': str(row[2]),
                    'latitude': float(row[3]) if row[3] else None,
                    'longitude': float(row[4]) if row[4] else None,
                    'wmo_number': row[5],
                    'ocean_basin': row[6],
                    'platform_type': row[7],
                    'measurements': []
                }
            
            # Add measurement to the profile
            if row[8] is not None:  # pressure
                profile_data[profile_id]['measurements'].append({
                    'pressure': float(row[8]),
                    'depth': None,  # Will be calculated from pressure
                    'temperature': float(row[9]) if row[9] is not None else None,
                    'temperature_qc': row[10],
                    'salinity': float(row[11]) if row[11] is not None else None,
                    'salinity_qc': row[12]
                })
        
        cursor.close()
        conn.close()
        
        return {
            "profiles": list(profile_data.values()),
            "total": len(profile_data)
        }
        
    except Exception as e:
        return {"error": str(e), "profiles": []}

_rate_limit_enabled = os.getenv("RATE_LIMIT_ENABLED", "true").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
_rate_limit_requests = int(os.getenv("RATE_LIMIT_REQUESTS", "240"))
_rate_limit_window = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
_exempt_paths_raw = os.getenv(
    "RATE_LIMIT_EXEMPT_PATHS",
    "/,/health,/docs,/redoc,/openapi.json",
)
_exempt_paths = [path.strip() for path in _exempt_paths_raw.split(",") if path.strip()]

app.add_middleware(
    RequestContextRateLimitMiddleware,
    enabled=_rate_limit_enabled,
    requests_per_window=_rate_limit_requests,
    window_seconds=_rate_limit_window,
    exempt_paths=_exempt_paths,
)

# Import and include routers
try:
    from routers import argo_filter

    app.include_router(argo_filter.router)
    logger.info("ARGO filter router loaded successfully")
except Exception as e:
    logger.warning(f"Could not load ARGO filter router: {e}")

try:
    from routers import tools

    app.include_router(tools.router)
    logger.info("Tools router loaded successfully")
except Exception as e:
    logger.warning(f"Could not load tools router: {e}")

try:
    from routers import export

    app.include_router(export.router)
    logger.info("Export router loaded successfully")
except Exception as e:
    logger.warning(f"Could not load export router: {e}")

try:
    from routers import auth

    app.include_router(auth.router)
    logger.info("Auth router loaded successfully")
except Exception as e:
    logger.warning(f"Could not load auth router: {e}")

try:
    from routers import study

    app.include_router(study.router)
    logger.info("Study router loaded successfully")
except Exception as e:
    logger.warning(f"Could not load study router: {e}")

try:
    from routers import bgc

    app.include_router(bgc.router)
    logger.info("BGC router loaded successfully")
except Exception as e:
    logger.warning(f"Could not load BGC router: {e}")

try:
    from routers import argovis

    app.include_router(argovis.router)
    logger.info("ArgoVis external API router loaded successfully")
except Exception as e:
    logger.warning(f"Could not load ArgoVis router: {e}")

try:
    from routers import cmems

    app.include_router(cmems.router)
    logger.info("Copernicus CMEMS router loaded successfully")
except Exception as e:
    logger.warning(f"Could not load CMEMS router: {e}")

try:
    from routers import noaa

    app.include_router(noaa.router)
    logger.info("NOAA external API router loaded successfully")
except Exception as e:
    logger.warning(f"Could not load NOAA router: {e}")

try:
    from routers import obis

    app.include_router(obis.router)
    logger.info("OBIS external API router loaded successfully")
except Exception as e:
    logger.warning(f"Could not load OBIS router: {e}")

try:
    from routers import open_meteo_marine

    app.include_router(open_meteo_marine.router)
    logger.info("Open-Meteo Marine router loaded successfully")
except Exception as e:
    logger.warning(f"Could not load Open-Meteo Marine router: {e}")

try:
    from routers import erddap

    app.include_router(erddap.router)
    logger.info("ERDDAP router loaded successfully")
except Exception as e:
    logger.warning(f"Could not load ERDDAP router: {e}")

try:
    from routers import gebco

    app.include_router(gebco.router)
    logger.info("GEBCO bathymetry router loaded successfully")
except Exception as e:
    logger.warning(f"Could not load GEBCO router: {e}")

try:
    from routers import gfw

    app.include_router(gfw.router)
    logger.info("Global Fishing Watch router loaded successfully")
except Exception as e:
    logger.warning(f"Could not load GFW router: {e}")

try:
    from routers import wod

    app.include_router(wod.router)
    logger.info("World Ocean Database router loaded successfully")
except Exception as e:
    logger.warning(f"Could not load WOD router: {e}")

try:
    from routers import ooi

    app.include_router(ooi.router)
    logger.info("Ocean Observatories Initiative router loaded successfully")
except Exception as e:
    logger.warning(f"Could not load OOI router: {e}")

try:
    from routers import icoads

    app.include_router(icoads.router)
    logger.info("ICOADS router loaded successfully")
except Exception as e:
    logger.warning(f"Could not load ICOADS router: {e}")

try:
    from routers import ioos

    app.include_router(ioos.router)
    logger.info("IOOS router loaded successfully")
except Exception as e:
    logger.warning(f"Could not load IOOS router: {e}")

try:
    from routers import onc

    app.include_router(onc.router)
    logger.info("Ocean Networks Canada router loaded successfully")
except Exception as e:
    logger.warning(f"Could not load ONC router: {e}")


# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


_chat_service_lock = Lock()
_chat_service = None
_chat_metrics_lock = Lock()
_chat_metrics = deque(maxlen=max(1000, int(os.getenv("CHAT_METRICS_MAXLEN", "5000"))))
_app_started_at = time.time()


def _get_chat_service():
    global _chat_service
    with _chat_service_lock:
        if _chat_service is None:
            from llm.chat_service import HybridChatService

            _chat_service = HybridChatService()
        return _chat_service


def _refresh_chat_service():
    global _chat_service
    with _chat_service_lock:
        from llm.chat_service import HybridChatService

        _chat_service = HybridChatService()
        return _chat_service


def _record_chat_metric(
    requested_provider: str,
    source: Optional[str],
    success: bool,
    latency_ms: float,
    cached: bool,
    intent: Optional[str] = None,
) -> None:
    with _chat_metrics_lock:
        _chat_metrics.append(
            {
                "ts": time.time(),
                "requested_provider": requested_provider,
                "source": source or "none",
                "success": bool(success),
                "latency_ms": float(latency_ms),
                "cached": bool(cached),
                "intent": intent or "unknown",
            }
        )


def _percentile(values: List[float], p: float) -> Optional[float]:
    if not values:
        return None
    sorted_values = sorted(values)
    k = (len(sorted_values) - 1) * p
    lower = int(k)
    upper = min(lower + 1, len(sorted_values) - 1)
    if lower == upper:
        return round(sorted_values[lower], 2)
    weight = k - lower
    interpolated = sorted_values[lower] * (1 - weight) + sorted_values[upper] * weight
    return round(interpolated, 2)


def _require_admin_key(x_admin_key: Optional[str]) -> None:
    configured_key = os.getenv("ADMIN_API_KEY", "").strip()
    if not configured_key:
        return
    if (x_admin_key or "").strip() != configured_key:
        raise HTTPException(status_code=401, detail="Invalid admin key")


# Pydantic models
class FloatResponse(BaseModel):
    id: int
    wmo_number: str
    platform_type: Optional[str]
    last_latitude: Optional[float]
    last_longitude: Optional[float]
    status: Optional[str]
    ocean_basin: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class ProfileResponse(BaseModel):
    id: int
    wmo_number: str
    cycle_number: int
    profile_date: datetime
    latitude: float
    longitude: float

    model_config = ConfigDict(from_attributes=True)


class StatsResponse(BaseModel):
    total_floats: int
    active_floats: int
    total_profiles: int
    ocean_basins: List[str]


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=8000)
    provider: Optional[str] = "auto"


class ChatFeedbackRequest(BaseModel):
    rating: Literal[1, -1]
    user_message: Optional[str] = None
    assistant_message: Optional[str] = None
    source: Optional[str] = None
    query_type: Optional[str] = None


def _ensure_chat_feedback_table(db: Session) -> None:
    db.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS chat_feedback (
                id SERIAL PRIMARY KEY,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                rating SMALLINT NOT NULL CHECK (rating IN (-1, 1)),
                user_message TEXT,
                assistant_message TEXT,
                source VARCHAR(64),
                query_type VARCHAR(32)
            )
            """
        )
    )


# API Routes
@app.get("/")
async def root():
    return {
        "message": "FloatChat Ultimate API",
        "version": "1.0.0",
        "status": "running",
    }


@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    try:
        # Test database connection
        db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Database connection failed: {str(e)}"
        )


@app.get("/api/floats", response_model=List[FloatResponse])
async def get_floats(
    limit: int = Query(default=100, ge=1, le=5000),
    ocean_basin: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Get list of ARGO floats"""
    query = "SELECT id, wmo_number, platform_type, last_latitude, last_longitude, status, ocean_basin FROM argo_floats"
    params = {}

    if ocean_basin:
        query += " WHERE ocean_basin = :ocean_basin"
        params["ocean_basin"] = ocean_basin

    query += " LIMIT :limit"
    params["limit"] = limit

    result = db.execute(text(query), params)
    floats = []
    for row in result:
        floats.append(
            {
                "id": row[0],
                "wmo_number": row[1],
                "platform_type": row[2],
                "last_latitude": row[3],
                "last_longitude": row[4],
                "status": row[5],
                "ocean_basin": row[6],
            }
        )

    return floats


@app.get("/api/floats/{wmo_number}", response_model=FloatResponse)
async def get_float(wmo_number: str, db: Session = Depends(get_db)):
    """Get specific ARGO float by WMO number"""
    query = text(
        "SELECT id, wmo_number, platform_type, last_latitude, last_longitude, status, ocean_basin FROM argo_floats WHERE wmo_number = :wmo"
    )
    result = db.execute(query, {"wmo": wmo_number}).first()

    if not result:
        raise HTTPException(status_code=404, detail="Float not found")

    return {
        "id": result[0],
        "wmo_number": result[1],
        "platform_type": result[2],
        "last_latitude": result[3],
        "last_longitude": result[4],
        "status": result[5],
        "ocean_basin": result[6],
    }


@app.get("/api/profiles", response_model=List[ProfileResponse])
async def get_profiles(
    wmo_number: Optional[str] = None,
    limit: int = Query(default=100, ge=1, le=5000),
    db: Session = Depends(get_db),
):
    """Get ARGO profiles"""
    query = "SELECT id, wmo_number, cycle_number, profile_date, latitude, longitude FROM argo_profiles"
    params = {}

    if wmo_number:
        query += " WHERE wmo_number = :wmo_number"
        params["wmo_number"] = wmo_number

    query += " ORDER BY profile_date DESC LIMIT :limit"
    params["limit"] = limit

    result = db.execute(text(query), params)
    profiles = []
    for row in result:
        profiles.append(
            {
                "id": row[0],
                "wmo_number": row[1],
                "cycle_number": row[2],
                "profile_date": row[3],
                "latitude": row[4],
                "longitude": row[5],
            }
        )

    return profiles


@app.get("/api/stats", response_model=StatsResponse)
async def get_stats(db: Session = Depends(get_db)):
    """Get platform statistics"""
    # Total floats
    total_floats = db.execute(text("SELECT COUNT(*) FROM argo_floats")).scalar()

    # Active floats
    active_floats = db.execute(
        text("SELECT COUNT(*) FROM argo_floats WHERE status = 'ACTIVE'")
    ).scalar()

    # Total profiles
    total_profiles = db.execute(text("SELECT COUNT(*) FROM argo_profiles")).scalar()

    # Ocean basins
    basins_result = db.execute(
        text(
            "SELECT DISTINCT ocean_basin FROM argo_floats WHERE ocean_basin IS NOT NULL"
        )
    )
    ocean_basins = [row[0] for row in basins_result]

    return {
        "total_floats": total_floats or 0,
        "active_floats": active_floats or 0,
        "total_profiles": total_profiles or 0,
        "ocean_basins": ocean_basins,
    }


@app.post("/api/chat")
async def chat(payload: ChatRequest, db: Session = Depends(get_db)):
    """
    Chat endpoint with multi-LLM support (Ollama + OpenAI + Gemini)

    Request body:
        - message: User's question (required)
        - provider: "ollama", "openai", "gemini", or "auto" (optional, default: "auto")
    """
    user_message = payload.message.strip()
    provider = payload.provider or "auto"
    if isinstance(provider, str):
        provider = provider.lower().strip()
    else:
        provider = "auto"
    if provider not in {"auto", "groq", "gemini", "openai", "ollama"}:
        raise HTTPException(
            status_code=400,
            detail="Invalid provider. Use 'auto', 'groq', 'gemini', 'openai', or 'ollama'.",
        )
    if not user_message:
        raise HTTPException(status_code=400, detail="Message is required")

    started = time.perf_counter()
    api_response = None
    try:
        service = _get_chat_service()
        result = service.process_query(user_message, provider=provider)

        api_response = {
            "success": result.get("success", False),
            "response": result.get("response"),
            "sql_query": result.get("sql_query"),
            "data": result.get("data", [])[:10],  # Limit to 10 rows
            "row_count": result.get("row_count", 0),
            "source": result.get("source"),  # Which LLM was used
            "query_type": result.get("query_type"),  # "data" or "general"
            "intent": result.get("intent"),
            "intent_confidence": result.get("intent_confidence"),
            "confidence": result.get("confidence"),
            "evidence_score": result.get("evidence_score"),
            "evidence_coverage_score": result.get("evidence_coverage_score"),
            "method": result.get("method"),
            "data_source": result.get("data_source", []),
            "limitations": result.get("limitations", []),
            "next_checks": result.get("next_checks", []),
            "reliability_warnings": result.get("reliability_warnings", []),
            "provider_metrics": result.get("provider_metrics", []),
            "sources": result.get("sources", []),  # Optional RAG citation sources
            "cached": result.get("cached", False),
            "error": result.get("error"),
        }
    except Exception as e:
        logger.error(f"Chat error: {e}")
        api_response = {
            "success": False,
            "response": "I'm sorry, I encountered an error processing your request. Please try again.",
            "error": str(e),
        }
    finally:
        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        _record_chat_metric(
            requested_provider=provider,
            source=(api_response or {}).get("source"),
            success=bool((api_response or {}).get("success")),
            latency_ms=elapsed_ms,
            cached=bool((api_response or {}).get("cached")),
            intent=(api_response or {}).get("intent"),
        )

    return api_response


@app.post("/api/chat/feedback")
async def chat_feedback(payload: ChatFeedbackRequest, db: Session = Depends(get_db)):
    """Persist thumbs-up/down feedback for chat responses."""
    try:
        _ensure_chat_feedback_table(db)
        db.execute(
            text(
                """
                INSERT INTO chat_feedback (rating, user_message, assistant_message, source, query_type)
                VALUES (:rating, :user_message, :assistant_message, :source, :query_type)
                """
            ),
            {
                "rating": payload.rating,
                "user_message": (payload.user_message or "")[:8000],
                "assistant_message": (payload.assistant_message or "")[:12000],
                "source": (payload.source or "")[:64],
                "query_type": (payload.query_type or "")[:32],
            },
        )
        db.commit()
        return {"success": True, "message": "Feedback recorded"}
    except Exception as e:
        db.rollback()
        logger.error(f"Chat feedback error: {e}")
        raise HTTPException(status_code=500, detail="Failed to save feedback")


@app.get("/api/chat/feedback/stats")
async def chat_feedback_stats(limit: int = 20, db: Session = Depends(get_db)):
    """Aggregate chat feedback analytics for admin monitoring."""
    if limit < 1 or limit > 100:
        raise HTTPException(status_code=400, detail="limit must be between 1 and 100")

    try:
        _ensure_chat_feedback_table(db)

        totals = (
            db.execute(
                text(
                    """
                SELECT
                    COUNT(*) AS total_feedback,
                    COALESCE(SUM(CASE WHEN rating = 1 THEN 1 ELSE 0 END), 0) AS helpful_count,
                    COALESCE(SUM(CASE WHEN rating = -1 THEN 1 ELSE 0 END), 0) AS not_helpful_count
                FROM chat_feedback
                """
                )
            )
            .mappings()
            .first()
        )

        by_source_rows = (
            db.execute(
                text(
                    """
                SELECT COALESCE(source, 'unknown') AS label, COUNT(*) AS count
                FROM chat_feedback
                GROUP BY COALESCE(source, 'unknown')
                ORDER BY COUNT(*) DESC
                """
                )
            )
            .mappings()
            .all()
        )

        by_query_type_rows = (
            db.execute(
                text(
                    """
                SELECT COALESCE(query_type, 'unknown') AS label, COUNT(*) AS count
                FROM chat_feedback
                GROUP BY COALESCE(query_type, 'unknown')
                ORDER BY COUNT(*) DESC
                """
                )
            )
            .mappings()
            .all()
        )

        recent_rows = (
            db.execute(
                text(
                    """
                SELECT created_at, rating, source, query_type
                FROM chat_feedback
                ORDER BY id DESC
                LIMIT :limit
                """
                ),
                {"limit": limit},
            )
            .mappings()
            .all()
        )

        db.commit()

        total_feedback = int(totals["total_feedback"] if totals else 0)
        helpful_count = int(totals["helpful_count"] if totals else 0)
        not_helpful_count = int(totals["not_helpful_count"] if totals else 0)
        helpful_ratio = (
            round((helpful_count / total_feedback) * 100, 2)
            if total_feedback > 0
            else None
        )

        return {
            "success": True,
            "total_feedback": total_feedback,
            "helpful_count": helpful_count,
            "not_helpful_count": not_helpful_count,
            "helpful_ratio": helpful_ratio,
            "by_source": [
                {"label": row["label"], "count": int(row["count"])}
                for row in by_source_rows
            ],
            "by_query_type": [
                {"label": row["label"], "count": int(row["count"])}
                for row in by_query_type_rows
            ],
            "recent": [
                {
                    "created_at": row["created_at"].isoformat()
                    if row.get("created_at")
                    else None,
                    "rating": int(row["rating"]),
                    "source": row.get("source"),
                    "query_type": row.get("query_type"),
                }
                for row in recent_rows
            ],
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Chat feedback stats error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch feedback stats")


@app.get("/api/chat/providers")
async def get_chat_providers(refresh: bool = Query(default=False)):
    """Get available LLM providers"""
    try:
        service = _refresh_chat_service() if refresh else _get_chat_service()
        return {
            "providers": service.get_available_providers(),
            "health": service.health_check(),
        }
    except Exception as e:
        return {"providers": [], "health": {}, "error": str(e)}


@app.get("/api/admin/metrics/summary")
async def admin_metrics_summary(
    window_minutes: int = Query(default=60, ge=1, le=1440),
    include_recent_events: int = Query(default=0, ge=0, le=100),
    x_admin_key: Optional[str] = Header(default=None, alias="X-Admin-Key"),
    db: Session = Depends(get_db),
):
    _require_admin_key(x_admin_key)
    cutoff_ts = time.time() - (window_minutes * 60)
    with _chat_metrics_lock:
        metrics = [entry for entry in _chat_metrics if entry["ts"] >= cutoff_ts]

    latencies = [float(entry["latency_ms"]) for entry in metrics]
    total = len(metrics)
    success_count = sum(1 for entry in metrics if entry["success"])
    failed_count = max(0, total - success_count)
    cached_count = sum(1 for entry in metrics if entry["cached"])
    cache_hit_rate = round((cached_count / total) * 100, 2) if total > 0 else None

    provider_requested: dict = {}
    provider_source: dict = {}
    intent_breakdown: dict = {}
    provider_success: dict = {}
    provider_failure: dict = {}
    for entry in metrics:
        req = entry["requested_provider"]
        src = entry["source"]
        intent = entry["intent"]
        provider_requested[req] = provider_requested.get(req, 0) + 1
        provider_source[src] = provider_source.get(src, 0) + 1
        intent_breakdown[intent] = intent_breakdown.get(intent, 0) + 1
        if entry["success"]:
            provider_success[src] = provider_success.get(src, 0) + 1
        else:
            provider_failure[src] = provider_failure.get(src, 0) + 1

    db_latency_ms = None
    db_connected = False
    try:
        db_started = time.perf_counter()
        db.execute(text("SELECT 1"))
        db_latency_ms = round((time.perf_counter() - db_started) * 1000, 2)
        db_connected = True
    except Exception as exc:
        logger.warning("Admin metrics DB probe failed: %s", exc)

    ingestion = {"available": False, "total_jobs": 0, "status_counts": {}}
    try:
        rows = (
            db.execute(
                text(
                    """
                SELECT status, COUNT(*) AS count
                FROM argo_ingestion_jobs
                GROUP BY status
                """
                )
            )
            .mappings()
            .all()
        )
        status_counts = {row["status"]: int(row["count"]) for row in rows}
        ingestion = {
            "available": True,
            "total_jobs": int(sum(status_counts.values())),
            "status_counts": status_counts,
        }
    except Exception:
        ingestion = {"available": False, "total_jobs": 0, "status_counts": {}}

    recent_events = []
    if include_recent_events > 0:
        sorted_events = sorted(metrics, key=lambda m: m["ts"], reverse=True)
        for event in sorted_events[:include_recent_events]:
            recent_events.append(
                {
                    "timestamp": datetime.fromtimestamp(
                        event["ts"], timezone.utc
                    ).isoformat(),
                    "requested_provider": event["requested_provider"],
                    "source": event["source"],
                    "intent": event["intent"],
                    "latency_ms": round(float(event["latency_ms"]), 2),
                    "success": bool(event["success"]),
                    "cached": bool(event["cached"]),
                }
            )

    provider_health = {}
    try:
        provider_health = _get_chat_service().health_check()
    except Exception as exc:
        logger.warning("Admin metrics provider health failed: %s", exc)

    now_ts = time.time()
    uptime_seconds = max(0, int(now_ts - _app_started_at))

    return {
        "period": {
            "window_minutes": window_minutes,
            "started_at": datetime.fromtimestamp(cutoff_ts, timezone.utc).isoformat(),
            "ended_at": datetime.fromtimestamp(now_ts, timezone.utc).isoformat(),
        },
        "window_minutes": window_minutes,
        "chat": {
            "total_requests": total,
            "successful_requests": success_count,
            "failed_requests": failed_count,
            "cached_responses": cached_count,
            "cache_hit_rate": cache_hit_rate,
            "success_rate": round((success_count / total) * 100, 2)
            if total > 0
            else None,
            "latency_ms": {
                "p50": _percentile(latencies, 0.50),
                "p95": _percentile(latencies, 0.95),
                "avg": round((sum(latencies) / len(latencies)), 2)
                if latencies
                else None,
                "max": round(max(latencies), 2) if latencies else None,
            },
            "requested_provider_counts": provider_requested,
            "response_source_counts": provider_source,
            "provider_success_counts": provider_success,
            "provider_failure_counts": provider_failure,
            "intent_counts": intent_breakdown,
            "recent_events": recent_events,
        },
        "providers": provider_health,
        "database": {
            "connected": db_connected,
            "probe_latency_ms": db_latency_ms,
        },
        "ingestion": ingestion,
        "service": {
            "uptime_seconds": uptime_seconds,
            "started_at": datetime.fromtimestamp(
                _app_started_at, timezone.utc
            ).isoformat(),
        },
    }


@app.get("/api/admin/metrics/slo")
async def admin_metrics_slo(
    window_minutes: int = Query(default=60, ge=1, le=1440),
    x_admin_key: Optional[str] = Header(default=None, alias="X-Admin-Key"),
    db: Session = Depends(get_db),
):
    summary = await admin_metrics_summary(
        window_minutes=window_minutes,
        include_recent_events=0,
        x_admin_key=x_admin_key,
        db=db,
    )
    chat = summary.get("chat", {})
    database = summary.get("database", {})
    ingestion = summary.get("ingestion", {})

    target_p95_ms = float(os.getenv("SLO_CHAT_P95_MS", "4000"))
    target_success_rate = float(os.getenv("SLO_CHAT_SUCCESS_RATE_PERCENT", "98"))
    target_db_probe_ms = float(os.getenv("SLO_DB_PROBE_MS", "250"))

    p95 = chat.get("latency_ms", {}).get("p95")
    success_rate = chat.get("success_rate")
    db_probe = database.get("probe_latency_ms")
    db_connected = bool(database.get("connected"))

    p95_ok = isinstance(p95, (int, float)) and float(p95) <= target_p95_ms
    success_ok = (
        isinstance(success_rate, (int, float))
        and float(success_rate) >= target_success_rate
    )
    db_probe_ok = (
        isinstance(db_probe, (int, float)) and float(db_probe) <= target_db_probe_ms
    )
    db_ok = db_connected and (db_probe_ok if db_probe is not None else True)

    checks = [
        {
            "name": "chat_p95_latency",
            "target": f"<= {target_p95_ms}ms",
            "value": p95,
            "ok": bool(p95_ok),
        },
        {
            "name": "chat_success_rate",
            "target": f">= {target_success_rate}%",
            "value": success_rate,
            "ok": bool(success_ok),
        },
        {
            "name": "database_probe",
            "target": f"connected and <= {target_db_probe_ms}ms",
            "value": {"connected": db_connected, "probe_latency_ms": db_probe},
            "ok": bool(db_ok),
        },
        {
            "name": "ingestion_available",
            "target": "available",
            "value": ingestion.get("available"),
            "ok": bool(ingestion.get("available", False)),
        },
    ]
    overall_ok = all(check["ok"] for check in checks)
    return {
        "window_minutes": window_minutes,
        "overall_ok": overall_ok,
        "checks": checks,
    }


@app.get("/api/admin/metrics/prometheus", response_class=PlainTextResponse)
async def admin_metrics_prometheus(
    window_minutes: int = Query(default=60, ge=1, le=1440),
    x_admin_key: Optional[str] = Header(default=None, alias="X-Admin-Key"),
    db: Session = Depends(get_db),
):
    summary = await admin_metrics_summary(
        window_minutes=window_minutes,
        include_recent_events=0,
        x_admin_key=x_admin_key,
        db=db,
    )
    chat = summary.get("chat", {})
    database = summary.get("database", {})
    ingestion = summary.get("ingestion", {})

    lines = [
        "# HELP floatchat_chat_requests_total Total chat requests in the summary window",
        "# TYPE floatchat_chat_requests_total gauge",
        f"floatchat_chat_requests_total {int(chat.get('total_requests') or 0)}",
        "# HELP floatchat_chat_success_rate_percent Chat success rate percent in the summary window",
        "# TYPE floatchat_chat_success_rate_percent gauge",
        f"floatchat_chat_success_rate_percent {float(chat.get('success_rate') or 0.0)}",
        "# HELP floatchat_chat_latency_p95_ms P95 chat latency in milliseconds",
        "# TYPE floatchat_chat_latency_p95_ms gauge",
        f"floatchat_chat_latency_p95_ms {float(chat.get('latency_ms', {}).get('p95') or 0.0)}",
        "# HELP floatchat_chat_cache_hit_rate_percent Cache hit rate percent in the summary window",
        "# TYPE floatchat_chat_cache_hit_rate_percent gauge",
        f"floatchat_chat_cache_hit_rate_percent {float(chat.get('cache_hit_rate') or 0.0)}",
        "# HELP floatchat_database_connected Database connectivity (1 connected, 0 disconnected)",
        "# TYPE floatchat_database_connected gauge",
        f"floatchat_database_connected {1 if database.get('connected') else 0}",
        "# HELP floatchat_database_probe_latency_ms Database probe latency in milliseconds",
        "# TYPE floatchat_database_probe_latency_ms gauge",
        f"floatchat_database_probe_latency_ms {float(database.get('probe_latency_ms') or 0.0)}",
        "# HELP floatchat_ingestion_total_jobs Total ingestion jobs tracked",
        "# TYPE floatchat_ingestion_total_jobs gauge",
        f"floatchat_ingestion_total_jobs {int(ingestion.get('total_jobs') or 0)}",
        "# HELP floatchat_ingestion_available Ingestion availability (1 available, 0 unavailable)",
        "# TYPE floatchat_ingestion_available gauge",
        f"floatchat_ingestion_available {1 if ingestion.get('available') else 0}",
    ]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
