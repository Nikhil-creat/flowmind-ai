"""
Document intelligence engine: extracts text (or, for images, a vision-model
description), chunks it, embeds it into a per-workspace Chroma collection,
and answers questions with retrieval-augmented generation (RAG).
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

IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp", ".gif")
IMAGE_MEDIA_TYPES = {
    ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
    ".webp": "image/webp", ".gif": "image/gif",
}

# Lazily initialized on first real use (not at import time). This makes app
# startup instant and means the test suite / CI don't need to download the
# embedding model just to import the module.
_chroma_client = None
_embedder = None


def _get_client_and_embedder():
    global _chroma_client, _embedder
    if _chroma_client is None:
        _chroma_client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
    if _embedder is None:
        _embedder = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=settings.EMBEDDING_MODEL
        )
    return _chroma_client, _embedder


def _collection_for_workspace(workspace_id: str):
    client, embedder = _get_client_and_embedder()
    return client.get_or_create_collection(name=f"workspace_{workspace_id}", embedding_function=embedder)


def is_image(filename: str) -> bool:
    return filename.lower().endswith(IMAGE_EXTENSIONS)


def extract_text(filename: str, raw_bytes: bytes) -> str:
    lower = filename.lower()
    if lower.endswith(".pdf"):
        reader = PdfReader(io.BytesIO(raw_bytes))
        return "\n".join(page.extract_text() or "" for page in reader.pages)

    if is_image(filename):
        ext = next(e for e in IMAGE_EXTENSIONS if lower.endswith(e))
        media_type = IMAGE_MEDIA_TYPES[ext]
        result = ai_provider.describe_image(raw_bytes, media_type)
        if result["text"]:
            return result["text"]
        return f"[Image file: {filename} - no AI provider configured to describe it]"

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


def index_document(workspace_id: str, document_id: str, filename: str, text: str) -> int:
    """Chunk + embed a document's text into the workspace's shared vector
    collection, so any teammate's search can retrieve it."""
    chunks = chunk_text(text)
    if not chunks:
        return 0
    collection = _collection_for_workspace(workspace_id)
    ids = [f"{document_id}::{i}" for i in range(len(chunks))]
    metadatas = [{"document_id": document_id, "filename": filename} for _ in chunks]
    collection.add(documents=chunks, ids=ids, metadatas=metadatas)
    return len(chunks)


def delete_document_vectors(workspace_id: str, document_id: str) -> None:
    collection = _collection_for_workspace(workspace_id)
    collection.delete(where={"document_id": document_id})


def search(workspace_id: str, query: str, k: int = 5, document_ids: list[str] | None = None) -> list[dict[str, Any]]:
    cache_key = f"search:{workspace_id}:{hash((query, k, tuple(document_ids or [])))}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    collection = _collection_for_workspace(workspace_id)
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
