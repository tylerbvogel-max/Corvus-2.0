"""Age-based review — stale neuron content surfacing.

Biological analogue: reconsolidation — memories become labile on recall,
allowing updating. Here we don't auto-modify (preserving traceability),
but surface neurons whose content hasn't been verified within a
source-type-appropriate threshold for human review.

Four metadata dimensions tracked:
  - created_at: when the neuron was first added
  - last_verified: when content was last confirmed accurate
  - last_accessed_at: when the neuron last fired in a query
  - source_origin: provenance (seed/autopilot/corvus/ingest)
"""

import json
from datetime import datetime, timedelta

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import Neuron, IntegrityScan, IntegrityFinding
from app.services.integrity import IntegrityFindingData, IntegrityScanResult


def _get_threshold_days(source_type: str, source_origin: str, overrides: dict | None = None) -> int:
    """Get staleness threshold in days based on source metadata."""
    overrides = overrides or {}
    # Engram-sourced neurons use regulatory threshold regardless of source_type
    if source_origin == "engram":
        return overrides.get("regulatory", settings.integrity_aging_regulatory_days)

    thresholds = {
        "regulatory": overrides.get("regulatory", settings.integrity_aging_regulatory_days),
        "operational": overrides.get("operational", settings.integrity_aging_operational_days),
    }
    assert isinstance(thresholds, dict), "Thresholds must be a dict"
    return thresholds.get(source_type, overrides.get("default", settings.integrity_aging_default_days))


def _compute_aging_priority(days_overdue: float, threshold_days: int, invocations: int) -> float:
    """Compute priority score for a stale neuron.

    Higher priority for neurons that are both stale and frequently used.
    """
    assert threshold_days > 0, "Threshold must be positive"
    base = min(2.0, days_overdue / threshold_days)
    # Boost for heavily-used neurons (important + stale = urgent)
    usage_boost = min(0.3, invocations / 100.0 * 0.3) if invocations > 0 else 0.0
    return min(1.0, (base + usage_boost) / 2.3)


def _classify_severity(days_overdue: float, threshold_days: int) -> str:
    """Classify severity based on how far past the threshold."""
    assert threshold_days > 0, "Threshold must be positive"
    ratio = days_overdue / threshold_days
    if ratio >= 2.0:
        return "critical"
    if ratio >= 1.0:
        return "warning"
    return "info"


def _build_aging_finding(
    neuron_id: int, label: str, department: str | None,
    source_type: str, source_origin: str,
    verified_at: datetime | None, created_at: datetime,
    last_accessed_at: datetime | None, invocations: int,
    threshold_days: int, now: datetime,
) -> IntegrityFindingData:
    """Build a finding for a single stale neuron."""
    reference_date = verified_at or created_at
    days_overdue = (now - reference_date).total_seconds() / 86400

    detail = {
        "neuron_id": neuron_id, "label": label, "department": department,
        "source_type": source_type, "source_origin": source_origin,
        "created_at": created_at.isoformat(),
        "last_verified": verified_at.isoformat() if verified_at else None,
        "last_accessed_at": last_accessed_at.isoformat() if last_accessed_at else None,
        "invocations": invocations,
        "threshold_days": threshold_days,
        "days_since_verification": round(days_overdue, 1),
        "never_verified": verified_at is None,
    }

    severity = _classify_severity(days_overdue, threshold_days)
    priority = _compute_aging_priority(days_overdue, threshold_days, invocations)

    never_tag = " (never verified)" if verified_at is None else ""
    assert neuron_id > 0, "Neuron ID must be positive"

    return IntegrityFindingData(
        finding_type="stale_content",
        severity=severity,
        priority_score=priority,
        description=(
            f"Stale: '{label}' — {round(days_overdue)} days since verification"
            f"{never_tag}, {invocations} invocations"
        ),
        detail_json=json.dumps(detail),
        neuron_ids=[neuron_id],
    )


async def scan_stale_neurons(
    db: AsyncSession,
    scope: str = "global",
    staleness_overrides: dict | None = None,
    include_never_verified: bool = True,
    min_invocations: int = 0,
    initiated_by: str | None = None,
) -> tuple[IntegrityScan, IntegrityScanResult]:
    """Scan for neurons whose content hasn't been verified recently.

    Staleness thresholds vary by source_type:
      - regulatory: 3 years (1095 days)
      - operational: 1.5 years (548 days)
      - default: 2 years (730 days)
    """
    scan = IntegrityScan(
        scan_type="aging_review", scope=scope, status="running",
        parameters_json=json.dumps({
            "staleness_overrides": staleness_overrides,
            "include_never_verified": include_never_verified,
            "min_invocations": min_invocations,
        }),
        initiated_by=initiated_by,
    )
    db.add(scan)
    await db.flush()

    neurons = await _load_candidate_neurons(db, scope, min_invocations)
    now = datetime.utcnow()
    findings_data = _evaluate_staleness(
        neurons, now, staleness_overrides, include_never_verified,
    )

    _persist_findings(db, scan, findings_data)

    scan.status = "completed"
    scan.completed_at = now
    scan.findings_count = len(findings_data)
    await db.commit()

    return scan, IntegrityScanResult(
        scan_type="aging_review", scope=scope,
        findings=findings_data,
        extra={"neurons_checked": len(neurons), "stale_found": len(findings_data)},
    )


async def _load_candidate_neurons(
    db: AsyncSession, scope: str, min_invocations: int,
) -> list[tuple]:
    """Load active neurons with their aging metadata."""
    stmt = (
        select(
            Neuron.id, Neuron.label, Neuron.department,
            Neuron.source_type, Neuron.source_origin,
            Neuron.last_verified, Neuron.created_at,
            Neuron.last_accessed_at, Neuron.invocations,
        )
        .where(Neuron.is_active.is_(True))
        .where(Neuron.invocations >= min_invocations)
    )
    if scope.startswith("department:"):
        dept = scope.split(":", 1)[1]
        stmt = stmt.where(Neuron.department == dept)
    elif scope.startswith("layer:"):
        layer_num = int(scope.split(":", 1)[1])
        stmt = stmt.where(Neuron.layer == layer_num)

    result = await db.execute(stmt)
    rows = result.all()
    assert isinstance(rows, list), "Must return a list"
    return rows


def _evaluate_staleness(
    neurons: list[tuple],
    now: datetime,
    staleness_overrides: dict | None,
    include_never_verified: bool,
) -> list[IntegrityFindingData]:
    """Evaluate each neuron against its source-appropriate threshold."""
    findings: list[IntegrityFindingData] = []

    for row in neurons:
        nid, label, dept, src_type, src_origin, verified, created, accessed, invocations = row
        threshold = _get_threshold_days(src_type, src_origin, staleness_overrides)
        reference_date = verified or created
        days_since = (now - reference_date).total_seconds() / 86400

        is_stale = days_since >= threshold
        is_never_verified = verified is None and (now - created).days > 90

        if is_stale or (include_never_verified and is_never_verified):
            findings.append(_build_aging_finding(
                nid, label, dept, src_type, src_origin,
                verified, created, accessed, invocations, threshold, now,
            ))

    findings.sort(key=lambda f: f.priority_score, reverse=True)
    return findings


def _persist_findings(
    db: AsyncSession,
    scan: IntegrityScan,
    findings_data: list[IntegrityFindingData],
) -> None:
    """Persist findings to the database."""
    assert scan.id is not None, "Scan must be flushed"
    for fd in findings_data:
        finding = IntegrityFinding(
            scan_id=scan.id, finding_type=fd.finding_type,
            severity=fd.severity, priority_score=fd.priority_score,
            description=fd.description, detail_json=fd.detail_json,
            neuron_ids_json=json.dumps(fd.neuron_ids),
        )
        db.add(finding)
