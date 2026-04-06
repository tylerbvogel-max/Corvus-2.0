"""In-memory adjacency cache for spread activation — eliminates DB round trips.

Biological analogue: pre-synaptic vesicle pools. Instead of synthesizing
neurotransmitters on demand (DB query per hop), the cell maintains a ready
pool of vesicles (in-memory adjacency dict) that can release instantly.

Cache architecture:
- On first spread activation, loads all edges above min_weight (~80MB at 1M edges)
- Subsequent spread activations do pure in-memory dict lookups (~microseconds)
- Incremental update after co-firing edge writes (no full reload needed)
- Invalidate on edge pruning or bulk edge operations

Feature-flagged via settings.spread_enabled (if spread is off, cache is never loaded).
"""

import threading


class _AdjacencyCache:
    """Thread-safe in-memory cache of the co-firing edge graph as adjacency lists."""

    def __init__(self):
        self._lock = threading.Lock()
        # neuron_id -> [(neighbor_id, weight, edge_type)]
        self._adjacency: dict[int, list[tuple[int, float, str]]] = {}
        self._loaded = False

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    def load(
        self,
        edges: list[tuple[int, int, float, str]],
    ) -> None:
        """Build bidirectional adjacency dict from all edges.

        Each edge tuple: (source_id, target_id, weight, edge_type).
        """
        assert isinstance(edges, list), "edges must be a list"
        with self._lock:
            adj: dict[int, list[tuple[int, float, str]]] = {}
            for src, tgt, weight, etype in edges:
                adj.setdefault(src, []).append((tgt, weight, etype))
                adj.setdefault(tgt, []).append((src, weight, etype))
            self._adjacency = adj
            self._loaded = True

    def invalidate(self) -> None:
        """Force reload on next access (e.g. after edge pruning)."""
        with self._lock:
            self._loaded = False
            self._adjacency = {}

    def update_edges(
        self,
        pairs: list[tuple[int, int]],
        weights: list[float],
        edge_types: list[str],
    ) -> None:
        """Incremental update after co-firing edge writes.

        Updates existing edges or adds new ones without full cache rebuild.
        """
        assert len(pairs) == len(weights) == len(edge_types), \
            "pairs, weights, and edge_types must have equal length"
        with self._lock:
            if not self._loaded:
                return
            for (src, tgt), weight, etype in zip(pairs, weights, edge_types):
                # Update or add src -> tgt
                self._update_single_direction(src, tgt, weight, etype)
                # Update or add tgt -> src
                self._update_single_direction(tgt, src, weight, etype)

    def _update_single_direction(
        self, from_id: int, to_id: int, weight: float, etype: str,
    ) -> None:
        """Update a single direction of an edge in the adjacency dict.

        Must be called while holding self._lock.
        """
        neighbors = self._adjacency.get(from_id)
        if neighbors is None:
            self._adjacency[from_id] = [(to_id, weight, etype)]
            return
        for i, (nid, _w, _e) in enumerate(neighbors):
            if nid == to_id:
                neighbors[i] = (to_id, weight, etype)
                return
        neighbors.append((to_id, weight, etype))

    def remove_neuron(self, neuron_id: int) -> None:
        """Remove all edges for a neuron from the cache."""
        with self._lock:
            if not self._loaded:
                return
            # Remove the neuron's own adjacency list
            neighbors = self._adjacency.pop(neuron_id, [])
            # Remove reverse references from all neighbors
            for nid, _w, _e in neighbors:
                peer_list = self._adjacency.get(nid)
                if peer_list is not None:
                    self._adjacency[nid] = [
                        (n, w, e) for n, w, e in peer_list if n != neuron_id
                    ]

    def remove_edges(
        self,
        pairs: list[tuple[int, int]],
    ) -> None:
        """Remove specific edges from the cache (e.g. after demotion to JSONB)."""
        assert isinstance(pairs, list), "pairs must be a list"
        with self._lock:
            if not self._loaded:
                return
            for src, tgt in pairs:
                self._remove_single_direction(src, tgt)
                self._remove_single_direction(tgt, src)

    def _remove_single_direction(self, from_id: int, to_id: int) -> None:
        """Remove a single direction of an edge. Must hold self._lock."""
        neighbors = self._adjacency.get(from_id)
        if neighbors is not None:
            self._adjacency[from_id] = [
                (n, w, e) for n, w, e in neighbors if n != to_id
            ]

    def get_neighbors(
        self,
        neuron_ids: set[int],
        min_weight: float,
    ) -> dict[int, list[tuple[int, float, str]]]:
        """Return filtered neighbor lists for a set of neuron IDs.

        Returns {neuron_id: [(neighbor_id, weight, edge_type), ...]}
        with only edges at or above min_weight.
        """
        assert isinstance(neuron_ids, set), "neuron_ids must be a set"
        with self._lock:
            if not self._loaded:
                return {}
            result: dict[int, list[tuple[int, float, str]]] = {}
            for nid in neuron_ids:
                neighbors = self._adjacency.get(nid)
                if neighbors is not None:
                    filtered = [
                        (n, w, e) for n, w, e in neighbors if w >= min_weight
                    ]
                    if filtered:
                        result[nid] = filtered
            return result


# Module-level singleton
_cache = _AdjacencyCache()


async def ensure_adjacency_loaded(db) -> None:
    """Load the adjacency cache from DB if not already loaded (neurons + engrams).

    Engram IDs are stored as negative values to avoid collision with neuron IDs
    in the shared adjacency dict.  Callers use engram_id_to_key() / key_to_engram_id()
    to convert.
    """
    if _cache.is_loaded:
        return

    from sqlalchemy import text

    # Load neuron-neuron edges
    result = await db.execute(
        text("SELECT source_id, target_id, weight, edge_type FROM neuron_edges")
    )
    edges = [
        (int(src), int(tgt), float(w), etype or "pyramidal")
        for src, tgt, w, etype in result.all()
    ]
    neuron_edge_count = len(edges)

    # Load engram-neuron edges (engram IDs negated to avoid collision)
    try:
        engram_result = await db.execute(
            text("SELECT engram_id, neuron_id, weight, edge_type FROM engram_edges")
        )
        for eid, nid, w, etype in engram_result.all():
            edges.append((-int(eid), int(nid), float(w), etype or "regulatory"))
    except Exception:
        pass  # engram_edges table may not exist yet

    engram_edge_count = len(edges) - neuron_edge_count

    if edges:
        _cache.load(edges)
        total_nodes = len(_cache._adjacency)
        print(f"Adjacency cache loaded: {neuron_edge_count} neuron + {engram_edge_count} engram edges, {total_nodes} nodes in graph")
    else:
        _cache.load([])
        print("Adjacency cache: no edges found")


def engram_id_to_key(engram_id: int) -> int:
    """Convert an engram ID to its adjacency cache key (negative)."""
    return -engram_id


def key_to_engram_id(key: int) -> int:
    """Convert a negative adjacency key back to an engram ID."""
    return -key


def is_engram_key(key: int) -> bool:
    """Check if an adjacency cache key represents an engram (negative)."""
    return key < 0


def invalidate_adjacency_cache() -> None:
    """Call after edge pruning or bulk edge operations to force reload."""
    _cache.invalidate()


def update_adjacency_incremental(
    pairs: list[tuple[int, int]],
    weights: list[float],
    edge_types: list[str],
) -> None:
    """Incrementally update the cache after co-firing edge writes."""
    assert len(pairs) > 0, "pairs must not be empty"
    _cache.update_edges(pairs, weights, edge_types)


def remove_adjacency_edges(
    pairs: list[tuple[int, int]],
) -> None:
    """Remove specific edges from the cache after demotion to JSONB."""
    if pairs:
        _cache.remove_edges(pairs)


def get_cached_neighbors(
    neuron_ids: set[int],
    min_weight: float,
) -> dict[int, list[tuple[int, float, str]]]:
    """Return cached neighbor lists for spread activation."""
    return _cache.get_neighbors(neuron_ids, min_weight)


def is_adjacency_loaded() -> bool:
    """Check if the adjacency cache has been loaded."""
    return _cache.is_loaded
