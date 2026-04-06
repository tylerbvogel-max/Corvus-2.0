"""Fluent workflow wrappers — composite endpoints for chat-based governance.

Each endpoint combines multiple API calls into a single Fluent tool call
and returns a FluentResponse with a conversational summary.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.rbac import require_role
from app.models import (
    AutopilotProposal, Neuron, NeuronEdge, ObservationQueue,
    Query, SystemState,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/fluent", tags=["fluent"])


class FluentResponse(BaseModel):
    """Standard response envelope for Fluent tool calls."""

    summary: str = Field(description="Conversational summary for Fluent to read aloud")
    details: dict = Field(default_factory=dict, description="Structured data for follow-ups")
    requires_action: bool = Field(default=False, description="Whether user needs to act")
    suggested_prompt: str = Field(default="", description="What Fluent should suggest next")


# ── Document ingestion wrapper ──

class IngestDocumentRequest(BaseModel):
    """Request body for document ingestion via Fluent."""

    text: str = Field(min_length=10, max_length=100_000)
    citation: str = Field(min_length=1, max_length=500)
    source_type: str = Field(default="technical_primary")
    department: str | None = None
    role_key: str | None = None


@router.post("/ingest-document", response_model=FluentResponse)
async def ingest_document(
    req: IngestDocumentRequest,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_role("reviewer")),
):
    """Parse a document into neuron proposals and return a review summary."""
    from app.routers.admin import (
        _validate_ingest_body, _find_parent_neuron, _build_parent_context,
        _build_ingest_prompts, _parse_proposals, _enrich_proposals,
    )
    from app.services.llm_provider import llm_chat

    body = {
        "source_text": req.text, "citation": req.citation,
        "source_type": req.source_type, "department": req.department,
        "role_key": req.role_key,
    }
    source_text, citation, source_type, dept, role, _ = _validate_ingest_body(body)
    parent = await _find_parent_neuron(db, role, dept)
    context = await _build_parent_context(db, parent)
    sys_prompt, user_msg = _build_ingest_prompts(
        citation, source_type, dept, role, source_text, context,
    )

    try:
        result = await llm_chat(sys_prompt, user_msg, max_tokens=8192, model="sonnet")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"LLM segmentation failed: {exc}")

    proposals = _parse_proposals(result["text"].strip())
    _enrich_proposals(proposals, dept, role, parent, source_type, citation, body)

    # Build conversational summary
    layer_counts: dict[str, int] = {}
    for p in proposals:
        layer = f"L{p.get('layer', '?')}"
        layer_counts[layer] = layer_counts.get(layer, 0) + 1
    layer_desc = ", ".join(f"{c} {l}" for l, c in sorted(layer_counts.items()))

    summary = (
        f"Parsed {citation} into {len(proposals)} knowledge units"
        f"{': ' + layer_desc if layer_desc else ''}. "
        f"Department: {dept or 'auto-detected'}. "
        f"Cost: ${result.get('cost_usd', 0):.4f}."
    )
    return FluentResponse(
        summary=summary,
        details={"proposals": proposals, "citation": citation, "count": len(proposals)},
        requires_action=True,
        suggested_prompt="Would you like to review these individually or approve all?",
    )


# ── Batch review wrapper ──

class BatchReviewRequest(BaseModel):
    """Approve or reject multiple proposals in one call."""

    proposal_ids: list[int]
    action: str = Field(pattern="^(approve|reject)$")
    reviewed_by: str = "fluent-user"
    notes: str = ""


@router.post("/batch-review", response_model=FluentResponse)
async def batch_review(
    req: BatchReviewRequest,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_role("reviewer")),
):
    """Review multiple proposals and optionally apply approved ones."""
    reviewed = 0
    errors = []
    for pid in req.proposal_ids:
        proposal = await db.get(AutopilotProposal, pid)
        if not proposal:
            errors.append(f"#{pid}: not found")
            continue
        if proposal.status != "proposed":
            errors.append(f"#{pid}: status is {proposal.status}")
            continue
        proposal.status = "approved" if req.action == "approve" else "rejected"
        proposal.reviewed_by = req.reviewed_by
        proposal.review_notes = req.notes
        reviewed += 1

    await db.commit()

    summary = f"{req.action.title()}d {reviewed} of {len(req.proposal_ids)} proposals."
    if errors:
        summary += f" {len(errors)} skipped: {'; '.join(errors[:3])}."

    next_prompt = ""
    if req.action == "approve" and reviewed > 0:
        next_prompt = "Shall I apply the approved proposals to the live graph?"

    return FluentResponse(
        summary=summary,
        details={"reviewed": reviewed, "errors": errors, "action": req.action},
        requires_action=(req.action == "approve" and reviewed > 0),
        suggested_prompt=next_prompt,
    )


# ── Observation triage wrapper ──

@router.get("/triage-observations", response_model=FluentResponse)
async def triage_observations(
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_role("reviewer")),
):
    """Summarize the observation queue for triage."""
    result = await db.execute(
        select(ObservationQueue)
        .where(ObservationQueue.status == "queued")
        .order_by(ObservationQueue.id.desc())
        .limit(limit)
    )
    observations = result.scalars().all()

    if not observations:
        return FluentResponse(
            summary="No observations pending triage.",
            details={"count": 0, "observations": []},
        )

    # Summarize by type
    type_counts: dict[str, int] = {}
    dept_counts: dict[str, int] = {}
    for obs in observations:
        ot = obs.observation_type or "unknown"
        type_counts[ot] = type_counts.get(ot, 0) + 1
        dept = obs.proposed_department or "unclassified"
        dept_counts[dept] = dept_counts.get(dept, 0) + 1

    type_desc = ", ".join(f"{c} {t}" for t, c in sorted(type_counts.items()))
    dept_desc = ", ".join(f"{c} {d}" for d, c in sorted(dept_counts.items()))
    obs_list = [
        {"id": o.id, "type": o.observation_type, "dept": o.proposed_department,
         "text": (o.text[:120] + "...") if len(o.text) > 120 else o.text,
         "similarity": o.similarity_score}
        for o in observations
    ]

    return FluentResponse(
        summary=f"{len(observations)} observations pending: {type_desc}. Departments: {dept_desc}.",
        details={"count": len(observations), "observations": obs_list},
        requires_action=True,
        suggested_prompt="Would you like to evaluate these or approve/reject specific ones?",
    )


# ── Health summary wrapper ──

@router.get("/health-summary", response_model=FluentResponse)
async def health_summary(
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_role("reader")),
):
    """Combined health check: neuron stats, alerts, system state."""
    # Neuron counts
    neuron_count = await db.scalar(
        select(func.count()).select_from(Neuron).where(Neuron.is_active == True)
    )
    edge_count = await db.scalar(select(func.count()).select_from(NeuronEdge))
    query_count = await db.scalar(select(func.count()).select_from(Query))

    # Department breakdown
    dept_result = await db.execute(
        select(Neuron.department, func.count())
        .where(Neuron.is_active == True)
        .group_by(Neuron.department)
    )
    dept_counts = {row[0]: row[1] for row in dept_result.all()}

    # System state
    state = await db.scalar(select(SystemState).where(SystemState.id == 1))
    total_tokens = state.global_token_counter if state else 0

    # Pending proposals
    pending = await db.scalar(
        select(func.count()).select_from(AutopilotProposal)
        .where(AutopilotProposal.status == "proposed")
    )

    dept_desc = ", ".join(f"{d}: {c}" for d, c in sorted(dept_counts.items()))
    summary = (
        f"Corvus healthy. {neuron_count} neurons, {edge_count} promoted edges, "
        f"{query_count} queries. {pending} proposals pending. "
        f"Departments: {dept_desc}."
    )

    return FluentResponse(
        summary=summary,
        details={
            "neuron_count": neuron_count, "edge_count": edge_count,
            "query_count": query_count, "pending_proposals": pending,
            "total_tokens": total_tokens, "departments": dept_counts,
        },
        requires_action=(pending > 0),
        suggested_prompt="Would you like to review pending proposals?" if pending else "",
    )


# ── Cost summary wrapper ──

@router.get("/cost-summary", response_model=FluentResponse)
async def cost_summary(
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_role("reader")),
):
    """Conversational cost report."""
    total_result = await db.execute(
        select(
            func.count().label("count"),
            func.coalesce(func.sum(Query.input_tokens), 0).label("input"),
            func.coalesce(func.sum(Query.output_tokens), 0).label("output"),
            func.coalesce(func.sum(Query.cost_usd), 0).label("cost"),
        ).select_from(Query)
    )
    row = total_result.one()
    count, input_tok, output_tok, total_cost = row

    if count == 0:
        return FluentResponse(summary="No queries recorded yet. Cost is $0.00.")

    avg = total_cost / count if count > 0 else 0
    summary = (
        f"{count} queries total. {input_tok:,} input tokens, {output_tok:,} output tokens. "
        f"Total cost: ${total_cost:.2f}. Average: ${avg:.4f}/query."
    )

    return FluentResponse(
        summary=summary,
        details={
            "query_count": count, "input_tokens": int(input_tok),
            "output_tokens": int(output_tok),
            "total_cost_usd": float(total_cost), "avg_cost_usd": float(avg),
        },
    )


# ── Graph status wrapper ──

@router.get("/graph-status", response_model=FluentResponse)
async def graph_status(
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_role("reader")),
):
    """Neuron graph statistics overview."""
    neuron_count = await db.scalar(
        select(func.count()).select_from(Neuron).where(Neuron.is_active == True)
    )
    edge_count = await db.scalar(select(func.count()).select_from(NeuronEdge))

    # Layer breakdown
    layer_result = await db.execute(
        select(Neuron.layer, func.count())
        .where(Neuron.is_active == True)
        .group_by(Neuron.layer)
        .order_by(Neuron.layer)
    )
    layer_labels = {0: "Dept", 1: "Role", 2: "Task", 3: "System", 4: "Decision", 5: "Output"}
    layers = {layer_labels.get(row[0], f"L{row[0]}"): row[1] for row in layer_result.all()}
    layer_desc = ", ".join(f"{k}: {v}" for k, v in layers.items())

    summary = f"{neuron_count} active neurons, {edge_count} promoted edges. Layers: {layer_desc}."

    return FluentResponse(
        summary=summary,
        details={"neuron_count": neuron_count, "edge_count": edge_count, "layers": layers},
    )
