"""Action: edge.link — create a new NeuronEdge with tiered storage.

Wraps the logic from `backend/app/routers/proposals.py:_apply_link_item` and
also covers the admin ingest edge-creation path. Edges above the promotion
threshold go into the neuron_edges table; below it they get stored as JSONB
in the holder neuron's weak_edges column.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.middleware.rbac import UserIdentity
from app.models import Action, NeuronEdge


class EdgeLinkInput(BaseModel):
    source_id: int
    target_id: int
    weight: float = Field(0.15, ge=0.0, le=1.0)
    co_fire_count: int = Field(1, ge=0)
    edge_type: str = Field("pyramidal", max_length=50)
    source: str = Field("integrity_completion", max_length=80)
    context: str = ""
    last_updated_query: int = 0


async def handle_edge_link(
    payload: EdgeLinkInput,
    actor: UserIdentity,
    db: AsyncSession,
    action_row: Action,
) -> dict[str, Any]:
    """Create an edge, routing to promoted table or weak_edges JSONB."""
    from app.services.edge_tier import (
        is_promoted, upsert_weak_edge, delete_weak_edge,
    )

    promoted = is_promoted(payload.weight, payload.co_fire_count)

    if promoted:
        edge = NeuronEdge(
            source_id=payload.source_id,
            target_id=payload.target_id,
            weight=payload.weight,
            co_fire_count=payload.co_fire_count,
            edge_type=payload.edge_type,
            source=payload.source,
            context=payload.context,
        )
        db.add(edge)
        await delete_weak_edge(db, payload.source_id, payload.target_id)
    else:
        data = {
            "w": payload.weight,
            "t": payload.edge_type,
            "c": payload.co_fire_count,
            "s": payload.source,
            "q": payload.last_updated_query,
        }
        await upsert_weak_edge(
            db, payload.source_id, payload.target_id, data,
        )

    return {
        "audit": {
            "source_id": payload.source_id,
            "target_id": payload.target_id,
            "weight": payload.weight,
            "promoted": promoted,
        },
        "payload": {"promoted": promoted},
    }
