"""Regulatory resolve pipeline stage: fetch live text from eCFR API for fired engrams.

Runs after scoring, before prompt assembly.  Converts engram retrieval cues
into full regulatory text by querying the eCFR API.  Results are cached on
the engram record with a configurable TTL (default 24 hours).
"""

import datetime
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import Engram
from app.services.ecfr_client import get_ecfr_client, estimate_tokens


@dataclass
class ResolvedRegulation:
    """A single resolved regulatory text from an engram."""
    engram_id: int
    cfr_ref: str              # e.g. "48 CFR 31.205-14"
    text: str                 # full or extracted section text
    token_count: int
    source: str               # "live_api" | "cache" | "fallback_summary"
    fetched_at: datetime.datetime


def _cfr_ref(engram: Engram) -> str:
    """Build a human-readable CFR reference string."""
    section = f".{engram.cfr_section}" if engram.cfr_section else ""
    return f"{engram.cfr_title} CFR {engram.cfr_part}{section}"


def _cache_is_valid(engram: Engram) -> bool:
    """Check if the engram's cached text is still within TTL."""
    if not engram.cached_text or not engram.cached_at:
        return False
    ttl_hours = engram.cache_ttl_hours or settings.engram_cache_ttl_hours
    expiry = engram.cached_at + datetime.timedelta(hours=ttl_hours)
    return datetime.datetime.utcnow() < expiry


async def resolve_engrams(
    db: AsyncSession,
    fired_engrams: list[tuple[Engram, float]],
    token_budget: int,
) -> list[ResolvedRegulation]:
    """Fetch live regulatory text for fired engrams within token budget.

    Priority order: highest-scored engrams first.  Stops when token budget
    is exhausted.  Falls back to engram summary if API fails.
    """
    if not fired_engrams:
        return []

    # Sort by score descending
    fired_engrams.sort(key=lambda pair: pair[1], reverse=True)

    results: list[ResolvedRegulation] = []
    tokens_used = 0
    client = get_ecfr_client()

    for engram, _score in fired_engrams:
        ref = _cfr_ref(engram)
        now = datetime.datetime.utcnow()

        # Check cache first
        if _cache_is_valid(engram):
            tc = engram.cached_token_count or estimate_tokens(engram.cached_text)
            if tokens_used + tc <= token_budget:
                results.append(ResolvedRegulation(
                    engram_id=engram.id,
                    cfr_ref=ref,
                    text=engram.cached_text,
                    token_count=tc,
                    source="cache",
                    fetched_at=engram.cached_at,
                ))
                tokens_used += tc
            continue

        # Fetch live from eCFR
        text_content = await client.fetch_section(
            title=engram.cfr_title,
            part=engram.cfr_part,
            section=engram.cfr_section,
        )

        if text_content:
            tc = estimate_tokens(text_content)

            # Update cache on the engram record
            engram.cached_text = text_content
            engram.cached_at = now
            engram.cached_token_count = tc
            engram.last_verified = now

            if tokens_used + tc <= token_budget:
                results.append(ResolvedRegulation(
                    engram_id=engram.id,
                    cfr_ref=ref,
                    text=text_content,
                    token_count=tc,
                    source="live_api",
                    fetched_at=now,
                ))
                tokens_used += tc
            elif tc > token_budget and engram.summary:
                # Section too large even alone — use summary as fallback
                summary_tc = estimate_tokens(engram.summary)
                if tokens_used + summary_tc <= token_budget:
                    results.append(ResolvedRegulation(
                        engram_id=engram.id,
                        cfr_ref=ref,
                        text=f"[Summary — full text cached] {engram.summary}",
                        token_count=summary_tc,
                        source="fallback_summary",
                        fetched_at=now,
                    ))
                    tokens_used += summary_tc

        elif settings.engram_fallback_on_api_failure and engram.summary:
            # API failed — use summary
            summary_tc = estimate_tokens(engram.summary)
            if tokens_used + summary_tc <= token_budget:
                results.append(ResolvedRegulation(
                    engram_id=engram.id,
                    cfr_ref=ref,
                    text=f"[API unavailable — summary only] {engram.summary}",
                    token_count=summary_tc,
                    source="fallback_summary",
                    fetched_at=now,
                ))
                tokens_used += summary_tc

    # Commit cache updates
    await db.flush()

    return results
