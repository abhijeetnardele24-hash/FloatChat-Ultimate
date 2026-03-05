# FloatChat Ultimate - Technology Stack Guide & Quick Start

## 🎯 Complete Technology Stack

### **Frontend Stack**

#### Core Framework
- **Next.js 14+** - React framework with App Router
  - Server Components for performance
  - Streaming SSR
  - Built-in optimization
  - Installation: `npx create-next-app@latest`

#### UI & Styling
- **Tailwind CSS** - Utility-first CSS framework
  - Installation: `npm install -D tailwindcss postcss autoprefixer`
  - Config: `npx tailwindcss init -p`

- **shadcn/ui** - High-quality React components
  - Installation: `npx shadcn-ui@latest init`
  - Components: `npx shadcn-ui@latest add button card dialog`

- **Radix UI** - Unstyled, accessible components
  - Automatically installed with shadcn/ui

#### Animation & Motion
- **Framer Motion** - React animation library
  - Installation: `npm install framer-motion`
  - Usage: Layout animations, gestures, variants

- **GSAP** - Professional animation library
  - Installation: `npm install gsap`
  - Usage: Complex timelines, scroll animations

- **Lottie** - Vector animations
  - Installation: `npm install lottie-react`

#### State Management
- **Zustand** - Lightweight state management
  - Installation: `npm install zustand`
  - Simple, no boilerplate

- **TanStack Query (React Query)** - Server state management
  - Installation: `npm install @tanstack/react-query`
  - Caching, refetching, optimistic updates

#### Visualization Libraries

**3D Graphics**
- **Three.js** - WebGL library
  - Installation: `npm install three`
- **React Three Fiber** - React renderer for Three.js
  - Installation: `npm install @react-three/fiber`
- **Drei** - Useful helpers for R3F
  - Installation: `npm install @react-three/drei`

**2D Charts**
- **D3.js** - Data visualization
  - Installation: `npm install d3`
- **Visx** - Low-level React primitives
  - Installation: `npm install @visx/visx`
- **Plotly.js** - Scientific plotting
  - Installation: `npm install plotly.js react-plotly.js`
- **Recharts** - Composable charts
  - Installation: `npm install recharts`

**Maps**
- **Mapbox GL JS** - Interactive maps
  - Installation: `npm install mapbox-gl react-map-gl`
- **Deck.gl** - WebGL data visualization
  - Installation: `npm install deck.gl @deck.gl/react`

**Data Grids**
- **AG Grid** - Enterprise data grid
  - Installation: `npm install ag-grid-react ag-grid-community`

#### Icons & Fonts
- **Lucide React** - Beautiful icons
  - Installation: `npm install lucide-react`
- **Google Fonts** - Typography
  - Next.js: Use `next/font/google`

---

### **Backend Stack**

#### API Framework
- **FastAPI** - Modern Python web framework
  - Installation: `pip install fastapi[all]`
  - Features: Auto docs, validation, async support

#### Database
- **PostgreSQL 16** - Relational database
  - Docker: `docker run -d postgres:16-alpine`

- **TimescaleDB** - Time-series extension
  - Docker: `docker run -d timescale/timescaledb-ha:pg16-latest`

- **PostGIS** - Spatial extension
  - Included in TimescaleDB image

#### ORM & Migrations
- **SQLAlchemy** - Python ORM
  - Installation: `pip install sqlalchemy`

- **Alembic** - Database migrations
  - Installation: `pip install alembic`
  - Init: `alembic init migrations`

- **GeoAlchemy2** - Spatial types for SQLAlchemy
  - Installation: `pip install geoalchemy2`

#### Caching
- **Redis** - In-memory cache
  - Docker: `docker run -d redis:7-alpine`
  - Python client: `pip install redis`

- **Memcached** - Distributed cache
  - Docker: `docker run -d memcached:alpine`
  - Python client: `pip install pymemcache`

#### Message Queue
- **Apache Kafka** - Event streaming
  - Docker: Use Confluent Platform
  - Python client: `pip install kafka-python`

- **RabbitMQ** - Message broker
  - Docker: `docker run -d rabbitmq:management`
  - Python client: `pip install pika`

#### Search
- **Elasticsearch** - Full-text search
  - Docker: `docker run -d elasticsearch:8.11.0`
  - Python client: `pip install elasticsearch`

- **Typesense** - Fast search engine
  - Docker: `docker run -d typesense/typesense:latest`
  - Python client: `pip install typesense`

---

### **AI/ML Stack**

#### LLM Serving
- **Ollama** - Local LLM runtime
  - Installation: `curl -fsSL https://ollama.com/install.sh | sh`
  - Docker: `docker run -d ollama/ollama`
  - Models: `ollama pull mistral:7b-instruct`

- **vLLM** - High-performance inference
  - Installation: `pip install vllm`
  - GPU required

- **Text Generation Inference (TGI)** - HuggingFace inference
  - Docker: `docker run -d ghcr.io/huggingface/text-generation-inference`

#### Vector Database
- **Qdrant** - Vector search engine
  - Docker: `docker run -d qdrant/qdrant`
  - Python client: `pip install qdrant-client`

- **Weaviate** - Vector database
  - Docker: `docker run -d semitechnologies/weaviate`
  - Python client: `pip install weaviate-client`

#### Embeddings
- **Sentence Transformers** - Embedding models
  - Installation: `pip install sentence-transformers`
  - Models: `all-MiniLM-L6-v2`, `BGE-M3`, `E5-Mistral`

- **HuggingFace Transformers** - Model library
  - Installation: `pip install transformers`

#### ML Frameworks
- **PyTorch** - Deep learning
  - Installation: `pip install torch torchvision`

- **Scikit-learn** - ML algorithms
  - Installation: `pip install scikit-learn`

- **XGBoost** - Gradient boosting
  - Installation: `pip install xgboost`

#### ML Ops
- **MLflow** - Experiment tracking
  - Installation: `pip install mlflow`
  - UI: `mlflow ui`

- **Weights & Biases** - ML platform
  - Installation: `pip install wandb`

- **DVC** - Data version control
  - Installation: `pip install dvc`

---

### **Data Processing Stack**

#### Data Formats
- **NetCDF4** - Scientific data format
  - Installation: `pip install netCDF4`

- **Apache Parquet** - Columnar storage
  - Installation: `pip install pyarrow`

- **HDF5** - Hierarchical data
  - Installation: `pip install h5py`

#### Processing Frameworks
- **Apache Spark** - Distributed processing
  - Installation: `pip install pyspark`

- **Dask** - Parallel computing
  - Installation: `pip install dask[complete]`

- **Polars** - Fast DataFrame library
  - Installation: `pip install polars`

#### Workflow Orchestration
- **Prefect** - Modern workflow engine
  - Installation: `pip install prefect`
  - UI: `prefect server start`

- **Dagster** - Data orchestration
  - Installation: `pip install dagster dagit`

- **Apache Airflow** - Workflow platform
  - Installation: `pip install apache-airflow`

#### Geospatial
- **Shapely** - Geometric operations
  - Installation: `pip install shapely`

- **GeoPandas** - Spatial DataFrames
  - Installation: `pip install geopandas`

- **Rasterio** - Raster data
  - Installation: `pip install rasterio`

---

### **DevOps Stack**

#### Containerization
- **Docker** - Container platform
  - Installation: https://docs.docker.com/get-docker/

- **Docker Compose** - Multi-container apps
  - Included with Docker Desktop

#### Orchestration
- **Kubernetes** - Container orchestration
  - Local: Minikube, Kind, K3s
  - Cloud: EKS, GKE, AKS

- **Helm** - Kubernetes package manager
  - Installation: `curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash`

#### Infrastructure as Code
- **Terraform** - IaC tool
  - Installation: https://www.terraform.io/downloads

- **Pulumi** - Modern IaC
  - Installation: `curl -fsSL https://get.pulumi.com | sh`

#### CI/CD
- **GitHub Actions** - CI/CD platform
  - Built into GitHub

- **ArgoCD** - GitOps CD
  - Installation: `kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml`

#### Monitoring
- **Prometheus** - Metrics collection
  - Docker: `docker run -d prom/prometheus`

- **Grafana** - Visualization
  - Docker: `docker run -d grafana/grafana`

- **Loki** - Log aggregation
  - Docker: `docker run -d grafana/loki`

- **Jaeger** - Distributed tracing
  - Docker: `docker run -d jaegertracing/all-in-one`

#### Secrets Management
- **HashiCorp Vault** - Secrets storage
  - Docker: `docker run -d vault`

---

## 🚀 Quick Start Guide

### Prerequisites

**Required Software**
- Node.js 18+ (LTS)
- Python 3.11+
- Docker & Docker Compose
- Git
- pnpm (recommended) or npm

**Optional**
- NVIDIA GPU (for local LLM)
- CUDA Toolkit (for GPU support)

### Step 1: Install Core Tools

```bash
# Node.js (using nvm)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
nvm install 18
nvm use 18

# pnpm
npm install -g pnpm

# Python (using pyenv)
curl https://pyenv.run | bash
pyenv install 3.11
pyenv global 3.11

# Poetry (Python package manager)
curl -sSL https://install.python-poetry.org | python3 -

# Docker Desktop
# Download from https://www.docker.com/products/docker-desktop
```

### Step 2: Clone and Setup Project

```bash
# Create project directory
mkdir floatchat-ultimate
cd floatchat-ultimate

# Initialize Git
git init

# Create basic structure
mkdir -p apps/{web,api,streamlit}
mkdir -p services/{llm-service,auth-service}
mkdir -p data/ingestion/argo
mkdir -p infrastructure/{docker,kubernetes}
mkdir -p packages/{ui,types,utils}

# Initialize pnpm workspace
cat > pnpm-workspace.yaml << EOF
packages:
  - 'apps/*'
  - 'packages/*'
  - 'services/*'
EOF

# Initialize root package.json
pnpm init
```

### Step 3: Set Up Docker Environment

```bash
# Create docker-compose.yml
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  postgres:
    image: timescale/timescaledb-ha:pg16-latest
    container_name: floatchat-postgres
    environment:
      POSTGRES_DB: floatchat
      POSTGRES_USER: floatchat
      POSTGRES_PASSWORD: dev_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U floatchat"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: floatchat-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  qdrant:
    image: qdrant/qdrant:latest
    container_name: floatchat-qdrant
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - qdrant_data:/qdrant/storage

  ollama:
    image: ollama/ollama:latest
    container_name: floatchat-ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama

volumes:
  postgres_data:
  redis_data:
  qdrant_data:
  ollama_data:
EOF

# Start services
docker-compose up -d

# Wait for services to be ready
sleep 10

# Pull Mistral model
docker exec floatchat-ollama ollama pull mistral:7b-instruct
```

### Step 4: Initialize Database

```bash
# Connect to PostgreSQL
docker exec -it floatchat-postgres psql -U floatchat -d floatchat

# Run SQL commands
CREATE EXTENSION IF NOT EXISTS timescaledb;
CREATE EXTENSION IF NOT EXISTS postgis;

CREATE SCHEMA argo;
CREATE SCHEMA users;

-- Create floats table
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
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Exit psql
\q
```

### Step 5: Set Up Backend API

```bash
cd apps/api

# Initialize Poetry project
poetry init -n
poetry add fastapi uvicorn sqlalchemy psycopg2-binary alembic geoalchemy2 redis pydantic-settings

# Create basic structure
mkdir -p src/{api/v1,models,schemas,services,core,db}

# Create main.py
cat > src/main.py << 'EOF'
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="FloatChat API",
    description="AI-Powered Ocean Data Platform",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "FloatChat API is running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
EOF

# Run API
poetry run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### Step 6: Set Up Streamlit Frontend

```bash
cd apps/streamlit

# Initialize Poetry
poetry init -n
poetry add streamlit plotly pandas requests

# Create app.py
cat > app.py << 'EOF'
import streamlit as st

st.set_page_config(
    page_title="FloatChat Ultimate",
    page_icon="🌊",
    layout="wide"
)

st.title("🌊 FloatChat Ultimate")
st.markdown("### AI-Powered Ocean Data Platform")

st.info("Welcome to FloatChat Ultimate MVP!")

# Sidebar
with st.sidebar:
    st.markdown("### Navigation")
    page = st.radio("Go to", ["Dashboard", "Chat", "Explorer"])

if page == "Dashboard":
    st.header("Dashboard")
    col1, col2, col3 = st.columns(3)
    col1.metric("Active Floats", "0")
    col2.metric("Total Profiles", "0")
    col3.metric("Data Coverage", "0%")

elif page == "Chat":
    st.header("AI Chat")
    st.chat_input("Ask about ocean data...")

elif page == "Explorer":
    st.header("Data Explorer")
    st.info("Coming soon...")
EOF

# Run Streamlit
poetry run streamlit run app.py
```

### Step 7: Verify Installation

```bash
# Check Docker services
docker-compose ps

# Test PostgreSQL
docker exec floatchat-postgres psql -U floatchat -d floatchat -c "SELECT version();"

# Test Redis
docker exec floatchat-redis redis-cli ping

# Test Ollama
curl http://localhost:11434/api/tags

# Test API
curl http://localhost:8000/health

# Access Streamlit
# Open browser: http://localhost:8501
```

---

## 📚 Learning Resources

### Frontend
- **Next.js**: https://nextjs.org/docs
- **React**: https://react.dev
- **Tailwind CSS**: https://tailwindcss.com/docs
- **Three.js**: https://threejs.org/docs
- **D3.js**: https://d3js.org

### Backend
- **FastAPI**: https://fastapi.tiangolo.com
- **SQLAlchemy**: https://docs.sqlalchemy.org
- **PostgreSQL**: https://www.postgresql.org/docs
- **TimescaleDB**: https://docs.timescale.com

### AI/ML
- **Ollama**: https://ollama.com/docs
- **LangChain**: https://python.langchain.com
- **Qdrant**: https://qdrant.tech/documentation
- **HuggingFace**: https://huggingface.co/docs

### Data Science
- **Pandas**: https://pandas.pydata.org/docs
- **NumPy**: https://numpy.org/doc
- **NetCDF4**: https://unidata.github.io/netcdf4-python
- **GeoPandas**: https://geopandas.org

### DevOps
- **Docker**: https://docs.docker.com
- **Kubernetes**: https://kubernetes.io/docs
- **Terraform**: https://www.terraform.io/docs

---

## 🎯 Next Steps

1. **Complete Database Schema** - Implement all tables
2. **Build Data Ingestion** - Fetch and parse ARGO data
3. **Implement LLM Service** - Natural language to SQL
4. **Create Visualizations** - Maps, charts, 3D views
5. **Build Chat Interface** - Interactive AI assistant
6. **Add Authentication** - User management
7. **Deploy to Cloud** - Oracle Cloud free tier

---

## 💡 Development Tips

### Performance
- Use database indices strategically
- Implement caching (Redis) for frequent queries
- Lazy load components in React
- Use React Server Components for static content
- Optimize images (WebP, AVIF)

### Security
- Never commit secrets to Git
- Use environment variables
- Implement rate limiting
- Validate all inputs
- Use parameterized SQL queries

### Code Quality
- Write tests (pytest, Jest)
- Use type hints (Python) and TypeScript
- Follow linting rules (ESLint, Ruff)
- Document your code
- Use meaningful variable names

### Debugging
- Use browser DevTools
- Check Docker logs: `docker-compose logs -f`
- Use debugger (pdb, VS Code debugger)
- Monitor database queries
- Profile performance bottlenecks

---

## 🆘 Common Issues

### Docker Issues
```bash
# Reset Docker environment
docker-compose down -v
docker-compose up -d

# Check logs
docker-compose logs -f postgres
```

### Database Connection Issues
```bash
# Check PostgreSQL is running
docker exec floatchat-postgres pg_isready

# Reset password
docker exec -it floatchat-postgres psql -U postgres -c "ALTER USER floatchat PASSWORD 'dev_password';"
```

### Ollama Model Issues
```bash
# List models
docker exec floatchat-ollama ollama list

# Re-pull model
docker exec floatchat-ollama ollama pull mistral:7b-instruct
```

---

This guide provides everything you need to get started with FloatChat Ultimate! 🚀
