"""Corvus Advisor — read-only consumer of neuron graph for proactive guidance.

Watches screen activity and queries the neuron graph for relevant knowledge.
Surfaces guidance with full provenance when relevance exceeds threshold.
Stays silent otherwise. Never writes to the graph.
"""

import json
import time
from datetime import datetime, timezone

from app.corvus.ocr import text_similarity
from app.database import async_session
from app.models_corvus import CorvusAdvisory
from app.services.llm_provider import llm_chat
from app.services.executor import prepare_context

import app.corvus.capture as capture_mod

# Module-level state for novelty dedup
_last_advisory_query: str = ""
_last_advisory_time: float = 0.0

NOVELTY_THRESHOLD = 0.7   # Skip if new query >70% similar to last
MIN_INTERVAL_SECONDS = 30  # Minimum time between advisories


def distill_screen_query(ocr_texts: list[str], app_id: str | None) -> str:
    """Heuristic extraction of query from OCR content. No LLM call.

    Takes the most recent non-empty OCR texts (last 2-3 frames),
    prepends app context, and truncates to ~500 chars.
    """
    assert isinstance(ocr_texts, list), "ocr_texts must be a list"

    # Take last 3 non-empty texts
    recent = [t for t in ocr_texts[-3:] if t and t.strip()]
    if not recent:
        return ""

    combined = " ".join(recent)

    # Prepend app context if available
    prefix = f"User viewing {app_id}: " if app_id else ""
    query = prefix + combined

    # Truncate to ~500 chars at word boundary
    if len(query) > 500:
        query = query[:500].rsplit(" ", 1)[0]

    return query.strip()


async def _peek_and_distill() -> tuple[str, str | None] | None:
    """Peek at pending OCR buffers and distill into a query.

    Returns (query, app_id) or None if content is stale/empty.
    """
    global _last_advisory_query, _last_advisory_time

    # Check minimum interval
    now = time.time()
    if now - _last_advisory_time < MIN_INTERVAL_SECONDS:
        return None

    # Peek at pending diffs without consuming them
    diffs = capture_mod.capture_state._pending_diffs[:]
    if not diffs:
        return None

    ocr_texts = [d["diff_text"] for d in diffs]
    app_id = diffs[-1].get("app_id")

    query = distill_screen_query(ocr_texts, app_id)
    if not query:
        return None

    # Check novelty against last query
    if _last_advisory_query and text_similarity(query, _last_advisory_query) > NOVELTY_THRESHOLD:
        return None

    return (query, app_id)


async def _run_pipeline_and_score(
    query: str, threshold: float,
) -> tuple | None:
    """Run the neuron graph pipeline and check if top score exceeds threshold.

    Returns (result, top_score) or None if below threshold.
    """
    async with async_session() as db:
        result = await prepare_context(
            db, query, top_k=5, token_budget=2000,
        )

    if not result.all_scored:
        return None

    top_score = result.all_scored[0].combined
    if top_score < threshold:
        return None

    return (result, top_score)


def _build_citations(scored_list: list, neuron_map: dict) -> list[dict]:
    """Build citation dicts from scored neurons and neuron map.

    Returns list of citation dicts with provenance fields.
    """
    citations = []
    for scored in scored_list[:5]:
        neuron = neuron_map.get(scored.neuron_id)
        if neuron is None:
            continue
        citations.append({
            "id": neuron.id,
            "label": neuron.label,
            "department": neuron.department,
            "source_type": neuron.source_type,
            "citation": neuron.citation,
            "source_url": neuron.source_url,
            "score": round(scored.combined, 3),
            "content_preview": (neuron.content or "")[:200],
        })
    return citations


async def _format_advisory(
    screen_context: str, citations: list[dict], intent: str,
) -> dict:
    """Format advisory guidance via Haiku. Returns dict with text and cost."""
    neuron_summaries = "\n".join(
        f"- [{c['label']}] ({c['source_type']}): {c['content_preview']}"
        for c in citations
    )

    system = (
        "You are a domain knowledge advisor. Based on what the user is currently "
        "viewing and relevant knowledge from the neuron graph, provide brief "
        "actionable guidance. Cite specific standards or sources. 2-3 sentences max."
    )
    user_msg = (
        f"Screen context: {screen_context[:300]}\n\n"
        f"Intent: {intent}\n\n"
        f"Relevant knowledge:\n{neuron_summaries}"
    )

    resp = await llm_chat(system, user_msg, max_tokens=200, model="haiku", timeout=30)
    return {"text": resp["text"], "cost_usd": resp["cost_usd"]}


async def _store_advisory(
    query: str, app_id: str | None, guidance: str, top_score: float,
    citations: list[dict], intent: str, departments: list[str],
    session_id: int | None, cost_usd: float,
) -> dict:
    """Persist advisory to database and return serialized dict."""
    neuron_ids = [c["id"] for c in citations]
    timestamp = datetime.now(timezone.utc).isoformat()

    advisory = CorvusAdvisory(
        timestamp=timestamp,
        trigger_context=query[:1000],
        guidance=guidance,
        top_score=top_score,
        neuron_ids_json=json.dumps(neuron_ids),
        citations_json=json.dumps(citations),
        intent=intent,
        departments_json=json.dumps(departments) if departments else None,
        app_id=app_id,
        session_id=session_id,
        cost_usd=cost_usd,
    )

    async with async_session() as db:
        db.add(advisory)
        await db.commit()
        await db.refresh(advisory)

    return {
        "id": advisory.id,
        "timestamp": timestamp,
        "trigger_context": query[:200],
        "guidance": guidance,
        "top_score": top_score,
        "citations": citations,
        "intent": intent,
        "departments": departments,
        "app_id": app_id,
        "cost_usd": cost_usd,
    }


async def run_advisory_check(
    trigger: str, threshold: float = 0.5, session_id: int | None = None,
) -> dict | None:
    """Main entry point. Check screen content against neuron graph.

    Returns advisory dict if relevant knowledge found, None otherwise.
    Consumes pending buffers on success.
    """
    global _last_advisory_query, _last_advisory_time

    # Step 1-3: Peek and distill, check novelty
    peek_result = await _peek_and_distill()
    if peek_result is None:
        return None

    query, app_id = peek_result

    # Step 4-6: Run pipeline, check threshold
    pipeline_result = await _run_pipeline_and_score(query, threshold)
    if pipeline_result is None:
        return None

    result, top_score = pipeline_result

    # Step 7: Build citations
    citations = _build_citations(result.all_scored, result.neuron_map)
    if not citations:
        return None

    # Step 8: Format via Haiku
    formatted = await _format_advisory(query, citations, result.intent)

    # Step 9: Store
    advisory = await _store_advisory(
        query=query,
        app_id=app_id,
        guidance=formatted["text"],
        top_score=top_score,
        citations=citations,
        intent=result.intent,
        departments=result.departments,
        session_id=session_id,
        cost_usd=result.classify_cost_usd + formatted["cost_usd"],
    )

    # Step 10: Update novelty state
    _last_advisory_query = query
    _last_advisory_time = time.time()

    return advisory
