"""Pass 2: LLM-driven knowledge extraction from parsed document sections.

For each section, builds a context-aware prompt, calls the LLM to extract
neuron proposals, checks for semantic duplicates, and creates AutopilotProposals
in the existing proposal queue with gap_source="document_ingest".
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import logging
from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session
from app.models import (
    AutopilotProposal,
    DocumentIngestJob,
    Neuron,
    ProposalItem,
)
from app.services.document_parser import DocumentStructure, Section
from app.services.embedding_service import batch_cosine_similarity, embed_text
from app.services.llm_provider import llm_chat

logger = logging.getLogger(__name__)

# Similarity threshold for flagging duplicates
DUPLICATE_THRESHOLD = 0.85

# Max section text length sent to the LLM (chars)
MAX_SECTION_CHARS = 12_000

# Retry configuration: 3 attempts with exponential backoff (10s, 20s)
MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 10


async def _get_existing_neurons(
    db: AsyncSession,
    department: str | None,
) -> list[dict]:
    """Fetch active neurons in the target department for dedup context."""
    query = select(Neuron).where(Neuron.is_active.is_(True))
    if department:
        query = query.where(Neuron.department == department)
    query = query.order_by(Neuron.layer, Neuron.id)
    result = await db.execute(query)
    neurons = result.scalars().all()

    return [
        {
            "id": n.id,
            "label": n.label,
            "layer": n.layer,
            "department": n.department,
            "role_key": n.role_key,
            "parent_id": n.parent_id,
            "summary": n.summary or "",
            "embedding": n.embedding,
        }
        for n in neurons
    ]


def _build_extraction_prompt(
    section: Section,
    section_text: str,
    doc_title: str,
    toc_outline: str,
    existing_neurons_summary: str,
    department: str | None,
    role_key: str | None,
) -> tuple[str, str]:
    """Build system + user prompt for knowledge extraction.

    Returns (system_prompt, user_message).
    """
    system_prompt = """You are a knowledge extraction specialist for Corvus, a hierarchical neuron graph system.

Your task: extract structured knowledge from a document section and propose neurons for the graph.

The graph has 6 layers:
- Layer 0: Department (top-level organizational unit)
- Layer 1: Role (functional role within a department)
- Layer 2: Task (specific task or process)
- Layer 3: System (system, tool, or standard involved)
- Layer 4: Decision (decision point, rule, or criterion)
- Layer 5: Output (deliverable, metric, or communication)

For each piece of extractable knowledge, output a JSON object with:
- "action": "create" (new neuron) or "update" (modify existing)
- "label": concise title (max 200 chars)
- "content": full knowledge content (detailed, actionable)
- "summary": one-line summary (max 500 chars)
- "layer": integer 2-5 (departments and roles are pre-existing)
- "node_type": "knowledge" | "process" | "standard" | "decision" | "metric"
- "parent_label": label of the parent neuron this should attach to (use existing neuron labels when possible)
- "reason": why this knowledge is valuable for the graph

For updates to existing neurons:
- "action": "update"
- "target_label": label of the existing neuron to update
- "field": "content" or "summary"
- "new_value": the updated text
- "reason": what new information this adds

Output ONLY a JSON array of objects. No markdown, no explanation outside the array."""

    dept_context = f"Target department: {department}" if department else "No specific department targeted"
    role_context = f"Target role: {role_key}" if role_key else ""

    user_message = f"""Document: "{doc_title}"
Section: "{section.title}" (Level {section.level})

Table of Contents:
{toc_outline}

{dept_context}
{role_context}

Existing neurons in this area (for deduplication and parent matching):
{existing_neurons_summary}

--- SECTION TEXT ---
{section_text[:MAX_SECTION_CHARS]}
--- END SECTION TEXT ---

Extract all valuable knowledge from this section as neuron proposals. Focus on:
1. Actionable processes, procedures, and best practices
2. Standards, rules, and decision criteria
3. Metrics, KPIs, and quality thresholds
4. System interactions and tool requirements

Skip: table of contents entries, blank sections, boilerplate disclaimers, pure definitions without actionable context.

If the section contains no extractable knowledge, return an empty array: []"""

    return system_prompt, user_message


def _build_toc_outline(structure: DocumentStructure) -> str:
    """Build a compact TOC string from the document structure."""
    lines = []
    for sec in structure.sections[:50]:  # Cap at 50 entries
        indent = "  " * (sec.level - 1)
        lines.append(f"{indent}{sec.title}")
    return "\n".join(lines) if lines else "(no TOC detected)"


def _build_neuron_summary(neurons: list[dict], limit: int = 80) -> str:
    """Build a compact summary of existing neurons for the prompt."""
    if not neurons:
        return "(no existing neurons in this area)"

    lines = []
    for n in neurons[:limit]:
        lines.append(f"- [{n['layer']}] {n['label']}: {n['summary'][:100]}")
    suffix = f"\n... and {len(neurons) - limit} more" if len(neurons) > limit else ""
    return "\n".join(lines) + suffix


async def extract_section_knowledge(
    section: Section,
    section_text: str,
    doc_title: str,
    toc_outline: str,
    existing_neurons: list[dict],
    department: str | None,
    role_key: str | None,
    model: str,
) -> tuple[list[dict], dict]:
    """Extract knowledge from one section via LLM.

    Returns (proposals_list, usage_dict).
    """
    neuron_summary = _build_neuron_summary(existing_neurons)
    system_prompt, user_message = _build_extraction_prompt(
        section, section_text, doc_title, toc_outline,
        neuron_summary, department, role_key,
    )

    result = await llm_chat(
        system_prompt=system_prompt,
        user_message=user_message,
        max_tokens=4096,
        model=model,
        timeout=300,
    )

    usage = {
        "input_tokens": result.get("input_tokens", 0),
        "output_tokens": result.get("output_tokens", 0),
        "cost_usd": result.get("cost_usd", 0.0),
    }

    # Parse LLM response
    text = result.get("text", "").strip()
    proposals = _parse_llm_proposals(text)

    return proposals, usage


def _parse_llm_proposals(text: str) -> list[dict]:
    """Parse the LLM's JSON array response, handling common formatting issues."""
    # Strip markdown code fences if present
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines)

    text = text.strip()
    if not text or text == "[]":
        return []

    try:
        parsed = json.loads(text)
        assert isinstance(parsed, list), "LLM response must be a JSON array"
        return parsed
    except (json.JSONDecodeError, AssertionError) as exc:
        logger.warning("Failed to parse LLM extraction response: %s", exc)
        return []


async def check_semantic_duplicates(
    proposals: list[dict],
    existing_neurons: list[dict],
) -> list[dict]:
    """Check each create proposal against existing neurons for semantic similarity.

    Adds a "duplicate_of" field to proposals that are too similar to existing neurons.
    Returns the annotated proposals list.
    """
    if not proposals or not existing_neurons:
        return proposals

    # Build embedding vectors for existing neurons that have them
    neurons_with_embeddings = [
        n for n in existing_neurons if n.get("embedding")
    ]
    if not neurons_with_embeddings:
        return proposals

    neuron_vecs = [json.loads(n["embedding"]) for n in neurons_with_embeddings]

    for prop in proposals:
        if prop.get("action") != "create":
            continue

        label = prop.get("label", "")
        content = prop.get("content", "")
        text_to_embed = f"{label}: {content[:500]}"

        prop_vec = embed_text(text_to_embed)
        similarities = batch_cosine_similarity(prop_vec, neuron_vecs)
        max_sim = max(similarities) if similarities else 0.0

        if max_sim >= DUPLICATE_THRESHOLD:
            max_idx = similarities.index(max_sim)
            dup_neuron = neurons_with_embeddings[max_idx]
            prop["duplicate_of"] = {
                "neuron_id": dup_neuron["id"],
                "label": dup_neuron["label"],
                "similarity": round(max_sim, 3),
            }

    return proposals


async def _resolve_parent_id(
    prop: dict,
    existing_neurons: list[dict],
    department: str | None,
    role_key: str | None,
) -> int | None:
    """Resolve a parent neuron ID from the proposal's parent_label."""
    parent_label = prop.get("parent_label", "")
    if not parent_label:
        # Default: find first matching role neuron
        for n in existing_neurons:
            if n["layer"] == 1 and (not department or n["department"] == department):
                if not role_key or n.get("role_key") == role_key:
                    return n["id"]
        # Fallback: first department neuron
        for n in existing_neurons:
            if n["layer"] == 0 and (not department or n["department"] == department):
                return n["id"]
        return None

    # Fuzzy match on label
    parent_label_lower = parent_label.lower().strip()
    best_match = None
    best_score = 0.0

    for n in existing_neurons:
        n_label = n["label"].lower().strip()
        if n_label == parent_label_lower:
            return n["id"]
        # Partial match score
        if parent_label_lower in n_label or n_label in parent_label_lower:
            score = len(min(parent_label_lower, n_label, key=len)) / len(max(parent_label_lower, n_label, key=len))
            if score > best_score:
                best_score = score
                best_match = n

    if best_match and best_score > 0.5:
        return best_match["id"]

    return None


async def _add_create_item(
    db: AsyncSession,
    proposal_id: int,
    prop: dict,
    job: DocumentIngestJob,
    section: Section,
    existing_neurons: list[dict],
) -> None:
    """Add a create ProposalItem for a single extracted neuron."""
    parent_id = await _resolve_parent_id(
        prop, existing_neurons, job.department, job.role_key,
    )
    spec = {
        "parent_id": parent_id,
        "layer": prop.get("layer", 3),
        "node_type": prop.get("node_type", "knowledge"),
        "label": prop.get("label", ""),
        "content": prop.get("content", ""),
        "summary": prop.get("summary", ""),
        "department": job.department,
        "role_key": job.role_key,
        "source_origin": "document",
        "source_type": job.source_type,
        "citation": job.citation,
        "source_url": job.source_url,
        "authority_level": job.authority_level,
    }
    reason = prop.get("reason", f"Extracted from {job.filename}, section: {section.title}")
    if prop.get("duplicate_of"):
        dup = prop["duplicate_of"]
        reason += f" [DUPLICATE WARNING: {dup['similarity']:.0%} similar to neuron #{dup['neuron_id']} '{dup['label']}']"

    db.add(ProposalItem(
        proposal_id=proposal_id,
        action="create",
        target_neuron_id=parent_id,
        neuron_spec_json=json.dumps(spec),
        reason=reason,
    ))


def _add_update_item(
    db: AsyncSession,
    proposal_id: int,
    prop: dict,
    job: DocumentIngestJob,
    section: Section,
    existing_neurons: list[dict],
) -> None:
    """Add an update ProposalItem for a single neuron field change."""
    target_label = prop.get("target_label", "")
    target_id = None
    for n in existing_neurons:
        if n["label"].lower().strip() == target_label.lower().strip():
            target_id = n["id"]
            break

    if target_id:
        db.add(ProposalItem(
            proposal_id=proposal_id,
            action="update",
            target_neuron_id=target_id,
            field=prop.get("field", "content"),
            old_value=None,
            new_value=prop.get("new_value", ""),
            reason=prop.get("reason", f"Updated from {job.filename}, section: {section.title}"),
        ))


async def create_section_proposal(
    job: DocumentIngestJob,
    section: Section,
    proposals: list[dict],
    existing_neurons: list[dict],
    db: AsyncSession,
) -> int | None:
    """Create an AutopilotProposal from extracted section proposals.

    Returns the proposal ID, or None if no valid proposals.
    """
    if not proposals:
        return None

    valid_proposals = [p for p in proposals if p.get("action") in ("create", "update")]
    if not valid_proposals:
        return None

    prompt_hash = hashlib.sha256(
        f"{job.id}:{section.id}:{job.model}".encode()
    ).hexdigest()

    n_creates = sum(1 for p in valid_proposals if p["action"] == "create")
    n_updates = sum(1 for p in valid_proposals if p["action"] == "update")
    n_dupes = sum(1 for p in valid_proposals if p.get("duplicate_of"))

    proposal = AutopilotProposal(
        state="proposed",
        gap_source="document_ingest",
        gap_description=f"Section: {section.title} (from {job.filename})",
        gap_evidence_json=json.dumps([{
            "source": "document_ingest",
            "document": job.filename,
            "section": section.title,
            "section_id": section.id,
            "job_id": job.id,
        }]),
        priority_score=0.5,
        llm_reasoning=f"Extracted {n_creates} new neurons and {n_updates} updates. {n_dupes} potential duplicates.",
        llm_model=job.model,
        prompt_hash=prompt_hash,
        eval_overall=0,
        eval_text=None,
    )
    db.add(proposal)
    await db.flush()

    for prop in valid_proposals:
        if prop["action"] == "create":
            await _add_create_item(db, proposal.id, prop, job, section, existing_neurons)
        elif prop["action"] == "update":
            _add_update_item(db, proposal.id, prop, job, section, existing_neurons)

    await db.flush()
    return proposal.id


@dataclass
class _ExtractionProgress:
    """Mutable accumulator for extraction progress across sections."""
    proposal_ids: list[int] = field(default_factory=list)
    total_cost: float = 0.0
    total_input: int = 0
    total_output: int = 0
    duplicates_flagged: int = 0
    errors: list[str] = field(default_factory=list)


async def _process_section(
    db: AsyncSession,
    job: DocumentIngestJob,
    section: Section,
    section_text: str,
    toc_outline: str,
    doc_title: str,
    existing_neurons: list[dict],
    progress: _ExtractionProgress,
) -> None:
    """Extract knowledge from one section and create a proposal."""
    proposals, usage = await extract_section_knowledge(
        section=section,
        section_text=section_text,
        doc_title=doc_title,
        toc_outline=toc_outline,
        existing_neurons=existing_neurons,
        department=job.department,
        role_key=job.role_key,
        model=job.model,
    )

    progress.total_cost += usage.get("cost_usd", 0.0)
    progress.total_input += usage.get("input_tokens", 0)
    progress.total_output += usage.get("output_tokens", 0)

    if proposals:
        proposals = await check_semantic_duplicates(proposals, existing_neurons)
        progress.duplicates_flagged += sum(1 for p in proposals if p.get("duplicate_of"))

    proposal_id = await create_section_proposal(
        job, section, proposals, existing_neurons, db,
    )
    if proposal_id is not None:
        progress.proposal_ids.append(proposal_id)


def _sync_progress(job: DocumentIngestJob, progress: _ExtractionProgress) -> None:
    """Write accumulated progress onto the job record."""
    job.cost_usd = progress.total_cost
    job.input_tokens = progress.total_input
    job.output_tokens = progress.total_output
    job.duplicates_flagged = progress.duplicates_flagged
    job.proposal_ids_json = json.dumps(progress.proposal_ids)
    job.errors_json = json.dumps(progress.errors)


async def run_document_extraction(job_id: str) -> None:
    """Orchestrator: run Pass 2 (LLM extraction) for a document ingest job.

    Pass 1 (structure) should already be complete when this is called.
    """
    async with async_session() as db:
        job = await db.get(DocumentIngestJob, job_id)
        if not job or job.status == "cancelled":
            return

        assert job.structure_json, "structure_json must be populated before extraction"
        assert job.extracted_text, "extracted_text must be populated before extraction"

        structure_data = json.loads(job.structure_json)
        structure = DocumentStructure(
            title=structure_data["title"],
            total_pages=structure_data.get("total_pages"),
            sections=[Section(**s) for s in structure_data["sections"]],
        )

        full_text = job.extracted_text
        toc_outline = _build_toc_outline(structure)

        job.status = "extracting"
        job.step = "Loading existing neurons..."
        job.total_sections = len(structure.sections)
        job.current_section = 0
        await db.commit()

        existing_neurons = await _get_existing_neurons(db, job.department)
        progress = _ExtractionProgress()

        for i, section in enumerate(structure.sections):
            await db.refresh(job)
            if job.status == "cancelled":
                logger.info("Job %s cancelled at section %d", job_id, i)
                return

            job.current_section = i + 1
            job.step = f"Extracting section {i + 1}/{len(structure.sections)}: {section.title[:80]}"
            await db.commit()

            section_text = full_text[section.char_start:section.char_end].strip()
            if not section_text or len(section_text) < 50:
                continue

            succeeded = False
            for attempt in range(MAX_RETRIES):
                try:
                    await _process_section(
                        db, job, section, section_text,
                        toc_outline, structure.title, existing_neurons, progress,
                    )
                    succeeded = True
                    break
                except Exception as exc:
                    if attempt < MAX_RETRIES - 1:
                        wait = RETRY_BACKOFF_BASE * (2 ** attempt)
                        logger.warning(
                            "Job %s section %s attempt %d failed: %s. Retrying in %ds...",
                            job_id, section.id, attempt + 1, exc, wait,
                        )
                        job.step = f"Retry {attempt + 2}/{MAX_RETRIES} for: {section.title[:60]}..."
                        await db.commit()
                        await asyncio.sleep(wait)
                    else:
                        error_msg = f"Section {section.id} ({section.title}): failed after {MAX_RETRIES} attempts. Last error: {exc}"
                        logger.error("Extraction failed in job %s: %s", job_id, error_msg)
                        progress.errors.append(error_msg)

            _sync_progress(job, progress)
            await db.commit()

        job.status = "done"
        job.step = f"Complete: {len(progress.proposal_ids)} proposals from {len(structure.sections)} sections"
        _sync_progress(job, progress)
        await db.commit()

        logger.info(
            "Document ingest job %s complete: %d proposals, $%.4f cost, %d duplicates",
            job_id, len(progress.proposal_ids), progress.total_cost, progress.duplicates_flagged,
        )
