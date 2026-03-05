"""
Ollama LLM Integration for Natural Language to SQL
Converts user queries into SQL and executes them against the ARGO database
"""

import os
import logging
import time
from typing import Dict, Optional, List

import requests
from sqlalchemy import text

from core.db import build_engine, build_session_local, get_database_url, load_backend_env

load_backend_env()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = get_database_url()
engine = build_engine(DATABASE_URL)
SessionLocal = build_session_local(engine)

# Ollama configuration
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_CONNECT_TIMEOUT_SECONDS = float(os.getenv("OLLAMA_CONNECT_TIMEOUT_SECONDS", "2.0"))
OLLAMA_READ_TIMEOUT_SECONDS = float(os.getenv("OLLAMA_READ_TIMEOUT_SECONDS", "20.0"))
OLLAMA_SQL_NUM_PREDICT = int(os.getenv("OLLAMA_SQL_NUM_PREDICT", "180"))
OLLAMA_GENERAL_NUM_PREDICT = int(os.getenv("OLLAMA_GENERAL_NUM_PREDICT", "360"))

# Database schema context for LLM
DATABASE_SCHEMA = """
Database Schema:

1. argo_floats table:
   - id (integer, primary key)
   - wmo_number (varchar, unique identifier for each float)
   - platform_type (varchar, e.g., 'APEX', 'ARVOR')
   - deployment_date (timestamp)
   - last_location_date (timestamp)
   - last_latitude (double precision)
   - last_longitude (double precision)
   - status (varchar, e.g., 'ACTIVE', 'INACTIVE')
   - ocean_basin (varchar, e.g., 'Indian Ocean')

2. argo_profiles table:
   - id (integer, primary key)
   - float_id (integer, foreign key to argo_floats)
   - wmo_number (varchar)
   - cycle_number (integer)
   - profile_date (timestamp)
   - latitude (double precision)
   - longitude (double precision)
   - data_mode (char)

3. argo_measurements table:
   - id (bigint, primary key)
   - profile_id (integer, foreign key to argo_profiles)
   - pressure (double precision, in decibars)
   - depth (double precision, in meters)
   - temperature (double precision, in Celsius)
   - salinity (double precision, in PSU)
   - temperature_qc (integer, quality control flag)
   - salinity_qc (integer, quality control flag)

Geographic bounds for Indian Ocean:
- Latitude: -40 to 30
- Longitude: 30 to 120
"""

class OllamaQueryEngine:
    """Natural language to SQL query engine using Ollama"""
    
    def __init__(self, model: str = OLLAMA_MODEL):
        self.model = model
        self.session_factory = SessionLocal
        self.base_url = OLLAMA_BASE_URL.rstrip("/")
        self.connect_timeout = OLLAMA_CONNECT_TIMEOUT_SECONDS
        self.read_timeout = OLLAMA_READ_TIMEOUT_SECONDS
        self.available_models: List[str] = []
        self.last_health_latency_ms: Optional[float] = None

        # Fast-fail when Ollama is unreachable so provider health is accurate.
        try:
            self._refresh_models()
        except Exception as e:
            raise RuntimeError(f"Ollama connection failed at {OLLAMA_BASE_URL}: {e}")

    def _refresh_models(self) -> None:
        start = time.perf_counter()
        tags_url = f"{self.base_url}/api/tags"
        response = requests.get(tags_url, timeout=(self.connect_timeout, self.read_timeout))
        response.raise_for_status()
        elapsed_ms = (time.perf_counter() - start) * 1000
        payload = response.json() if response.content else {}
        models = payload.get("models", []) if isinstance(payload, dict) else []
        names: List[str] = []
        for item in models:
            name = (item.get("name") or "").strip() if isinstance(item, dict) else ""
            if name:
                # Ollama sometimes returns model tags (e.g., mistral:latest).
                names.append(name.split(":")[0])
        unique_names = list(dict.fromkeys(names))
        self.available_models = unique_names
        self.last_health_latency_ms = round(elapsed_ms, 2)
        if self.available_models and self.model not in self.available_models:
            fallback = self.available_models[0]
            logger.warning(
                "Configured Ollama model '%s' not found; falling back to '%s'.",
                self.model,
                fallback,
            )
            self.model = fallback

    def _generate_text(self, prompt: str, options: Dict) -> str:
        response = requests.post(
            f"{self.base_url}/api/generate",
            json={"model": self.model, "prompt": prompt, "options": options, "stream": False},
            timeout=(self.connect_timeout, self.read_timeout),
        )
        response.raise_for_status()
        payload = response.json() if response.content else {}
        if not isinstance(payload, dict):
            raise RuntimeError("Unexpected Ollama response payload")
        text_response = (payload.get("response") or "").strip()
        if not text_response:
            raise RuntimeError("Ollama returned an empty response")
        return text_response
    
    def generate_sql(self, user_query: str) -> Optional[str]:
        """Convert natural language query to SQL using Ollama"""
        
        prompt = f"""You are an expert SQL query generator for an oceanographic database containing ARGO float data.

{DATABASE_SCHEMA}

User Question: {user_query}

Generate a PostgreSQL SQL query to answer this question. Follow these rules:
1. Return ONLY the SQL query, no explanations
2. Use proper PostgreSQL syntax
3. Include appropriate JOINs when needed
4. Limit results to 100 rows unless specified
5. Use meaningful column aliases
6. Handle NULL values appropriately
7. For temperature queries, remember values are in Celsius
8. For location queries, use latitude and longitude columns

SQL Query:"""

        try:
            logger.info(f"Generating SQL for query: {user_query}")
            sql_query = self._generate_text(
                prompt,
                options={
                    "temperature": 0.1,
                    "top_p": 0.9,
                    "num_predict": OLLAMA_SQL_NUM_PREDICT,
                },
            )
            
            # Clean up the SQL query
            sql_query = sql_query.replace('```sql', '').replace('```', '').strip()
            
            # Remove any trailing semicolons (SQLAlchemy adds them)
            sql_query = sql_query.rstrip(';')
            
            logger.info(f"Generated SQL: {sql_query}")
            return sql_query
            
        except Exception as e:
            logger.error(f"Error generating SQL: {e}")
            return None
    
    def execute_sql(self, sql_query: str) -> Dict:
        """Execute SQL query and return results"""
        try:
            # Security check: only allow SELECT queries
            if not sql_query.strip().upper().startswith('SELECT'):
                return {
                    "success": False,
                    "error": "Only SELECT queries are allowed for security reasons"
                }
            
            with self.session_factory() as session:
                result = session.execute(text(sql_query))
                rows = result.fetchall()
                columns = result.keys()
            
            # Convert to list of dictionaries
            data = []
            for row in rows:
                data.append(dict(zip(columns, row)))
            
            return {
                "success": True,
                "data": data,
                "row_count": len(data),
                "columns": list(columns)
            }
            
        except Exception as e:
            logger.error(f"Error executing SQL: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def generate_natural_response(self, user_query: str, sql_result: Dict) -> str:
        """Generate a natural language response from SQL results"""
        
        if not sql_result.get("success"):
            return f"I encountered an error: {sql_result.get('error')}"
        
        data = sql_result.get("data", [])
        row_count = sql_result.get("row_count", 0)
        
        if row_count == 0:
            return "I couldn't find any data matching your query."
        
        # Create a summary of the results
        summary_prompt = f"""Based on the following data, provide a concise natural language answer to the user's question.

User Question: {user_query}

Data (showing first 5 rows):
{data[:5]}

Total rows: {row_count}

Provide a clear, concise answer in 2-3 sentences:"""

        try:
            return self._generate_text(
                summary_prompt,
                options={
                    "temperature": 0.4,
                    "top_p": 0.9,
                    "num_predict": max(120, OLLAMA_SQL_NUM_PREDICT),
                },
            )
            
        except Exception as e:
            logger.error(f"Error generating natural response: {e}")
            return f"I found {row_count} results. Here's a sample: {data[0] if data else 'No data'}"

    def answer_general_question(self, question: str, context: Optional[str] = None) -> str:
        """Answer conceptual ocean questions directly (without SQL execution)."""
        prompt = (
            "You are an expert oceanographer. Respond in clear, simple language suitable for students and researchers. "
            "Keep answers concise (2-3 short paragraphs), scientifically accurate, and practical."
        )
        if context:
            prompt += f"\n\nUse this context when relevant:\n{context.strip()}\n"
        prompt += f"\nQuestion: {question.strip()}\nAnswer:"

        try:
            answer = self._generate_text(
                prompt,
                options={
                    "temperature": 0.35,
                    "top_p": 0.9,
                    "num_predict": OLLAMA_GENERAL_NUM_PREDICT,
                },
            )
            if not answer:
                raise RuntimeError("Ollama returned empty response for general question")
            return answer
        except Exception as e:
            logger.error(f"Error generating general response: {e}")
            return "I couldn't generate a clear conceptual response. Please rephrase your question."

    def query(self, user_query: str, context: Optional[str] = None) -> Dict:
        """Complete query pipeline: NL -> SQL -> Execute -> NL Response"""

        # Generate SQL
        sql_query = self.generate_sql(user_query)
        if not sql_query:
            fallback_text = self.answer_general_question(user_query, context=context)
            return {
                "success": True,
                "error": None,
                "sql_query": None,
                "data": [],
                "row_count": 0,
                "response": fallback_text,
            }
        
        # Execute SQL
        sql_result = self.execute_sql(sql_query)
        
        # Generate natural language response
        nl_response = self.generate_natural_response(user_query, sql_result)
        
        return {
            "success": sql_result.get("success", False),
            "sql_query": sql_query,
            "data": sql_result.get("data", []),
            "row_count": sql_result.get("row_count", 0),
            "response": nl_response,
            "error": sql_result.get("error")
        }

    def health_check(self) -> Dict:
        try:
            self._refresh_models()
            return {
                "available": True,
                "status": "healthy",
                "model": self.model,
                "available_models": self.available_models,
                "base_url": self.base_url,
                "latency_ms": self.last_health_latency_ms,
                "timeouts": {
                    "connect_seconds": self.connect_timeout,
                    "read_seconds": self.read_timeout,
                },
            }
        except Exception as exc:
            return {
                "available": False,
                "status": "error",
                "model": self.model,
                "base_url": self.base_url,
                "error": str(exc),
            }

# Example usage
if __name__ == "__main__":
    engine = OllamaQueryEngine()
    
    # Test queries
    test_queries = [
        "How many active ARGO floats are in the Indian Ocean?",
        "Show me the latest temperature measurements",
        "What is the average salinity at 100 meters depth?",
        "List all floats deployed in 2020"
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print(f"{'='*60}")
        
        result = engine.query(query)
        
        print(f"SQL: {result.get('sql_query')}")
        print(f"Response: {result.get('response')}")
        print(f"Rows: {result.get('row_count')}")
