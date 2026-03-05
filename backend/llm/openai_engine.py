"""OpenAI query engine for general ocean-study answers."""

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
    # Only reject obvious placeholders, not real keys
    obvious_placeholders = ["sk-your-openai", "your-openai", "sk-example", "sk-test"]
    return any(placeholder in lowered for placeholder in obvious_placeholders)


class OpenAIQueryEngine:
    """OpenAI-backed engine for conceptual and method-focused questions."""

    def __init__(self):
        api_key = (os.getenv("OPENAI_API_KEY") or "").strip()
        if not api_key or _is_placeholder_key(api_key):
            raise ValueError(
                "OPENAI_API_KEY is missing. For optional OpenAI support, set a valid key in backend/.env."
            )

        self.model_name = (os.getenv("OPENAI_MODEL") or "gpt-4o-mini").strip() or "gpt-4o-mini"
        base_url = (os.getenv("OPENAI_BASE_URL") or "").strip() or None
        self.timeout_seconds = float(os.getenv("OPENAI_TIMEOUT_SECONDS", "12"))
        self.client = OpenAI(api_key=api_key, base_url=base_url, timeout=self.timeout_seconds)
        self.base_url = base_url
        logger.info("OpenAI engine initialized with model: %s", self.model_name)

    def answer_general_question(self, question: str, context: Optional[str] = None) -> str:
        system_prompt = (
            "You are an expert oceanographer. Provide scientifically accurate, concise responses. "
            "For explanatory answers, stay under 3 short paragraphs. "
            "If context snippets are provided, ground the answer in those snippets and avoid fabricating sources."
        )

        user_prompt = question.strip()
        if context:
            user_prompt = (
                "Use the context below when relevant.\n\n"
                f"Context:\n{context}\n\n"
                f"Question: {question.strip()}"
            )

        response = self.client.chat.completions.create(
            model=self.model_name,
            temperature=0.3,
            max_tokens=700,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        text = (response.choices[0].message.content or "").strip()
        if not text:
            raise RuntimeError("OpenAI returned an empty response.")
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
                "source": "openai_general",
            }
        except Exception as exc:
            logger.error("OpenAI query failed: %s", exc)
            return {
                "success": False,
                "response": f"OpenAI error: {exc}",
                "error": str(exc),
                "source": "openai",
            }

    def health_check(self) -> Dict:
        return {
            "available": True,
            "status": "healthy",
            "model": self.model_name,
            "timeout_seconds": self.timeout_seconds,
            "base_url": self.base_url or "default",
        }
