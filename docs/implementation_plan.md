# FloatChat Ultimate - Phase 1 MVP Implementation Plan

## 🎯 Phase 1 Goal

Build a **functional, production-ready MVP** in 6 months that demonstrates the core value proposition:
- Natural language queries about ARGO ocean data
- AI-powered SQL generation and data retrieval
- Beautiful, interactive visualizations
- Focus on Indian Ocean region
- Local LLM deployment (no cloud dependencies for inference)

---

## 📅 Timeline: 6 Months (26 Weeks)

### Month 1-2: Foundation & Data Pipeline (Weeks 1-8)
### Month 3-4: Backend API & LLM Integration (Weeks 9-16)
### Month 5-6: Frontend & Polish (Weeks 17-26)

---

## 🏗️ Detailed Week-by-Week Plan

## **MONTH 1-2: FOUNDATION & DATA PIPELINE**

### **Week 1-2: Project Setup & Infrastructure**

#### Objectives
- Set up development environment
- Initialize project structure
- Configure databases
- Set up version control and CI/CD

#### Tasks

**Day 1-3: Repository & Monorepo Setup**
```bash
# Initialize project
mkdir floatchat-ultimate
cd floatchat-ultimate
git init

# Set up pnpm workspace
pnpm init
# Create pnpm-workspace.yaml
```

**pnpm-workspace.yaml**
```yaml
packages:
  - 'apps/*'
  - 'packages/*'
  - 'services/*'
  - 'data/*'
```

**Day 4-7: Docker Environment**
```yaml
# docker-compose.yml
version: '3.8'
services:
  postgres:
    image: timescale/timescaledb-ha:pg16-latest
    environment:
      POSTGRES_DB: floatchat
      POSTGRES_USER: floatchat
      POSTGRES_PASSWORD: dev_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
```

**Day 8-10: Database Setup**
```sql
-- Enable extensions
CREATE EXTENSION IF NOT EXISTS timescaledb;
CREATE EXTENSION IF NOT EXISTS postgis;

-- Create schemas
CREATE SCHEMA argo;
CREATE SCHEMA users;
CREATE SCHEMA analytics;
```

**Day 11-14: CI/CD Pipeline**
```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Run tests
        run: |
          pip install poetry
          poetry install
          poetry run pytest
```

**Deliverables**
- ✅ Monorepo structure initialized
- ✅ Docker Compose running locally
- ✅ PostgreSQL + TimescaleDB + PostGIS operational
- ✅ CI/CD pipeline configured

---

### **Week 3-4: Database Schema & Models**

#### Objectives
- Design comprehensive database schema
- Implement data models
- Set up migrations
- Create indices for performance

#### Database Schema

```sql
-- Floats table
CREATE TABLE argo.floats (
    float_id SERIAL PRIMARY KEY,
    wmo_number VARCHAR(10) UNIQUE NOT NULL,
    platform_type VARCHAR(50),
    deployment_date TIMESTAMP,
    deployment_lon FLOAT,
    deployment_lat FLOAT,
    deployment_location GEOGRAPHY(POINT, 4326),
    status VARCHAR(20) DEFAULT 'active',
    last_update TIMESTAMP,
    data_center VARCHAR(50),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Profiles table (hypertable for time-series)
CREATE TABLE argo.profiles (
    profile_id BIGSERIAL,
    float_id INTEGER REFERENCES argo.floats(float_id),
    cycle_number INTEGER,
    profile_date TIMESTAMP NOT NULL,
    longitude FLOAT,
    latitude FLOAT,
    location GEOGRAPHY(POINT, 4326),
    data_mode CHAR(1), -- R=real-time, D=delayed, A=adjusted
    position_qc INTEGER,
    profile_qc INTEGER,
    num_measurements INTEGER,
    max_pressure FLOAT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Convert to hypertable
SELECT create_hypertable('argo.profiles', 'profile_date');

-- Measurements table (hypertable)
CREATE TABLE argo.measurements (
    measurement_id BIGSERIAL,
    profile_id BIGINT,
    pressure FLOAT,
    depth FLOAT,
    temperature FLOAT,
    salinity FLOAT,
    temp_qc INTEGER,
    sal_qc INTEGER,
    measurement_time TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

SELECT create_hypertable('argo.measurements', 'measurement_time');

-- Indices
CREATE INDEX idx_floats_wmo ON argo.floats(wmo_number);
CREATE INDEX idx_floats_location ON argo.floats USING GIST(deployment_location);
CREATE INDEX idx_profiles_float ON argo.profiles(float_id);
CREATE INDEX idx_profiles_date ON argo.profiles(profile_date);
CREATE INDEX idx_profiles_location ON argo.profiles USING GIST(location);
CREATE INDEX idx_measurements_profile ON argo.measurements(profile_id);
CREATE INDEX idx_measurements_depth ON argo.measurements(depth);
```

#### Python Models (SQLAlchemy)

```python
# apps/api/src/models/float.py
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON
from sqlalchemy.dialects.postgresql import JSONB
from geoalchemy2 import Geography
from .base import Base

class Float(Base):
    __tablename__ = 'floats'
    __table_args__ = {'schema': 'argo'}
    
    float_id = Column(Integer, primary_key=True)
    wmo_number = Column(String(10), unique=True, nullable=False)
    platform_type = Column(String(50))
    deployment_date = Column(DateTime)
    deployment_lon = Column(Float)
    deployment_lat = Column(Float)
    deployment_location = Column(Geography('POINT', srid=4326))
    status = Column(String(20), default='active')
    last_update = Column(DateTime)
    data_center = Column(String(50))
    metadata = Column(JSONB)
    created_at = Column(DateTime, server_default='NOW()')
```

**Deliverables**
- ✅ Complete database schema
- ✅ SQLAlchemy models
- ✅ Alembic migrations
- ✅ Database indices optimized

---

### **Week 5-6: ARGO Data Research & Fetching**

#### Objectives
- Research ARGO data sources
- Understand NetCDF format
- Build data fetcher
- Test with sample data

#### ARGO Data Sources

**Primary Source**: ARGO GDAC (Global Data Assembly Center)
- FTP: `ftp.ifremer.fr/ifremer/argo`
- HTTPS: `https://data-argo.ifremer.fr`

**Data Structure**:
```
/dac/{data_center}/{float_wmo}/
  ├── {float_wmo}_meta.nc          # Metadata
  ├── {float_wmo}_prof.nc          # All profiles (monolithic)
  ├── {float_wmo}_tech.nc          # Technical data
  └── profiles/
      ├── D{float_wmo}_{cycle}.nc  # Individual delayed-mode profiles
      └── R{float_wmo}_{cycle}.nc  # Individual real-time profiles
```

#### Data Fetcher Implementation

```python
# data/ingestion/argo/src/fetchers/gdac_fetcher.py
import ftplib
import requests
from pathlib import Path
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

class ARGOGDACFetcher:
    """Fetch ARGO data from IFREMER GDAC"""
    
    BASE_URL = "https://data-argo.ifremer.fr"
    FTP_HOST = "ftp.ifremer.fr"
    FTP_PATH = "/ifremer/argo"
    
    def __init__(self, cache_dir: str = "./cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def get_indian_ocean_floats(self) -> List[str]:
        """Get list of floats in Indian Ocean region"""
        # Indian Ocean bounds: 20°E to 120°E, 30°S to 30°N
        url = f"{self.BASE_URL}/ar_index_global_prof.txt"
        response = requests.get(url)
        
        floats = set()
        for line in response.text.split('\n')[9:]:  # Skip header
            if not line.strip():
                continue
            parts = line.split(',')
            if len(parts) < 6:
                continue
            
            try:
                lat = float(parts[2])
                lon = float(parts[3])
                
                # Check if in Indian Ocean
                if 20 <= lon <= 120 and -30 <= lat <= 30:
                    wmo = parts[0]
                    floats.add(wmo)
            except ValueError:
                continue
        
        logger.info(f"Found {len(floats)} floats in Indian Ocean")
        return list(floats)
    
    def download_float_profile(self, wmo: str, data_center: str = "aoml") -> Path:
        """Download monolithic profile file for a float"""
        filename = f"{wmo}_prof.nc"
        local_path = self.cache_dir / filename
        
        if local_path.exists():
            logger.info(f"Using cached file: {local_path}")
            return local_path
        
        url = f"{self.BASE_URL}/dac/{data_center}/{wmo}/{filename}"
        logger.info(f"Downloading {url}")
        
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(local_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        logger.info(f"Downloaded to {local_path}")
        return local_path
```

**Deliverables**
- ✅ ARGO data source documented
- ✅ Data fetcher implemented
- ✅ Indian Ocean float list (500-1000 floats)
- ✅ Sample NetCDF files downloaded

---

### **Week 7-8: NetCDF Parser & Data Validation**

#### Objectives
- Parse NetCDF files
- Extract profiles and measurements
- Implement quality control
- Validate data integrity

#### NetCDF Parser

```python
# data/ingestion/argo/src/parsers/netcdf_parser.py
import netCDF4 as nc
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class ARGONetCDFParser:
    """Parse ARGO NetCDF profile files"""
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.dataset = nc.Dataset(filepath, 'r')
    
    def get_float_metadata(self) -> Dict:
        """Extract float metadata"""
        return {
            'platform_number': self._get_string_var('PLATFORM_NUMBER'),
            'platform_type': self._get_string_var('PLATFORM_TYPE'),
            'wmo_inst_type': self._get_string_var('WMO_INST_TYPE'),
            'data_center': self._get_string_var('DATA_CENTRE'),
            'deployment_date': self._parse_date('LAUNCH_DATE'),
            'deployment_lat': float(self.dataset.variables['LAUNCH_LATITUDE'][0]),
            'deployment_lon': float(self.dataset.variables['LAUNCH_LONGITUDE'][0]),
        }
    
    def get_profiles(self) -> List[Dict]:
        """Extract all profiles from the file"""
        n_prof = self.dataset.dimensions['N_PROF'].size
        profiles = []
        
        for i in range(n_prof):
            profile = self._parse_profile(i)
            if profile:
                profiles.append(profile)
        
        logger.info(f"Parsed {len(profiles)} profiles")
        return profiles
    
    def _parse_profile(self, index: int) -> Optional[Dict]:
        """Parse a single profile"""
        try:
            # Get profile metadata
            juld = self.dataset.variables['JULD'][index]
            if np.ma.is_masked(juld):
                return None
            
            profile_date = self._julian_to_datetime(juld)
            
            profile = {
                'cycle_number': int(self.dataset.variables['CYCLE_NUMBER'][index]),
                'profile_date': profile_date,
                'latitude': float(self.dataset.variables['LATITUDE'][index]),
                'longitude': float(self.dataset.variables['LONGITUDE'][index]),
                'position_qc': int(self.dataset.variables['POSITION_QC'][index]),
                'data_mode': self._get_string_var('DATA_MODE', index),
                'measurements': self._parse_measurements(index)
            }
            
            return profile
        except Exception as e:
            logger.error(f"Error parsing profile {index}: {e}")
            return None
    
    def _parse_measurements(self, prof_index: int) -> List[Dict]:
        """Parse measurements for a profile"""
        n_levels = self.dataset.dimensions['N_LEVELS'].size
        measurements = []
        
        pres = self.dataset.variables['PRES'][prof_index, :]
        temp = self.dataset.variables['TEMP'][prof_index, :]
        psal = self.dataset.variables['PSAL'][prof_index, :]
        pres_qc = self.dataset.variables['PRES_QC'][prof_index, :]
        temp_qc = self.dataset.variables['TEMP_QC'][prof_index, :]
        psal_qc = self.dataset.variables['PSAL_QC'][prof_index, :]
        
        for i in range(n_levels):
            # Skip masked/missing values
            if np.ma.is_masked(pres[i]) or np.ma.is_masked(temp[i]):
                continue
            
            measurement = {
                'pressure': float(pres[i]),
                'temperature': float(temp[i]) if not np.ma.is_masked(temp[i]) else None,
                'salinity': float(psal[i]) if not np.ma.is_masked(psal[i]) else None,
                'temp_qc': int(temp_qc[i]) if not np.ma.is_masked(temp_qc[i]) else 9,
                'sal_qc': int(psal_qc[i]) if not np.ma.is_masked(psal_qc[i]) else 9,
            }
            
            # Calculate depth from pressure (simplified)
            measurement['depth'] = self._pressure_to_depth(measurement['pressure'])
            
            measurements.append(measurement)
        
        return measurements
    
    @staticmethod
    def _pressure_to_depth(pressure: float, latitude: float = 0) -> float:
        """Convert pressure (dbar) to depth (m) using simplified formula"""
        # UNESCO 1983 formula (simplified)
        x = np.sin(np.radians(latitude)) ** 2
        g = 9.780318 * (1.0 + (5.2788e-3 + 2.36e-5 * x) * x)
        return (pressure * 1e4) / (g * 1025)  # Assuming density = 1025 kg/m³
    
    @staticmethod
    def _julian_to_datetime(julian_day: float) -> datetime:
        """Convert ARGO Julian day to datetime"""
        # ARGO reference: 1950-01-01 00:00:00
        reference = datetime(1950, 1, 1)
        return reference + timedelta(days=float(julian_day))
    
    def _get_string_var(self, var_name: str, index: Optional[int] = None) -> str:
        """Get string variable from NetCDF"""
        if var_name not in self.dataset.variables:
            return ""
        
        var = self.dataset.variables[var_name]
        if index is not None:
            value = var[index]
        else:
            value = var[0] if len(var.shape) > 0 else var[:]
        
        if isinstance(value, np.ndarray):
            return ''.join(c.decode('utf-8') if isinstance(c, bytes) else c for c in value).strip()
        return str(value).strip()
    
    def close(self):
        """Close the NetCDF file"""
        self.dataset.close()
```

#### Quality Control Validator

```python
# data/ingestion/argo/src/validators/qc_validator.py
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

class ARGOQCValidator:
    """Validate ARGO data quality"""
    
    # ARGO QC flags
    QC_GOOD = 1
    QC_PROBABLY_GOOD = 2
    QC_PROBABLY_BAD = 3
    QC_BAD = 4
    QC_CHANGED = 5
    QC_NOT_USED = 8
    QC_MISSING = 9
    
    # Reasonable ranges for parameters
    TEMP_RANGE = (-2.5, 40.0)  # °C
    SALINITY_RANGE = (0, 42)    # PSU
    PRESSURE_RANGE = (0, 7000)  # dbar
    
    @classmethod
    def validate_measurement(cls, measurement: Dict) -> bool:
        """Validate a single measurement"""
        # Check QC flags
        if measurement.get('temp_qc', 9) > cls.QC_PROBABLY_GOOD:
            return False
        if measurement.get('sal_qc', 9) > cls.QC_PROBABLY_GOOD:
            return False
        
        # Check ranges
        temp = measurement.get('temperature')
        if temp is not None:
            if not (cls.TEMP_RANGE[0] <= temp <= cls.TEMP_RANGE[1]):
                logger.warning(f"Temperature out of range: {temp}")
                return False
        
        sal = measurement.get('salinity')
        if sal is not None:
            if not (cls.SALINITY_RANGE[0] <= sal <= cls.SALINITY_RANGE[1]):
                logger.warning(f"Salinity out of range: {sal}")
                return False
        
        pressure = measurement.get('pressure')
        if not (cls.PRESSURE_RANGE[0] <= pressure <= cls.PRESSURE_RANGE[1]):
            logger.warning(f"Pressure out of range: {pressure}")
            return False
        
        return True
    
    @classmethod
    def filter_measurements(cls, measurements: List[Dict]) -> List[Dict]:
        """Filter measurements by quality"""
        return [m for m in measurements if cls.validate_measurement(m)]
```

**Deliverables**
- ✅ NetCDF parser working
- ✅ Quality control implemented
- ✅ Data validation tests passing
- ✅ Sample data parsed successfully

---

## **MONTH 3-4: BACKEND API & LLM INTEGRATION**

### **Week 9-10: FastAPI Backend Setup**

#### FastAPI Application Structure

```python
# apps/api/src/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config.settings import settings
from .api.v1 import auth, data, chat
from .db.session import engine
from .models import Base

app = FastAPI(
    title="FloatChat API",
    description="AI-Powered Ocean Data Platform",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(data.router, prefix="/api/v1/data", tags=["data"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])

@app.on_event("startup")
async def startup():
    # Create tables
    Base.metadata.create_all(bind=engine)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

```python
# apps/api/src/api/v1/data.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from ...db.session import get_db
from ...services.data_service import DataService
from ...schemas.data import FloatResponse, ProfileResponse

router = APIRouter()

@router.get("/floats", response_model=List[FloatResponse])
async def get_floats(
    min_lat: Optional[float] = Query(None),
    max_lat: Optional[float] = Query(None),
    min_lon: Optional[float] = Query(None),
    max_lon: Optional[float] = Query(None),
    db: Session = Depends(get_db)
):
    """Get ARGO floats with optional geographic filtering"""
    service = DataService(db)
    return service.get_floats(
        min_lat=min_lat,
        max_lat=max_lat,
        min_lon=min_lon,
        max_lon=max_lon
    )

@router.get("/profiles", response_model=List[ProfileResponse])
async def get_profiles(
    float_id: Optional[int] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    min_lat: Optional[float] = Query(None),
    max_lat: Optional[float] = Query(None),
    min_lon: Optional[float] = Query(None),
    max_lon: Optional[float] = Query(None),
    db: Session = Depends(get_db)
):
    """Get ARGO profiles with filtering"""
    service = DataService(db)
    return service.get_profiles(
        float_id=float_id,
        start_date=start_date,
        end_date=end_date,
        min_lat=min_lat,
        max_lat=max_lat,
        min_lon=min_lon,
        max_lon=max_lon
    )
```

**Deliverables**
- ✅ FastAPI application running
- ✅ Data endpoints implemented
- ✅ API documentation (Swagger)
- ✅ Basic authentication

---

### **Week 11-12: LLM Integration with Ollama**

#### Ollama Setup

```bash
# Pull Mistral model
docker exec -it ollama ollama pull mistral:7b-instruct

# Test
curl http://localhost:11434/api/generate -d '{
  "model": "mistral:7b-instruct",
  "prompt": "Explain ARGO floats",
  "stream": false
}'
```

#### LLM Service

```python
# services/llm-service/src/models/inference.py
import requests
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class OllamaClient:
    """Client for Ollama LLM inference"""
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.model = "mistral:7b-instruct"
    
    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str:
        """Generate text completion"""
        url = f"{self.base_url}/api/generate"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        
        if system:
            payload["system"] = system
        
        try:
            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()
            return response.json()["response"]
        except Exception as e:
            logger.error(f"LLM generation error: {e}")
            raise
    
    def chat(self, messages: List[Dict[str, str]]) -> str:
        """Chat completion"""
        url = f"{self.base_url}/api/chat"
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False
        }
        
        try:
            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()
            return response.json()["message"]["content"]
        except Exception as e:
            logger.error(f"LLM chat error: {e}")
            raise
```

#### Natural Language to SQL

```python
# services/llm-service/src/agents/sql_agent.py
from typing import Dict, Optional
from ..models.inference import OllamaClient
from ..prompts.sql_generation import SQL_GENERATION_PROMPT
import re
import logging

logger = logging.getLogger(__name__)

class SQLAgent:
    """Convert natural language to SQL queries"""
    
    def __init__(self):
        self.llm = OllamaClient()
        self.schema = self._load_schema()
    
    def _load_schema(self) -> str:
        """Load database schema description"""
        return """
        Database Schema:
        
        Table: argo.floats
        - float_id (INTEGER): Primary key
        - wmo_number (VARCHAR): WMO identifier
        - platform_type (VARCHAR): Type of float
        - deployment_date (TIMESTAMP): When deployed
        - deployment_lat (FLOAT): Deployment latitude
        - deployment_lon (FLOAT): Deployment longitude
        - status (VARCHAR): active/inactive
        
        Table: argo.profiles
        - profile_id (BIGINT): Primary key
        - float_id (INTEGER): Foreign key to floats
        - cycle_number (INTEGER): Profile cycle number
        - profile_date (TIMESTAMP): Date of profile
        - latitude (FLOAT): Profile latitude
        - longitude (FLOAT): Profile longitude
        - data_mode (CHAR): R=real-time, D=delayed
        
        Table: argo.measurements
        - measurement_id (BIGINT): Primary key
        - profile_id (BIGINT): Foreign key to profiles
        - pressure (FLOAT): Pressure in dbar
        - depth (FLOAT): Depth in meters
        - temperature (FLOAT): Temperature in °C
        - salinity (FLOAT): Salinity in PSU
        - temp_qc (INTEGER): Temperature QC flag (1=good, 2=probably good)
        - sal_qc (INTEGER): Salinity QC flag
        """
    
    def generate_sql(self, question: str) -> Dict:
        """Generate SQL from natural language question"""
        prompt = SQL_GENERATION_PROMPT.format(
            schema=self.schema,
            question=question
        )
        
        response = self.llm.generate(
            prompt=prompt,
            temperature=0.1,  # Low temperature for deterministic SQL
            max_tokens=1000
        )
        
        # Extract SQL from response
        sql = self._extract_sql(response)
        
        # Validate SQL
        if not self._validate_sql(sql):
            raise ValueError("Generated SQL failed validation")
        
        return {
            "sql": sql,
            "explanation": response
        }
    
    def _extract_sql(self, response: str) -> str:
        """Extract SQL query from LLM response"""
        # Look for SQL in code blocks
        pattern = r"```sql\n(.*?)\n```"
        match = re.search(pattern, response, re.DOTALL)
        if match:
            return match.group(1).strip()
        
        # Fallback: look for SELECT statement
        pattern = r"(SELECT.*?;)"
        match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        raise ValueError("Could not extract SQL from response")
    
    def _validate_sql(self, sql: str) -> bool:
        """Basic SQL validation"""
        # Check for dangerous operations
        dangerous = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE']
        sql_upper = sql.upper()
        for keyword in dangerous:
            if keyword in sql_upper:
                logger.warning(f"Dangerous SQL keyword detected: {keyword}")
                return False
        
        # Must start with SELECT
        if not sql_upper.strip().startswith('SELECT'):
            return False
        
        # Check for required tables
        if 'argo.' not in sql.lower():
            return False
        
        return True
```

```python
# services/llm-service/src/prompts/sql_generation.py
SQL_GENERATION_PROMPT = """You are an expert SQL query generator for oceanographic ARGO float data.

{schema}

User Question: {question}

Generate a PostgreSQL query to answer this question. Follow these rules:
1. Use ONLY SELECT statements (no INSERT, UPDATE, DELETE, DROP)
2. Always use schema-qualified table names (argo.floats, argo.profiles, argo.measurements)
3. Use appropriate JOINs when querying multiple tables
4. Apply QC filters: temp_qc <= 2 AND sal_qc <= 2 for good quality data
5. Use ST_MakePoint(longitude, latitude) for geographic queries
6. Use proper date formatting for timestamps
7. Limit results to 1000 rows unless specifically asked for more
8. Include meaningful column aliases

Return ONLY the SQL query in a ```sql code block, followed by a brief explanation.

Example:
```sql
SELECT 
    f.wmo_number,
    p.profile_date,
    AVG(m.temperature) as avg_temperature
FROM argo.floats f
JOIN argo.profiles p ON f.float_id = p.float_id
JOIN argo.measurements m ON p.profile_id = m.profile_id
WHERE p.profile_date >= '2023-01-01'
  AND m.depth BETWEEN 0 AND 100
  AND m.temp_qc <= 2
GROUP BY f.wmo_number, p.profile_date
ORDER BY p.profile_date DESC
LIMIT 100;
```

This query retrieves average surface temperature (0-100m depth) for each float profile since 2023, using only good quality data.

Now generate the SQL for the user's question.
"""
```

**Deliverables**
- ✅ Ollama running locally
- ✅ LLM service implemented
- ✅ SQL generation working
- ✅ Query validation in place

---

## **MONTH 5-6: FRONTEND & VISUALIZATION**

### **Week 17-20: Streamlit Dashboard**

#### Main Dashboard

```python
# apps/streamlit/app.py
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Page config
st.set_page_config(
    page_title="FloatChat Ultimate",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        background: linear-gradient(90deg, #0066cc, #00ccff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 1rem 0;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<h1 class="main-header">🌊 FloatChat Ultimate</h1>', unsafe_allow_html=True)
st.markdown("### AI-Powered Ocean Data Platform")

# Sidebar
with st.sidebar:
    st.image("logo.png", width=200)
    st.markdown("---")
    
    page = st.radio(
        "Navigation",
        ["🏠 Dashboard", "💬 AI Chat", "📊 Data Explorer", "📈 Analytics"]
    )
    
    st.markdown("---")
    st.markdown("### Filters")
    
    date_range = st.date_input(
        "Date Range",
        value=(datetime.now() - timedelta(days=365), datetime.now())
    )
    
    region = st.selectbox(
        "Ocean Region",
        ["All", "Arabian Sea", "Bay of Bengal", "Southern Indian Ocean"]
    )

# Main content
if page == "🏠 Dashboard":
    show_dashboard()
elif page == "💬 AI Chat":
    show_chat()
elif page == "📊 Data Explorer":
    show_explorer()
elif page == "📈 Analytics":
    show_analytics()

def show_dashboard():
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Active Floats", "847", "+12")
    with col2:
        st.metric("Total Profiles", "125,432", "+1,234")
    with col3:
        st.metric("Data Coverage", "94.2%", "+2.1%")
    with col4:
        st.metric("Last Update", "2 hours ago", "")
    
    st.markdown("---")
    
    # Map
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🗺️ Float Locations")
        floats_df = fetch_floats()
        fig = create_map(floats_df)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("📊 Recent Activity")
        activity_df = fetch_recent_activity()
        st.dataframe(activity_df, use_container_width=True)
    
    # Charts
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🌡️ Temperature Trends")
        temp_df = fetch_temperature_trends()
        fig = px.line(temp_df, x='date', y='temperature', color='region')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("🧂 Salinity Distribution")
        sal_df = fetch_salinity_distribution()
        fig = px.histogram(sal_df, x='salinity', nbins=50)
        st.plotly_chart(fig, use_container_width=True)

def show_chat():
    st.subheader("💬 AI Ocean Assistant")
    
    # Chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Display chat
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "chart" in message:
                st.plotly_chart(message["chart"])
    
    # Input
    if prompt := st.chat_input("Ask about ocean data..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = get_ai_response(prompt)
                st.markdown(response["text"])
                
                if "data" in response:
                    df = pd.DataFrame(response["data"])
                    st.dataframe(df)
                
                if "chart" in response:
                    st.plotly_chart(response["chart"])
        
        st.session_state.messages.append({
            "role": "assistant",
            "content": response["text"],
            "chart": response.get("chart")
        })

def get_ai_response(question: str) -> dict:
    """Get response from AI backend"""
    response = requests.post(
        "http://localhost:8000/api/v1/chat/query",
        json={"question": question}
    )
    return response.json()

def create_map(df: pd.DataFrame):
    """Create interactive map of float locations"""
    fig = go.Figure()
    
    fig.add_trace(go.Scattergeo(
        lon=df['longitude'],
        lat=df['latitude'],
        mode='markers',
        marker=dict(
            size=8,
            color=df['status'].map({'active': 'green', 'inactive': 'red'}),
            line=dict(width=1, color='white')
        ),
        text=df['wmo_number'],
        hovertemplate='<b>%{text}</b><br>Lat: %{lat}<br>Lon: %{lon}<extra></extra>'
    ))
    
    fig.update_geos(
        projection_type="natural earth",
        showland=True,
        landcolor="lightgray",
        showocean=True,
        oceancolor="lightblue",
        center=dict(lat=0, lon=70),
        projection_scale=2
    )
    
    fig.update_layout(
        height=600,
        margin=dict(l=0, r=0, t=0, b=0)
    )
    
    return fig
```

**Deliverables**
- ✅ Streamlit dashboard running
- ✅ Interactive visualizations
- ✅ Chat interface
- ✅ Data explorer

---

## 🎯 Success Criteria for MVP

### Functional Requirements
- ✅ 500+ ARGO floats ingested (Indian Ocean)
- ✅ 50,000+ profiles in database
- ✅ Natural language queries working (80%+ accuracy)
- ✅ 10+ visualization types available
- ✅ Response time <5 seconds for queries
- ✅ Chat interface functional

### Technical Requirements
- ✅ PostgreSQL + TimescaleDB operational
- ✅ Local LLM (Ollama) running
- ✅ FastAPI backend deployed
- ✅ Streamlit frontend accessible
- ✅ Docker Compose setup working
- ✅ CI/CD pipeline functional

### Quality Requirements
- ✅ 70%+ test coverage
- ✅ API documentation complete
- ✅ User guide written
- ✅ Deployment guide documented

---

## 📦 Deployment Strategy

### Local Development
```bash
docker-compose up -d
pnpm run dev
```

### Production (Oracle Cloud Free Tier)
- 4 ARM cores, 24GB RAM
- Ubuntu 22.04 LTS
- Docker + Docker Compose
- NGINX reverse proxy
- Let's Encrypt SSL

---

This implementation plan provides a **realistic, achievable path** to building the MVP in 6 months with a small team (2-3 developers). Each week has clear objectives, deliverables, and code examples to follow.
