# Classic Multi-Slot Execution Path (Archived)

**Archived Date:** Session 3 (2026-03-31)
**Reason:** Transition to agent-based orchestration with per-query agent control.

## What This Contains

This directory preserves the classic multi-slot query execution pipeline that was removed when Corvus transitioned from multi-slot execution to agent-based orchestration.

### Files

- **`executor_classic_path.py`** — Functions extracted from `app/services/executor.py`:
  - `_normalize_slot_specs()` — Normalize modes/token_budget or slots_v2 into uniform spec list
  - `_get_cached_prompt()` — Assemble and cache neuron-enriched prompts by budget/top_k
  - `_execute_and_collect_slots()` — Run all slots concurrently with per-slot error handling
  - `_populate_query_from_results()` — Populate Query record from slot results

- **`schemas_classic.py`** — Pydantic models extracted from `app/schemas.py`:
  - `QuerySlotRequest` — Configuration for a single slot
  - `SlotResult` — Result from executing a slot
  - `ClassicQueryRequest` — Full QueryRequest with multi-slot support
  - `ClassicQueryResponse` — QueryResponse with slots array

## Why It Was Archived

Session 3 introduced:
1. **Per-query agent control** via `agent_mode` (True/False) and `confidence_threshold` (0.0–1.0) in QueryRequest
2. **Agent-based orchestration path** (primary): classify → score → partition by domain → dispatch agents → synthesize
3. **Direct call fallback path** (agent_mode=False): classify → score → assemble → single Haiku call
4. **Removal of multi-slot machinery** to simplify API and reduce complexity

The classic path supported running multiple LLM slots in parallel (e.g., haiku_neuron + opus_raw), with per-slot caching and error handling. This was replaced by the agent-based approach, which is more scalable and specialized per-domain.

## How to Restore

If you need to restore the classic multi-slot path:

### 1. Restore Functions in `executor.py`

Copy the following functions back from `executor_classic_path.py`:
```python
def _normalize_slot_specs(modes, token_budget, slots_v2) -> list[dict]
def _get_cached_prompt(prompt_cache, budget, slot_top_k, intent, all_scored, neuron_map) -> str
def _build_slot_system_prompt(mode, neuron_prompt, chat_style=None) -> tuple[str, int]
def _format_slot_result(spec, result) -> dict
async def _execute_and_collect_slots(slot_specs, user_message, prompt_cache, intent, all_scored, neuron_map, on_stage, chat_style=None) -> list[dict]
def _populate_query_from_results(query, slot_results, all_scored, neuron_map, classify_result) -> float
```

Also restore the constants:
```python
NEURON_MODES = {m for m in MODEL_REGISTRY.keys() if "_neuron" in m}
MODEL_MAP = {...}  # from archived file
SONNET_EFFICIENCY_PREFIX = "..."
CONVERSATIONAL_STYLE_SUFFIX = "..."
```

### 2. Update `execute_query()` in `executor.py`

The current execute_query() signature (Session 3):
```python
async def execute_query(
    db: AsyncSession,
    user_message: str,
    agent_mode: bool = True,
    confidence_threshold: float = 0.5,
    on_stage: StageCallback = None,
    prior_neuron_ids: list[int] | None = None,
) -> dict
```

Needs to be changed back to support slots:
```python
async def execute_query(
    db: AsyncSession,
    user_message: str,
    modes: list[str],
    token_budget: int | None = None,
    slots_v2: list[dict] | None = None,
    on_stage: StageCallback = None,
    chat_style: str | None = None,
    prior_neuron_ids: list[int] | None = None,
) -> dict
```

Re-add the `else` branch that was removed:
```python
else:
    # Classic slot execution path (restored)
    prompt_cache: dict[tuple[int, int], str] = {}
    primary_budget = _compute_neuron_slot_max(slot_specs, "token_budget", settings.token_budget)
    primary_top_k = _compute_neuron_slot_max(slot_specs, "top_k", settings.top_k_neurons)
    primary_prompt = _get_cached_prompt(
        prompt_cache, primary_budget, primary_top_k, intent, all_scored, neuron_map,
    ) if needs_neurons else ""
    query.assembled_prompt = primary_prompt

    slot_results = await _execute_and_collect_slots(
        slot_specs, user_message, prompt_cache, intent, all_scored, neuron_map, on_stage,
        chat_style=chat_style,
    )
    total_cost = _populate_query_from_results(query, slot_results, all_scored, neuron_map, classify_result)
    agent_execution_result = None
```

### 3. Restore Schemas in `schemas.py`

Add back to `QueryRequest`:
```python
modes: list[str] = ["haiku_neuron"]
token_budget: int | None = Field(None, ge=1000, le=32000)
slots_v2: list[QuerySlotRequest] | None = None
chat_style: str | None = None
```

Re-add the classes:
```python
class QuerySlotRequest(BaseModel):
    mode: str
    token_budget: int = Field(8000, ge=1000, le=32000)
    top_k: int = Field(60, ge=1, le=500)
    max_output_tokens: int | None = Field(None, ge=256, le=8192)
    label: str | None = None

class SlotResult(BaseModel):
    mode: str
    model: str
    neurons: bool
    response: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    token_budget: int | None = None
    top_k: int | None = None
    label: str | None = None
```

Add back to `QueryResponse`:
```python
slots: list[SlotResult] = []
```

### 4. Restore API Route Handler

In `routers/query.py`, update the POST /query handler to accept `modes`, `token_budget`, `slots_v2`, `chat_style`:
```python
@router.post("/query")
async def post_query(request: QueryRequest, db: AsyncSession):
    result = await execute_query(
        db, request.message,
        modes=request.modes,
        token_budget=request.token_budget,
        slots_v2=request.slots_v2,
        on_stage=on_stage,
        chat_style=request.chat_style,
        prior_neuron_ids=request.prior_neuron_ids,
    )
    return result
```

### 5. Run Tests

After restoration, test that:
- Multi-slot requests execute all slots in parallel
- Slot caching works (same budget/top_k reuses prompt)
- Per-slot error handling captures failures without killing other slots
- Results include neuron_scores, slots, total_cost

## Design Notes

### Why Multi-Slot Was Useful

Multi-slot allowed running multiple LLM configurations in a single query:
- `haiku_neuron`: fast, neuron-enriched response
- `opus_raw`: comprehensive, no neuron constraints
- Different token budgets per slot
- Independent error handling per slot

### Why It Was Removed

1. **Complexity**: Three separate execution paths (raw, neuron, agent) vs. two (agent, direct call)
2. **Specialization**: Agents partition neurons by domain; multi-slot treats all neurons equally
3. **API clarity**: Single per-query choice (agent_mode) easier to reason about than slot configuration
4. **Cost**: Agent path with domain specialization produces higher quality per dollar than multi-slot

### Remaining Compatibility

The neuron selection, scoring, and assembly pipeline (`prepare_context()`, `assemble_prompt()`, etc.) remains intact. Only the multi-slot execution and result collection was removed.

## Questions?

Refer to the Session 2 Handoff document (`SESSION-2-HANDOFF.md`) for architectural context on the agent orchestration path that replaced multi-slot execution.
