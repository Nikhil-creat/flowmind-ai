"""
Document intelligence engine: extracts text, chunks it, embeds it into a
per-user Chroma collection, and answers questions with retrieval-augmented
generation (RAG) using Claude as the reasoning model.
"""
from __future__ import annotations

import io
from typing import Any

import chromadb
from chromadb.utils import embedding_functions
from pypdf import PdfReader

from app.core import cache
from app.core.config import get_settings
from app.services import ai_provider

settings = get_settings()

_chroma_client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
_embedder = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name=settings.EMBEDDING_MODEL
)


def _collection_for_user(user_id: str):
    return _chroma_client.get_or_create_collection(
        name=f"user_{user_id}", embedding_function=_embedder
    )


def extract_text(filename: str, raw_bytes: bytes) -> str:
    if filename.lower().endswith(".pdf"):
        reader = PdfReader(io.BytesIO(raw_bytes))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    # Fall back to plain-text decoding for .txt/.md/.csv etc.
    return raw_bytes.decode("utf-8", errors="ignore")


def chunk_text(text: str, chunk_size: int = 900, overlap: int = 150) -> list[str]:
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunks.append(" ".join(words[start:end]))
        start = end - overlap
    return [c for c in chunks if c.strip()]


def index_document(user_id: str, document_id: str, filename: str, text: str) -> int:
    """Chunk + embed a document's text into the user's vector collection."""
    chunks = chunk_text(text)
    if not chunks:
        return 0
    collection = _collection_for_user(user_id)
    ids = [f"{document_id}::{i}" for i in range(len(chunks))]
    metadatas = [{"document_id": document_id, "filename": filename} for _ in chunks]
    collection.add(documents=chunks, ids=ids, metadatas=metadatas)
    return len(chunks)


def delete_document_vectors(user_id: str, document_id: str) -> None:
    collection = _collection_for_user(user_id)
    collection.delete(where={"document_id": document_id})


def search(user_id: str, query: str, k: int = 5, document_ids: list[str] | None = None) -> list[dict[str, Any]]:
    cache_key = f"search:{user_id}:{hash((query, k, tuple(document_ids or [])))}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    collection = _collection_for_user(user_id)
    where = {"document_id": {"$in": document_ids}} if document_ids else None
    results = collection.query(query_texts=[query], n_results=k, where=where)
    hits = []
    for doc, meta in zip(results.get("documents", [[]])[0], results.get("metadatas", [[]])[0]):
        hits.append({"snippet": doc, "document_id": meta["document_id"], "filename": meta["filename"]})

    cache.set(cache_key, hits, ttl=120)
    return hits


def summarize_text(text: str) -> str:
    """Short extractive-style fallback summary, used before/without an LLM call."""
    sentences = text.replace("\n", " ").split(". ")
    return ". ".join(sentences[:4]).strip()[:800]


def generate_answer(question: str, context_chunks: list[dict[str, Any]]) -> dict[str, str]:
    """Generate a grounded answer via the multi-provider AI layer (Claude,
    with automatic Gemini fallback). Falls back to a simple extractive
    response if neither provider is configured, so the project still runs
    end-to-end without external credentials.

    Returns {"text": ..., "provider": "claude"|"gemini"|"extractive"}.
    """
    context = "\n\n---\n\n".join(f"[{c['filename']}]: {c['snippet']}" for c in context_chunks)
    prompt = (
        "You are a document intelligence assistant. Answer the user's question "
        "using ONLY the context below. If the answer isn't in the context, say so.\n\n"
        f"Context:\n{context}\n\nQuestion: {question}"
    )

    result = ai_provider.generate(prompt, max_tokens=600)
    if result["text"]:
        return result

    if not context_chunks:
        return {"text": "I couldn't find anything relevant in your documents yet.", "provider": "extractive"}
    joined = "\n\n".join(c["snippet"] for c in context_chunks[:2])
    return {"text": f"Based on your documents:\n\n{joined[:600]}", "provider": "extractive"}
