"""Action: edge.rescale — rescale an existing NeuronEdge weight.

Wraps the logic from `backend/app/routers/proposals.py:_apply_rescale_item`.
Handles tier demotion when weight drops below the promotion threshold.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.middleware.rbac import UserIdentity
from app.models import Action, NeuronEdge


class EdgeRescaleInput(BaseModel):
    source_id: int
    target_id: int
    new_weight: float = Field(..., ge=0.0, le=1.0)


async def handle_edge_rescale(
    payload: EdgeRescaleInput,
    actor: UserIdentity,
    db: AsyncSession,
    action_row: Action,
) -> dict[str, Any]:
    """Rescale an edge weight and demote if below threshold."""
    edge = await db.get(NeuronEdge, (payload.source_id, payload.target_id))
    if edge is None:
        return {
            "audit": {
                "source_id": payload.source_id,
                "target_id": payload.target_id,
                "skipped": "edge_not_found",
            },
            "payload": {"rescaled": False},
        }

    old_weight = edge.weight
    edge.weight = payload.new_weight
    edge.last_adjusted = datetime.utcnow()

    from app.services.edge_tier import maybe_demote
    await maybe_demote(
        db, payload.source_id, payload.target_id,
        payload.new_weight, edge.co_fire_count,
    )

    return {
        "audit": {
            "source_id": payload.source_id,
            "target_id": payload.target_id,
            "old_weight": old_weight,
            "new_weight": payload.new_weight,
        },
        "payload": {"rescaled": True},
    }
