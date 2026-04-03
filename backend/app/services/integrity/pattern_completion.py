"""Pattern completion — missing semantic connection detection.

Biological analogue: the hippocampal CA3 region takes partial or degraded
inputs and reconstructs complete patterns. For the neuron graph, this means
identifying neuron pairs that are semantically similar but have no co-firing
edge between them — connections the graph is missing.

This is top-down (semantic inference) rather than bottom-up (observed co-firing).
"""

import json
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import NeuronEdge, Neuron, IntegrityScan, IntegrityFinding
from app.services.integrity import IntegrityFindingData, IntegrityScanResult
from app.services.integrity.similarity import (
    load_neuron_embeddings, compute_pairwise_similarity,
    extract_pairs_above_threshold, SimilarPair,
)


async def _load_existing_edges(db: AsyncSession) -> set[tuple[int, int]]:
    """Load all existing edge pairs as a set for O(1) lookup."""
    result = await db.execute(
        select(NeuronEdge.source_id, NeuronEdge.target_id)
    )
    edges = set()
    for row in result.all():
        edges.add((row[0], row[1]))
        edges.add((row[1], row[0]))  # Bidirectional lookup
    assert isinstance(edges, set), "Must return a set"
    return edges


async def _load_parent_chains(db: AsyncSession) -> dict[int, int | None]:
    """Load neuron parent_id map for same-parent filtering."""
    result = await db.execute(
        select(Neuron.id, Neuron.parent_id).where(Neuron.is_active.is_(True))
    )
    parent_map = {row[0]: row[1] for row in result.all()}
    assert isinstance(parent_map, dict), "Must return a dict"
    return parent_map


def _shares_parent_chain(
    a_id: int, b_id: int, parent_map: dict[int, int | None],
) -> bool:
    """Check if two neurons are in the same parent-child chain."""
    # Direct parent-child
    if parent_map.get(a_id) == b_id or parent_map.get(b_id) == a_id:
        return True
    # Same parent
    a_parent = parent_map.get(a_id)
    b_parent = parent_map.get(b_id)
    if a_parent is not None and a_parent == b_parent:
        return True
    return False


def _build_connection_finding(pair: SimilarPair) -> IntegrityFindingData:
    """Build a finding for a missing connection pair."""
    cross_dept = pair.a_department != pair.b_department
    edge_type = "pyramidal" if cross_dept else "stellate"
    assert pair.similarity > 0.0, "Pair must have positive similarity"

    detail = {
        "neuron_a": {"id": pair.neuron_a_id, "label": pair.a_label,
                     "department": pair.a_department, "layer": pair.a_layer},
        "neuron_b": {"id": pair.neuron_b_id, "label": pair.b_label,
                     "department": pair.b_department, "layer": pair.b_layer},
        "cosine_similarity": round(pair.similarity, 4),
        "suggested_edge_type": edge_type,
        "cross_department": cross_dept,
    }

    return IntegrityFindingData(
        finding_type="missing_connection",
        severity="info",
        priority_score=pair.similarity,
        description=(
            f"Missing link: '{pair.a_label}' ↔ '{pair.b_label}' "
            f"(similarity {pair.similarity:.3f}, suggest {edge_type})"
        ),
        detail_json=json.dumps(detail),
        neuron_ids=[pair.neuron_a_id, pair.neuron_b_id],
    )


async def scan_missing_connections(
    db: AsyncSession,
    scope: str = "global",
    similarity_threshold: float | None = None,
    max_suggestions: int = 50,
    exclude_same_parent: bool = True,
    initiated_by: str | None = None,
) -> tuple[IntegrityScan, IntegrityScanResult]:
    """Scan for semantically similar neurons with no co-firing edge.

    Dry-run only — creates findings but does not modify the graph.
    """
    threshold = similarity_threshold or settings.integrity_completion_threshold
    assert 0.0 < threshold <= 1.0, f"threshold must be in (0, 1], got {threshold}"

    scan = IntegrityScan(
        scan_type="pattern_completion", scope=scope, status="running",
        parameters_json=json.dumps({
            "similarity_threshold": threshold, "max_suggestions": max_suggestions,
            "exclude_same_parent": exclude_same_parent,
        }),
        initiated_by=initiated_by,
    )
    db.add(scan)
    await db.flush()

    metadata, matrix = await load_neuron_embeddings(
        db, scope=scope, max_neurons=settings.integrity_max_scan_neurons,
    )
    existing_edges = await _load_existing_edges(db)

    if matrix.shape[0] < 2:
        scan.status = "completed"
        scan.completed_at = datetime.utcnow()
        scan.findings_count = 0
        await db.commit()
        return scan, IntegrityScanResult(scan_type="pattern_completion", scope=scope)

    sim_matrix = compute_pairwise_similarity(matrix)
    # Fetch more than needed to account for filtering
    candidates = extract_pairs_above_threshold(
        sim_matrix, metadata, threshold, max_suggestions * 5,
    )

    parent_map = await _load_parent_chains(db) if exclude_same_parent else {}

    filtered = _filter_candidates(
        candidates, existing_edges, parent_map, exclude_same_parent,
    )
    filtered = filtered[:max_suggestions]

    findings_data = [_build_connection_finding(p) for p in filtered]
    _persist_findings(db, scan, findings_data)

    scan.status = "completed"
    scan.completed_at = datetime.utcnow()
    scan.findings_count = len(findings_data)
    await db.commit()

    return scan, IntegrityScanResult(
        scan_type="pattern_completion", scope=scope,
        findings=findings_data,
        extra={"neurons_scanned": matrix.shape[0], "suggestions": len(filtered)},
    )


def _filter_candidates(
    candidates: list[SimilarPair],
    existing_edges: set[tuple[int, int]],
    parent_map: dict[int, int | None],
    exclude_same_parent: bool,
) -> list[SimilarPair]:
    """Filter out pairs that already have edges or share parent chains."""
    assert isinstance(candidates, list), "Candidates must be a list"
    filtered: list[SimilarPair] = []
    for pair in candidates:
        # Skip if edge already exists
        if (pair.neuron_a_id, pair.neuron_b_id) in existing_edges:
            continue
        # Skip if same parent chain
        if exclude_same_parent and _shares_parent_chain(
            pair.neuron_a_id, pair.neuron_b_id, parent_map,
        ):
            continue
        filtered.append(pair)
    return filtered


def _persist_findings(
    db: AsyncSession,
    scan: IntegrityScan,
    findings_data: list[IntegrityFindingData],
) -> None:
    """Persist IntegrityFindingData objects as IntegrityFinding rows."""
    assert scan.id is not None, "Scan must be flushed"
    for fd in findings_data:
        finding = IntegrityFinding(
            scan_id=scan.id, finding_type=fd.finding_type,
            severity=fd.severity, priority_score=fd.priority_score,
            description=fd.description, detail_json=fd.detail_json,
            neuron_ids_json=json.dumps(fd.neuron_ids),
        )
        db.add(finding)
