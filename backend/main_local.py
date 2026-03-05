from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import sqlite3
import os
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="FloatChat Ultimate API",
    description="AI-Powered Ocean Data Platform API",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and include routers (optional, will work without PostgreSQL)
try:
    from routers import argo_filter
    app.include_router(argo_filter.router)
    logger.info("ARGO filter router loaded successfully")
except ImportError as e:
    logger.warning(f"Could not load ARGO filter router (requires PostgreSQL): {e}")

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

# Initialize SQLite database
DB_PATH = "floatchat.db"

def init_db():
    """Initialize SQLite database with sample data"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS argo_floats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            wmo_number TEXT UNIQUE NOT NULL,
            platform_type TEXT,
            last_latitude REAL,
            last_longitude REAL,
            status TEXT,
            ocean_basin TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS argo_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            wmo_number TEXT NOT NULL,
            cycle_number INTEGER NOT NULL,
            profile_date TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL
        )
    """)
    
    # Insert sample data
    sample_floats = [
        ('2902756', 'APEX', 10.5, 75.2, 'ACTIVE', 'Indian Ocean'),
        ('2902834', 'ARVOR', 12.3, 78.5, 'ACTIVE', 'Indian Ocean'),
        ('2902912', 'APEX', 8.7, 72.1, 'ACTIVE', 'Indian Ocean'),
        ('2903015', 'APEX', 15.2, 80.3, 'ACTIVE', 'Indian Ocean'),
        ('2903124', 'ARVOR', 5.8, 85.6, 'ACTIVE', 'Indian Ocean'),
    ]
    
    for float_data in sample_floats:
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO argo_floats 
                (wmo_number, platform_type, last_latitude, last_longitude, status, ocean_basin)
                VALUES (?, ?, ?, ?, ?, ?)
            """, float_data)
        except:
            pass
    
    # Insert sample profiles
    sample_profiles = [
        ('2902756', 1, '2024-01-15 10:30:00', 10.5, 75.2),
        ('2902756', 2, '2024-01-20 14:15:00', 10.6, 75.3),
        ('2902834', 1, '2024-01-16 08:45:00', 12.3, 78.5),
        ('2902912', 1, '2024-01-17 12:00:00', 8.7, 72.1),
    ]
    
    for profile_data in sample_profiles:
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO argo_profiles 
                (wmo_number, cycle_number, profile_date, latitude, longitude)
                VALUES (?, ?, ?, ?, ?)
            """, profile_data)
        except:
            pass
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

# Pydantic models
class FloatResponse(BaseModel):
    id: int
    wmo_number: str
    platform_type: Optional[str]
    last_latitude: Optional[float]
    last_longitude: Optional[float]
    status: Optional[str]
    ocean_basin: Optional[str]

class ProfileResponse(BaseModel):
    id: int
    wmo_number: str
    cycle_number: int
    profile_date: str
    latitude: float
    longitude: float

class StatsResponse(BaseModel):
    total_floats: int
    active_floats: int
    total_profiles: int
    ocean_basins: List[str]

# API Routes
@app.get("/")
async def root():
    return {
        "message": "FloatChat Ultimate API",
        "version": "1.0.0",
        "status": "running",
        "mode": "local_development"
    }

@app.get("/health")
async def health_check():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        conn.close()
        return {"status": "healthy", "database": "connected", "mode": "sqlite"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")

@app.get("/api/floats", response_model=List[FloatResponse])
async def get_floats(limit: int = 100, ocean_basin: Optional[str] = None):
    """Get list of ARGO floats"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    query = "SELECT id, wmo_number, platform_type, last_latitude, last_longitude, status, ocean_basin FROM argo_floats"
    params = []

    if ocean_basin:
        query += " WHERE ocean_basin = ?"
        params.append(ocean_basin)

    query += " LIMIT ?"
    params.append(limit)

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    floats = []
    for row in rows:
        floats.append({
            "id": row[0],
            "wmo_number": row[1],
            "platform_type": row[2],
            "last_latitude": row[3],
            "last_longitude": row[4],
            "status": row[5],
            "ocean_basin": row[6]
        })
    
    return floats

@app.get("/api/floats/{wmo_number}", response_model=FloatResponse)
async def get_float(wmo_number: str):
    """Get specific ARGO float by WMO number"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, wmo_number, platform_type, last_latitude, last_longitude, status, ocean_basin 
        FROM argo_floats WHERE wmo_number = ?
    """, (wmo_number,))
    
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="Float not found")
    
    return {
        "id": row[0],
        "wmo_number": row[1],
        "platform_type": row[2],
        "last_latitude": row[3],
        "last_longitude": row[4],
        "status": row[5],
        "ocean_basin": row[6]
    }

@app.get("/api/profiles", response_model=List[ProfileResponse])
async def get_profiles(wmo_number: Optional[str] = None, limit: int = 100):
    """Get ARGO profiles"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    query = "SELECT id, wmo_number, cycle_number, profile_date, latitude, longitude FROM argo_profiles"
    params = []

    if wmo_number:
        query += " WHERE wmo_number = ?"
        params.append(wmo_number)

    query += " ORDER BY profile_date DESC LIMIT ?"
    params.append(limit)

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    profiles = []
    for row in rows:
        profiles.append({
            "id": row[0],
            "wmo_number": row[1],
            "cycle_number": row[2],
            "profile_date": row[3],
            "latitude": row[4],
            "longitude": row[5]
        })
    
    return profiles

@app.get("/api/stats", response_model=StatsResponse)
async def get_stats():
    """Get platform statistics"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Total floats
    cursor.execute("SELECT COUNT(*) FROM argo_floats")
    total_floats = cursor.fetchone()[0]
    
    # Active floats
    cursor.execute("SELECT COUNT(*) FROM argo_floats WHERE status = 'ACTIVE'")
    active_floats = cursor.fetchone()[0]
    
    # Total profiles
    cursor.execute("SELECT COUNT(*) FROM argo_profiles")
    total_profiles = cursor.fetchone()[0]
    
    # Ocean basins
    cursor.execute("SELECT DISTINCT ocean_basin FROM argo_floats WHERE ocean_basin IS NOT NULL")
    ocean_basins = [row[0] for row in cursor.fetchall()]
    
    conn.close()
    
    return {
        "total_floats": total_floats,
        "active_floats": active_floats,
        "total_profiles": total_profiles,
        "ocean_basins": ocean_basins
    }

@app.post("/api/chat")
async def chat(message: dict):
    """
    Chat endpoint with multi-LLM support (Ollama + OpenAI + Gemini)
    
    Request body:
        - message: User's question (required)
        - provider: "auto", "groq", "gemini", "openai", or "ollama" (optional, default: "auto")
    """
    user_message = message.get("message", "")
    provider = message.get("provider", "auto")
    if isinstance(provider, str):
        provider = provider.lower().strip()
    else:
        provider = "auto"
    if provider not in {"auto", "groq", "gemini", "openai", "ollama"}:
        raise HTTPException(status_code=400, detail="Invalid provider. Use 'auto', 'groq', 'gemini', 'openai', or 'ollama'.")
    
    if not user_message:
        raise HTTPException(status_code=400, detail="Message is required")
    
    try:
        # Import hybrid chat service
        from llm.chat_service import HybridChatService
        
        # Create chat service
        service = HybridChatService()
        
        # Process query with selected provider
        result = service.process_query(user_message, provider=provider)
        
        return {
            "success": result.get("success", False),
            "response": result.get("response"),
            "sql_query": result.get("sql_query"),
            "data": result.get("data", [])[:10],  # Limit to 10 rows
            "row_count": result.get("row_count", 0),
            "source": result.get("source"),  # Which LLM was used
            "query_type": result.get("query_type"),  # "data" or "general"
            "sources": result.get("sources", []),
            "error": result.get("error")
        }
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return {
            "success": False,
            "response": f"I received your question: '{user_message}'. The AI chat feature requires Ollama or Gemini. Error: {str(e)}",
            "error": str(e)
        }

@app.get("/api/chat/providers")
async def get_chat_providers():
    """Get available LLM providers"""
    try:
        from llm.chat_service import HybridChatService
        service = HybridChatService()
        return {
            "providers": service.get_available_providers(),
            "health": service.health_check()
        }
    except Exception as e:
        return {
            "providers": [],
            "health": {},
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    print("🌊 Starting FloatChat Ultimate API (Local Development Mode)")
    print("📊 Database: SQLite (floatchat.db)")
    print("🚀 Server: http://localhost:8000")
    print("📖 API Docs: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
