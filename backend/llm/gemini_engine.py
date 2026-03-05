"""
Google Gemini Query Engine
Handles general ocean knowledge questions using Gemini API
"""

import os
import logging
from typing import Dict, Optional, Any
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError

import google.generativeai as genai
from sqlalchemy import text

from core.db import build_engine, build_session_local, get_database_url
logger = logging.getLogger(__name__)

DEFAULT_MODEL_CANDIDATES = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-flash-latest",
]

def _get_gemini_text(response) -> Optional[str]:
    """Safely extract text from Gemini response (handles blocked/empty)."""
    if response is None:
        return None
    try:
        if hasattr(response, "text") and response.text:
            return response.text.strip()
    except (ValueError, Exception):
        pass
    try:
        if response.candidates:
            for c in response.candidates:
                if c.content and c.content.parts:
                    for p in c.content.parts:
                        if hasattr(p, "text") and p.text:
                            return p.text.strip()
    except (AttributeError, IndexError, Exception):
        pass
    return None


class GeminiQueryEngine:
    """
    Gemini-powered query engine for general ocean knowledge
    """
    _last_working_model: Optional[str] = None
    
    def __init__(self):
        # Support both GOOGLE_API_KEY and GEMINI_API_KEY
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key or api_key.startswith("your-") or api_key == "your-google-gemini-api-key-here":
            raise ValueError(
                "Gemini API key not set. Set GOOGLE_API_KEY or GEMINI_API_KEY in .env with your key from https://aistudio.google.com/apikey"
            )
        
        genai.configure(api_key=api_key)
        self.timeout_seconds = float(os.getenv("GEMINI_TIMEOUT_SECONDS", "12"))
        self._executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="gemini-engine")
        
        # Prefer user-configured model, but keep fallback candidates for runtime retries.
        _env_model = (os.getenv("GEMINI_MODEL") or "gemini-2.5-flash").strip()
        if _env_model.startswith("models/"):
            _env_model = _env_model.replace("models/", "")
        self.model_name = _env_model or "gemini-2.5-flash"
        base_candidates = [self.model_name] + [
            m for m in DEFAULT_MODEL_CANDIDATES if m != self.model_name
        ]
        preferred_model = GeminiQueryEngine._last_working_model
        if preferred_model:
            ordered = [preferred_model] + base_candidates
            seen = set()
            self.model_candidates = [m for m in ordered if not (m in seen or seen.add(m))]
        else:
            self.model_candidates = base_candidates
        self.model_name = self.model_candidates[0]
        self.model = genai.GenerativeModel(self.model_name)
        
        logger.info(f"Gemini engine initialized with model: {self.model_name}")

    def _generate_content(self, prompt: str, generation_config: Any):
        future = self._executor.submit(
            self.model.generate_content,
            prompt,
            generation_config=generation_config,
        )
        try:
            return future.result(timeout=self.timeout_seconds)
        except FutureTimeoutError as exc:
            future.cancel()
            raise TimeoutError(
                f"Gemini generation timed out after {self.timeout_seconds:.1f}s"
            ) from exc

    def _switch_model(self, model_name: str) -> None:
        """Switch to a different Gemini model and persist for subsequent calls."""
        if model_name == self.model_name:
            return
        self.model = genai.GenerativeModel(model_name)
        self.model_name = model_name
        logger.warning(f"Switched Gemini model to fallback: {model_name}")

    def _generate_content_with_fallback(self, prompt: str, generation_config: Any):
        """
        Generate content with model fallback.
        Retries with alternate models on not-found or quota/rate-limit errors.
        """
        last_error = None
        for idx, model_name in enumerate(self.model_candidates):
            if idx > 0:
                self._switch_model(model_name)
            try:
                response = self._generate_content(prompt, generation_config)
                GeminiQueryEngine._last_working_model = model_name
                return response
            except Exception as e:
                last_error = e
                msg = str(e).lower()
                recoverable = (
                    "not found" in msg
                    or "quota" in msg
                    or "rate limit" in msg
                    or "resource_exhausted" in msg
                    or "429" in msg
                    or "timed out" in msg
                )
                if recoverable and idx < len(self.model_candidates) - 1:
                    logger.warning(
                        f"Gemini model '{model_name}' failed ({e}); trying next fallback model."
                    )
                    continue
                raise
        if last_error:
            raise last_error
        raise RuntimeError("Gemini generation failed without a captured error.")
    
    def generate_sql(self, user_query: str, schema_context: str) -> Optional[str]:
        """
        Generate SQL query using Gemini
        
        Args:
            user_query: Natural language question
            schema_context: Database schema information
            
        Returns:
            SQL query string or None if generation fails
        """
        prompt = f"""You are an expert SQL generator for oceanographic ARGO float data.

Database Schema:
{schema_context}

User Question: {user_query}

Generate a PostgreSQL query to answer this question. 
Rules:
- Return ONLY the SQL query, no explanation
- Use proper JOIN syntax
- Include LIMIT clause for safety
- Use parameterized queries where possible
- Handle NULL values appropriately

SQL Query:"""
        
        try:
            response = self._generate_content_with_fallback(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.1,
                    top_p=0.8,
                    top_k=40,
                    max_output_tokens=320,
                ),
            )
            
            sql_query = _get_gemini_text(response)
            if not sql_query:
                logger.warning("Gemini returned empty or blocked SQL response")
                return None
            
            # Clean up the response (remove markdown code blocks if present)
            if sql_query.startswith('```sql'):
                sql_query = sql_query.replace('```sql', '').replace('```', '').strip()
            elif sql_query.startswith('```'):
                sql_query = sql_query.replace('```', '').strip()
            
            logger.info(f"Generated SQL: {sql_query[:100]}...")
            return sql_query
            
        except Exception as e:
            logger.error(f"Gemini SQL generation failed: {e}")
            return None
    
    def answer_general_question(self, question: str, context: str = None) -> str:
        """
        Answer general ocean science questions using Gemini
        
        Args:
            question: User's question
            context: Optional context from RAG or database
            
        Returns:
            Natural language answer
        """
        system_instruction = """You are an expert oceanographer and marine scientist with deep knowledge of:
- Physical oceanography (currents, temperature, salinity, density)
- ARGO float technology and data collection
- Ocean circulation patterns
- Marine ecosystems and biology
- Climate and ocean interactions
- Oceanographic measurement techniques

Provide accurate, educational answers that are:
- Scientifically rigorous but accessible
- Concise (2-3 paragraphs maximum)
- Include relevant examples when helpful
- Cite scientific principles when appropriate

If the question is about ARGO data specifically, mention that the user can query the database for specific measurements."""

        if context:
            system_instruction += f"\n\nRelevant context from database:\n{context}"
        
        prompt = f"{system_instruction}\n\nQuestion: {question}\n\nAnswer:"
        
        try:
            response = self._generate_content_with_fallback(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.7,
                    top_p=0.9,
                    top_k=40,
                    max_output_tokens=520,
                ),
            )
            
            answer = _get_gemini_text(response)
            if not answer:
                return "I couldn't generate a response for that. Please try rephrasing or ask about ocean data."
            logger.info(f"Generated answer: {answer[:100]}...")
            return answer
            
        except Exception as e:
            logger.error(f"Gemini answer generation failed: {e}")
            return f"I apologize, but I encountered an error generating a response: {str(e)}"
    
    def _is_general_question(self, text: str) -> bool:
        """Quick heuristic: question is likely general (no DB needed)."""
        t = text.lower().strip()
        if not t:
            return True
        starters = ("what is", "what are", "who is", "explain", "tell me about", "tell me what", "why ", "how does", "define ")
        return any(t.startswith(s) for s in starters) or t.startswith("what is ") or "?" in t and len(t) < 80

    def query(self, user_message: str) -> Dict:
        """
        Main query method compatible with existing chat interface.
        For clearly general questions, answers with Gemini only (no SQL/DB).
        """
        # Fast path: general questions -> answer directly (no DB, no SQL)
        if self._is_general_question(user_message):
            try:
                answer = self.answer_general_question(user_message)
                return {
                    "success": True,
                    "response": answer,
                    "sql_query": None,
                    "data": [],
                    "row_count": 0,
                    "source": "gemini_general"
                }
            except Exception as e:
                logger.error(f"Gemini general answer failed: {e}")
                return {
                    "success": False,
                    "response": f"Gemini couldn't answer that. Error: {str(e)}. Check your GOOGLE_API_KEY in backend .env and try again.",
                    "error": str(e),
                    "source": "gemini"
                }

        # Data-style query: try SQL path (needs DB)
        try:
            engine = build_engine(get_database_url())
            SessionLocal = build_session_local(engine)
            schema_context = self._get_schema_context()
            sql_query = self.generate_sql(user_message, schema_context)

            if not sql_query:
                answer = self.answer_general_question(user_message)
                return {
                    "success": True,
                    "response": answer,
                    "sql_query": None,
                    "data": [],
                    "row_count": 0,
                    "source": "gemini_general"
                }

            db = SessionLocal()
            try:
                result = db.execute(text(sql_query))
                rows = result.fetchall()
                data = []
                if rows:
                    columns = result.keys()
                    for row in rows:
                        data.append(dict(zip(columns, row)))
                if data:
                    answer = self.answer_general_question(
                        f"Summarize these ARGO data results for the user's question: '{user_message}'",
                        context=str(data[:5])
                    )
                else:
                    answer = "I executed the query but found no matching results. Try adjusting your search criteria."
                return {
                    "success": True,
                    "response": answer,
                    "sql_query": sql_query,
                    "data": data[:10],
                    "row_count": len(data),
                    "source": "gemini_sql"
                }
            except Exception as e:
                logger.error(f"SQL execution failed: {e}")
                answer = self.answer_general_question(user_message)
                return {
                    "success": False,
                    "response": answer,
                    "sql_query": sql_query,
                    "error": str(e),
                    "source": "gemini_fallback"
                }
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Gemini query failed: {e}")
            try:
                answer = self.answer_general_question(user_message)
                return {
                    "success": True,
                    "response": answer,
                    "sql_query": None,
                    "data": [],
                    "row_count": 0,
                    "source": "gemini_general"
                }
            except Exception as e2:
                logger.error(f"Gemini fallback answer also failed: {e2}")
            return {
                "success": False,
                "response": f"Gemini error: {str(e)}. Check GOOGLE_API_KEY in backend .env and that the key is valid at https://aistudio.google.com/apikey",
                "error": str(e),
                "source": "gemini"
            }
    
    def _get_schema_context(self) -> str:
        """Get database schema information for SQL generation"""
        return """
Database Tables:

1. argo_floats
   - id (SERIAL PRIMARY KEY)
   - wmo_number (VARCHAR, UNIQUE)
   - platform_type (VARCHAR)
   - deployment_date (TIMESTAMP)
   - last_latitude (DOUBLE PRECISION)
   - last_longitude (DOUBLE PRECISION)
   - last_location_date (TIMESTAMP)
   - status (VARCHAR) - 'ACTIVE' or 'INACTIVE'
   - ocean_basin (VARCHAR)
   - location (GEOGRAPHY)

2. argo_profiles
   - id (SERIAL PRIMARY KEY)
   - float_id (INTEGER, FK to argo_floats)
   - wmo_number (VARCHAR)
   - cycle_number (INTEGER)
   - profile_date (TIMESTAMP)
   - latitude (DOUBLE PRECISION)
   - longitude (DOUBLE PRECISION)
   - data_mode (CHAR) - 'R', 'A', or 'D'
   - location (GEOGRAPHY)

3. argo_measurements
   - id (BIGSERIAL PRIMARY KEY)
   - profile_id (INTEGER, FK to argo_profiles)
   - pressure (DOUBLE PRECISION)
   - depth (DOUBLE PRECISION)
   - temperature (DOUBLE PRECISION)
   - temperature_qc (INTEGER)
   - salinity (DOUBLE PRECISION)
   - salinity_qc (INTEGER)

Common Queries:
- Count floats: SELECT COUNT(*) FROM argo_floats
- Active floats: SELECT * FROM argo_floats WHERE status = 'ACTIVE'
- Recent profiles: SELECT * FROM argo_profiles ORDER BY profile_date DESC LIMIT 10
- Temperature data: SELECT * FROM argo_measurements WHERE temperature IS NOT NULL
"""

    def health_check(self) -> Dict:
        return {
            "available": True,
            "status": "healthy",
            "model": self.model_name,
            "candidate_models": self.model_candidates,
            "timeout_seconds": self.timeout_seconds,
        }
