 FloatChat Ultimate - Tech Stack & Project Architecture

This document outlines the entire technology stack used in the FloatChat project, explaining what each technology is, why we chose it, and what role it plays. It also provides a comprehensive file-by-file breakdown of the project architecture.

---

## 🎨 1. Frontend Technology Stack (Web Interface)

The frontend is built for performance, aesthetics, and rich user interaction.

### **Next.js (v16)**
- **What it is:** A React framework for building web applications with Server-Side Rendering (SSR) and Static Site Generation (SSG).
- **Why it's useful:** It provides out-of-the-box routing (App Router), performance optimizations, and SEO capabilities.
- **Role in the project:** Acts as the foundation for the entire frontend application, handling routing for the dashboard, chat, map explorer, and visualizations.

### **React (v19)**
- **What it is:** A JavaScript library for building user interfaces using reusable components.
- **Why it's useful:** Enables writing modular, maintainable, and reactive code.
- **Role in the project:** Renders the elements on the screen, manages state (e.g., chat history, map coordinates), and handles user interactions.

### **Tailwind CSS & Tailwind Animate**
- **What it is:** A utility-first CSS framework.
- **Why it's useful:** Allows rapid styling directly within components without switching out to separate CSS files, ensuring a highly customized, premium UI without bloat.
- **Role in the project:** Styles everything from the layout, colors, typography, buttons, and responsive design for mobile screens.

### **Radix UI components (Dialog, Dropdown, Select, Tabs, etc.)**
- **What it is:** Unstyled, highly accessible UI primitives for React.
- **Why it's useful:** Gives us a robust foundation for complex interactive elements (like modals and dropdowns) that are fully accessible and keyboard-friendly, which we then style beautifully with Tailwind.
- **Role in the project:** Powers the underlying logic of our interactive UI elements (Shadcn UI approach).

### **Framer Motion**
- **What it is:** A production-ready animation library for React.
- **Why it's useful:** Makes it easy to implement smooth, physics-based micro-animations and page transitions.
- **Role in the project:** Adds the "wow" factor with smooth entrances, satisfying button clicks, and dynamic data presentation.

### **Chart.js & Recharts**
- **What it is:** Robust JavaScript data visualization libraries.
- **Why it's useful:** They can handle plotting large amounts of numerical data efficiently.
- **Role in the project:** Responsible for rendering the scientific ocean plots (temperature profiles, salinity charts) in the visualization and study modules.

### **TypeScript**
- **What it is:** A strongly typed superset of JavaScript.
- **Why it's useful:** Prevents runtime bugs by enforcing data types during development.
- **Role in the project:** Ensures the frontend correctly handles the complex JSON payloads returned by the backend data APIs.

---

## ⚙️ 2. Backend Technology Stack (API & Data Processing)

The backend is built for high-performance data crunching, AI intelligence, and scientific data ingestion.

### **FastAPI & Uvicorn**
- **What it is:** A modern, fast web framework for building APIs with Python (FastAPI). Uvicorn is the lightning-fast ASGI web server that runs it.
- **Why it's useful:** Incredibly fast and automatically generates interactive API documentation.
- **Role in the project:** Serves as the central API gateway. It handles all incoming requests from the Next.js frontend, coordinates data fetching, and streams AI responses back.

### **SQLAlchemy & PostgreSQL (via psycopg2)**
- **What it is:** SQLAlchemy is a Python Object Relational Mapper (ORM), and PostgreSQL is a robust relational database.
- **Why it's useful:** Allows us to interact with a powerful relational database using Python objects instead of raw SQL strings.
- **Role in the project:** Stores structured application data like User Profiles, Chat Histories, and application settings.

### **Large Language Models (Ollama, Gemini, OpenAI, Groq, Sambanova)**
- **What it is:** Different AI providers and local engines for generating human-like text.
- **Why it's useful:** They provide the conversational intelligence required for user interaction.
- **Role in the project:** The core brain of the Chatbot. Depending on configuration, the system routes the user’s query to the active LLM engine.

### **Qdrant & Sentence-Transformers (RAG Stack)**
- **What it is:** Qdrant is an Open-Source Vector Search Engine. Sentence-Transformers is a library to convert text into mathematical "embeddings" (vectors).
- **Why it's useful:** Large language models don't know the specifics of our ocean data. RAG (Retrieval-Augmented Generation) allows us to inject our own documentation context into the AI prompts.
- **Role in the project:** Powers the "knowledge base." It loads oceanography concepts, searches for the most relevant context, and feeds it to the AI for accurate, non-hallucinated answers.

### **Science Data Stack: Pandas, NumPy, Xarray, NetCDF4, Dask**
- **What it is:** Python libraries designed for heavy numerical computing and reading scientific file formats (.nc).
- **Why it's useful:** Oceanographic data (like from the Argo program) is distributed in massive multi-dimensional files (NetCDF). Standard tools cannot process them efficiently.
- **Role in the project:** Parses raw ocean float data, performs statistical calculations, handles missing values, and processes multi-dimensional grid data.

### **GSW (Gibbs SeaWater Oceanographic Package)**
- **What it is:** An implementation of the Thermodynamic Equation of Seawater – 2010 (TEOS-10).
- **Why it's useful:** Specifically built for ocean science calculations.
- **Role in the project:** Calculates absolute salinity, conservative temperature, and water density from raw sensor pressure, temperature, and conductivity measurements to provide scientifically accurate analysis.

### **Redis**
- **What it is:** An in-memory data structure store.
- **Why it's useful:** Extremely fast read/write speeds.
- **Role in the project:** Acts as a caching layer to avoid querying expensive external APIs (NOAA, CMEMS) repeatedly, and handles application rate limiting.

---

## 📂 3. File & Directory Breakdown

Here is a detailed breakdown of what each major file and folder does in the workspace.

### **Root Directory (Configuration)**
- `package.json` / `package-lock.json`: Lists all frontend dependencies and npm scripts (`dev`, `build`).
- `tailwind.config.ts`: Configuration rules for the styling framework (colors, fonts, custom animations).
- `next.config.ts`: Configurations for the Next.js framework (image domains, redirects, strict mode).
- `tsconfig.json`: TypeScript compiler rules.
- `.gitignore`: Files that Git shouldn't track (e.g., node_modules, .env secrets, python cache).
- `docker-compose.yml`: Script to easily run complex services (like PostgreSQL or Qdrant) in isolated Docker containers.

### **`/app` (Frontend Pages & Routing)**
Next.js uses folder-based routing. Every folder with a `page.tsx` represents a URL route.
- `app/layout.tsx`: The main HTML wrapper. Contains the navbar/sidebar that persists across all pages.
- `app/page.tsx`: The landing page `/`.
- `app/chat/page.tsx`: The AI Chatbot interface page `/chat`.
- `app/dashboard/page.tsx`: User stats and unified dashboard `/dashboard`.
- `app/explorer/page.tsx`: Interactive Map interface for ocean floats `/explorer`.
- `app/study/page.tsx`: Educational material layout `/study`.
- `app/tools/page.tsx`: Scientific tools & calculators `/tools`.
- `app/visualizations/page.tsx`: Rich charts for presenting backend data `/visualizations`.

### **`/components` (Frontend UI Modules)**
Reusable React components.
- `components/Brand.tsx`: The logo and branding UI.
- `components/charts/DataCharts.tsx`: Wrappers for Recharts to display ocean temperature/salinity profiles.
- `components/chat/ChatInterface.tsx`: The core logic and UI for the message bubble view.
- `components/map/FloatMap.tsx`: The map component (likely utilizing Leaflet or Mapbox) plotting Argo float coordinates.
- `components/ui/*`: Various primitive Radix UI components constructed nicely.

### **`/lib` (Frontend Utilities)**
- `lib/api-client.ts`: The bridge between Frontend and Backend. Contains functions to `GET`/`POST` data to the Python FastAPI server.
- `lib/utils.ts`: Generic helper functions (e.g., classname merging for Tailwind).

### **`/backend` (The API Server)**
Contains the entirety of the Python application.
- `backend/main.py`: The root of the Python server. This starts FastAPI, connects routers, and opens the port for the frontend.
- `backend/requirements.txt`: List of Python packages to install mapped to exact versions.

#### **`/backend/core` (Backend Infrastructure)**
- `core/db.py`: Establishes the connection to the PostgreSQL database using SQLAlchemy.
- `core/security.py`: Logic for JWT Tokens, password hashing, and protecting routes so only logged-in users access them.
- `core/middleware.py`: Captures incoming requests globally for logging or modifying headers.

#### **`/backend/routers` (The API Endpoints)**
These files define the URL paths (e.g., `/api/cmems`) the frontend calls to fetch data. Grouped by data source:
- `routers/auth.py`: Login, Registration, and Token generation logic.
- `routers/noaa.py`, `routers/obis.py`, `routers/cmems.py`, `routers/ooi.py`, etc.: Each file is responsible for speaking to a specific external oceanographic API, transforming their raw data, and sending it back to our frontend as clean JSON.
- `routers/argovis.py`: Logic specifically for querying the Argovis platform for Argo float telemetry.
- `routers/chat.py` / `routers/study.py`: Endpoints for submitting chat queries or educational checks.

#### **`/backend/llm` (AI Integrations)**
- `llm/chat_service.py`: Central manager that receives a user text prompt and decides what context to fetch before sending it to the AI.
- `llm/openai_engine.py`, `llm/gemini_engine.py`, `llm/ollama_engine.py`, etc.: The specific implementations on how to format HTTP requests securely to each distinct AI provider API.

#### **`/backend/rag` (Knowledge Base Search)**
- `rag/retriever.py`: Searches the Qdrant Vector database for sentences similar to what the user just asked.
- `rag/ingest_corpus.py`: Administration script to read markdown files and pump them into the Vector database as embeddings.
- `rag/corpus/*`: Static Markdown articles about oceanography used to train the system's context.

#### **`/backend/data_ingestion`**
- `data_ingestion/argo_ingestion.py`: Scripts meant for downloading huge `.nc` (NetCDF) Argo profile files from public FTP servers and extracting the raw arrays using `xarray` and `numpy`.

#### **`/backend/tests`**
- `test_*.py` files run automated checks via `pytest` to ensure APIs respond correctly and don't break when new code is pushed.

### **`/docs` (Documentation)**
- Contains guides that explain how to run things (`RUNNING_LOCALLY.md`), lists of environment keys needed (`FREE_API_KEYS_SETUP.md`), to-do lists (`ENTERPRISE_TODO.md`), and the architecture visual diagrams.
