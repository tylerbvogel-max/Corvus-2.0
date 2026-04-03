"""Pattern separation — near-duplicate neuron detection.

Biological analogue: the dentate gyrus takes similar inputs and makes their
internal representations more distinct. When two neurons encode essentially
the same knowledge, they should be merged or differentiated with additional
context to clarify what makes each unique.

Resolution paths:
  - Merge: deactivate duplicate, update survivor content, transfer edges
  - Differentiate: add distinguishing context to both neurons
"""

import json
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import IntegrityScan, IntegrityFinding
from app.services.integrity import IntegrityFindingData, IntegrityScanResult
from app.services.integrity.similarity import (
    load_neuron_embeddings, compute_pairwise_similarity,
    extract_pairs_above_threshold, SimilarPair,
)


def _classify_severity(similarity: float) -> str:
    """Classify finding severity based on similarity score."""
    assert 0.0 <= similarity <= 1.0, f"Similarity must be in [0,1], got {similarity}"
    if similarity >= 0.98:
        return "critical"
    if similarity >= 0.95:
        return "warning"
    return "info"


def _build_duplicate_finding(pair: SimilarPair) -> IntegrityFindingData:
    """Build a finding for a single near-duplicate pair."""
    cross_dept = pair.a_department != pair.b_department
    assert pair.similarity > 0.0, "Pair must have positive similarity"

    detail = {
        "neuron_a": {"id": pair.neuron_a_id, "label": pair.a_label,
                     "department": pair.a_department, "layer": pair.a_layer},
        "neuron_b": {"id": pair.neuron_b_id, "label": pair.b_label,
                     "department": pair.b_department, "layer": pair.b_layer},
        "cosine_similarity": round(pair.similarity, 4),
        "cross_department": cross_dept,
    }

    return IntegrityFindingData(
        finding_type="near_duplicate",
        severity=_classify_severity(pair.similarity),
        priority_score=pair.similarity,
        description=(
            f"Near-duplicate: '{pair.a_label}' ↔ '{pair.b_label}' "
            f"(similarity {pair.similarity:.3f}"
            f"{', cross-dept' if cross_dept else ''})"
        ),
        detail_json=json.dumps(detail),
        neuron_ids=[pair.neuron_a_id, pair.neuron_b_id],
    )


async def scan_duplicates(
    db: AsyncSession,
    scope: str = "global",
    similarity_threshold: float | None = None,
    max_pairs: int = 100,
    cross_department_only: bool = False,
    initiated_by: str | None = None,
) -> tuple[IntegrityScan, IntegrityScanResult]:
    """Scan for near-duplicate neurons using embedding similarity.

    Dry-run only — creates findings but does not modify the graph.
    """
    threshold = similarity_threshold or settings.integrity_duplicate_threshold
    assert 0.0 < threshold <= 1.0, f"threshold must be in (0, 1], got {threshold}"
    assert max_pairs > 0, "max_pairs must be positive"

    scan = IntegrityScan(
        scan_type="pattern_separation", scope=scope, status="running",
        parameters_json=json.dumps({
            "similarity_threshold": threshold, "max_pairs": max_pairs,
            "cross_department_only": cross_department_only,
        }),
        initiated_by=initiated_by,
    )
    db.add(scan)
    await db.flush()

    metadata, matrix = await load_neuron_embeddings(
        db, scope=scope, max_neurons=settings.integrity_max_scan_neurons,
    )

    if matrix.shape[0] < 2:
        scan.status = "completed"
        scan.completed_at = datetime.utcnow()
        scan.findings_count = 0
        await db.commit()
        return scan, IntegrityScanResult(scan_type="pattern_separation", scope=scope)

    sim_matrix = compute_pairwise_similarity(matrix)
    pairs = extract_pairs_above_threshold(sim_matrix, metadata, threshold, max_pairs * 2)

    if cross_department_only:
        pairs = [p for p in pairs if p.a_department != p.b_department]
    pairs = pairs[:max_pairs]

    findings_data = [_build_duplicate_finding(p) for p in pairs]

    _persist_findings(db, scan, findings_data)

    scan.status = "completed"
    scan.completed_at = datetime.utcnow()
    scan.findings_count = len(findings_data)
    await db.commit()

    return scan, IntegrityScanResult(
        scan_type="pattern_separation", scope=scope,
        findings=findings_data,
        extra={"neurons_scanned": matrix.shape[0], "pairs_found": len(pairs)},
    )


def _persist_findings(
    db: AsyncSession,
    scan: IntegrityScan,
    findings_data: list[IntegrityFindingData],
) -> None:
    """Persist IntegrityFindingData objects as IntegrityFinding rows."""
    assert scan.id is not None, "Scan must be flushed before persisting findings"
    for fd in findings_data:
        finding = IntegrityFinding(
            scan_id=scan.id, finding_type=fd.finding_type,
            severity=fd.severity, priority_score=fd.priority_score,
            description=fd.description, detail_json=fd.detail_json,
            neuron_ids_json=json.dumps(fd.neuron_ids),
            edge_ids_json=json.dumps(fd.edge_ids) if fd.edge_ids else None,
        )
        db.add(finding)
