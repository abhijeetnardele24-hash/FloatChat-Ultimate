"""Groq engine for fast, free LLM inference with Llama and Mixtral models."""

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
    return lowered.startswith("gsk_") and len(lowered) < 40


class GroqQueryEngine:
    """Groq engine for fast LLM inference with oceanographic specialization."""

    def __init__(self):
        api_key = (os.getenv("GROQ_API_KEY") or "").strip()
        if not api_key or _is_placeholder_key(api_key):
            raise ValueError(
                "GROQ_API_KEY is missing. Get your free API key from https://console.groq.com/keys"
            )

        # Use the best available model for oceanographic analysis
        self.model_name = (os.getenv("GROQ_MODEL") or "llama-3.1-70b-versatile").strip()
        self.base_url = "https://api.groq.com/openai/v1"
        self.timeout_seconds = float(os.getenv("GROQ_TIMEOUT_SECONDS", "25"))
        
        self.client = OpenAI(
            api_key=api_key,
            base_url=self.base_url,
            timeout=self.timeout_seconds
        )
        
        logger.info("Groq engine initialized with model: %s", self.model_name)

    def answer_general_question(self, question: str, context: Optional[str] = None) -> str:
        system_prompt = (
            "You are an expert oceanographer and marine scientist specializing in ARGO float data, "
            "oceanographic analysis, and marine ecosystem research. Provide scientifically accurate, "
            "detailed responses with proper context and citations when possible. "
            "\n\nFor oceanographic queries:\n"
            "- Explain underlying physical principles\n"
            "- Consider temperature, salinity, depth profiles, and currents\n"
            "- Reference relevant oceanographic phenomena\n"
            "- Provide data interpretation methods\n"
            "\nWhen analyzing ARGO float data:\n"
            "- Interpret temperature and salinity profiles\n"
            "- Explain ocean circulation patterns\n"
            "- Discuss climate implications\n"
            "- Suggest further analysis approaches"
        )

        user_prompt = question.strip()
        if context:
            user_prompt = (
                "Using the oceanographic data context below, provide comprehensive analysis:\n\n"
                f"Context:\n{context}\n\n"
                f"Question: {question.strip()}\n\n"
                "Please analyze this data with scientific rigor and explain the implications."
            )

        response = self.client.chat.completions.create(
            model=self.model_name,
            temperature=0.3,  # Balanced for scientific accuracy
            max_tokens=1000,  # Detailed responses
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        
        text = (response.choices[0].message.content or "").strip()
        if not text:
            raise RuntimeError("Groq returned an empty response.")
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
                "source": "groq_llama70b",
                "model": self.model_name,
                "confidence": "high",
                "inference_speed": "fast"
            }
        except Exception as exc:
            logger.error("Groq query failed: %s", exc)
            return {
                "success": False,
                "response": f"Groq error: {exc}",
                "error": str(exc),
                "source": "groq",
            }

    def health_check(self) -> Dict:
        return {
            "available": True,
            "status": "healthy",
            "model": self.model_name,
            "timeout_seconds": self.timeout_seconds,
            "base_url": self.base_url,
            "provider": "Groq",
            "capabilities": [
                "Fast inference",
                "Oceanographic analysis",
                "Scientific reasoning",
                "Data interpretation"
            ],
            "speed": "Very Fast (~300 tokens/s)"
        }

    def get_model_info(self) -> Dict:
        return {
            "name": self.model_name,
            "parameters": "70B",
            "provider": "Meta (via Groq)",
            "strengths": [
                "Extremely fast inference",
                "Scientific analysis",
                "Data interpretation",
                "Technical explanations"
            ],
            "ideal_for": [
                "Real-time oceanographic analysis",
                "ARGO float data interpretation",
                "Climate pattern analysis",
                "Marine research assistance"
            ],
            "pricing": "Free tier available"
        }
