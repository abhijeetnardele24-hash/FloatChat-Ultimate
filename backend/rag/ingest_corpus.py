"""Ingest local ocean-study corpus into Qdrant for vector retrieval."""

from __future__ import annotations

import argparse
import json
import logging
import os
from pathlib import Path
from typing import Dict, Iterable, List

from dotenv import load_dotenv

from .default_corpus import get_default_corpus

try:
    from qdrant_client import QdrantClient
    from qdrant_client.http import models as qmodels
except Exception as exc:  # pragma: no cover
    raise RuntimeError(
        "qdrant-client is required for ingestion. Install backend requirements first."
    ) from exc

try:
    from sentence_transformers import SentenceTransformer
except Exception as exc:  # pragma: no cover
    raise RuntimeError(
        "sentence-transformers is required for ingestion. Install backend requirements first."
    ) from exc


logger = logging.getLogger(__name__)


def _chunk_text(text: str, max_chars: int = 900, overlap: int = 120) -> List[str]:
    if not text:
        return []
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    chunks: List[str] = []
    buffer = ""
    for para in paragraphs:
        if len(buffer) + len(para) + 1 <= max_chars:
            buffer = f"{buffer}\n{para}".strip()
            continue
        if buffer:
            chunks.append(buffer)
        if len(para) <= max_chars:
            buffer = para
            continue
        start = 0
        while start < len(para):
            end = min(start + max_chars, len(para))
            chunks.append(para[start:end])
            if end == len(para):
                break
            start = max(end - overlap, 0)
        buffer = ""
    if buffer:
        chunks.append(buffer)
    return chunks


def _load_json_docs(path: Path) -> List[Dict[str, str]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        payload = [payload]
    docs: List[Dict[str, str]] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title") or path.stem)
        source = str(item.get("source") or f"file://{path.name}")
        content = str(item.get("content") or item.get("text") or "")
        if content.strip():
            docs.append({"title": title, "source": source, "content": content})
    return docs


def load_corpus(corpus_dir: Path) -> List[Dict[str, str]]:
    docs: List[Dict[str, str]] = []
    if corpus_dir.exists():
        for path in sorted(corpus_dir.rglob("*")):
            if not path.is_file():
                continue
            suffix = path.suffix.lower()
            if suffix not in {".md", ".txt", ".json"}:
                continue
            if suffix == ".json":
                docs.extend(_load_json_docs(path))
                continue
            content = path.read_text(encoding="utf-8", errors="ignore")
            if not content.strip():
                continue
            docs.append(
                {
                    "title": path.stem.replace("_", " ").replace("-", " ").title(),
                    "source": f"file://{path.name}",
                    "content": content,
                }
            )
    if docs:
        return docs
    return get_default_corpus()


def build_points(docs: Iterable[Dict[str, str]], model: SentenceTransformer):
    points: List[qmodels.PointStruct] = []
    idx = 1
    for doc in docs:
        chunks = _chunk_text(doc["content"])
        if not chunks:
            continue
        vectors = model.encode(chunks)
        for chunk, vector in zip(chunks, vectors):
            points.append(
                qmodels.PointStruct(
                    id=idx,
                    vector=vector.tolist(),
                    payload={
                        "title": doc["title"],
                        "source": doc["source"],
                        "content": chunk,
                    },
                )
            )
            idx += 1
    return points


def ingest(
    qdrant_url: str,
    collection: str,
    embedding_model: str,
    corpus_dir: Path,
    recreate: bool,
):
    docs = load_corpus(corpus_dir)
    logger.info("Loaded %s corpus documents.", len(docs))

    model = SentenceTransformer(embedding_model)
    sample_vector = model.encode(["vector size probe"])[0]
    vector_size = len(sample_vector)

    client = QdrantClient(url=qdrant_url, timeout=30.0)
    exists = client.collection_exists(collection)

    if recreate and exists:
        logger.info("Recreating collection %s", collection)
        client.delete_collection(collection)
        exists = False

    if not exists:
        client.create_collection(
            collection_name=collection,
            vectors_config=qmodels.VectorParams(size=vector_size, distance=qmodels.Distance.COSINE),
        )

    points = build_points(docs, model=model)
    if not points:
        raise RuntimeError("No corpus chunks were created for ingestion.")

    client.upsert(collection_name=collection, points=points)
    logger.info("Upserted %s chunks into collection '%s'.", len(points), collection)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest ocean-study corpus into Qdrant")
    parser.add_argument(
        "--qdrant-url",
        default=os.getenv("QDRANT_URL", "http://localhost:6333"),
        help="Qdrant base URL",
    )
    parser.add_argument(
        "--collection",
        default=os.getenv("QDRANT_COLLECTION", "ocean_knowledge"),
        help="Qdrant collection name",
    )
    parser.add_argument(
        "--embedding-model",
        default=os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"),
        help="SentenceTransformer model name",
    )
    parser.add_argument(
        "--corpus-dir",
        default=str(Path(__file__).resolve().parent / "corpus"),
        help="Folder containing .md/.txt/.json corpus files",
    )
    parser.add_argument(
        "--recreate",
        action="store_true",
        help="Drop and recreate the collection before ingestion",
    )
    return parser.parse_args()


def main() -> int:
    load_dotenv()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    args = parse_args()
    ingest(
        qdrant_url=args.qdrant_url,
        collection=args.collection,
        embedding_model=args.embedding_model,
        corpus_dir=Path(args.corpus_dir),
        recreate=args.recreate,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

