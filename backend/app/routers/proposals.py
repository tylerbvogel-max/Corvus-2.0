"""Proposals router — CRUD, approve/reject, apply, provenance chain.

Staged autopilot proposals with full audit trail. Nothing modifies the
neuron graph until a proposal is explicitly approved and applied.
"""

import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db, async_session
from app.models import (
    AutopilotProposal, ProposalItem, Neuron, NeuronEdge, NeuronRefinement,
    NeuronSourceLink, EmergentQueue, Query,
)
from app.schemas import (
    ProposalOut, ProposalDetailOut, ProposalItemOut,
    GapEvidenceOut, DocumentEvidenceOut,
    ProposalReviewRequest, ProposalApplyRequest, ProposalStatsOut,
)

router = APIRouter(prefix="/admin/proposals", tags=["proposals"])


def _proposal_summary(p: AutopilotProposal) -> ProposalOut:
    """Convert proposal model to summary schema."""
    return ProposalOut(
        id=p.id,
        autopilot_run_id=p.autopilot_run_id,
        query_id=p.query_id,
        state=p.state,
        gap_source=p.gap_source,
        gap_description=p.gap_description,
        priority_score=p.priority_score,
        llm_model=p.llm_model,
        eval_overall=p.eval_overall,
        reviewed_by=p.reviewed_by,
        reviewed_at=p.reviewed_at.isoformat() if p.reviewed_at else None,
        applied_at=p.applied_at.isoformat() if p.applied_at else None,
        applied_by=p.applied_by,
        item_count=len(p.items) if p.items else 0,
        created_at=p.created_at.isoformat() if p.created_at else None,
    )


def _proposal_detail(p: AutopilotProposal) -> ProposalDetailOut:
    """Convert proposal model to full detail schema."""
    evidence: list[GapEvidenceOut | DocumentEvidenceOut | dict] = []
    if p.gap_evidence_json:
        try:
            raw = json.loads(p.gap_evidence_json)
            for e in raw:
                if "signal" in e:
                    evidence.append(GapEvidenceOut(**e))
                elif "source" in e and "document" in e:
                    evidence.append(DocumentEvidenceOut(**e))
                else:
                    evidence.append(e)
        except (json.JSONDecodeError, TypeError):
            pass

    items = [
        ProposalItemOut(
            id=item.id,
            action=item.action,
            target_neuron_id=item.target_neuron_id,
            field=item.field,
            old_value=item.old_value,
            new_value=item.new_value,
            neuron_spec_json=item.neuron_spec_json,
            reason=item.reason,
            created_neuron_id=item.created_neuron_id,
            refinement_id=item.refinement_id,
        )
        for item in (p.items or [])
    ]

    return ProposalDetailOut(
        id=p.id,
        autopilot_run_id=p.autopilot_run_id,
        query_id=p.query_id,
        state=p.state,
        gap_source=p.gap_source,
        gap_description=p.gap_description,
        gap_evidence=evidence,
        priority_score=p.priority_score,
        llm_reasoning=p.llm_reasoning,
        llm_model=p.llm_model,
        prompt_hash=p.prompt_hash,
        eval_overall=p.eval_overall,
        eval_text=p.eval_text,
        reviewed_by=p.reviewed_by,
        reviewed_at=p.reviewed_at.isoformat() if p.reviewed_at else None,
        review_notes=p.review_notes,
        applied_at=p.applied_at.isoformat() if p.applied_at else None,
        applied_by=p.applied_by,
        items=items,
        created_at=p.created_at.isoformat() if p.created_at else None,
        updated_at=p.updated_at.isoformat() if p.updated_at else None,
    )


@router.get("/", response_model=list[ProposalOut])
async def list_proposals(
    state: str | None = None,
    gap_source: str | None = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """List proposals, optionally filtered by state or gap_source."""
    stmt = select(AutopilotProposal).order_by(AutopilotProposal.id.desc())
    if state:
        stmt = stmt.where(AutopilotProposal.state == state)
    if gap_source:
        stmt = stmt.where(AutopilotProposal.gap_source == gap_source)
    stmt = stmt.limit(limit)
    result = await db.execute(stmt)
    return [_proposal_summary(p) for p in result.scalars().all()]


@router.get("/stats", response_model=ProposalStatsOut)
async def proposal_stats(db: AsyncSession = Depends(get_db)):
    """Aggregate counts by proposal state."""
    result = await db.execute(
        select(AutopilotProposal.state, func.count(AutopilotProposal.id))
        .group_by(AutopilotProposal.state)
    )
    counts = {row[0]: row[1] for row in result.all()}
    return ProposalStatsOut(
        proposed=counts.get("proposed", 0),
        approved=counts.get("approved", 0),
        rejected=counts.get("rejected", 0),
        applied=counts.get("applied", 0),
        total=sum(counts.values()),
    )


@router.get("/{proposal_id}", response_model=ProposalDetailOut)
async def get_proposal(proposal_id: int, db: AsyncSession = Depends(get_db)):
    """Full proposal detail with evidence chain and items."""
    p = await db.get(AutopilotProposal, proposal_id)
    if not p:
        raise HTTPException(404, "Proposal not found")
    return _proposal_detail(p)


@router.post("/{proposal_id}/review", response_model=ProposalDetailOut)
async def review_proposal(
    proposal_id: int,
    req: ProposalReviewRequest,
    db: AsyncSession = Depends(get_db),
):
    """Approve or reject a proposal. Only 'proposed' state proposals can be reviewed."""
    p = await db.get(AutopilotProposal, proposal_id)
    if not p:
        raise HTTPException(404, "Proposal not found")
    if p.state != "proposed":
        raise HTTPException(400, f"Cannot review proposal in state '{p.state}'")

    p.state = "approved" if req.action == "approve" else "rejected"
    p.reviewed_by = req.reviewer
    p.reviewed_at = datetime.utcnow()
    p.review_notes = req.notes
    await db.commit()
    await db.refresh(p)
    return _proposal_detail(p)


async def _apply_update_item(
    db: AsyncSession, item: ProposalItem, proposal_id: int, query_id: int | None,
) -> None:
    """Apply a single update item to the graph."""
    from app.services.reference_hooks import populate_external_references
    neuron = await db.get(Neuron, item.target_neuron_id)
    if not neuron:
        return
    field = item.field or ""
    new_val = item.new_value or ""
    old_val = item.old_value or ""
    if field == "content":
        neuron.content = new_val
    elif field == "summary":
        neuron.summary = new_val
    elif field == "label":
        neuron.label = new_val
    elif field == "is_active":
        neuron.is_active = new_val.lower() in ("true", "1", "yes")
    else:
        return
    if field in ("content", "summary"):
        populate_external_references(neuron)
    ref = NeuronRefinement(
        query_id=query_id, neuron_id=item.target_neuron_id,
        action="update", field=field, old_value=old_val, new_value=new_val,
        reason=item.reason or f"Applied from proposal #{proposal_id}",
    )
    db.add(ref)
    await db.flush()
    item.refinement_id = ref.id


async def _apply_create_item(
    db: AsyncSession, item: ProposalItem, proposal_id: int,
    query_id: int | None, total_queries: int,
) -> None:
    """Apply a single create item to the graph."""
    from app.services.reference_hooks import populate_external_references
    assert item.neuron_spec_json is not None
    spec = json.loads(item.neuron_spec_json)
    neuron = Neuron(
        parent_id=spec.get("parent_id"), layer=spec.get("layer", 3),
        node_type=spec.get("node_type", "knowledge"), label=spec.get("label", ""),
        content=spec.get("content", ""), summary=spec.get("summary", ""),
        department=spec.get("department"), role_key=spec.get("role_key"),
        is_active=True, created_at_query_count=total_queries,
        source_origin=spec.get("source_origin", "autopilot"),
        source_type=spec.get("source_type", "operational"),
        citation=spec.get("citation"),
        source_url=spec.get("source_url"),
        authority_level=spec.get("authority_level"),
        proposal_item_id=item.id,
    )
    populate_external_references(neuron)
    db.add(neuron)
    await db.flush()
    item.created_neuron_id = neuron.id
    ref = NeuronRefinement(
        query_id=query_id, neuron_id=neuron.id,
        action="create", field=None, old_value=None,
        new_value=spec.get("label", ""),
        reason=item.reason or f"Created from proposal #{proposal_id}",
    )
    db.add(ref)
    await db.flush()
    item.refinement_id = ref.id


async def _apply_rescale_item(
    db: AsyncSession, item: ProposalItem,
) -> None:
    """Apply a single edge weight rescale item."""
    assert item.neuron_spec_json is not None, "rescale item must have spec"
    spec = json.loads(item.neuron_spec_json)
    source_id = spec["source_id"]
    target_id = spec["target_id"]
    new_weight = spec["new_weight"]

    edge = await db.get(NeuronEdge, (source_id, target_id))
    if edge:
        edge.weight = new_weight
        edge.last_adjusted = datetime.utcnow()


async def _apply_link_item(
    db: AsyncSession, item: ProposalItem,
) -> None:
    """Apply a new edge creation (pattern completion)."""
    assert item.neuron_spec_json is not None, "link item must have spec"
    spec = json.loads(item.neuron_spec_json)

    edge = NeuronEdge(
        source_id=spec["source_id"],
        target_id=spec["target_id"],
        weight=spec.get("initial_weight", 0.15),
        co_fire_count=1,
        edge_type=spec.get("edge_type", "pyramidal"),
        source=spec.get("source", "integrity_completion"),
        context=spec.get("context", ""),
    )
    db.add(edge)


async def _apply_merge_item(
    db: AsyncSession, item: ProposalItem, proposal_id: int, query_id: int | None,
) -> None:
    """Apply a merge action — delegates to update (content merge or deactivation)."""
    # Merge is implemented as sequential update items (content update + deactivation).
    # This handler delegates to _apply_update_item for each sub-operation.
    await _apply_update_item(db, item, proposal_id, query_id)


@router.post("/{proposal_id}/apply", response_model=ProposalDetailOut)
async def apply_proposal(
    proposal_id: int,
    req: ProposalApplyRequest,
    db: AsyncSession = Depends(get_db),
):
    """Apply an approved proposal — writes neurons/updates to the graph."""
    p = await db.get(AutopilotProposal, proposal_id)
    if not p:
        raise HTTPException(404, "Proposal not found")
    if p.state != "approved":
        raise HTTPException(400, f"Cannot apply proposal in state '{p.state}' — must be 'approved'")

    from app.services.neuron_service import get_system_state
    state = await get_system_state(db)

    has_edge_changes = False
    for item in (p.items or []):
        if item.action == "update" and item.target_neuron_id:
            await _apply_update_item(db, item, p.id, p.query_id)
        elif item.action == "create" and item.neuron_spec_json:
            await _apply_create_item(db, item, p.id, p.query_id, state.total_queries)
        elif item.action == "rescale" and item.neuron_spec_json:
            await _apply_rescale_item(db, item)
            has_edge_changes = True
        elif item.action == "link" and item.neuron_spec_json:
            await _apply_link_item(db, item)
            has_edge_changes = True
        elif item.action == "merge" and item.target_neuron_id:
            await _apply_merge_item(db, item, p.id, p.query_id)

    p.state = "applied"
    p.applied_at = datetime.utcnow()
    p.applied_by = req.applied_by
    await db.commit()

    # Invalidate adjacency cache if edges were modified
    if has_edge_changes:
        from app.services.adjacency_cache import invalidate_adjacency_cache
        invalidate_adjacency_cache()

    await db.refresh(p)
    return _proposal_detail(p)


# ── Provenance chain ─────────────────────────────────────────────────

provenance_router = APIRouter(prefix="/admin/neurons", tags=["provenance"])


def _serialize_proposal(p: AutopilotProposal) -> dict:
    """Serialize proposal for provenance response."""
    evidence: list = []
    if p.gap_evidence_json:
        try:
            evidence = json.loads(p.gap_evidence_json)
        except (json.JSONDecodeError, TypeError):
            pass
    return {
        "id": p.id, "state": p.state,
        "gap_source": p.gap_source, "gap_description": p.gap_description,
        "gap_evidence": evidence, "priority_score": p.priority_score,
        "llm_reasoning": p.llm_reasoning, "llm_model": p.llm_model,
        "prompt_hash": p.prompt_hash,
        "eval_overall": p.eval_overall, "eval_text": p.eval_text,
        "reviewed_by": p.reviewed_by,
        "reviewed_at": p.reviewed_at.isoformat() if p.reviewed_at else None,
        "review_notes": p.review_notes,
        "applied_at": p.applied_at.isoformat() if p.applied_at else None,
        "applied_by": p.applied_by,
        "created_at": p.created_at.isoformat() if p.created_at else None,
    }


async def _get_refinements(db: AsyncSession, neuron_id: int) -> list[dict]:
    """Load refinement history for a neuron."""
    refs_result = await db.execute(
        select(NeuronRefinement)
        .where(NeuronRefinement.neuron_id == neuron_id)
        .order_by(NeuronRefinement.id)
    )
    return [
        {"id": r.id, "action": r.action, "field": r.field,
         "old_value": r.old_value, "new_value": r.new_value,
         "reason": r.reason, "query_id": r.query_id,
         "created_at": r.created_at.isoformat() if r.created_at else None}
        for r in refs_result.scalars().all()
    ]


async def _get_source_links(db: AsyncSession, neuron_id: int) -> list[dict]:
    """Load source document links for a neuron."""
    links_result = await db.execute(
        select(NeuronSourceLink)
        .where(NeuronSourceLink.neuron_id == neuron_id)
        .order_by(NeuronSourceLink.id)
    )
    return [
        {"id": lk.id, "source_document_id": lk.source_document_id,
         "derivation_type": lk.derivation_type, "section_ref": lk.section_ref,
         "review_status": lk.review_status, "link_origin": lk.link_origin}
        for lk in links_result.scalars().all()
    ]


@provenance_router.get("/{neuron_id}/provenance")
async def neuron_provenance(neuron_id: int, db: AsyncSession = Depends(get_db)):
    """Full provenance chain: neuron → proposal → gap evidence → approval."""
    neuron = await db.get(Neuron, neuron_id)
    if not neuron:
        raise HTTPException(404, "Neuron not found")

    result: dict = {
        "neuron": {
            "id": neuron.id, "label": neuron.label, "layer": neuron.layer,
            "node_type": neuron.node_type, "department": neuron.department,
            "source_origin": neuron.source_origin, "source_type": neuron.source_type,
            "citation": neuron.citation, "authority_level": neuron.authority_level,
            "created_at": neuron.created_at.isoformat() if neuron.created_at else None,
        },
        "proposal_item": None,
        "proposal": None,
        "refinements": await _get_refinements(db, neuron_id),
        "source_links": await _get_source_links(db, neuron_id),
    }

    if neuron.proposal_item_id:
        item = await db.get(ProposalItem, neuron.proposal_item_id)
        if item:
            result["proposal_item"] = {
                "id": item.id, "action": item.action, "reason": item.reason,
                "proposal_id": item.proposal_id, "neuron_spec_json": item.neuron_spec_json,
            }
            proposal = await db.get(AutopilotProposal, item.proposal_id)
            if proposal:
                result["proposal"] = _serialize_proposal(proposal)

    return result
