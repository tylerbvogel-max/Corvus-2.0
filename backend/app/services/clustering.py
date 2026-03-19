"""Community detection via Leiden algorithm on co-firing edges.

Discovers cross-department neuron clusters that the manual hierarchy
doesn't capture. Uses igraph + leidenalg for deterministic, high-quality
community detection with configurable resolution.

Replaces the earlier label propagation approach for better cluster quality
and determinism (same input = same output).
"""

import numpy as np
from collections import Counter

import igraph as ig
import leidenalg

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Neuron, NeuronEdge


def _build_igraph(
    edges: list, node_set: set[int]
) -> tuple[ig.Graph, list[int]]:
    """Build an igraph Graph from edge tuples and node set."""
    nodes = sorted(node_set)
    node_to_idx = {nid: i for i, nid in enumerate(nodes)}
    n = len(nodes)

    g = ig.Graph(n=n, directed=False)
    edge_list: list[tuple[int, int]] = []
    weights: list[float] = []
    for src, tgt, w in edges:
        i, j = node_to_idx[src], node_to_idx[tgt]
        edge_list.append((i, j))
        weights.append(w)

    g.add_edges(edge_list)
    g.es["weight"] = weights
    assert g.vcount() == n, f"Graph vertex count mismatch: {g.vcount()} != {n}"
    return g, nodes


def _leiden_clustering(
    g: ig.Graph,
    resolution: float = 1.0,
    seed: int = 42,
) -> list[int]:
    """Run Leiden community detection, return membership list.

    Uses RBConfigurationVertexPartition (modularity-like with resolution parameter).
    Higher resolution = more, smaller clusters. Lower = fewer, larger clusters.
    """
    assert g.vcount() > 0, "Graph must have at least one vertex"
    partition = leidenalg.find_partition(
        g,
        leidenalg.RBConfigurationVertexPartition,
        weights="weight",
        resolution_parameter=resolution,
        seed=seed,
    )
    assert len(partition.membership) == g.vcount(), "Membership length mismatch"
    return partition.membership


def _build_cluster_record(
    cluster_id: int,
    nids: list[int],
    edges: list,
    neuron_info: dict[int, dict],
    min_departments: int,
) -> dict | None:
    """Build a cluster record dict, or None if it doesn't meet dept threshold."""
    depts: set[str] = set()
    for nid in nids:
        info = neuron_info.get(nid, {})
        dept = info.get("department")
        if dept:
            depts.add(dept)
    if len(depts) < min_departments:
        return None

    nid_set = set(nids)
    internal_weights = [w for src, tgt, w in edges if src in nid_set and tgt in nid_set]
    avg_weight = float(np.mean(internal_weights)) if internal_weights else 0.0

    words: list[str] = []
    for nid in nids:
        info = neuron_info.get(nid, {})
        label = info.get("label", "")
        words.extend(w.lower() for w in label.split() if len(w) > 3)
    common = Counter(words).most_common(3)
    suggested = " + ".join(w for w, _ in common) if common else f"Cluster {cluster_id}"

    return {
        "cluster_id": cluster_id,
        "neuron_ids": sorted(nids),
        "departments": sorted(depts),
        "avg_internal_weight": avg_weight,
        "suggested_label": suggested,
    }


async def find_clusters(
    db: AsyncSession,
    min_weight: float = 0.3,
    min_size: int = 3,
    min_departments: int = 2,
    resolution: float = 1.0,
) -> list[dict]:
    """Run Leiden community detection and return cross-department clusters.

    Args:
        min_weight: Minimum edge weight to include (default 0.3)
        min_size: Minimum cluster size (default 3)
        min_departments: Minimum departments spanned (default 2)
        resolution: Leiden resolution parameter (default 1.0). Higher = more clusters.

    Returns list of dicts with: cluster_id, neuron_ids, departments,
    avg_internal_weight, suggested_label.
    """
    result = await db.execute(
        select(NeuronEdge.source_id, NeuronEdge.target_id, NeuronEdge.weight)
        .where(NeuronEdge.weight >= min_weight)
    )
    edges = result.all()

    if not edges:
        return []

    node_set: set[int] = set()
    for src, tgt, _ in edges:
        node_set.add(src)
        node_set.add(tgt)

    g, nodes = _build_igraph(edges, node_set)
    membership = _leiden_clustering(g, resolution=resolution)

    # Group nodes by community label
    clusters_raw: dict[int, list[int]] = {}
    for i, lbl in enumerate(membership):
        clusters_raw.setdefault(lbl, []).append(nodes[i])

    # Load neuron info for labeling
    neuron_result = await db.execute(
        select(Neuron.id, Neuron.label, Neuron.department, Neuron.layer)
        .where(Neuron.id.in_(list(node_set)))
    )
    neuron_info = {r[0]: {"label": r[1], "department": r[2], "layer": r[3]} for r in neuron_result.all()}

    clusters: list[dict] = []
    for cluster_id, (lbl, nids) in enumerate(clusters_raw.items()):
        if len(nids) < min_size:
            continue
        record = _build_cluster_record(cluster_id, nids, edges, neuron_info, min_departments)
        if record is not None:
            clusters.append(record)

    clusters.sort(key=lambda c: len(c["neuron_ids"]), reverse=True)

    return clusters
