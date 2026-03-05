# FloatChat — Data Ingestion Guide
## No Docker | All Oceans | Last 5 Years | NetCDF → Readable + Visual

**Agent: Read this BEFORE writing any ingestion or visualization code.**
**Date written: 2026-02-27**

---

## 1. Reality Check — Where We Are Right Now

| Item | Status | Detail |
|------|--------|--------|
| ARGO data in database | **EMPTY** | Only 3 fake seed rows (WMO 2902756, 2902834, 2902912) |
| Indian Ocean only | **WAS the default** | Now changing to ALL oceans |
| Docker requirement | **Removing** | Switching to no-Docker path |
| NetCDF parsing code | **Ready** | `argo_ingestion.py` fully written, never run |
| Gemini API key | **SET** | In `.env` as `GROQ_API_KEY` (Groq is active, Gemini needs key) |
| Data date range | **Not filtered** | Need to add `--start-date 2021-01-01` to get last 5 years |
| Visualization | **Frontend exists** | Charts built with Recharts, but showing fake data |

---

## 2. No-Docker Setup — What to Use Instead

### Why no Docker?
Docker requires WSL2 or Hyper-V on Windows 10. We are avoiding that complexity.

### What was Docker providing?
| Docker Service | No-Docker Replacement | How to Install |
|---|---|---|
| PostgreSQL (port 5432) | **PostgreSQL 16 native on Windows** | https://www.postgresql.org/download/windows/ |
| Redis (port 6379) | **Redis for Windows (Memurai)** or skip | https://www.memurai.com/ (free tier) |
| Qdrant (port 6333) | **Qdrant Windows binary** or **skip RAG for now** | https://qdrant.tech/documentation/guides/installation/ |
| Ollama (port 11434) | **Ollama native Windows app** | https://ollama.com/download |

### Minimum required (to actually run the app with real data):
1. **PostgreSQL 16** — mandatory (stores all ARGO data)
2. **Python 3.11+** — mandatory (runs the backend)
3. **Node.js 20+** — mandatory (runs the frontend)

Redis and Qdrant are optional for the core app. The backend gracefully degrades without them.

---

## 3. PostgreSQL Setup (No Docker)

### Step 1 — Install PostgreSQL 16 for Windows
1. Download installer from: https://www.postgresql.org/download/windows/
2. During install:
   - Password for `postgres` superuser: set something you remember (e.g. `admin1234`)
   - Port: `5432` (default)
   - Locale: Default
3. After install, open **pgAdmin 4** (installed alongside)

### Step 2 — Create the database
Open pgAdmin 4 or psql and run:
```sql
CREATE USER floatchat_user WITH PASSWORD '1234';
CREATE DATABASE floatchat OWNER floatchat_user;
GRANT ALL PRIVILEGES ON DATABASE floatchat TO floatchat_user;
```

### Step 3 — Apply the schema (NO timescaledb extension needed)
The current `init-db.sql` has `CREATE EXTENSION IF NOT EXISTS timescaledb` — this will FAIL without Docker.

Use the **simplified schema** instead (see Section 7 below — we need to update init-db.sql).

Run from psql or pgAdmin Query Tool:
```bash
psql -U floatchat_user -d floatchat -f backend/init-db.sql
```

### Step 4 — Update the .env file
Edit `backend/.env`:
```env
DATABASE_URL=postgresql+psycopg2://floatchat_user:1234@localhost:5432/floatchat
GROQ_API_KEY=gsk_****************************  # Add your real key in backend/.env only
GROQ_MODEL=llama-3.3-70b-versatile
GOOGLE_API_KEY=          # ADD YOUR GEMINI KEY HERE
REDIS_URL=               # leave blank — app works without Redis
QDRANT_URL=              # leave blank — RAG falls back to lexical search
```

---

## 4. All Oceans — What ARGO Actually Covers

The global ARGO index (`ar_index_global_prof.txt`) uses a single-letter ocean code in column 5:

| ARGO Code | Ocean | Approximate Bounds |
|---|---|---|
| `I` | Indian Ocean | lon 30–120, lat -40 to 30 |
| `P` | Pacific Ocean | lon 120–290, lat -60 to 65 |
| `A` | Atlantic Ocean | lon 290–360 + 0–30, lat -65 to 70 |
| `S` | Southern Ocean | lat -90 to -35 (all longitudes) |
| `M` | Mediterranean Sea | lon 0–42, lat 30–46 |
| `N` | Arctic Ocean | lat 65–90 |
| `T` | N Atlantic Subpolar | subset of Atlantic |

**To get all oceans:** use `--region global` in the ingestion script.
The script already supports this — `_active_bbox()` returns `None` for global, meaning no bbox filter is applied.

---

## 5. Last 5 Years of Data (2021–2026)

ARGO floats profile approximately every 10 days globally. Over 5 years, globally:
- ~4,000 active floats × 36 profiles/year × 5 years = **~720,000 profiles**
- Each profile has ~100–2000 pressure levels = **potentially 100M+ measurement rows**

### Recommended ingestion strategy (practical for a student machine):

| Tier | Command | Profiles | DB Size | Purpose |
|---|---|---|---|---|
| **Start small** | `--max-profiles 2000 --region global --start-date 2024-01-01` | 2,000 | ~200 MB | Dev & testing |
| **Medium** | `--max-profiles 20000 --region global --start-date 2023-01-01` | 20,000 | ~2 GB | Demo quality |
| **Full 5 years** | `--max-profiles 200000 --region global --start-date 2021-01-01 --index-limit 500000` | 200,000+ | ~20 GB | Research quality |

Start with Tier 1 to validate everything works, then expand.

### Exact command to run (from project root, after PostgreSQL is set up):
```bash
cd "C:\Users\Abhijeet Nardele\OneDrive\Desktop\Edi project\floatchat-ultimate"

python backend/data_ingestion/argo_ingestion.py \
  --region global \
  --start-date 2021-01-01 \
  --end-date 2026-02-27 \
  --index-limit 50000 \
  --max-profiles 5000 \
  --cache-dir backend/data/argo \
  --sleep-seconds 0.05

# Windows single-line version:
python backend\data_ingestion\argo_ingestion.py --region global --start-date 2021-01-01 --end-date 2026-02-27 --index-limit 50000 --max-profiles 5000 --cache-dir backend\data\argo --sleep-seconds 0.05
```

**This will:**
1. Download the global ARGO profile index (~10 MB text file) from IFREMER
2. Filter to profiles dated between 2021-01-01 and 2026-02-27
3. Download up to 5,000 NetCDF profile files (~2 KB each = ~10 MB total)
4. Parse temperature + salinity + pressure from each file
5. Insert into `argo_floats` → `argo_profiles` → `argo_measurements` tables
6. Detect `ocean_basin` from the ARGO ocean code column

**Expected run time:** ~20–40 minutes for 5,000 profiles (network-bound)

---

## 6. How NetCDF Becomes Readable + Visual

### What is a NetCDF file?
A binary scientific data format. A typical ARGO NetCDF file (`R1234567_001.nc`) contains:
```
PLATFORM_NUMBER = "1234567"
CYCLE_NUMBER    = 1
JULD            = 25000.5          (days since 1950-01-01)
LATITUDE        = 12.34
LONGITUDE       = 78.56
PRES[N_LEVELS]  = [5, 10, 20, 50, 100, 200, 500, 1000, 2000] dbar
TEMP[N_LEVELS]  = [28.5, 28.4, 27.9, 26.1, 21.3, 15.2, 7.1, 3.8, 2.1] °C
PSAL[N_LEVELS]  = [35.1, 35.1, 35.2, 35.5, 35.8, 35.9, 35.6, 34.9, 34.7]
TEMP_QC[N_LEVELS] = [1, 1, 1, 1, 1, 1, 2, 1, 1]  (1=good, 4=bad)
```

### The pipeline (already built — just needs to be run):

```
IFREMER GDAC (FTP/HTTPS)
        ↓  [argo_ingestion.py downloads files]
  NetCDF files (.nc)  
        ↓  [parse_netcdf_profile() in argo_ingestion.py]
  Python dict with pressure[], temp[], salinity[]
        ↓  [insert_profile() → insert measurements]
  PostgreSQL tables:
    argo_floats      → float identity, location, ocean
    argo_profiles    → one row per profile (date, lat, lon)
    argo_measurements → one row per depth level (pressure, temp, salinity)
        ↓  [FastAPI endpoints: /api/v1/argo/*]
  JSON API responses
        ↓  [Frontend: Next.js + Recharts]
  Interactive charts and maps
```

### What the user sees after ingestion:

**1. Dashboard** (`/dashboard`)
- Total floats count (real number, not 3)
- Active floats count
- Temperature anomaly chart (by month, real data)
- Regional coverage by ocean basin

**2. Explorer** (`/explorer`)
- Filter by: ocean basin, date range, lat/lon bbox, depth, QC flag
- Map: float positions plotted on Leaflet map
- Table: all matching profiles with columns (WMO, date, lat, lon, basin)
- Export buttons: CSV / JSON / NetCDF

**3. Visualizations** (`/visualizations`)
- Float deployment trend (line chart by year)
- DAC distribution (pie chart by institution)
- Monthly profile volume (bar chart)
- Temperature vs Depth profile chart (NEW — needs to be built)
- Salinity vs Depth profile chart (NEW — needs to be built)
- T-S diagram (NEW — needs to be built)

**4. Chat** (`/chat`)
- Ask: "How many floats are in the Southern Ocean?"
- Ask: "What is the average surface temperature in the Indian Ocean in 2024?"
- Ask: "Show me salinity at 500m depth in the Pacific"
- Gemini/Groq generates SQL → runs against real data → returns answer

---

## 7. Schema Fix Required (Remove TimescaleDB dependency)

The current `init-db.sql` will fail on plain PostgreSQL because of:
1. `CREATE EXTENSION IF NOT EXISTS timescaledb` — not installed
2. `CREATE EXTENSION IF NOT EXISTS postgis` — may not be installed
3. `SELECT create_hypertable(...)` — TimescaleDB function

**Fix: Replace `init-db.sql` with a plain PostgreSQL version** (no extensions needed).

The measurements table with a plain B-tree index on `profile_id` is sufficient for research-scale data (up to ~10M rows). TimescaleDB optimization is only needed for production at 100M+ rows.

The `ocean_basin` column in `argo_floats` also needs to be populated correctly from the ARGO ocean code column 5. Currently the ingestion script hardcodes `"Indian Ocean"` unless `--region global` is used. Needs fix (see Section 8).

---

## 8. Code Fixes Required Before Ingestion Works

### Fix 1 — Ocean basin detection in `argo_ingestion.py`
Current code at line 313:
```python
"ocean_basin": "Indian Ocean" if self.config.region == "indian" else "Unknown",
```

This is wrong for global ingestion. The ARGO index has an ocean code in column 5 (`I`, `P`, `A`, `S`, `M`, `N`). Fix:
```python
OCEAN_CODE_MAP = {
    "I": "Indian Ocean",
    "P": "Pacific Ocean",
    "A": "Atlantic Ocean",
    "S": "Southern Ocean",
    "M": "Mediterranean Sea",
    "N": "Arctic Ocean",
    "T": "N Atlantic Subpolar",
}
```
And pass `item["ocean"]` through the chain to `insert_float()`.

### Fix 2 — Remove TimescaleDB/PostGIS from `init-db.sql`
Remove or comment out:
```sql
CREATE EXTENSION IF NOT EXISTS timescaledb;
CREATE EXTENSION IF NOT EXISTS postgis;
SELECT create_hypertable('argo_profiles', 'profile_date', ...);
```
Replace spatial indexes with plain B-tree indexes on `(latitude, longitude)`.

### Fix 3 — `insert_float()` needs ocean_basin from index data
The `insert_float()` method signature only takes `wmo_number` and `platform_type`. It needs to also accept `ocean_basin` from the parsed index row so basin is correctly written per float.

---

## 9. New Visualizations Needed for Study

After real data is ingested, these charts should be built (they don't exist yet):

### Priority 1 — Core oceanographic charts
| Chart | What it shows | Data source |
|---|---|---|
| **Temperature-Depth Profile** | Temp (°C) vs Depth (m) for one float/profile | `argo_measurements` WHERE profile_id=X |
| **Salinity-Depth Profile** | Salinity vs Depth for one float/profile | `argo_measurements` WHERE profile_id=X |
| **T-S Diagram (Water Mass)** | Temperature vs Salinity scatter — reveals water mass type | `argo_measurements` |
| **Float Track Map** | Path of a single float over time (Leaflet polyline) | `argo_profiles` WHERE wmo_number=X |
| **Depth-Time Heatmap** | Color = temp/salinity, x=time, y=depth | `argo_measurements` JOIN profiles |

### Priority 2 — Multi-float comparison
| Chart | What it shows |
|---|---|
| **Basin Temperature Trend** | Monthly avg surface temp by ocean basin (line chart) |
| **Salinity Anomaly Map** | World map colored by salinity deviation from mean |
| **Float Activity Heatmap** | World map tile density of float profiles per cell |

### Priority 3 — BGC (Bio-Geochemical) charts
| Chart | What it shows |
|---|---|
| **Chlorophyll vs Depth** | BGC float data — primary productivity |
| **Oxygen vs Depth** | Dissolved O2 profile |
| **Nitrate vs Depth** | Nutrient profile |

---

## 10. Gemini API Key — How to Get and Set It

The `.env` currently only has `GROQ_API_KEY`. Gemini works but needs its own key.

### Get Gemini API key (free):
1. Go to: https://aistudio.google.com/app/apikey
2. Click "Create API Key"
3. Copy the key (starts with `AIza...`)

### Set in `.env`:
```env
GOOGLE_API_KEY=AIzaSy...your_key_here
```

The Gemini engine (`backend/llm/gemini_engine.py`) reads `GOOGLE_API_KEY`.
With both Groq and Gemini set, the chat will:
- Try Groq first (faster, free, llama-3.3-70b)
- Fall back to Gemini if Groq fails
- Both can answer questions about the real ARGO data once ingested

---

## 11. Complete Step-by-Step Checklist (No Docker)

```
[ ] 1. Install PostgreSQL 16 for Windows
[ ] 2. Create database: floatchat, user: floatchat_user, password: 1234
[ ] 3. Update init-db.sql — remove timescaledb/postgis extensions
[ ] 4. Fix argo_ingestion.py — ocean_basin from ARGO ocean code, not hardcoded
[ ] 5. Run: psql -U floatchat_user -d floatchat -f backend/init-db.sql
[ ] 6. Update backend/.env — add GOOGLE_API_KEY
[ ] 7. Run: pip install -r backend/requirements.txt
[ ] 8. Run ingestion (start small — 2000 profiles, global, 2024+):
         python backend\data_ingestion\argo_ingestion.py --region global --start-date 2024-01-01 --max-profiles 2000 --cache-dir backend\data\argo
[ ] 9. Verify: hit http://localhost:8000/api/stats — should show real counts
[ ] 10. Start backend: python -m uvicorn backend.main:app --reload --port 8000
[ ] 11. Start frontend: pnpm dev
[ ] 12. Open http://localhost:3000/dashboard — should show real ocean data
[ ] 13. Once validated, run full 5-year global ingestion:
         python backend\data_ingestion\argo_ingestion.py --region global --start-date 2021-01-01 --max-profiles 50000 --index-limit 200000 --cache-dir backend\data\argo --sleep-seconds 0.05
[ ] 14. Build new visualization pages: T-S diagram, depth profiles, float track map
```

---

## 12. Argovis API — Alternative to Direct GDAC Download

If IFREMER GDAC is slow or rate-limited, use the **Argovis API** instead. This is already routed in the backend (`routers/argovis.py` stub).

Argovis URL pattern:
```
https://argovis-api.colorado.edu/argo?
  startDate=2024-01-01T00:00:00Z
  &endDate=2024-12-31T23:59:59Z
  &polygon=[[-180,-90],[-180,90],[180,90],[180,-90],[-180,-90]]
  &data=temp,psal,pres
```

Returns JSON directly — no NetCDF parsing needed. Much easier for small queries.
The `argovis.py` router stub is already wired into `main.py` — just needs implementation.

---

## 13. How Gemini + Groq Read Real Data

Once PostgreSQL has real profiles, the chat pipeline works like this:

1. User asks: *"What is the average temperature at 200m depth in the Pacific Ocean?"*
2. `chat_service.py` classifies query as `"data"` type
3. Routes to Groq (or Gemini) engine
4. Engine gets injected system context: *"Live ARGO dataset: floats=3847, profiles=52,000..."*
5. Engine generates SQL: `SELECT AVG(temperature) FROM argo_measurements am JOIN argo_profiles ap ON am.profile_id=ap.id JOIN argo_floats af ON ap.float_id=af.id WHERE am.pressure BETWEEN 190 AND 210 AND af.ocean_basin='Pacific Ocean'`
6. SQL executes against PostgreSQL
7. Returns: *"Average temperature at ~200m in Pacific Ocean is 14.2°C based on 8,432 measurements from 2021–2026"*

This is the core value proposition — **NetCDF → PostgreSQL → Natural language query → Chart/Answer**.

---

*This document is the ground truth for the no-Docker, all-ocean, 5-year data strategy.*
*Agent: After completing the checklist in Section 11, update CURRENT_STATE.md with the actual counts of ingested data.*
