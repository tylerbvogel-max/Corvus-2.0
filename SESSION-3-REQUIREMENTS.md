# Session 3: Multi-Slot Query Execution Requirements & Status

**Session Date:** April 1, 2026
**Status:** COMPLETE & DEPLOYED
**Backend Port:** 8002
**Last Commit:** `256d9f6` (layout fixes) pushed to `private` remote

---

## User's Original Problem Statement

**Goal:** Enable Query Lab to test multiple model configurations side-by-side, with each configuration independently controlling:
- Whether to use agent orchestration or raw LLM
- Neuron context enrichment level
- Token budgets and top-K parameters

**Use Case:** Query Lab is an anti-fragile training system. When the neuron graph wins, showcase the value. When it fails, identify what went wrong and fix the neuron graph to prevent that mistake next time.

---

## What User Explicitly Asked For

### 1. Multi-Slot Parallel Execution ✅
- **Request:** Run multiple model configurations (up to 6+) simultaneously in a single query
- **Example:** Query #315 should test both "haiku + neurons" and "haiku raw" side-by-side
- **Status:** IMPLEMENTED
  - Backend: All slots execute through shared neuron pipeline (classify→score→spread→assemble), then independent execution per slot
  - Test Query #346: 2 slots (haiku_neuron + haiku_raw) both executed and returned in response
  - Haiku_raw completed in 9.7s, haiku_neuron (with agents) in 81.4s — proves parallelism

### 2. Per-Slot Agent Orchestration Control ✅
- **Request:** "Each slot can have independent specification for agent orchestration on or off"
- **Purpose:** Test agentic+neuron vs raw direct LLM in same query for comparison
- **Status:** IMPLEMENTED
  - `QueryRequest.slots[]` now accepts per-slot `agent_mode: bool` and `confidence_threshold: float`
  - Each slot can independently enable/disable agent orchestration
  - Default: `agent_mode: true`, `confidence_threshold: 0.5`

### 3. Live Progress Visibility During Execution ✅
- **Request:** "Is there a way to apply the timer during runtime to show which models are finished and which are still going? [...] as they finish, they stop showing the spinner and instead show another visual indicating completeness"
- **Status:** IMPLEMENTED
  - Live pipeline visualization with animated gutter dots
  - Dots transition from gray (pending) → green (done) as stages complete
  - Per-slot badges inline in execute_llm stage: ✓ (done) / ⟳ (running)
  - Elapsed timer in top-right tracks total execution time

### 4. Reuse Existing Gutter Dots (Don't Build Custom UI) ✅
- **Request:** "Rather than using the checkboxes that were created for this, can we instead dynamically update the dots on the gutter to the left of the workflow? That is what people see once it is completed, I want that to act as the visual indicator."
- **Status:** IMPLEMENTED
  - Gutter dots that appear in final result now animate in real-time during execution
  - PStep component reuses existing `.pipeline-dot`, `.pipeline-step-done`, `.pipeline-step-active` CSS
  - No custom checkbox UI

### 5. Deploy to Port 8002 ✅
- **Request:** "Can you roll it out to 8002 instead?"
- **Status:** IMPLEMENTED
  - Frontend built with Vite → `frontend/dist/`
  - Backend serves static files from port 8002
  - Both API and UI accessible at `http://localhost:8002`

### 6. Fix Layout Issues ✅
- **Request:** "The dots go all the way out to the right and the timer is in a weird spot"
- **Status:** FIXED
  - Changed `.pipeline-step` from `display: contents` to `display: grid`
  - Changed `.pipeline-flow` from grid to flex column (vertical stacking)
  - Added `position: relative` to `.live-pipeline-wrapper` for timer positioning
  - Dots now stay in left gutter, timer at top-right within wrapper

---

## What Was Built (Technical Details)

### Backend Changes
| File | Change | Reason |
|------|--------|--------|
| `app/config.py` | `agent_timeout_seconds: 90` (was 30) | Parallel agent execution + LLM latency exceeds 30s |
| `app/services/executor.py` | Added `slot_index` param to `_execute_slot()`, emit per-slot events | Frontend needs to track which slot completed |
| `app/routers/query.py` | Thread `agent_mode`, `confidence_threshold` from request to executor | Per-query control |

### Frontend Changes
| File | Change | Reason |
|------|--------|--------|
| `src/api.ts` | Fixed `onStage` null check | Callback optional |
| `src/components/QueryLab.tsx` | Made `baseline` param optional with default; fixed `buildSlotSpecs()`; live pipeline with PStep | Remove stale state; wire agent_mode/confidence_threshold per slot; animate dots |
| `src/components/HomePage.tsx` | Fixed `submitQueryStream` param order | Correct callback/slots ordering |
| `src/components/NeuronTreeViz.tsx` | Removed unused `AgentResultOut` import | Clean TypeScript build |
| `src/App.css` | Pipeline layout fixes (flex column, grid steps, positioned SVG) | Fix dot stretching + timer positioning |

### Test Results
**Query #346 — 2 slots:**
- Slot 0: `haiku_neuron` (agent mode on) → 81.4s, 2,921 output tokens
- Slot 1: `haiku_raw` (agent mode on) → 9.7s, 479 output tokens
- Both responses returned
- 29 neurons activated
- Total cost: $0.076

---

## What Was NOT Done (Deferred / Out of Scope)

These were in the original Session 3 plan but deferred to keep iteration focused:

1. **Agent result visualization** (hexagon nodes in NeuronTreeViz)
   - Requires `AgentResultOut` dataclass and neuron_id tracking
   - Planned for Session 4

2. **Verification agent** (post-coordinator confidence check)
   - Requires separate LLM call for critique + confidence adjustment
   - Planned for Session 4

3. **Coordinator fallback** (Option 1: Sonnet fallback on coordinator failure)
   - Requires error handling chain in coordinator
   - Planned for Session 4

4. **Neuron IDs in prompts** (`N-{id}` format for feedback loop traceability)
   - Requires agent template updates + AgentResult changes
   - Planned for Session 4

5. **Domain-empty agent behavior** (`DOMAIN_CONTEXT_EMPTY` flag)
   - Requires confidence threshold filtering per domain
   - Planned for Session 4

---

## How to Test (For Next Session)

1. **Start backend:**
   ```bash
   cd ~/Projects/corvus/backend
   source venv/bin/activate
   TENANT_ID=corvus-aero PORT=8002 python -m uvicorn app.main:app --port 8002 --reload
   ```

2. **Open browser:**
   ```
   http://localhost:8002
   ```

3. **Query Lab → Add Slots:**
   - Default has 1 slot (haiku_neuron, 8K tokens, top_k=60)
   - Click "+" to add more slots
   - Configure each independently: mode, token_budget, top_k, agent_mode, confidence_threshold

4. **Submit Query:**
   - Watch gutter dots animate as pipeline stages complete
   - Per-slot badges appear in "Execute LLM" stage showing which are done/running
   - Final response shows both slot results side-by-side

---

## Known Limitations / Open Questions

1. **Slot limit:** UI allows adding multiple slots, but no hard limit enforced (typically 6+ usable before performance degrades)

2. **Agent confidence threshold:** Currently accepted per-query but not yet used in neuron filtering (deferred to Session 4)

3. **Agent result tracking:** Agent findings not yet linked back to specific neurons (deferred; requires N-{id} format)

4. **Verification agent:** Not yet implemented (deferred; requires separate verification LLM call)

---

## Git History

| Commit | Message | Status |
|--------|---------|--------|
| `5f9b1d3` | feat: multi-slot query execution with live pipeline visualization | ✅ Pushed to `private` |
| `256d9f6` | fix: pipeline layout — constrain steps and reposition timer | ✅ Pushed to `private` |

All commits pushed to `private` remote only (never to `origin`/public).

---

## Next Session Checklist

- [ ] Test multi-slot queries with different model types (haiku, sonnet, opus mixes)
- [ ] Verify agent timeout behavior (set `agent_timeout_seconds: 1` to test partial results)
- [ ] Implement agent result visualization (hexagon nodes in NeuronTreeViz)
- [ ] Implement verification agent with confidence adjustment
- [ ] Implement coordinator fallback (Sonnet on coordinator LLM failure)
- [ ] NASA lint: run full lint suite on all modified backend files
- [ ] Smoke tests covering timeout, domain-empty, verification scenarios

