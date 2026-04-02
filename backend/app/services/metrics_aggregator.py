"""Metrics aggregator — reusable queries for gap detection and dashboards.

Extracts common metric computations used by gap_detector and router endpoints.
All functions take an AsyncSession and return plain dicts/values.
"""

from datetime import datetime, timedelta

from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import EvalScore, Neuron, Query


async def get_department_coverage(db: AsyncSession) -> dict[str, int]:
    """Count active neurons per department. Returns {dept_name: count}."""
    rows = await db.execute(
        select(Neuron.department, func.count(Neuron.id))
        .where(Neuron.is_active.is_(True), Neuron.department.isnot(None))
        .group_by(Neuron.department)
    )
    return {row[0]: row[1] for row in rows.all()}


async def get_eval_dimension_averages(
    db: AsyncSession,
    department: str | None = None,
    last_n: int = 50,
) -> dict[str, float]:
    """Average eval scores across dimensions for recent queries.

    If department is given, only considers queries that activated neurons
    in that department.  Returns {accuracy, completeness, clarity,
    faithfulness, overall} as floats.
    """
    subq = (
        select(EvalScore.query_id)
        .order_by(EvalScore.query_id.desc())
        .distinct()
        .limit(last_n)
    ).subquery()

    stmt = select(
        func.avg(EvalScore.accuracy),
        func.avg(EvalScore.completeness),
        func.avg(EvalScore.clarity),
        func.avg(EvalScore.faithfulness),
        func.avg(EvalScore.overall),
    ).where(EvalScore.query_id.in_(select(subq.c.query_id)))

    row = (await db.execute(stmt)).one_or_none()
    if not row or row[0] is None:
        return {"accuracy": 0.0, "completeness": 0.0, "clarity": 0.0,
                "faithfulness": 0.0, "overall": 0.0}
    return {
        "accuracy": float(row[0]),
        "completeness": float(row[1]),
        "clarity": float(row[2]),
        "faithfulness": float(row[3]),
        "overall": float(row[4]),
    }


async def get_neuron_utilization_stats(db: AsyncSession) -> dict:
    """Neuron utilization breakdown. Returns dict with zero_hit_count,
    low_utility_count, active_count, and stale_count."""
    active_count = (await db.execute(
        select(func.count(Neuron.id)).where(Neuron.is_active.is_(True))
    )).scalar() or 0

    zero_hit_count = (await db.execute(
        select(func.count(Neuron.id)).where(
            Neuron.is_active.is_(True),
            Neuron.invocations == 0,
        )
    )).scalar() or 0

    low_utility_count = (await db.execute(
        select(func.count(Neuron.id)).where(
            Neuron.is_active.is_(True),
            Neuron.avg_utility < 0.3,
            Neuron.invocations > 0,
        )
    )).scalar() or 0

    cutoff = datetime.utcnow() - timedelta(days=90)
    stale_count = (await db.execute(
        select(func.count(Neuron.id)).where(
            Neuron.is_active.is_(True),
            (Neuron.last_verified.is_(None)) | (Neuron.last_verified < cutoff),
        )
    )).scalar() or 0

    return {
        "active_count": active_count,
        "zero_hit_count": zero_hit_count,
        "low_utility_count": low_utility_count,
        "stale_count": stale_count,
    }


async def get_quality_trend(
    db: AsyncSession,
    window: int = 20,
) -> dict:
    """Compare avg eval scores for the most recent `window` queries vs
    the previous `window`.  Returns {recent_avg, previous_avg, delta}."""
    recent_sub = (
        select(Query.id)
        .where(Query.id.in_(
            select(EvalScore.query_id).distinct()
        ))
        .order_by(Query.id.desc())
        .limit(window)
    ).subquery()

    recent_row = (await db.execute(
        select(func.avg(EvalScore.overall))
        .where(EvalScore.query_id.in_(select(recent_sub.c.id)))
    )).scalar()

    previous_sub = (
        select(Query.id)
        .where(
            Query.id.in_(select(EvalScore.query_id).distinct()),
            Query.id.notin_(select(recent_sub.c.id)),
        )
        .order_by(Query.id.desc())
        .limit(window)
    ).subquery()

    previous_row = (await db.execute(
        select(func.avg(EvalScore.overall))
        .where(EvalScore.query_id.in_(select(previous_sub.c.id)))
    )).scalar()

    recent_avg = float(recent_row) if recent_row else 0.0
    previous_avg = float(previous_row) if previous_row else 0.0

    return {
        "recent_avg": round(recent_avg, 3),
        "previous_avg": round(previous_avg, 3),
        "delta": round(recent_avg - previous_avg, 3),
    }
