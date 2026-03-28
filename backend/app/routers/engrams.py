"""Admin API endpoints for engram management."""

import json
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Engram
from app.services.engram_service import list_engrams, get_engram
from app.services.ecfr_client import get_ecfr_client, estimate_tokens
from app.seed.engram_loader import load_engram_seeds, auto_embed_engrams

router = APIRouter(prefix="/engrams", tags=["engrams"])


@router.get("/")
async def get_all_engrams(db: AsyncSession = Depends(get_db)):
    """List all active engrams with cache status."""
    engrams = await list_engrams(db)
    return [
        {
            "id": e.id,
            "label": e.label,
            "summary": e.summary,
            "cfr_title": e.cfr_title,
            "cfr_part": e.cfr_part,
            "cfr_section": e.cfr_section,
            "source_api": e.source_api,
            "authority_level": e.authority_level,
            "issuing_body": e.issuing_body,
            "invocations": e.invocations,
            "avg_utility": e.avg_utility,
            "cached": e.cached_text is not None,
            "cached_at": e.cached_at.isoformat() if e.cached_at else None,
            "cached_token_count": e.cached_token_count,
            "has_embedding": e.embedding is not None and e.embedding != "",
            "is_active": e.is_active,
        }
        for e in engrams
    ]


@router.get("/{engram_id}")
async def get_engram_detail(engram_id: int, db: AsyncSession = Depends(get_db)):
    """Get full engram detail including cache status."""
    e = await get_engram(db, engram_id)
    if e is None:
        return {"error": "Engram not found"}
    return {
        "id": e.id,
        "label": e.label,
        "summary": e.summary,
        "content": e.content,
        "cfr_title": e.cfr_title,
        "cfr_part": e.cfr_part,
        "cfr_section": e.cfr_section,
        "source_api": e.source_api,
        "authority_level": e.authority_level,
        "issuing_body": e.issuing_body,
        "effective_date": e.effective_date.isoformat() if e.effective_date else None,
        "invocations": e.invocations,
        "avg_utility": e.avg_utility,
        "cached": e.cached_text is not None,
        "cached_at": e.cached_at.isoformat() if e.cached_at else None,
        "cached_token_count": e.cached_token_count,
        "cached_text_preview": (e.cached_text[:500] + "...") if e.cached_text and len(e.cached_text) > 500 else e.cached_text,
        "has_embedding": e.embedding is not None and e.embedding != "",
        "last_verified": e.last_verified.isoformat() if e.last_verified else None,
        "is_active": e.is_active,
    }


@router.post("/seed")
async def seed_engrams(force: bool = False, db: AsyncSession = Depends(get_db)):
    """Seed engrams from tenant configuration."""
    result = await load_engram_seeds(db, force=force)
    return result


@router.post("/embed")
async def embed_engrams(db: AsyncSession = Depends(get_db)):
    """Generate embeddings for all engrams missing them."""
    count = await auto_embed_engrams(db)
    return {"embedded": count}


@router.post("/{engram_id}/resolve")
async def resolve_engram(engram_id: int, db: AsyncSession = Depends(get_db)):
    """Test-fetch regulatory text from eCFR for a specific engram."""
    e = await get_engram(db, engram_id)
    if e is None:
        return {"error": "Engram not found"}

    client = get_ecfr_client()
    text_content = await client.fetch_section(
        title=e.cfr_title,
        part=e.cfr_part,
        section=e.cfr_section,
    )

    if text_content is None:
        return {"error": "eCFR API returned no content", "engram_id": engram_id}

    tc = estimate_tokens(text_content)
    now = datetime.utcnow()

    # Update cache
    e.cached_text = text_content
    e.cached_at = now
    e.cached_token_count = tc
    e.last_verified = now
    await db.commit()

    section_ref = f"{e.cfr_title} CFR {e.cfr_part}"
    if e.cfr_section:
        section_ref += f".{e.cfr_section}"

    return {
        "engram_id": engram_id,
        "cfr_ref": section_ref,
        "token_count": tc,
        "text_preview": text_content[:500] + ("..." if len(text_content) > 500 else ""),
        "cached_at": now.isoformat(),
    }


@router.get("/stats/summary")
async def engram_stats(db: AsyncSession = Depends(get_db)):
    """Summary statistics for engrams."""
    total = (await db.execute(select(func.count(Engram.id)))).scalar() or 0
    active = (await db.execute(
        select(func.count(Engram.id)).where(Engram.is_active == True)  # noqa: E712
    )).scalar() or 0
    cached = (await db.execute(
        select(func.count(Engram.id)).where(Engram.cached_text != None)  # noqa: E711
    )).scalar() or 0
    embedded = (await db.execute(
        select(func.count(Engram.id)).where(
            Engram.embedding != None,  # noqa: E711
            Engram.embedding != "",
        )
    )).scalar() or 0

    return {
        "total": total,
        "active": active,
        "cached": cached,
        "embedded": embedded,
    }
