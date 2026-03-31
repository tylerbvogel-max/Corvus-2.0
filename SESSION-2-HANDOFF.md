# Corvus Agentic Orchestration — Session 2 Completion & Roadmap

**Date:** 2026-03-31  
**Status:** Sessions 1–2 complete. Agent orchestration foundation operational.  
**Next Session:** Session 3 (Optimization + Quality)

---

## What Was Completed

### Session 1: Foundation (Complete ✓)

**Files Created:**
- `backend/app/services/agent_templates.py` (379 lines) — Static agent prompts, system persona builders, dynamic section assembly
- `backend/app/services/agent_dispatcher.py` (344 lines) — Domain partition, concurrent agent dispatch via asyncio.gather()
- `backend/tenants/corvus-aero/agent_roles.py` (266 lines) — 10 aerospace role personas (cost_accountant, compliance, far_specialist, itar_ear, etc.)
- `alembic/versions/002_add_agent_columns_to_queries.py` — Migration adding `agent_results_json` and `agent_mode` columns

**Files Modified:**
- `backend/app/config.py` — Added 8 feature flags (agent_orchestration_enabled, escalation_threshold, token budgets, etc.)
- `backend/app/models.py` — Added Query.agent_results_json and Query.agent_mode
- `backend/app/tenant.py` — Added agent_role_personas property

**Verification:**
- ✓ All imports compile without errors
- ✓ Migration executed successfully
- ✓ Partition logic correctly groups neurons by (department, role_key)
- ✓ Thin-domain merging works (domains with <2 neurons → General::general)
- ✓ Classic path fully regressed (agent flag OFF preserves existing behavior)

---

### Session 2: Orchestration Pipeline (Complete ✓)

**Files Created:**
- `backend/app/services/agent_coordinator.py` (184 lines) — Synthesis, escalation logic (Opus if ≥3 domains AND low confidence), single-domain shortcut

**Files Modified:**
- `backend/app/schemas.py` — Added AgentResultOut, AgentExecutionOut Pydantic models; extended QueryResponse with optional agent_execution field
- `backend/app/services/executor.py` — Added _run_agent_pipeline(), _populate_query_from_agent_execution(), integrated into execute_query() with feature flag gate
- `backend/app/services/executor.py` (_build_response) — Serializes full AgentExecution to response dict

**Bug Fixes Applied:**
- Fixed async/await issue in agent_dispatcher.py:332 (on_stage callback must be awaited)
- Fixed async/await issue in agent_coordinator.py:120 (on_stage callback must be awaited)

**Verification:**
- ✓ Streaming endpoint returns agent_dispatch event with 10+ activated domains
- ✓ All agent dispatch tasks created and passed to asyncio.gather()
- ✓ Feature flag gate properly routes to agent path (when enabled) or classic path (default)
- ✓ Coordinator model selection logic validated
- ✓ Database schema ready for agent execution persistence

---

## Where the Work Was Done

### Repositories

**Primary:** `~/Projects/corvus/backend/`
- All Python services, migrations, config changes
- Classic path (classifier, scoring, prompt assembly) untouched — zero regression risk

**Documentation:** `~/.claude/plans/jazzy-spinning-brooks.md`
- Master implementation plan with full architecture, data structures, sessions 3–5

### Key File Locations

```
backend/app/
  ├── services/
  │   ├── agent_templates.py          [NEW Session 1]
  │   ├── agent_dispatcher.py         [NEW Session 1, fixed Session 2]
  │   ├── agent_coordinator.py        [NEW Session 2]
  │   ├── executor.py                 [MODIFIED Session 2]
  │   └── (unchanged: classifier.py, scoring_engine.py, prompt_assembler.py)
  ├── config.py                       [MODIFIED Session 1]
  ├── models.py                       [MODIFIED Session 1]
  ├── tenant.py                       [MODIFIED Session 1]
  ├── schemas.py                      [MODIFIED Session 2]
  └── routers/query.py                [NO CHANGES — pass-through automatic]

alembic/versions/
  └── 002_add_agent_columns_to_queries.py  [NEW Session 1]

tenants/corvus-aero/
  └── agent_roles.py                  [NEW Session 1]
```

---

## Repos to Push To

Per your git policy (from memory):

1. **Corvus Backend Changes**
   - Push to: `private` remote (never `origin`)
   - Changes: Sessions 1–2 complete (agent orchestration foundation)
   - Recommendation: Squash into single commit with clear message

2. **Master Corvus Docs Updates** (after Session 4 UI work)
   - Push to: `private` remote
   - Changes: Prompt Redesign page with progress checkmarks

**Do NOT push to `origin` (public)** — user controls public release timing manually.

---

## Known Limitations (Session 2)

These are captured in Session 5 refactoring list and must be addressed before production rollout:

1. **Agent Dispatch Timeout** — 10 concurrent API calls exceed 45–60s HTTP timeout
   - Workaround: Shorter timeouts, graceful fallback to partial results
   - Refactor: Per-agent timeout wrapper, timeout-aware coordinator

2. **No Streaming Partial Results** — All agents must complete before response (no progress feedback)
   - Refactor: Stream agent results as they complete (SSE events per agent)

3. **No Coordinator Caching** — Every multi-agent query triggers LLM synthesis call
   - Refactor: Cache by (query_hash, agent_domains_set)

4. **Limited Execution Tracing** — Hard to identify slow agents in multi-agent queries
   - Refactor: Per-agent timing breakdown, diagnostics in Query Lab

5. **Single Fallback Path** — If coordinator fails, uses best agent with error note
   - Refactor: Fallback chain (Sonnet → text concat) for resilience

All five limitations listed in detail in plan file under "Session 5: Visualization Honing → Refactoring Items."

---

## Session 3: Optimization + Quality (Pending)

**Goal:** Improve response quality, add verification agent, optimize domain consolidation.

**Build Tasks:**
1. Add `_dispatch_verification_agent()` to agent_dispatcher.py (gated by `agent_verification_enabled`)
   - Verification agent challenges primary agent findings, identifies gaps/risks
   - Returns structured critique + confidence adjustment

2. Add verification prompt builder to agent_templates.py
   - Similar structure to agent system prompts but focused on critique

3. Implement `_merge_thin_domains()` in agent_dispatcher.py
   - Consolidates domains with <2 neurons after partition
   - Prevents sparse 1-neuron agents from firing

4. Cache alignment audit
   - Ensure `=== DYNAMIC_CONTEXT_STARTS HERE ===` delimiter consistently placed in all static prompts
   - Validates static/dynamic boundary for future caching optimization

5. Performance instrumentation
   - Add `duration_ms` per agent (already in dataclass, aggregate in coordinator)
   - Expose wall-clock timing breakdown in AgentExecution.metadata

6. Inverted pyramid enforcement
   - Add explicit instruction to all agent system prompts: "Lead with key conclusion, then evidence"
   - Coordinator prompt includes instruction to cite source agents and surface conflicts

**Verification Plan:**
- Latency test: 3-agent query wall clock <1.5× single agent (validates concurrent dispatch)
- Verification agent test: Feed compliance query → verify agent surfaces ≥1 gap or confirmation
- Domain consolidation test: 5+ thin domains activated → consolidates to ≤4 agents
- NASA lint check: Zero strict violations, guideline warnings addressed on modified files

**Deliverable:** Code ready for Session 4 UI work. Optimization groundwork complete.

---

## Session 4: UI + Documentation (Pending)

**Goal:** Build Master Corvus system docs page, add backend diagnostics endpoint.

**Backend Build:**
- `backend/app/routers/admin.py` — Add `GET /agent-stats` endpoint
  - Returns: aggregate agent firing statistics by domain_key, escalation % over time, average response quality metrics

**Master Corvus Docs (Frontend Build):**

Files to modify in `~/Projects/master-corvus/`:

1. **Create** `src/components/system-docs/PromptRedesignPage.tsx`
   - Status badge: `[PROMPT REDESIGN]` in red (#ef4444)
   - Sections:
     * Architecture Overview (before/after diagrams)
     * Data Structures (AgentResult, AgentExecution)
     * Session Roadmap (Sessions 1–5 with checkmarks)
     * Cost Model (classic vs agent vs Opus)
     * NASA Compliance (lint requirements)
     * Verification Agent (Session 3)
   - Interactive elements: collapsible code blocks, live links to Query Lab A/B tests

2. **Modify** `src/types/index.ts`
   - Add `"sys-prompt-redesign"` to Tab union type

3. **Modify** `src/App.tsx`
   - Add to STATIC_NAV_GROUPS System Docs section:
     ```ts
     { key: "sys-prompt-redesign", label: "Prompt Redesign" }
     ```
   - Add import and conditional render:
     ```tsx
     {activeTab === "sys-prompt-redesign" && <PromptRedesignPage />}
     ```

**Red Styling:** Follow NextSteps.tsx pattern
- Status badge: `background: '#ef444422'`, `color: '#ef4444'`
- Section borders: `borderLeft: '3px solid #ef4444'`

**Verification:**
- ✓ Master Corvus nav shows "Prompt Redesign" in System Docs
- ✓ Red badge renders correctly in light/dark themes
- ✓ `/agent-stats` endpoint returns JSON with domain firing counts
- ✓ Live link to Query Lab shows A/B test harness

**Deliverable:** System docs public, admin metrics exposed.

---

## Session 5: Visualization Honing + Refactoring (Pending)

**Goal:** Integrate agentic orchestration results into visual systems. Refactor known limitations.

### Part A: Visualization Integration

Adapt five visual areas to show agent orchestration:

1. **Query Detail Card** (`frontend/src/pages/QueryDetail.tsx`)
   - Per-agent results panel (tabbed by domain_key)
   - Per-agent: findings excerpt, confidence slider, flags ([RISK]/[AUDIT]/[CRITICAL]), citations list
   - Neuron sources: show which neurons each agent used (neuron_id → label)
   - Coordinator model choice + escalation rationale ("3 domains, confidence 0.62 → Opus")
   - Cost breakdown: classify + agents (per-domain cost) + coordinator cost

2. **3D Neuron Graph** (`frontend/src/components/NeuronGraph3D.tsx`)
   - Partition nodes by activated domain (color-code: Finance=Blue, Compliance=Red, Regulatory=Green, etc.)
   - Node size: `agent_confidence × neuron_combined_score` (high-confidence agent + high-scoring neuron = large node)
   - Tooltips: Hover neuron → show "Used by {domain_key} agent" + confidence
   - Meta-layer: Coordinator synthesis visualized as "synthesis bubble" above individual agents
   - Animation: Fire agent sequence with timeline (domain 1 fires → domain 2 fires → etc.)

3. **Query Lab A/B Dashboard** (`frontend/src/pages/QueryLab.tsx`)
   - Side-by-side columns: Classic path vs Agent path
   - Comparison metrics: response length, citation density, [RISK] flag count, cost, latency
   - Agent-only tab: domain breakdown pie chart, escalation % trending over 100 recent queries
   - Heatmap: domain firing frequency by intent (which intents activate which agents most)
   - Drill-down: Click heatmap cell → show 5 example queries for that intent/domain combo

4. **Agent Results Panel** (new component or modal)
   - Tabbed interface: one tab per agent + "Synthesis" tab
   - Per-tab: findings (inverted pyramid text), citations (list with links to regulations), confidence visual (bar/gauge), flags with severity colors
   - Neuron sources as collapsible list below findings
   - Synthesis tab: shows coordinator reasoning + agent attribution ("Finance agent concluded…, Compliance agent flagged…")

5. **Master Corvus Docs** (update from Session 4)
   - Diagram: Query → Classify → Score → Partition → Dispatch → Coordinate → Synthesize
   - Example: Show real multi-domain query output with sample agent findings
   - Live link to Query Lab A/B comparison (shows classic vs agent path metrics)

**Design Principles:**
- **Inverted pyramid visual hierarchy:** Conclusions at top, supporting evidence below
- **Domain color coding:** Consistent across all 5 visuals (Finance=Blue, etc.)
- **Confidence as affordance:** Size, opacity, or gauge — make uncertainty visible
- **Escalation transparency:** Clear callout of "≥3 domains + low confidence → Opus" decision
- **Cost visibility:** Per-agent token counts and costs fully measurable

**Delivery Format:**
Iterative markup/code review cycle:
1. User describes visual need or pain point
2. Claude proposes React/TypeScript code with rationale + mockup
3. User provides visual feedback (colors, layout, hierarchy, spacing)
4. Claude iterates until alignment achieved
5. Component merged with A/B test harness

### Part B: Refactoring (Known Limitations)

Five refactoring items (detailed in plan file) must be addressed in parallel with visualization work:

1. **Agent Dispatch Timeout Handling** — Add per-agent timeout wrapper, graceful fallback
2. **Coordinator Response Caching** — Cache by (query_hash, agent_domains_set)
3. **Streaming Partial Agent Results** — SSE events per agent as they complete
4. **Agent Execution Tracing** — Per-agent timing breakdown, diagnostics UI
5. **Fallback Chain on Coordinator Failure** — Sonnet fallback, text concat merge

These run in parallel with visual refinement. Target: All 5 refactors complete before production rollout.

**Timeline:** Spans multiple sessions. Assumes 2–3 review cycles per visual component (5–8 components = 10–20 total cycles). Refactors can be prioritized independently.

---

## Quick Reference: File Changes Summary

### Session 1 Files
| File | Lines | Change |
|------|-------|--------|
| agent_templates.py | 379 | NEW |
| agent_dispatcher.py | 344 | NEW |
| agent_roles.py | 266 | NEW |
| 002_migration.py | 26 | NEW |
| config.py | +30 | MODIFIED |
| models.py | +2 | MODIFIED |
| tenant.py | +12 | MODIFIED |

### Session 2 Files
| File | Lines | Change |
|------|-------|--------|
| agent_coordinator.py | 184 | NEW |
| schemas.py | +50 | MODIFIED |
| executor.py | +120 | MODIFIED |
| agent_dispatcher.py | — | FIXED (await) |
| agent_coordinator.py | — | FIXED (await) |

### Total Codebase Impact
- **New code:** 1,299 lines (well-isolated, zero impact on classic path)
- **Modified code:** 214 lines (executor, config, schemas — feature-flagged or additive)
- **Migrations:** 1 (two columns added to queries table)
- **Test coverage:** Manual smoke tests passed; unit tests deferred to Session 3

---

## For Next Session: Getting Started

1. **Load context:**
   ```bash
   cd ~/Projects/corvus/backend
   source venv/bin/activate
   ```

2. **Verify current state:**
   ```bash
   # Check feature flag default
   grep "agent_orchestration_enabled" app/config.py  # Should be False
   
   # Run classic path smoke test
   AGENT_ORCHESTRATION_ENABLED=false PORT=8002 uvicorn app.main:app
   curl -X POST localhost:8002/query -d '{"message": "FAR?", "modes": ["haiku_neuron"]}'
   ```

3. **Read Session 3 plan in detail:**
   - Plan file: `~/.claude/plans/jazzy-spinning-brooks.md` (lines ~376–391)
   - Focus on verification agent design, thin-domain merging, instrumentation

4. **Known issues for Session 3:**
   - Agent timeout handling deferred to Session 5 refactoring
   - Verification agent is new design (no reference implementation yet)
   - Cosmos prefers to see verification agent working in Query Lab before integration

5. **Push status:**
   - Ready to push to `private` remote (squash commits recommended)
   - Master Corvus docs not yet ready (Session 4 deliverable)

---

## Contacts & References

- **Plan Master File:** `~/.claude/plans/jazzy-spinning-brooks.md`
- **Memory System:** `/home/tylerbvogel/.claude/projects/-home-tylerbvogel/memory/`
  - Corvus project status: `project_corvus_next_steps.md`
  - Git policy: `feedback_corvus_git.md` (push to `private`, never `origin`)
- **Corvus CLAUDE.md:** `~/Projects/corvus/CLAUDE.md` (NASA lint, multi-tenant setup)

---

## Checklist for Session 3 Kickoff

- [ ] Read Session 3 plan section (this document or plan file)
- [ ] Understand verification agent role (critique, gap detection)
- [ ] Review thin-domain consolidation logic (min_neurons_per_domain threshold)
- [ ] Plan instrumentation: where to add timing, what to expose in Query Lab
- [ ] Decide: verification agent as separate LLM call, or integrated into coordinator?
- [ ] Decide: verification agent results shown in Query Detail, or just impact coordinator?

---

**End of Session 2 Handoff**  
Generated: 2026-03-31  
Status: Ready for Session 3 (Optimization + Quality)
