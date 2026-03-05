"""
Hybrid Chat Service
Routes queries across Ollama, OpenAI, and Gemini with optional RAG context.
"""

from __future__ import annotations

import copy
import logging
import os
import time
from collections import OrderedDict
from threading import Lock
from typing import Any, Dict, List, Literal, Optional, Sequence, Tuple

from sqlalchemy import text

from core.db import build_engine, build_session_local, get_database_url

logger = logging.getLogger(__name__)
SupportedProvider = Literal["ollama", "openai", "gemini", "sambanova", "groq", "auto"]


class HybridChatService:
    """Unified chat orchestration across local and cloud providers."""

    def __init__(self, ollama_engine=None, openai_engine=None, gemini_engine=None, sambanova_engine=None, groq_engine=None, rag_retriever=None):
        self.ollama = ollama_engine if ollama_engine is not None else self._init_ollama()
        self.openai = openai_engine if openai_engine is not None else self._init_openai()
        self.gemini = gemini_engine if gemini_engine is not None else self._init_gemini()
        self.sambanova = sambanova_engine if sambanova_engine is not None else self._init_sambanova()
        self.groq = groq_engine if groq_engine is not None else self._init_groq()
        self.rag = rag_retriever if rag_retriever is not None else self._init_rag()
        self.cache_ttl_seconds = max(0, int(os.getenv("CHAT_CACHE_TTL_SECONDS", "45")))
        self.cache_max_items = max(10, int(os.getenv("CHAT_CACHE_MAX_ITEMS", "256")))
        self._cache: OrderedDict[str, Tuple[float, Dict]] = OrderedDict()
        self._cache_lock = Lock()
        self.dataset_context_ttl_seconds = max(0, int(os.getenv("CHAT_DATASET_CONTEXT_TTL_SECONDS", "60")))
        self._dataset_context_lock = Lock()
        self._dataset_context_value = ""
        self._dataset_context_expires_at = 0.0
        self._db_session_factory = self._init_dataset_session_factory()
        self.data_provider_order = self._parse_provider_order(
            os.getenv("CHAT_DATA_PROVIDER_ORDER", "groq,gemini,openai,ollama,sambanova"),
            default_order=["groq", "gemini", "openai", "ollama", "sambanova"],
        )
        self.general_provider_order = self._parse_provider_order(
            os.getenv("CHAT_GENERAL_PROVIDER_ORDER", "groq,gemini,openai,ollama,sambanova"),
            default_order=["groq", "gemini", "openai", "ollama", "sambanova"],
        )

        if not self.ollama and not self.openai and not self.gemini and not self.groq:
            raise RuntimeError(
                "No LLM engines available. Configure Ollama locally or set OPENAI_API_KEY / GOOGLE_API_KEY / GROQ_API_KEY."
            )

    def _init_ollama(self):
        try:
            from .ollama_engine import OllamaQueryEngine

            engine = OllamaQueryEngine()
            logger.info("Ollama engine initialized")
            return engine
        except Exception as exc:
            logger.warning("Ollama engine unavailable: %s", exc)
            return None

    def _init_openai(self):
        try:
            from .openai_engine import OpenAIQueryEngine

            engine = OpenAIQueryEngine()
            logger.info("OpenAI engine initialized")
            return engine
        except Exception as exc:
            logger.warning("OpenAI engine unavailable: %s", exc)
            return None

    def _init_gemini(self):
        try:
            from .gemini_engine import GeminiQueryEngine

            engine = GeminiQueryEngine()
            logger.info("Gemini engine initialized")
            return engine
        except Exception as exc:
            logger.warning("Gemini engine unavailable: %s", exc)
            return None

    def _init_sambanova(self):
        try:
            from .sambanova_engine import SambaNovaQueryEngine

            engine = SambaNovaQueryEngine()
            logger.info("SambaNova Llama 405B engine initialized")
            return engine
        except Exception as exc:
            logger.warning("SambaNova engine unavailable: %s", exc)
            return None

    def _init_groq(self):
        try:
            from .groq_engine import GroqQueryEngine

            engine = GroqQueryEngine()
            logger.info("Groq Llama 70B engine initialized")
            return engine
        except Exception as exc:
            logger.warning("Groq engine unavailable: %s", exc)
            return None

    def _init_rag(self):
        try:
            from rag.retriever import OceanRAGRetriever

            rag = OceanRAGRetriever()
            if rag.available:
                logger.info("RAG retriever ready in %s mode", rag.mode)
            return rag
        except Exception as exc:
            logger.warning("RAG retriever unavailable: %s", exc)
            return None

    def _init_dataset_session_factory(self):
        try:
            engine = build_engine(get_database_url())
            return build_session_local(engine)
        except Exception as exc:
            logger.warning("Dataset context DB session unavailable: %s", exc)
            return None

    @staticmethod
    def _parse_provider_order(value: str, default_order: List[str]) -> List[str]:
        allowed = {"ollama", "openai", "gemini", "sambanova", "groq"}
        candidates = [v.strip().lower() for v in value.split(",") if v.strip()]
        parsed: List[str] = []
        for candidate in candidates:
            if candidate in allowed and candidate not in parsed:
                parsed.append(candidate)
        if parsed:
            return parsed
        return default_order

    def classify_query(self, query: str) -> Literal["data", "general"]:
        """Classify whether a query should use database-first or explanation-first flow."""
        query_lower = query.lower()

        data_keywords = [
            "float",
            "floats",
            "wmo",
            "profile",
            "profiles",
            "temperature",
            "salinity",
            "pressure",
            "depth",
            "measurement",
            "measurements",
            "dataset",
            "how many",
            "count",
            "show me",
            "list",
            "find",
            "search",
            "latest",
            "active",
            "inactive",
            "latitude",
            "longitude",
            "ocean basin",
            "cycle",
            "deployment",
        ]

        general_keywords = [
            "what is",
            "what are",
            "how does",
            "why does",
            "explain",
            "definition",
            "meaning",
            "concept",
            "theory",
            "principle",
            "mechanism",
            "climate",
            "ecosystem",
            "circulation",
            "current",
            "difference between",
            "when should",
            "best practice",
        ]

        data_score = sum(1 for kw in data_keywords if kw in query_lower)
        general_score = sum(1 for kw in general_keywords if kw in query_lower)

        if data_score > general_score:
            return "data"
        if general_score > 0:
            return "general"
        return "data"

    def infer_intent(self, query: str, query_type: str) -> Tuple[str, float]:
        query_lower = query.lower().strip()
        if not query_lower:
            return "general_explanation", 0.5
        if query_type == "general" and (
            query_lower.startswith("what is")
            or query_lower.startswith("what are")
            or query_lower.startswith("explain")
            or query_lower.startswith("why")
            or query_lower.startswith("how does")
        ):
            return "general_explanation", 0.88

        intent_rules: List[Tuple[str, List[str]]] = [
            ("data_compare", ["compare", "difference", "vs", "versus"]),
            ("data_export", ["export", "download", "csv", "netcdf", "snapshot"]),
            ("anomaly_detection", ["anomaly", "outlier", "unusual", "deviation"]),
            ("forecast", ["forecast", "predict", "projection", "future"]),
            ("study_workflow", ["workspace", "note", "timeline", "saved query", "study"]),
            ("data_lookup", ["how many", "count", "list", "show", "find", "latest", "temperature", "salinity"]),
            ("general_explanation", ["what is", "explain", "why", "how does", "define"]),
        ]

        best_label = "general_explanation" if query_type == "general" else "data_lookup"
        best_score = 0
        for label, keywords in intent_rules:
            score = sum(1 for kw in keywords if kw in query_lower)
            if score > best_score:
                best_score = score
                best_label = label
        confidence = min(0.99, 0.55 + 0.12 * best_score)
        if best_score == 0:
            confidence = 0.6 if query_type == "general" else 0.65
        return best_label, round(confidence, 3)

    def _build_reliability_payload(
        self,
        query_type: str,
        rag_sources: List[Dict[str, str]],
        row_count: int,
        provider_metrics: List[Dict[str, Any]],
        fallback_used: bool,
    ) -> Dict[str, Any]:
        warnings: List[str] = []
        failed_attempts = sum(1 for metric in provider_metrics if not metric.get("success"))
        if failed_attempts > 0:
            warnings.append("One or more provider attempts failed before final response.")
        if fallback_used:
            warnings.append("Fallback provider was used after primary provider failed or was unavailable.")
        if query_type == "general" and not rag_sources:
            warnings.append("No external retrieval sources were attached for this explanation.")
        if query_type == "data" and row_count == 0:
            warnings.append("No matching dataset rows were returned for this request.")

        source_signal = min(0.25, len(rag_sources) * 0.07)
        data_signal = 0.32 if query_type == "data" and row_count > 0 else 0.12
        penalty = min(0.25, failed_attempts * 0.06)
        evidence_score = round(max(0.0, min(0.99, 0.48 + source_signal + data_signal - penalty)), 3)
        evidence_coverage_score = round(max(0.0, min(0.99, 0.42 + source_signal - penalty)), 3)

        if query_type == "data":
            method = "Executed structured SQL retrieval on ARGO tables and summarized returned rows."
            data_source = ["argo_floats", "argo_profiles", "argo_measurements"]
            limitations = [
                "Coverage depends on currently ingested profiles and applied filters.",
                "Returned counts can change as new data ingestion jobs complete.",
            ]
            next_checks = [
                "Run compare/timeline study endpoints to validate regional trends.",
                "Export snapshot for reproducibility before sharing findings.",
            ]
        else:
            method = "Generated explanation with LLM synthesis using retrieved ocean references and dataset context."
            data_source = [source.get("title", "source") for source in rag_sources] or ["llm_general_knowledge"]
            limitations = [
                "Narrative quality depends on retrieval coverage and provider behavior.",
                "Use direct data queries for numeric validation before publication.",
            ]
            next_checks = [
                "Ask a follow-up data query to verify specific numbers.",
                "Review linked sources and compare with domain references.",
            ]

        return {
            "evidence_score": evidence_score,
            "evidence_coverage_score": evidence_coverage_score,
            "reliability_warnings": warnings,
            "method": method,
            "data_source": data_source,
            "limitations": limitations,
            "next_checks": next_checks,
        }

    def _provider_order(self, query_type: str, provider: str) -> List[Tuple[str, object]]:
        providers = {
            "groq": self.groq,
            "gemini": self.gemini,
            "openai": self.openai,
            "ollama": self.ollama,
        }

        if provider == "auto":
            order = self.data_provider_order if query_type == "data" else self.general_provider_order
        elif provider == "groq":
            order = ["groq", "gemini", "openai", "ollama"]
        elif provider == "gemini":
            order = ["gemini", "groq", "openai", "ollama"]
        elif provider == "openai":
            order = ["openai", "groq", "gemini", "ollama"]
        else:  # ollama
            order = ["ollama", "groq", "gemini", "openai"]

        return [(name, providers[name]) for name in order if providers.get(name) is not None]

    def _get_rag_context(self, query: str) -> Tuple[str, List[Dict[str, str]]]:
        if not self.rag or not getattr(self.rag, "available", False):
            return "", []
        try:
            documents = self.rag.retrieve(query, top_k=4)
            if not documents:
                return "", []
            context = self.rag.format_context(documents)
            sources = self.rag.to_sources(documents)
            return context, sources
        except Exception as exc:
            logger.warning("RAG retrieval failed: %s", exc)
            return "", []

    def _cache_key(self, query: str, provider: str, query_type: str) -> str:
        normalized_query = " ".join(query.lower().split())
        return f"{provider}|{query_type}|{normalized_query}"

    def _cache_get(self, key: str) -> Optional[Dict]:
        if self.cache_ttl_seconds <= 0:
            return None
        now = time.monotonic()
        with self._cache_lock:
            item = self._cache.get(key)
            if not item:
                return None
            expires_at, cached_payload = item
            if now >= expires_at:
                self._cache.pop(key, None)
                return None
            self._cache.move_to_end(key)
            payload = copy.deepcopy(cached_payload)
            payload["cached"] = True
            return payload

    def _cache_set(self, key: str, payload: Dict) -> None:
        if self.cache_ttl_seconds <= 0:
            return
        cached_payload = copy.deepcopy(payload)
        cached_payload["cached"] = False
        expires_at = time.monotonic() + self.cache_ttl_seconds
        with self._cache_lock:
            self._cache[key] = (expires_at, cached_payload)
            self._cache.move_to_end(key)
            while len(self._cache) > self.cache_max_items:
                self._cache.popitem(last=False)

    def _get_dataset_context(self) -> str:
        if not self._db_session_factory:
            return ""
        now = time.monotonic()
        with self._dataset_context_lock:
            if self._dataset_context_value and now < self._dataset_context_expires_at:
                return self._dataset_context_value

        session = self._db_session_factory()
        try:
            total_floats = int(session.execute(text("SELECT COUNT(*) FROM argo_floats")).scalar() or 0)
            total_profiles = int(session.execute(text("SELECT COUNT(*) FROM argo_profiles")).scalar() or 0)
            total_measurements = int(session.execute(text("SELECT COUNT(*) FROM argo_measurements")).scalar() or 0)
            latest_profile = session.execute(text("SELECT MAX(profile_date) FROM argo_profiles")).scalar()
            basin_rows = session.execute(
                text(
                    """
                    SELECT ocean_basin, COUNT(*) AS count
                    FROM argo_floats
                    WHERE ocean_basin IS NOT NULL
                    GROUP BY ocean_basin
                    ORDER BY count DESC
                    LIMIT 3
                    """
                )
            ).fetchall()
            basin_summary = ", ".join([f"{row[0]} ({row[1]})" for row in basin_rows]) if basin_rows else "Unknown"
            latest_profile_text = latest_profile.isoformat() if hasattr(latest_profile, "isoformat") else str(latest_profile or "N/A")
            summary = (
                "Live ARGO dataset snapshot: "
                f"floats={total_floats}, profiles={total_profiles}, measurements={total_measurements}, "
                f"latest_profile={latest_profile_text}, top_basins={basin_summary}."
            )
        except Exception as exc:
            logger.warning("Failed building dataset context: %s", exc)
            return ""
        finally:
            session.close()

        with self._dataset_context_lock:
            self._dataset_context_value = summary
            self._dataset_context_expires_at = time.monotonic() + self.dataset_context_ttl_seconds
        return summary

    def _run_engine(self, engine, query: str, query_type: str, context: str) -> Dict:
        if query_type == "general":
            if hasattr(engine, "answer_general_question"):
                answer = engine.answer_general_question(query, context=context if context else None)
                return {
                    "success": True,
                    "response": answer,
                    "sql_query": None,
                    "data": [],
                    "row_count": 0,
                }
            try:
                return engine.query(query, context=context if context else None)
            except TypeError:
                return engine.query(query)
        return engine.query(query)

    def process_query(self, query: str, provider: Optional[SupportedProvider] = "auto") -> Dict:
        """
        Main entry point for chat processing.

        Args:
            query: User prompt.
            provider: "auto", "groq", "gemini", "openai", or "ollama".
        """
        query_type = self.classify_query(query)
        intent, intent_confidence = self.infer_intent(query=query, query_type=query_type)
        provider = (provider or "auto").strip().lower()
        if provider not in {"groq", "gemini", "openai", "ollama", "auto"}:
            logger.warning("Unsupported provider '%s'. Falling back to auto.", provider)
            provider = "auto"

        logger.info("Query classified as '%s' (provider=%s)", query_type, provider)
        cache_key = self._cache_key(query, provider, query_type)
        cached_result = self._cache_get(cache_key)
        if cached_result is not None:
            return cached_result

        rag_context = ""
        rag_sources: List[Dict[str, str]] = []
        if query_type == "general":
            rag_context, rag_sources = self._get_rag_context(query)
            dataset_context = self._get_dataset_context()
            if dataset_context:
                rag_context = f"{dataset_context}\n\n{rag_context}".strip()
                rag_sources.append(
                    {
                        "title": "ARGO Dataset Snapshot",
                        "source": "database://floatchat",
                        "snippet": dataset_context[:240],
                    }
                )

        ordered_engines = self._provider_order(query_type=query_type, provider=provider)
        provider_metrics: List[Dict[str, Any]] = []
        if not ordered_engines:
            reliability = self._build_reliability_payload(
                query_type=query_type,
                rag_sources=rag_sources,
                row_count=0,
                provider_metrics=provider_metrics,
                fallback_used=False,
            )
            return {
                "success": False,
                "response": "No providers are available. Configure Ollama, OpenAI, or Gemini in backend/.env.",
                "error": "No providers available",
                "source": "none",
                "query_type": query_type,
                "intent": intent,
                "intent_confidence": intent_confidence,
                "confidence": 0.0,
                "provider_metrics": provider_metrics,
                "sources": rag_sources,
                **reliability,
            }

        last_error: Optional[str] = None
        for index, (engine_name, engine) in enumerate(ordered_engines):
            started = time.perf_counter()
            try:
                result = self._run_engine(engine=engine, query=query, query_type=query_type, context=rag_context)
                elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
                provider_metrics.append(
                    {
                        "provider": engine_name,
                        "latency_ms": elapsed_ms,
                        "success": bool(result.get("success")),
                    }
                )
                if result.get("success"):
                    source = engine_name if index == 0 else f"{engine_name}_fallback"
                    row_count = int(result.get("row_count") or 0)
                    source_bonus = 0.08 if rag_sources else 0.0
                    data_bonus = 0.06 if query_type == "data" and row_count > 0 else 0.0
                    confidence = round(min(0.99, 0.68 + source_bonus + data_bonus), 3)
                    reliability = self._build_reliability_payload(
                        query_type=query_type,
                        rag_sources=rag_sources,
                        row_count=row_count,
                        provider_metrics=provider_metrics,
                        fallback_used=index > 0,
                    )
                    successful_result = {
                        **result,
                        "source": source,
                        "query_type": query_type,
                        "intent": intent,
                        "intent_confidence": intent_confidence,
                        "confidence": confidence,
                        "provider_metrics": provider_metrics,
                        "sources": rag_sources,
                        "cached": False,
                        **reliability,
                    }
                    self._cache_set(cache_key, successful_result)
                    return successful_result
                last_error = result.get("error") or "Unknown failure"
                logger.warning("Provider %s returned unsuccessful result: %s", engine_name, last_error)
            except Exception as exc:
                last_error = str(exc)
                elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
                provider_metrics.append(
                    {
                        "provider": engine_name,
                        "latency_ms": elapsed_ms,
                        "success": False,
                        "error": str(exc),
                    }
                )
                logger.error("Provider %s raised error: %s", engine_name, exc)

        reliability = self._build_reliability_payload(
            query_type=query_type,
            rag_sources=rag_sources,
            row_count=0,
            provider_metrics=provider_metrics,
            fallback_used=False,
        )
        return {
            "success": False,
            "response": (
                f"Could not generate a response. {last_error or 'All providers failed.'} "
                "Check backend logs and provider env keys (OPENAI_API_KEY, GOOGLE_API_KEY) or Ollama status."
            ),
            "error": last_error or "All providers failed",
            "source": "none",
            "query_type": query_type,
            "intent": intent,
            "intent_confidence": intent_confidence,
            "confidence": 0.0,
            "provider_metrics": provider_metrics,
            "sources": rag_sources,
            "cached": False,
            **reliability,
        }

    def get_available_providers(self) -> List[str]:
        providers: List[str] = []
        if self.ollama:
            providers.append("ollama")
        if self.openai:
            providers.append("openai")
        if self.gemini:
            providers.append("gemini")
        return providers

    def _engine_health(self, name: str, engine) -> Dict:
        if not engine:
            return {"available": False, "status": "unavailable"}
        if hasattr(engine, "health_check"):
            try:
                details = engine.health_check()
                if isinstance(details, dict):
                    details.setdefault("available", True)
                    details.setdefault("status", "healthy")
                    return details
            except Exception as exc:
                logger.warning("Health check failed for %s: %s", name, exc)
                return {"available": False, "status": "error", "error": str(exc)}
        return {"available": True, "status": "healthy"}

    def health_check(self) -> Dict:
        rag_available = bool(self.rag and getattr(self.rag, "available", False))
        rag_mode = self.rag.mode if self.rag else "disabled"
        return {
            "ollama": self._engine_health("ollama", self.ollama),
            "openai": self._engine_health("openai", self.openai),
            "gemini": self._engine_health("gemini", self.gemini),
            "rag": {
                "available": rag_available,
                "status": rag_mode,
            },
            "cache": {
                "enabled": self.cache_ttl_seconds > 0,
                "ttl_seconds": self.cache_ttl_seconds,
                "entries": len(self._cache),
            },
            "routing": {
                "data_provider_order": self.data_provider_order,
                "general_provider_order": self.general_provider_order,
            },
        }
