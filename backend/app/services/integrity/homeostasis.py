"""Synaptic homeostasis — multiplicative weight renormalization.

Biological analogue: during slow-wave sleep, the brain globally downscales
synaptic weights by a proportion. Strong connections stay strong (relatively)
while weak ones compress toward zero. This prevents weight inflation from
continuous additive learning without erasing rank ordering.

All scans are dry-run by default. The apply step creates proposals for
human review via the standard proposal workflow.
"""

import json
from datetime import datetime

import numpy as np
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import NeuronEdge, Neuron, AutopilotProposal, ProposalItem, IntegrityScan, IntegrityFinding
from app.services.integrity import IntegrityFindingData, IntegrityScanResult


def _compute_distribution(weights: np.ndarray) -> dict:
    """Compute weight distribution statistics."""
    assert len(weights) >= 0, "Weights array must exist"
    if len(weights) == 0:
        return {"count": 0, "mean": 0, "median": 0, "std": 0,
                "p10": 0, "p25": 0, "p75": 0, "p90": 0, "max": 0}
    return {
        "count": int(len(weights)),
        "mean": float(np.mean(weights)),
        "median": float(np.median(weights)),
        "std": float(np.std(weights)),
        "p10": float(np.percentile(weights, 10)),
        "p25": float(np.percentile(weights, 25)),
        "p75": float(np.percentile(weights, 75)),
        "p90": float(np.percentile(weights, 90)),
        "max": float(np.max(weights)),
    }


async def _load_edges_for_scope(
    db: AsyncSession, scope: str,
) -> list[tuple[int, int, float]]:
    """Load (source_id, target_id, weight) tuples matching scope."""
    stmt = select(NeuronEdge.source_id, NeuronEdge.target_id, NeuronEdge.weight)

    if scope.startswith("department:"):
        dept = scope.split(":", 1)[1]
        # Join to neurons to filter by department
        stmt = (
            select(NeuronEdge.source_id, NeuronEdge.target_id, NeuronEdge.weight)
            .join(Neuron, NeuronEdge.source_id == Neuron.id)
            .where(Neuron.department == dept)
        )
    elif scope.startswith("layer:"):
        layer_num = int(scope.split(":", 1)[1])
        stmt = (
            select(NeuronEdge.source_id, NeuronEdge.target_id, NeuronEdge.weight)
            .join(Neuron, NeuronEdge.source_id == Neuron.id)
            .where(Neuron.layer == layer_num)
        )

    result = await db.execute(stmt)
    rows = result.all()
    assert isinstance(rows, list), "Query result must be iterable"
    return [(r[0], r[1], r[2]) for r in rows]


def _build_homeostasis_finding(
    edges: list[tuple[int, int, float]],
    sf: float,
    ft: float,
) -> tuple[IntegrityFindingData, dict, dict]:
    """Build finding data from edge weights and rescaling parameters.

    Returns (finding_data, before_distribution, after_distribution).
    """
    weights = np.array([e[2] for e in edges], dtype=np.float32)
    before_dist = _compute_distribution(weights)
    after_weights = weights * sf
    after_dist = _compute_distribution(after_weights)
    below_floor_count = int(np.sum(after_weights < ft))

    detail = {
        "before_distribution": before_dist, "after_distribution": after_dist,
        "scale_factor": sf, "floor_threshold": ft,
        "total_edges": len(edges), "below_floor_count": below_floor_count,
    }
    severity = "warning" if below_floor_count > len(edges) * 0.3 else "info"

    assert len(edges) > 0, "Must have edges to build finding"
    assert before_dist["count"] > 0, "Distribution must be non-empty"

    finding_data = IntegrityFindingData(
        finding_type="weight_inflation", severity=severity,
        priority_score=min(1.0, before_dist["mean"] / 0.5),
        description=(
            f"Weight renormalization preview: {len(edges)} edges, "
            f"scale {sf}×. Mean {before_dist['mean']:.3f} → {after_dist['mean']:.3f}. "
            f"{below_floor_count} edges would fall below floor ({ft})."
        ),
        detail_json=json.dumps(detail),
        edge_ids=[(e[0], e[1]) for e in edges],
    )
    return finding_data, before_dist, after_dist


async def scan_homeostasis(
    db: AsyncSession,
    scope: str = "global",
    scale_factor: float | None = None,
    floor_threshold: float | None = None,
    initiated_by: str | None = None,
) -> tuple[IntegrityScan, IntegrityScanResult]:
    """Dry-run homeostasis scan: compute before/after weight distributions.

    Returns the persisted IntegrityScan and the scan result with findings.
    Does NOT modify any edge weights.
    """
    sf = scale_factor if scale_factor is not None else settings.integrity_homeostasis_default_scale
    ft = floor_threshold if floor_threshold is not None else settings.integrity_homeostasis_floor_threshold
    assert 0.0 < sf <= 1.0, f"scale_factor must be in (0, 1], got {sf}"
    assert ft >= 0.0, f"floor_threshold must be non-negative, got {ft}"

    scan = IntegrityScan(
        scan_type="homeostasis", scope=scope, status="running",
        parameters_json=json.dumps({"scale_factor": sf, "floor_threshold": ft}),
        initiated_by=initiated_by,
    )
    db.add(scan)
    await db.flush()

    edges = await _load_edges_for_scope(db, scope)
    if not edges:
        scan.status = "completed"
        scan.completed_at = datetime.utcnow()
        scan.findings_count = 0
        await db.commit()
        return scan, IntegrityScanResult(scan_type="homeostasis", scope=scope)

    finding_data, before_dist, after_dist = _build_homeostasis_finding(edges, sf, ft)

    finding = IntegrityFinding(
        scan_id=scan.id, finding_type=finding_data.finding_type,
        severity=finding_data.severity, priority_score=finding_data.priority_score,
        description=finding_data.description, detail_json=finding_data.detail_json,
        edge_ids_json=json.dumps(finding_data.edge_ids[:100]),
    )
    db.add(finding)

    scan.status = "completed"
    scan.completed_at = datetime.utcnow()
    scan.findings_count = 1
    await db.commit()

    return scan, IntegrityScanResult(
        scan_type="homeostasis", scope=scope,
        findings=[finding_data],
        extra={"before": before_dist, "after": after_dist},
    )


async def apply_homeostasis(
    db: AsyncSession,
    scan_id: int,
    reviewer: str = "system",
) -> AutopilotProposal:
    """Create a proposal from a homeostasis scan for human review.

    Reads the scan parameters, creates ProposalItems for each edge rescale.
    The proposal goes through the standard approve → apply workflow.
    """
    scan = await db.get(IntegrityScan, scan_id)
    assert scan is not None, f"Scan {scan_id} not found"
    assert scan.scan_type == "homeostasis", "Scan must be homeostasis type"
    assert scan.status == "completed", "Scan must be completed before apply"

    params = json.loads(scan.parameters_json or "{}")
    sf = params.get("scale_factor", settings.integrity_homeostasis_default_scale)

    # Load edges for this scope
    edges = await _load_edges_for_scope(db, scan.scope)
    assert len(edges) > 0, "No edges to rescale"

    # Create proposal
    proposal = AutopilotProposal(
        state="proposed",
        gap_source="integrity_homeostasis",
        gap_description=f"Homeostasis weight renormalization (×{sf}) on scope '{scan.scope}'",
        gap_evidence_json=json.dumps([{
            "signal": "weight_homeostasis",
            "metric_value": sf,
            "threshold": settings.integrity_homeostasis_floor_threshold,
            "neuron_ids": [],
        }]),
        priority_score=0.5,
        llm_reasoning=f"Multiplicative rescaling by {sf} to prevent weight inflation.",
    )
    db.add(proposal)
    await db.flush()

    # Create a ProposalItem per edge
    for source_id, target_id, old_weight in edges:
        new_weight = old_weight * sf
        item = ProposalItem(
            proposal_id=proposal.id,
            action="rescale",
            target_neuron_id=source_id,
            field="edge_weight",
            old_value=str(old_weight),
            new_value=str(new_weight),
            neuron_spec_json=json.dumps({
                "source_id": source_id,
                "target_id": target_id,
                "old_weight": old_weight,
                "new_weight": new_weight,
            }),
            reason=f"Homeostasis rescale ×{sf}",
        )
        db.add(item)

    # Link findings to this proposal
    for finding in (scan.findings or []):
        finding.status = "proposed"
        finding.proposal_id = proposal.id

    await db.commit()
    await db.refresh(proposal)
    return proposal
