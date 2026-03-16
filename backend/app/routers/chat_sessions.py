"""Chat session persistence — CRUD + LLM title generation."""

import json
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import ChatSession, ChatSessionMessage
from app.services.claude_cli import claude_chat, estimate_cost

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat Sessions"])


# ── Pydantic schemas ──

class SessionCreate(BaseModel):
    title: str | None = None


class SessionSummary(BaseModel):
    id: int
    title: str | None
    created_at: str
    updated_at: str
    message_count: int = 0


class MessageAppend(BaseModel):
    role: str = Field(..., pattern=r"^(user|assistant)$")
    text: str = Field(..., min_length=1)
    model: str | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    cost: float = 0.0
    neurons_activated: int = 0
    neuron_scores: list[dict] | None = None


class SessionTitleUpdate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)


class MessageOut(BaseModel):
    id: int
    role: str
    text: str
    model: str | None
    input_tokens: int
    output_tokens: int
    cost: float
    neurons_activated: int
    neuron_scores: list[dict] | None
    created_at: str


class SessionDetail(BaseModel):
    id: int
    title: str | None
    created_at: str
    updated_at: str
    messages: list[MessageOut]


# ── Endpoints ──

@router.post("/sessions")
async def create_session(
    body: SessionCreate | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Create a new chat session."""
    session = ChatSession(title=body.title if body else None)
    db.add(session)
    await db.commit()
    await db.refresh(session)
    assert session.id is not None, "Session ID must be set after commit"
    return {"id": session.id, "created_at": session.created_at.isoformat()}


@router.get("/sessions", response_model=list[SessionSummary])
async def list_sessions(
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List non-archived sessions, newest first."""
    stmt = (
        select(ChatSession)
        .where(ChatSession.archived_at.is_(None))
        .order_by(ChatSession.updated_at.desc())
        .limit(limit)
        .options(selectinload(ChatSession.messages))
    )
    result = await db.execute(stmt)
    sessions = result.scalars().all()
    assert isinstance(sessions, list) or hasattr(sessions, '__iter__'), "Expected iterable sessions"
    return [
        SessionSummary(
            id=s.id,
            title=s.title,
            created_at=s.created_at.isoformat(),
            updated_at=s.updated_at.isoformat(),
            message_count=len(s.messages),
        )
        for s in sessions
    ]


@router.get("/sessions/{session_id}", response_model=SessionDetail)
async def get_session(session_id: int, db: AsyncSession = Depends(get_db)):
    """Load a session with all its messages."""
    stmt = (
        select(ChatSession)
        .where(ChatSession.id == session_id)
        .options(selectinload(ChatSession.messages))
    )
    result = await db.execute(stmt)
    s = result.scalar_one_or_none()
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")
    assert s.id == session_id, "Loaded session ID mismatch"
    return SessionDetail(
        id=s.id,
        title=s.title,
        created_at=s.created_at.isoformat(),
        updated_at=s.updated_at.isoformat(),
        messages=[_msg_out(m) for m in s.messages],
    )


@router.post("/sessions/{session_id}/messages")
async def append_message(
    session_id: int,
    body: MessageAppend,
    db: AsyncSession = Depends(get_db),
):
    """Append a message to a session."""
    session = await db.get(ChatSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    msg = ChatSessionMessage(
        session_id=session_id,
        role=body.role,
        text=body.text,
        model=body.model,
        input_tokens=body.input_tokens,
        output_tokens=body.output_tokens,
        cost=body.cost,
        neurons_activated=body.neurons_activated,
        neuron_scores_json=json.dumps(body.neuron_scores) if body.neuron_scores else None,
    )
    db.add(msg)
    session.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(msg)
    assert msg.id is not None, "Message ID must be set after commit"
    return {"id": msg.id, "created_at": msg.created_at.isoformat()}


@router.patch("/sessions/{session_id}")
async def update_session_title(
    session_id: int,
    body: SessionTitleUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a session's title."""
    session = await db.get(ChatSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    session.title = body.title
    session.updated_at = datetime.utcnow()
    await db.commit()
    return {"ok": True}


@router.delete("/sessions/{session_id}")
async def archive_session(session_id: int, db: AsyncSession = Depends(get_db)):
    """Soft-delete (archive) a session."""
    session = await db.get(ChatSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    session.archived_at = datetime.utcnow()
    await db.commit()
    return {"ok": True}


@router.post("/sessions/{session_id}/generate-title")
async def generate_title(session_id: int, db: AsyncSession = Depends(get_db)):
    """Use Haiku to generate a 3-6 word title from the first exchange."""
    stmt = (
        select(ChatSession)
        .where(ChatSession.id == session_id)
        .options(selectinload(ChatSession.messages))
    )
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Extract the first user message only
    first_user_msg = next((m for m in session.messages if m.role == "user"), None)
    if not first_user_msg:
        raise HTTPException(status_code=400, detail="No user message to generate title from")

    system = (
        "You are a title generator. Given a user's message, output a 3-6 word topic title. "
        "Rules: NO quotes, NO punctuation, NO preamble, NO explanation. "
        "Output ONLY the title words. Examples:\n"
        "User: What are the key requirements of AS9100D? → AS9100D Key Requirements\n"
        "User: Help me understand our cost allocation process → Cost Allocation Process Overview\n"
        "User: Compare FAR and DFARS compliance → FAR vs DFARS Compliance"
    )
    try:
        res = await claude_chat(system, first_user_msg.text[:300], max_tokens=20, model="haiku")
        title = res["text"].strip().strip('"').strip("'").split("\n")[0].strip()[:200]
        assert len(title) > 0, "Generated title must not be empty"
    except Exception as e:
        logger.warning("Title generation failed: %s", e)
        title = "Untitled conversation"

    session.title = title
    session.updated_at = datetime.utcnow()
    await db.commit()
    cost = estimate_cost("haiku", res.get("input_tokens", 0), res.get("output_tokens", 0))
    return {"title": title, "cost_usd": cost}


def _msg_out(m: ChatSessionMessage) -> MessageOut:
    """Convert a ChatSessionMessage ORM object to a MessageOut schema."""
    scores = None
    if m.neuron_scores_json:
        try:
            scores = json.loads(m.neuron_scores_json)
        except json.JSONDecodeError:
            scores = None
    assert m.role in ("user", "assistant"), f"Invalid message role: {m.role}"
    return MessageOut(
        id=m.id,
        role=m.role,
        text=m.text,
        model=m.model,
        input_tokens=m.input_tokens,
        output_tokens=m.output_tokens,
        cost=m.cost,
        neurons_activated=m.neurons_activated,
        neuron_scores=scores,
        created_at=m.created_at.isoformat(),
    )
