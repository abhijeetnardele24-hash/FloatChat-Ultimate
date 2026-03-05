# RAG Ingestion Runbook

This runbook covers corpus ingestion for FloatChat RAG (Qdrant + embeddings) and fallback behavior.

## 1. Components

- Retriever runtime: `backend/rag/retriever.py`
- Default fallback corpus: `backend/rag/default_corpus.py`
- Local corpus files: `backend/rag/corpus/`
- Ingestion CLI: `backend/rag/ingest_corpus.py`

## 2. Prerequisites

- Qdrant reachable at `QDRANT_URL` (default `http://localhost:6333`)
- Backend dependencies installed (`qdrant-client`, `sentence-transformers`)
- Optional corpus files in `backend/rag/corpus/`

## 3. Ingestion Command

From project root:

```bash
cd backend
python -m rag.ingest_corpus --recreate
```

Optional flags:

- `--qdrant-url http://localhost:6333`
- `--collection ocean_knowledge`
- `--embedding-model sentence-transformers/all-MiniLM-L6-v2`
- `--corpus-dir backend/rag/corpus`

## 4. Verification

1. Check provider health endpoint:

```bash
curl http://localhost:8000/api/chat/providers
```

2. Confirm `health.rag.status`:
- `vector`: Qdrant retrieval active
- `lexical`: fallback mode (no vector collection or vector stack unavailable)
- `disabled`: `RAG_ENABLED=false`

3. Ask a conceptual chat question and verify `sources` field appears in response.

## 5. Operational Notes

- If ingestion is not run, the system still works in lexical fallback mode.
- If Qdrant is down, chat remains available with non-vector fallback.
- Re-run ingestion when corpus files or embedding model changes.

## 6. Troubleshooting

- Error: collection missing
  - Run ingestion with `--recreate`.
- Error: embedding model load failure
  - Confirm Python environment and dependency installation.
- No sources in chat response
  - Confirm RAG is enabled and question classified as general/conceptual.

