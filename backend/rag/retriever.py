"""RAG retriever with Qdrant + embedding support and lexical fallback."""

from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

from .default_corpus import get_default_corpus

try:
    from qdrant_client import QdrantClient
except Exception:
    QdrantClient = None

try:
    from sentence_transformers import SentenceTransformer
except Exception:
    SentenceTransformer = None

logger = logging.getLogger(__name__)


@dataclass
class RAGDocument:
    title: str
    source: str
    content: str
    score: float


def _tokenize(text: str) -> List[str]:
    return re.findall(r"[a-z0-9]+", (text or "").lower())


def _keyword_overlap_score(query_tokens: Sequence[str], doc_tokens: Sequence[str]) -> float:
    q = set(query_tokens)
    d = set(doc_tokens)
    if not q:
        return 0.0
    return len(q & d) / max(len(q), 1)


class OceanRAGRetriever:
    """Retrieves supporting ocean-study snippets for general chat answers."""

    def __init__(self):
        self.enabled = os.getenv("RAG_ENABLED", "true").strip().lower() in {"1", "true", "yes", "on"}
        self.qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333").strip()
        self.collection_name = os.getenv("QDRANT_COLLECTION", "ocean_knowledge").strip() or "ocean_knowledge"
        self.embedding_model_name = (
            os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2").strip()
        )
        self.min_vector_score = float(os.getenv("RAG_MIN_VECTOR_SCORE", "0.15"))

        self._default_docs = get_default_corpus()
        self._qdrant: Optional[QdrantClient] = None
        self._embedder = None
        self._vector_ready = False

        if not self.enabled:
            logger.info("RAG is disabled by env (RAG_ENABLED=false).")
            return

        if QdrantClient is None or SentenceTransformer is None:
            logger.info("Qdrant or sentence-transformers not available; using lexical RAG fallback.")
            return

        try:
            self._qdrant = QdrantClient(url=self.qdrant_url, timeout=2.0)
            self._vector_ready = self._has_vector_collection()
            if self._vector_ready:
                self._embedder = SentenceTransformer(self.embedding_model_name)
                logger.info("RAG vector retrieval enabled (collection=%s).", self.collection_name)
            else:
                logger.info("RAG collection not ready; using lexical fallback until ingestion runs.")
        except Exception as exc:
            logger.warning("Failed to initialize vector RAG stack: %s", exc)
            self._qdrant = None
            self._embedder = None
            self._vector_ready = False

    def _has_vector_collection(self) -> bool:
        if not self._qdrant:
            return False
        try:
            collections = self._qdrant.get_collections()
            names = {c.name for c in collections.collections}
            if self.collection_name not in names:
                return False
            count = self._qdrant.count(collection_name=self.collection_name, exact=False)
            return bool(getattr(count, "count", 0))
        except Exception:
            return False

    @property
    def available(self) -> bool:
        return self.enabled and (self._vector_ready or bool(self._default_docs))

    @property
    def mode(self) -> str:
        if not self.enabled:
            return "disabled"
        if self._vector_ready:
            return "vector"
        return "lexical"

    def retrieve(self, query: str, top_k: int = 4) -> List[RAGDocument]:
        if not self.enabled or not query.strip():
            return []
        if self._vector_ready:
            docs = self._retrieve_vector(query=query, top_k=top_k)
            if docs:
                return docs
        return self._retrieve_lexical(query=query, top_k=top_k)

    def _retrieve_vector(self, query: str, top_k: int) -> List[RAGDocument]:
        if not self._qdrant:
            return []
        if self._embedder is None:
            try:
                self._embedder = SentenceTransformer(self.embedding_model_name)
            except Exception as exc:
                logger.warning("Could not initialize embedder for vector retrieval: %s", exc)
                return []
        try:
            vector = self._embedder.encode(query).tolist()
            hits = self._qdrant.search(
                collection_name=self.collection_name,
                query_vector=vector,
                limit=top_k,
                with_payload=True,
            )
            docs: List[RAGDocument] = []
            for hit in hits:
                score = float(getattr(hit, "score", 0.0))
                if score < self.min_vector_score:
                    continue
                payload = getattr(hit, "payload", {}) or {}
                content = (
                    str(payload.get("content", ""))
                    or str(payload.get("chunk", ""))
                    or str(payload.get("text", ""))
                )
                if not content:
                    continue
                docs.append(
                    RAGDocument(
                        title=str(payload.get("title", "Ocean Reference")),
                        source=str(payload.get("source", "local-corpus")),
                        content=content.strip(),
                        score=score,
                    )
                )
            return docs
        except Exception as exc:
            logger.warning("Vector retrieval failed, falling back to lexical: %s", exc)
            return []

    def _retrieve_lexical(self, query: str, top_k: int) -> List[RAGDocument]:
        q_tokens = _tokenize(query)
        if not q_tokens:
            return []
        scored: List[Tuple[float, Dict[str, str]]] = []
        for doc in self._default_docs:
            score = _keyword_overlap_score(q_tokens, _tokenize(doc["content"]))
            if score <= 0:
                continue
            scored.append((score, doc))
        scored.sort(key=lambda item: item[0], reverse=True)
        top = scored[:top_k]
        return [
            RAGDocument(
                title=doc["title"],
                source=doc["source"],
                content=doc["content"],
                score=score,
            )
            for score, doc in top
        ]

    @staticmethod
    def format_context(documents: Sequence[RAGDocument], max_chars: int = 2500) -> str:
        if not documents:
            return ""
        sections: List[str] = []
        used = 0
        for idx, doc in enumerate(documents, start=1):
            chunk = f"[{idx}] {doc.title}\nSource: {doc.source}\n{doc.content.strip()}\n"
            if used + len(chunk) > max_chars:
                break
            sections.append(chunk)
            used += len(chunk)
        return "\n".join(sections).strip()

    @staticmethod
    def to_sources(documents: Sequence[RAGDocument]) -> List[Dict[str, str]]:
        sources: List[Dict[str, str]] = []
        for doc in documents:
            sources.append(
                {
                    "title": doc.title,
                    "source": doc.source,
                    "snippet": doc.content[:240].strip(),
                }
            )
        return sources
