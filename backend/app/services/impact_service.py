"""Graph-based impact analysis with depth-tiered blast radius.

BFS traversal through co-firing edges from seed neurons, classifying
results as direct (1-hop), indirect (2-hop), or transitive (3-hop).
Confidence per neuron: seed_similarity * product of edge weights along path.
"""

from collections import deque
from types import MappingProxyType

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import Neuron, NeuronEdge

# Depth tier labels (JPL-6: immutable mapping)
_DEPTH_TIERS = MappingProxyType({1: "direct", 2: "indirect", 3: "transitive"})


async def _load_seed_info(
    db: AsyncSession, seed_ids: list[int]
) -> dict[int, dict]:
    """Fetch seed neuron metadata from DB."""
    result = await db.execute(
        select(Neuron.id, Neuron.label, Neuron.department, Neuron.layer, Neuron.parent_id)
        .where(Neuron.id.in_(seed_ids))
    )
    assert result is not None, "Seed neuron query returned None"
    return {
        r[0]: {"id": r[0], "label": r[1], "department": r[2], "layer": r[3], "parent_id": r[4]}
        for r in result.all()
    }


async def _bfs_traverse(
    db: AsyncSession,
    seed_ids: list[int],
    seed_similarities: dict[int, float],
    max_hops: int,
    min_edge_weight: float,
) -> dict[int, tuple[int, float]]:
    """BFS through co-firing edges, returning visited: {nid: (depth, confidence)}."""
    visited: dict[int, tuple[int, float]] = {}
    queue: deque[tuple[int, int, float]] = deque()

    for nid in seed_ids:
        sim = seed_similarities.get(nid, 1.0)
        visited[nid] = (0, sim)
        queue.append((nid, 0, sim))

    for _safety in range(100_000):  # bounded loop (JPL-2)
        if not queue:
            break
        current_id, depth, confidence = queue.popleft()
        if depth >= max_hops:
            continue

        edge_result = await db.execute(
            select(NeuronEdge).where(and_(
                NeuronEdge.weight >= min_edge_weight,
                or_(NeuronEdge.source_id == current_id, NeuronEdge.target_id == current_id),
            ))
        )
        for edge in edge_result.scalars().all():
            neighbor_id = edge.target_id if edge.source_id == current_id else edge.source_id
            new_depth = depth + 1
            new_confidence = confidence * edge.weight

            if neighbor_id in visited:
                ex_depth, ex_conf = visited[neighbor_id]
                if new_depth < ex_depth or (new_depth == ex_depth and new_confidence > ex_conf):
                    visited[neighbor_id] = (new_depth, new_confidence)
                continue

            visited[neighbor_id] = (new_depth, new_confidence)
            queue.append((neighbor_id, new_depth, new_confidence))

    return visited


async def _trace_parent_chains(
    db: AsyncSession,
    seed_ids: list[int],
    seed_info: dict[int, dict],
    seed_similarities: dict[int, float],
    visited: dict[int, tuple[int, float]],
    max_hops: int,
) -> set[int]:
    """Trace parent_id chains upward from seeds, return set of parent-chain neuron IDs."""
    parent_chain_ids: set[int] = set()
    for nid in seed_ids:
        info = seed_info.get(nid, {})
        pid = info.get("parent_id")
        chain_depth = 1
        seen: set[int] = set()
        while pid is not None and chain_depth <= max_hops and pid not in seen:
            seen.add(pid)
            if pid not in visited:
                sim = seed_similarities.get(nid, 1.0) * (0.8 ** chain_depth)
                visited[pid] = (chain_depth, sim)
                parent_chain_ids.add(pid)
            parent_result = await db.execute(select(Neuron.parent_id).where(Neuron.id == pid))
            pid = parent_result.scalar_one_or_none()
            chain_depth += 1
    return parent_chain_ids


def _build_tiered_output(
    affected_info: dict[int, dict],
    visited: dict[int, tuple[int, float]],
    seed_set: set[int],
    parent_chain_ids: set[int],
) -> dict[str, list[dict]]:
    """Organize affected neurons into depth tiers."""
    tiers: dict[str, list[dict]] = {"direct": [], "indirect": [], "transitive": []}
    for nid, info in affected_info.items():
        if nid in seed_set:
            continue
        depth, confidence = visited[nid]
        tier_label = _DEPTH_TIERS.get(depth, "transitive")
        tiers[tier_label].append({
            **info,
            "depth": depth,
            "confidence": round(confidence, 4),
            "via_parent_chain": nid in parent_chain_ids,
        })
    for tier in tiers.values():
        tier.sort(key=lambda x: x["confidence"], reverse=True)
    return tiers


async def compute_blast_radius(
    db: AsyncSession,
    seed_neuron_ids: list[int],
    seed_similarities: dict[int, float],
    max_hops: int | None = None,
    min_edge_weight: float | None = None,
) -> dict:
    """BFS through co-firing edges from seed neurons, returning tiered results."""
    assert len(seed_neuron_ids) > 0, "At least one seed neuron required"
    max_hops = max_hops if max_hops is not None else settings.impact_max_hops
    min_edge_weight = min_edge_weight if min_edge_weight is not None else settings.impact_min_edge_weight
    assert 1 <= max_hops <= 5, f"max_hops must be in [1, 5], got {max_hops}"

    seed_info = await _load_seed_info(db, seed_neuron_ids)
    seed_set = set(seed_neuron_ids)

    visited = await _bfs_traverse(db, seed_neuron_ids, seed_similarities, max_hops, min_edge_weight)
    parent_chain_ids = await _trace_parent_chains(
        db, seed_neuron_ids, seed_info, seed_similarities, visited, max_hops,
    )

    affected_ids = [nid for nid in visited if nid not in seed_set]
    if not affected_ids:
        return {
            "tiers": {"direct": [], "indirect": [], "transitive": []},
            "seed_neurons": [
                {**seed_info.get(nid, {"id": nid}), "similarity": round(seed_similarities.get(nid, 0), 4)}
                for nid in seed_neuron_ids
            ],
            "total_affected": 0,
        }

    affected_result = await db.execute(
        select(Neuron.id, Neuron.label, Neuron.department, Neuron.layer, Neuron.role_key)
        .where(Neuron.id.in_(affected_ids), Neuron.is_active == True)
    )
    affected_info = {
        r[0]: {"id": r[0], "label": r[1], "department": r[2], "layer": r[3], "role_key": r[4]}
        for r in affected_result.all()
    }

    tiers = _build_tiered_output(affected_info, visited, seed_set, parent_chain_ids)
    return {
        "tiers": tiers,
        "seed_neurons": [
            {**seed_info.get(nid, {"id": nid}), "similarity": round(seed_similarities.get(nid, 0), 4)}
            for nid in seed_neuron_ids
        ],
        "total_affected": sum(len(t) for t in tiers.values()),
    }
