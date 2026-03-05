from __future__ import annotations

from typing import Dict, List

from llm.chat_service import HybridChatService


class FakeOllamaEngine:
    def query(self, query: str) -> Dict:
        return {
            "success": True,
            "response": f"ollama handled: {query}",
            "sql_query": "SELECT 1",
            "data": [{"value": 1}],
            "row_count": 1,
        }


class FakeOllamaGeneralEngine(FakeOllamaEngine):
    def __init__(self):
        self.received_context = None

    def answer_general_question(self, question: str, context: str | None = None) -> str:
        self.received_context = context
        return f"ollama general handled: {question}"


class FakeOpenAIEngine:
    def __init__(self, should_fail: bool = False):
        self.should_fail = should_fail
        self.received_context = None
        self.calls = 0

    def answer_general_question(self, question: str, context: str | None = None) -> str:
        if self.should_fail:
            raise RuntimeError("openai unavailable")
        self.calls += 1
        self.received_context = context
        return f"openai handled: {question}"


class FakeGeminiEngine:
    def __init__(self):
        self.received_context = None
        self.calls = 0

    def answer_general_question(self, question: str, context: str | None = None) -> str:
        self.calls += 1
        self.received_context = context
        return f"gemini handled: {question}"


class FakeRAGRetriever:
    available = True
    mode = "lexical"

    def retrieve(self, query: str, top_k: int = 4):
        return [
            type(
                "Doc",
                (),
                {
                    "title": "Argo QC",
                    "source": "https://argo.example/qc",
                    "content": "QC flags help screen profile quality.",
                    "score": 0.8,
                },
            )()
        ]

    @staticmethod
    def format_context(documents) -> str:
        return "\n".join(f"{d.title}: {d.content}" for d in documents)

    @staticmethod
    def to_sources(documents) -> List[Dict[str, str]]:
        return [
            {"title": d.title, "source": d.source, "snippet": d.content}
            for d in documents
        ]


def test_auto_general_prefers_openai_and_includes_rag_sources(monkeypatch):
    monkeypatch.setenv("CHAT_GENERAL_PROVIDER_ORDER", "openai,gemini,ollama")
    openai = FakeOpenAIEngine()
    service = HybridChatService(
        ollama_engine=FakeOllamaEngine(),
        openai_engine=openai,
        gemini_engine=FakeGeminiEngine(),
        rag_retriever=FakeRAGRetriever(),
    )

    result = service.process_query("What is salinity?", provider="auto")

    assert result["success"] is True
    assert result["source"] == "openai"
    assert result["query_type"] == "general"
    assert result["intent"] == "general_explanation"
    assert result["intent_confidence"] >= 0.6
    assert result["provider_metrics"]
    assert result.get("sources")
    assert result["evidence_score"] > 0
    assert result["evidence_coverage_score"] > 0
    assert result["method"]
    assert result["data_source"]
    assert result["limitations"]
    assert result["next_checks"]
    assert openai.received_context is not None


def test_data_query_prefers_ollama_in_auto_mode():
    service = HybridChatService(
        ollama_engine=FakeOllamaEngine(),
        openai_engine=FakeOpenAIEngine(),
        gemini_engine=None,
        rag_retriever=FakeRAGRetriever(),
    )

    result = service.process_query("How many active floats are in the Indian Ocean?", provider="auto")

    assert result["success"] is True
    assert result["source"] == "ollama"
    assert result["query_type"] == "data"
    assert result["intent"] in {"data_lookup", "data_compare"}
    assert result["evidence_score"] > 0
    assert result["data_source"]
    assert result["provider_metrics"]


def test_openai_falls_back_when_requested_provider_fails():
    service = HybridChatService(
        ollama_engine=FakeOllamaEngine(),
        openai_engine=FakeOpenAIEngine(should_fail=True),
        gemini_engine=None,
        rag_retriever=FakeRAGRetriever(),
    )

    result = service.process_query("Explain thermohaline circulation", provider="openai")

    assert result["success"] is True
    assert result["source"] == "ollama_fallback"


def test_general_query_uses_ollama_general_path_when_ollama_only():
    ollama = FakeOllamaGeneralEngine()
    service = HybridChatService(
        ollama_engine=ollama,
        openai_engine=None,
        gemini_engine=None,
        rag_retriever=FakeRAGRetriever(),
    )

    result = service.process_query("Explain ocean salinity", provider="ollama")

    assert result["success"] is True
    assert result["source"] == "ollama"
    assert result["query_type"] == "general"
    assert result["sources"]
    assert ollama.received_context is not None


def test_general_query_cache_returns_cached_result_on_repeat():
    openai = FakeOpenAIEngine()
    service = HybridChatService(
        ollama_engine=FakeOllamaEngine(),
        openai_engine=openai,
        gemini_engine=None,
        rag_retriever=FakeRAGRetriever(),
    )

    first = service.process_query("What is density?", provider="openai")
    second = service.process_query("What is density?", provider="openai")

    assert first["success"] is True
    assert first["cached"] is False
    assert second["cached"] is True
    assert openai.calls == 1


def test_health_check_exposes_cache_metadata():
    service = HybridChatService(
        ollama_engine=FakeOllamaEngine(),
        openai_engine=FakeOpenAIEngine(),
        gemini_engine=None,
        rag_retriever=FakeRAGRetriever(),
    )

    health = service.health_check()

    assert health["cache"]["enabled"] is True
    assert health["cache"]["entries"] >= 0
    assert health["routing"]["general_provider_order"][0] in {"gemini", "openai", "ollama"}


def test_auto_general_prefers_gemini_when_available(monkeypatch):
    monkeypatch.setenv("CHAT_GENERAL_PROVIDER_ORDER", "gemini,openai,ollama")
    gemini = FakeGeminiEngine()
    openai = FakeOpenAIEngine()
    service = HybridChatService(
        ollama_engine=FakeOllamaEngine(),
        openai_engine=openai,
        gemini_engine=gemini,
        rag_retriever=FakeRAGRetriever(),
    )

    result = service.process_query("Explain ocean circulation", provider="auto")

    assert result["success"] is True
    assert result["source"] == "gemini"
    assert gemini.calls == 1
    assert openai.calls == 0
    assert result["sources"]
