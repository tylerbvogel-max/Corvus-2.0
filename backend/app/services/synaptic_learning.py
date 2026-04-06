"""Synaptic learning: automatic weight adjustment from eval outcomes.

After each eval, the system adjusts neuron avg_utility and co-firing edge weights
based on whether the neuron-enriched response won or lost. Attribution is
score-weighted with a diminishing returns ceiling to prevent runaway dominance.
"""

import json
import logging
from dataclasses import dataclass

from sqlalchemy import text, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import Neuron, Query, NeuronFiring, SynapticLearningEvent

logger = logging.getLogger(__name__)


@dataclass
class SynapticLearningSummary:
    outcome: str          # "win" | "loss" | "tie" | "skip"
    winner_mode: str | None
    neurons_adjusted: int
    edges_adjusted: int
    avg_delta: float
    total_reward: float
    total_penalty: float


def determine_neuron_outcome(
    winner: str | None,
    answer_modes: dict[str, str],
) -> tuple[str, str | None]:
    """Determine whether the neuron-enriched slot won, lost, or tied.

    Returns (outcome, winner_mode) where outcome is "win"|"loss"|"tie"|"skip".
    """
    assert isinstance(answer_modes, dict), "answer_modes must be a dict"

    if not winner or winner.lower() == "tie":
        return "tie", None

    winner_mode = answer_modes.get(winner)
    if not winner_mode:
        return "skip", None

    has_neuron = any(m.endswith("_neuron") for m in answer_modes.values())
    has_raw = any(m.endswith("_raw") for m in answer_modes.values())
    if not has_neuron or not has_raw:
        return "skip", winner_mode

    assert isinstance(winner_mode, str), "winner_mode must be a string"
    if winner_mode.endswith("_neuron"):
        return "win", winner_mode
    return "loss", winner_mode


def compute_attribution_weights(
    neuron_scores: list[dict],
) -> dict[int, float]:
    """Score-weighted attribution: neurons with higher combined scores
    get proportionally more credit/blame. Returns {neuron_id: weight}, sum=1.0.
    """
    assert len(neuron_scores) > 0, "neuron_scores must be non-empty"

    total = sum(s.get("combined", 0) for s in neuron_scores)
    if total <= 0:
        uniform = 1.0 / len(neuron_scores)
        return {s["neuron_id"]: uniform for s in neuron_scores}

    weights = {
        s["neuron_id"]: s.get("combined", 0) / total
        for s in neuron_scores
    }
    assert abs(sum(weights.values()) - 1.0) < 0.01, "weights must sum to ~1.0"
    return weights


def compute_utility_adjustment(
    current_avg_utility: float,
    attribution_weight: float,
    is_win: bool,
    alpha: float,
    loss_penalty: float,
) -> tuple[float, float, float]:
    """Compute new avg_utility with diminishing returns ceiling.

    Returns (new_avg_utility, raw_delta, effective_delta).
    """
    assert 0.0 <= current_avg_utility <= 1.0, f"avg_utility out of range: {current_avg_utility}"
    assert 0.0 <= attribution_weight <= 1.0, f"attribution_weight out of range: {attribution_weight}"

    if is_win:
        raw_delta = alpha * attribution_weight
        diminishing = 1.0 - current_avg_utility
        effective_delta = raw_delta * diminishing
        new_avg = min(1.0, current_avg_utility + effective_delta)
    else:
        raw_delta = alpha * attribution_weight * loss_penalty
        diminishing = current_avg_utility
        effective_delta = -(raw_delta * diminishing)
        new_avg = max(0.0, current_avg_utility + effective_delta)

    assert 0.0 <= new_avg <= 1.0, f"new_avg out of range: {new_avg}"
    return new_avg, raw_delta, effective_delta


async def _apply_edge_learning(
    db: AsyncSession,
    neuron_ids: list[int],
    is_win: bool,
    query_offset: int,
) -> int:
    """Accelerated co-fire edge adjustment. Win: +2 co-fires. Loss: +0."""
    assert len(neuron_ids) >= 2, "need at least 2 neurons for edge learning"

    if not is_win:
        return 0

    increment = settings.outcome_win_cofire_multiplier
    pairs = [
        (min(a, b), max(a, b))
        for i, a in enumerate(neuron_ids)
        for b in neuron_ids[i + 1:]
    ]

    from app.services.edge_tier import (
        get_weak_edge, upsert_weak_edge, maybe_promote,
    )
    updated = 0
    for src, tgt in pairs:
        result = await db.execute(text(
            "UPDATE neuron_edges "
            "SET co_fire_count = co_fire_count + :inc, "
            "    weight = LEAST(1.0, (co_fire_count + :inc) / 20.0), "
            "    last_updated_query = :qoff, "
            "    last_adjusted = now() "
            "WHERE source_id = :src AND target_id = :tgt"
        ), {"inc": increment, "qoff": query_offset, "src": src, "tgt": tgt})
        if result.rowcount > 0:
            updated += 1
            continue
        # Not in promoted table — update in JSONB
        entry = await get_weak_edge(db, src, tgt)
        if entry is None:
            continue
        new_c = entry.get("c", 0) + increment
        new_w = min(1.0, (new_c + 1) / 20.0)
        data = {**entry, "w": new_w, "c": new_c, "q": query_offset}
        await upsert_weak_edge(db, src, tgt, data)
        await maybe_promote(db, src, tgt, new_w, new_c)
        updated += 1

    assert updated >= 0, "updated count must be non-negative"
    return updated


async def _update_firing_outcomes(
    db: AsyncSession,
    query_id: int,
    outcome_label: str,
) -> None:
    """Mark NeuronFiring records with eval outcome."""
    assert outcome_label in ("eval_win", "eval_loss"), f"invalid outcome: {outcome_label}"
    await db.execute(
        update(NeuronFiring)
        .where(NeuronFiring.query_id == query_id)
        .values(outcome=outcome_label)
    )


async def _load_learning_inputs(
    db: AsyncSession, query_id: int,
) -> tuple[Query | None, list[dict], list[int]]:
    """Load query, neuron scores, and neuron IDs for learning."""
    query = await db.get(Query, query_id)
    if not query:
        return None, [], []

    neuron_scores = []
    if query.neuron_scores_json:
        neuron_scores = json.loads(query.neuron_scores_json)

    neuron_ids = []
    if query.selected_neuron_ids:
        neuron_ids = json.loads(query.selected_neuron_ids)

    assert isinstance(neuron_scores, list), "neuron_scores must be a list"
    assert isinstance(neuron_ids, list), "neuron_ids must be a list"
    return query, neuron_scores, neuron_ids


async def apply_synaptic_learning(
    db: AsyncSession,
    query_id: int,
    winner: str | None,
    answer_map: list[tuple[str, object]],
) -> SynapticLearningSummary:
    """Apply synaptic weight adjustments after eval. Inline, same transaction."""
    assert isinstance(query_id, int) and query_id > 0, "query_id must be positive"

    answer_modes = {letter: slot.mode for letter, slot in answer_map}
    outcome, winner_mode = determine_neuron_outcome(winner, answer_modes)

    if outcome in ("tie", "skip"):
        return SynapticLearningSummary(
            outcome=outcome, winner_mode=winner_mode,
            neurons_adjusted=0, edges_adjusted=0,
            avg_delta=0.0, total_reward=0.0, total_penalty=0.0,
        )

    query, neuron_scores, neuron_ids = await _load_learning_inputs(db, query_id)
    if not query or not neuron_scores:
        return SynapticLearningSummary(
            outcome="skip", winner_mode=winner_mode,
            neurons_adjusted=0, edges_adjusted=0,
            avg_delta=0.0, total_reward=0.0, total_penalty=0.0,
        )

    is_win = outcome == "win"
    weights = compute_attribution_weights(neuron_scores)
    return await _apply_adjustments(
        db, query_id, neuron_scores, neuron_ids,
        weights, is_win, outcome, winner_mode,
    )


async def _apply_adjustments(
    db: AsyncSession,
    query_id: int,
    neuron_scores: list[dict],
    neuron_ids: list[int],
    weights: dict[int, float],
    is_win: bool,
    outcome: str,
    winner_mode: str | None,
) -> SynapticLearningSummary:
    """Apply utility adjustments to neurons and edges. Creates audit rows."""
    assert len(neuron_scores) > 0, "neuron_scores must be non-empty"

    alpha = settings.outcome_learning_alpha
    loss_penalty = settings.outcome_loss_penalty
    total_reward = 0.0
    total_penalty = 0.0
    adjusted = 0

    from app.services.neuron_service import get_system_state
    state = await get_system_state(db)

    for ns in neuron_scores:
        nid = ns["neuron_id"]
        attr_w = weights.get(nid, 0.0)
        if attr_w <= 0:
            continue

        neuron = await db.get(Neuron, nid)
        if not neuron:
            continue

        old_util = neuron.avg_utility or 0.5
        new_util, raw_delta, eff_delta = compute_utility_adjustment(
            old_util, attr_w, is_win, alpha, loss_penalty,
        )
        neuron.avg_utility = new_util

        db.add(SynapticLearningEvent(
            query_id=query_id, neuron_id=nid,
            event_type="reward" if is_win else "penalty",
            old_avg_utility=old_util, new_avg_utility=new_util,
            delta=raw_delta, effective_delta=eff_delta,
            combined_score=ns.get("combined", 0),
            attribution_weight=attr_w,
            outcome=outcome, winner_mode=winner_mode,
        ))

        if eff_delta > 0:
            total_reward += eff_delta
        else:
            total_penalty += abs(eff_delta)
        adjusted += 1

    edges_adjusted = 0
    if len(neuron_ids) >= 2:
        edges_adjusted = await _apply_edge_learning(
            db, neuron_ids, is_win, state.total_queries,
        )

    await _update_firing_outcomes(
        db, query_id, "eval_win" if is_win else "eval_loss",
    )

    avg_delta = (total_reward - total_penalty) / max(adjusted, 1)

    assert adjusted >= 0, "adjusted count must be non-negative"
    return SynapticLearningSummary(
        outcome=outcome, winner_mode=winner_mode,
        neurons_adjusted=adjusted, edges_adjusted=edges_adjusted,
        avg_delta=round(avg_delta, 6),
        total_reward=round(total_reward, 6),
        total_penalty=round(total_penalty, 6),
    )
