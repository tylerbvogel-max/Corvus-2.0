"""Seed engrams from tenant configuration and auto-embed."""

import json
import logging

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Engram
from app.tenant import tenant

logger = logging.getLogger(__name__)


async def load_engram_seeds(db: AsyncSession, force: bool = False) -> dict:
    """Seed engrams from tenant.engram_seeds.  Skip if already seeded."""
    seeds = tenant.engram_seeds
    if not seeds:
        return {"status": "no_seeds", "count": 0}

    count = (await db.execute(select(func.count(Engram.id)))).scalar() or 0
    if count > 0 and not force:
        return {"status": "already_seeded", "count": count}

    if force and count > 0:
        await db.execute(Engram.__table__.delete())
        await db.flush()
        logger.info("Force re-seed: deleted %d existing engrams", count)

    # Get current query count for novelty tracking
    from app.models import SystemState
    state = (await db.execute(select(SystemState).where(SystemState.id == 1))).scalar_one_or_none()
    total_queries = state.total_queries if state else 0

    created = 0
    for seed in seeds:
        engram = Engram(
            label=seed["label"],
            summary=seed.get("summary"),
            content=seed.get("content"),
            cfr_title=seed["cfr_title"],
            cfr_part=seed["cfr_part"],
            cfr_section=seed.get("cfr_section"),
            source_api=seed.get("source_api", "ecfr"),
            authority_level=seed.get("authority_level", "regulatory"),
            issuing_body=seed.get("issuing_body"),
            created_at_query_count=total_queries,
        )
        db.add(engram)
        created += 1

    await db.flush()
    await db.commit()
    logger.info("Seeded %d engrams", created)

    return {"status": "seeded", "count": created}


async def auto_embed_engrams(db: AsyncSession) -> int:
    """Embed any engrams missing embeddings.  Returns count embedded."""
    import asyncio

    rows = (await db.execute(
        select(Engram).where(
            Engram.is_active == True,  # noqa: E712
            (Engram.embedding == None) | (Engram.embedding == ""),  # noqa: E711
        )
    )).scalars().all()

    if not rows:
        return 0

    from app.services.embedding_service import embed_batch

    texts = [f"{e.label} {e.summary or ''} {e.content or ''}"[:1000] for e in rows]
    loop = asyncio.get_running_loop()
    vectors = await loop.run_in_executor(None, embed_batch, texts)

    for engram, vec in zip(rows, vectors):
        engram.embedding = json.dumps(vec)

    await db.commit()
    return len(rows)
