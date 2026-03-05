"""SambaNova Cloud Llama 405B engine for advanced oceanographic analysis."""

from __future__ import annotations

import logging
import os
from typing import Dict, Optional

from dotenv import load_dotenv
from openai import OpenAI

logger = logging.getLogger(__name__)

# Load environment variables from backend/.env when present
_env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
load_dotenv(_env_path)
load_dotenv()


def _is_placeholder_key(value: str) -> bool:
    lowered = value.lower().strip()
    return lowered.startswith("sk-") and len(lowered) < 40


class SambaNovaQueryEngine:
    """SambaNova Cloud Llama 405B engine for advanced oceanographic analysis."""

    def __init__(self):
        api_key = (os.getenv("SAMBAVA_API_KEY") or "").strip()
        if not api_key or _is_placeholder_key(api_key):
            raise ValueError(
                "SAMBAVA_API_KEY is missing. Get your free API key from https://cloud.sambanova.ai/apis"
            )

        self.model_name = (os.getenv("SAMBAVA_MODEL") or "Meta-Llama-3.1-405B-Instruct").strip()
        self.base_url = "https://api.sambanova.ai/v1"
        self.timeout_seconds = float(os.getenv("SAMBAVA_TIMEOUT_SECONDS", "30"))
        
        self.client = OpenAI(
            api_key=api_key,
            base_url=self.base_url,
            timeout=self.timeout_seconds
        )
        
        logger.info("SambaNova engine initialized with model: %s", self.model_name)

    def answer_general_question(self, question: str, context: Optional[str] = None) -> str:
        system_prompt = (
            "You are an expert oceanographer and marine scientist with deep knowledge of "
            "ARGO floats, oceanographic data analysis, climate patterns, and marine ecosystems. "
            "Provide scientifically accurate, detailed responses with proper context. "
            "For complex oceanographic questions, provide thorough explanations including "
            "underlying physical principles, data interpretation methods, and potential implications. "
            "When analyzing ARGO float data, consider temperature, salinity, depth profiles, "
            "and ocean currents. If context snippets are provided, ground your analysis in those "
            "specific data points and cite relevant oceanographic principles."
        )

        user_prompt = question.strip()
        if context:
            user_prompt = (
                "Using the oceanographic data context below, provide a comprehensive analysis:\n\n"
                f"Context:\n{context}\n\n"
                f"Question: {question.strip()}\n\n"
                "Please provide detailed analysis with scientific interpretation of the data."
            )

        response = self.client.chat.completions.create(
            model=self.model_name,
            temperature=0.2,  # Lower temperature for more scientific accuracy
            max_tokens=1200,   # Higher token limit for detailed responses
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        
        text = (response.choices[0].message.content or "").strip()
        if not text:
            raise RuntimeError("SambaNova returned an empty response.")
        return text

    def query(self, user_message: str, context: Optional[str] = None) -> Dict:
        try:
            answer = self.answer_general_question(user_message, context=context)
            return {
                "success": True,
                "response": answer,
                "sql_query": None,
                "data": [],
                "row_count": 0,
                "source": "sambanova_llama405b",
                "model": self.model_name,
                "confidence": "high"  # Llama 405B provides high confidence responses
            }
        except Exception as exc:
            logger.error("SambaNova query failed: %s", exc)
            return {
                "success": False,
                "response": f"SambaNova error: {exc}",
                "error": str(exc),
                "source": "sambanova",
            }

    def health_check(self) -> Dict:
        return {
            "available": True,
            "status": "healthy",
            "model": self.model_name,
            "timeout_seconds": self.timeout_seconds,
            "base_url": self.base_url,
            "provider": "SambaNova Cloud",
            "capabilities": [
                "Advanced oceanographic analysis",
                "Complex data interpretation",
                "Scientific reasoning",
                "Multi-modal understanding"
            ]
        }

    def get_model_info(self) -> Dict:
        return {
            "name": self.model_name,
            "parameters": "405B",
            "provider": "Meta (via SambaNova)",
            "strengths": [
                "Complex reasoning",
                "Scientific analysis",
                "Data interpretation",
                "Technical explanations"
            ],
            "ideal_for": [
                "ARGO float data analysis",
                "Oceanographic research",
                "Climate pattern analysis",
                "Marine ecosystem studies"
            ]
        }
