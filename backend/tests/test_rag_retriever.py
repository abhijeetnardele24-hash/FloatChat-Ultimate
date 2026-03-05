from __future__ import annotations

from rag import retriever as retriever_module


def test_lexical_rag_fallback_returns_sources(monkeypatch):
    monkeypatch.setattr(retriever_module, "QdrantClient", None)
    monkeypatch.setattr(retriever_module, "SentenceTransformer", None)
    monkeypatch.setenv("RAG_ENABLED", "true")

    retriever = retriever_module.OceanRAGRetriever()
    docs = retriever.retrieve("What is salinity and density?", top_k=3)

    assert docs
    context = retriever.format_context(docs)
    sources = retriever.to_sources(docs)

    assert "salinity" in context.lower() or "density" in context.lower()
    assert len(sources) >= 1
    assert {"title", "source", "snippet"}.issubset(sources[0].keys())

