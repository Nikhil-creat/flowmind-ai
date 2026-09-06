import asyncio

from fastapi import (APIRouter, BackgroundTasks, Depends, HTTPException,
                      Request, UploadFile, WebSocket, WebSocketDisconnect, File)
from loguru import logger
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import SessionLocal, get_db
from app.core.deps import get_current_user
from app.core.limiter import limiter
from app.core.security import decode_access_token
from app.models.models import ChatMessage, Document, User
from app.models.schemas import ChatRequest, ChatResponse, ChatSource, DocumentOut
from app.services import rag

router = APIRouter(prefix="/api/documents", tags=["documents"])
settings = get_settings()


def _process_document(document_id: str, owner_id: str, filename: str, raw: bytes) -> None:
    """Runs in the background so upload requests return instantly, even for
    large files - the frontend polls status via GET /api/documents."""
    db = SessionLocal()
    try:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            return
        try:
            text = rag.extract_text(filename, raw)
            chunk_count = rag.index_document(owner_id, document_id, filename, text)
            doc.chunk_count = chunk_count
            doc.summary = rag.summarize_text(text)
            doc.status = "ready"
        except Exception as exc:  # noqa: BLE001
            logger.error(f"Document processing failed for {document_id}: {exc}")
            doc.status = "failed"
            doc.summary = f"Processing failed: {exc}"
        db.commit()
    finally:
        db.close()


@router.post("/upload", response_model=DocumentOut)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    raw = await file.read()
    doc = Document(
        owner_id=current_user.id,
        filename=file.filename,
        content_type=file.content_type,
        size_bytes=len(raw),
        status="processing",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    background_tasks.add_task(_process_document, doc.id, current_user.id, file.filename, raw)
    return doc


@router.get("", response_model=list[DocumentOut])
def list_documents(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return (
        db.query(Document)
        .filter(Document.owner_id == current_user.id)
        .order_by(Document.created_at.desc())
        .all()
    )


@router.delete("/{document_id}")
def delete_document(document_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    doc = db.query(Document).filter(Document.id == document_id, Document.owner_id == current_user.id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    rag.delete_document_vectors(current_user.id, document_id)
    db.delete(doc)
    db.commit()
    return {"deleted": document_id}


@router.post("/chat", response_model=ChatResponse)
@limiter.limit(settings.RATE_LIMIT_CHAT)
def chat_with_documents(
    request: Request,
    payload: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    hits = rag.search(current_user.id, payload.message, k=5, document_ids=payload.document_ids)
    result = rag.generate_answer(payload.message, hits)

    db.add(ChatMessage(owner_id=current_user.id, session_id=payload.session_id, role="user", content=payload.message))
    db.add(
        ChatMessage(
            owner_id=current_user.id,
            session_id=payload.session_id,
            role="assistant",
            content=result["text"],
            sources=hits,
        )
    )
    db.commit()

    return ChatResponse(
        session_id=payload.session_id,
        reply=result["text"],
        ai_provider=result["provider"],
        sources=[ChatSource(document_id=h["document_id"], filename=h["filename"], snippet=h["snippet"][:300]) for h in hits],
    )


@router.websocket("/chat/stream")
async def chat_stream(websocket: WebSocket):
    """Real-time chat: client sends {token, session_id, message}, server
    streams the answer back word-by-word for a live-typing effect, then a
    final {done: true, sources, ai_provider} message."""
    await websocket.accept()
    try:
        while True:
            payload = await websocket.receive_json()
            user_id = decode_access_token(payload.get("token", ""))
            if not user_id:
                await websocket.send_json({"error": "unauthorized"})
                continue

            message = payload.get("message", "")
            hits = rag.search(user_id, message, k=5)
            result = rag.generate_answer(message, hits)

            words = result["text"].split(" ")
            for i, word in enumerate(words):
                await websocket.send_json({"token": word + (" " if i < len(words) - 1 else "")})
                await asyncio.sleep(0.02)

            await websocket.send_json({
                "done": True,
                "ai_provider": result["provider"],
                "sources": [{"document_id": h["document_id"], "filename": h["filename"]} for h in hits],
            })
    except WebSocketDisconnect:
        pass
