"""ARCHIVED: Classic multi-slot execution path.

This file contains the multi-slot query execution pipeline that was removed in Session 3
when the codebase transitioned to agent-based orchestration. The code is preserved here
for reference and potential restoration if needed.

To restore the classic path:
1. Copy _normalize_slot_specs(), _get_cached_prompt(), _execute_and_collect_slots(),
   and _populate_query_from_results() back to executor.py
2. Restore QuerySlotRequest and SlotResult classes to schemas.py
3. Re-add the else branch in execute_query() that calls _execute_and_collect_slots()
4. Re-add slots_v2, modes, token_budget, chat_style to QueryRequest schema
5. Wire QuerySlotRequest back into the API route handler

Session 3 replaced the multi-slot machinery with per-query agent_mode and confidence_threshold
fields, with agent-based dispatch as the primary path and a lightweight direct-call path
(single Haiku + assembled neurons) as the agent_mode=false fallback.
"""

import asyncio
import time
from dataclasses import dataclass
from app.models import Neuron
from app.services.claude_cli import claude_chat as llm_chat, MODEL_REGISTRY
from app.services.scoring_engine import NeuronScoreBreakdown
from app.config import settings
from app.services.prompt_assembler import assemble_prompt


# Constants from executor.py that the classic path depends on
NEURON_MODES = {m for m in MODEL_REGISTRY.keys() if "_neuron" in m}
MODEL_MAP = {
    "haiku_raw": "haiku",
    "haiku_neuron": "haiku",
    "sonnet_raw": "sonnet",
    "sonnet_neuron": "sonnet",
    "opus_raw": "opus",
    "opus_neuron": "opus",
}

SONNET_EFFICIENCY_PREFIX = """You are a highly skilled expert. Analyze the user's question with precision and brevity.
Prioritize directly addressing the user's intent. Structure your response with:
1. **Key Finding**: A single, direct answer or observation
2. **Supporting Evidence**: Relevant context or explanation
3. **Next Steps**: Actionable recommendations if applicable

Keep responses focused and efficient."""

CONVERSATIONAL_STYLE_SUFFIX = """
Remember to be conversational and approachable in tone. Use natural language
and explain technical concepts in accessible terms. Feel free to acknowledge
uncertainty or limitations in your analysis."""


def _normalize_slot_specs(
    modes: list[str],
    token_budget: int | None,
    slots_v2: list[dict] | None,
) -> list[dict]:
    """Normalize slot specifications from legacy (modes/token_budget) or v2 (slots_v2) format."""
    assert (modes and len(modes) > 0) or (slots_v2 and len(slots_v2) > 0), \
        "Either modes or slots_v2 must be provided and non-empty"
    if slots_v2:
        slot_specs = slots_v2
    else:
        slot_specs = [
            {"mode": m, "token_budget": token_budget or settings.token_budget,
             "top_k": settings.top_k_neurons, "label": None}
            for m in modes
        ]
    assert len(slot_specs) > 0, "slot_specs must be non-empty after normalization"
    return slot_specs


def _get_cached_prompt(
    prompt_cache: dict[tuple[int, int], str],
    budget: int,
    slot_top_k: int,
    intent: str,
    all_scored: list[NeuronScoreBreakdown],
    neuron_map: dict[int, Neuron],
) -> str:
    """Assemble and cache neuron-enriched prompt by (budget, top_k) key."""
    assert isinstance(budget, int) and budget > 0, "budget must be a positive int"
    assert isinstance(slot_top_k, int) and slot_top_k > 0, "slot_top_k must be a positive int"
    key = (budget, slot_top_k)
    if key not in prompt_cache:
        prompt_cache[key] = assemble_prompt(intent, all_scored[:slot_top_k], neuron_map, budget_tokens=budget)
    return prompt_cache[key]


def _build_slot_system_prompt(
    mode: str, neuron_prompt: str, chat_style: str | None = None,
) -> tuple[str, int]:
    """Build system prompt for a slot based on mode and neuron context."""
    assert mode in MODEL_MAP, f"Unknown mode: {mode}"
    model = MODEL_MAP[mode]
    is_sonnet = model == "sonnet"
    if mode in NEURON_MODES:
        prompt = (SONNET_EFFICIENCY_PREFIX + neuron_prompt) if is_sonnet else neuron_prompt
        if chat_style == "conversational":
            prompt += CONVERSATIONAL_STYLE_SUFFIX
        return prompt, 4096
    # Raw mode (no neurons)
    baseline = "You are a helpful, knowledgeable assistant."
    raw = (SONNET_EFFICIENCY_PREFIX + baseline) if is_sonnet else baseline
    if chat_style == "conversational":
        raw += CONVERSATIONAL_STYLE_SUFFIX
    return raw, 4096


def _format_slot_result(spec: dict, result: dict) -> dict:
    """Format LLM result into SlotResult schema."""
    assert "mode" in spec, "spec must contain 'mode'"
    assert "text" in result, "result must contain 'text'"
    mode = spec["mode"]
    budget = spec.get("token_budget", settings.token_budget)
    slot_top_k = spec.get("top_k", settings.top_k_neurons)
    return {
        "mode": mode,
        "model": MODEL_MAP.get(mode, mode.rsplit("_", 1)[0]),
        "neurons": mode in NEURON_MODES,
        "response": result["text"],
        "input_tokens": result["input_tokens"],
        "output_tokens": result["output_tokens"],
        "cost_usd": result["cost_usd"],
        "duration_ms": result.get("duration_ms", 0),
        "token_budget": budget if mode in NEURON_MODES else None,
        "top_k": slot_top_k if mode in NEURON_MODES else None,
        "label": spec.get("label"),
        "model_version": result.get("model_version"),
        "error": result.get("error", False),
    }


async def _execute_and_collect_slots(
    slot_specs: list[dict],
    user_message: str,
    prompt_cache: dict[tuple[int, int], str],
    intent: str,
    all_scored: list[NeuronScoreBreakdown],
    neuron_map: dict[int, Neuron],
    on_stage,  # StageCallback
    chat_style: str | None = None,
) -> list[dict]:
    """Execute all slots concurrently, collecting results with per-slot error handling."""
    assert len(slot_specs) > 0, "slot_specs must be non-empty"

    async def _timed_chat(*args, **kwargs):
        t0 = time.monotonic()
        result = await llm_chat(*args, **kwargs)
        result["duration_ms"] = round((time.monotonic() - t0) * 1000)
        return result

    tasks: list[asyncio.Task] = []
    for spec in slot_specs:
        mode = spec["mode"]
        budget = spec.get("token_budget", settings.token_budget)
        slot_top_k = spec.get("top_k", settings.top_k_neurons)
        model = MODEL_MAP.get(mode)
        if mode in NEURON_MODES:
            neuron_prompt = _get_cached_prompt(prompt_cache, budget, slot_top_k, intent, all_scored, neuron_map)
        else:
            neuron_prompt = ""
        prompt, default_max_tokens = _build_slot_system_prompt(mode, neuron_prompt, chat_style)
        max_tokens = spec.get("max_output_tokens") or default_max_tokens
        tasks.append(asyncio.create_task(
            _timed_chat(prompt, user_message, max_tokens=max_tokens, model=model)
        ))

    slot_results: list[dict | None] = [None] * len(slot_specs)

    async def _collect_slot(i: int, spec: dict, task: asyncio.Task):
        try:
            result = await task
        except Exception as e:
            # Per-slot resilience: capture error without killing other slots
            error_msg = str(e)
            # Extract a concise message from rate-limit / quota errors
            if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                error_msg = f"Rate limited — try again shortly or use a different model"
            elif "401" in error_msg or "403" in error_msg:
                error_msg = f"Authentication failed for this provider"
            slot_results[i] = _format_slot_result(spec, {
                "text": f"[Error: {error_msg}]",
                "input_tokens": 0,
                "output_tokens": 0,
                "cost_usd": 0.0,
                "model_version": None,
                "duration_ms": 0,
                "error": True,
            })
            if on_stage:
                await on_stage("execute_llm", {"status": "error", "detail": {
                    "slot_index": i, "mode": spec["mode"],
                    "error": error_msg,
                }})
            return
        slot_results[i] = _format_slot_result(spec, result)
        if on_stage:
            await on_stage("execute_llm", {"status": "done", "detail": {
                "slot_index": i, "mode": spec["mode"],
                "model": MODEL_MAP.get(spec["mode"], spec["mode"].rsplit("_", 1)[0]),
                "duration_ms": result.get("duration_ms", 0),
            }})

    collect_tasks = [
        asyncio.create_task(_collect_slot(i, spec, tasks[i]))
        for i, spec in enumerate(slot_specs)
    ]
    await asyncio.gather(*collect_tasks)
    assert all(s is not None for s in slot_results), "All slot results must be populated"
    return slot_results


def _populate_query_from_results(
    query,  # Query model
    slot_results: list[dict],
    all_scored: list[NeuronScoreBreakdown],
    neuron_map: dict[int, Neuron],
    classify_result: dict,
) -> float:
    """Populate Query record from slot execution results."""
    import json
    assert len(slot_results) > 0, "slot_results must be non-empty"
    query.results_json = json.dumps(slot_results)
    if all_scored:
        def _build_neuron_score_dicts(scored, nmap):
            return [
                {"neuron_id": s.neuron_id, "combined": s.combined, "burst": s.burst,
                 "impact": s.impact, "precision": s.precision, "novelty": s.novelty,
                 "recency": s.recency, "relevance": s.relevance, "spread_boost": s.spread_boost,
                 "label": nmap[s.neuron_id].label if s.neuron_id in nmap else None,
                 "department": nmap[s.neuron_id].department if s.neuron_id in nmap else None,
                 "layer": nmap[s.neuron_id].layer if s.neuron_id in nmap else 0,
                 "parent_id": nmap[s.neuron_id].parent_id if s.neuron_id in nmap else None,
                 "summary": nmap[s.neuron_id].summary if s.neuron_id in nmap else None}
                for s in scored
            ]
        query.neuron_scores_json = json.dumps(
            _build_neuron_score_dicts(all_scored, neuron_map)
        )
    for slot in slot_results:
        if slot["mode"] == "haiku_neuron" and not query.response_text:
            query.response_text = slot["response"]
            query.execute_input_tokens = slot["input_tokens"]
            query.execute_output_tokens = slot["output_tokens"]
        elif slot["mode"] == "opus_raw" and not query.opus_response_text:
            query.opus_response_text = slot["response"]
            query.opus_input_tokens = slot["input_tokens"]
            query.opus_output_tokens = slot["output_tokens"]
    total_cost = sum(s["cost_usd"] for s in slot_results) + classify_result.get("cost_usd", 0)
    query.cost_usd = total_cost
    for slot in slot_results:
        mv = slot.get("model_version")
        if mv:
            query.model_version = mv
            break
    assert total_cost >= 0, f"total_cost must be non-negative, got {total_cost}"
    return total_cost
