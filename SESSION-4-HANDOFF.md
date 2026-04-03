# Session 4 Handoff — Graph Integrity System

## What Was Built

A backend system for checking the internal consistency of the neuron graph, inspired by neurological self-correcting processes. Five processes were implemented as services + a unified API router. No frontend changes were made — the UI is the next step.

## Design Philosophy

The existing learning methods (query tests, autopilot, engrams, document ingestion) all **add** knowledge. The integrity system **audits** what's already there: detecting duplicates, contradictions, missing connections, weight drift, and stale content. Each process is modeled after a specific neurological mechanism. All graph modifications flow through the existing `AutopilotProposal` workflow — human approval required, full traceability preserved.

---

## Backend Changes

### New Files

| File | Purpose |
|---|---|
| `backend/alembic/versions/005_add_integrity_system.py` | Migration: `integrity_scans` table, `integrity_findings` table, `last_accessed_at` column on `neurons` |
| `backend/app/services/integrity/__init__.py` | Shared dataclasses (`IntegrityScanResult`, `IntegrityFindingData`) |
| `backend/app/services/integrity/similarity.py` | Bulk pairwise embedding similarity via numpy matrix multiply. Used by duplicate detection, missing connections, and conflict monitoring. |
| `backend/app/services/integrity/homeostasis.py` | **Synaptic Homeostasis** — Multiplicative weight renormalization. Prevents co-firing weight inflation from continuous learning. Configurable scale factor, floor threshold, scope. Dry-run shows before/after weight distributions. |
| `backend/app/services/integrity/pattern_separation.py` | **Pattern Separation** — Near-duplicate neuron detection via cosine similarity on 384-dim embeddings. Flags pairs above threshold (default 0.92). Resolution: merge or differentiate. |
| `backend/app/services/integrity/pattern_completion.py` | **Pattern Completion** — Missing semantic connections. Finds neuron pairs with high content similarity but no co-firing edge. Top-down (semantic inference) vs co-firing's bottom-up (observed correlation). Filters out existing edges and parent-child chains. |
| `backend/app/services/integrity/conflict_monitor.py` | **Conflict Monitoring** — Contradiction detection. Phase 1: embedding prefilter (similarity 0.60–0.85). Phase 2: Haiku LLM classification via `claude_chat()`. Three resolution paths: A correct, both correct + add context, unresolved. |
| `backend/app/services/integrity/aging_review.py` | **Age-Based Review** — Surfaces stale neurons. Thresholds by source_type: regulatory=3yr, operational=1.5yr, default=2yr. Prioritizes neurons that are stale AND heavily used. |
| `backend/app/routers/integrity.py` | Unified router at `/admin/integrity` with 14 endpoints |

### Modified Files

| File | Change |
|---|---|
| `backend/app/models.py` | Added `IntegrityScan` and `IntegrityFinding` models. Added `last_accessed_at` (DateTime, nullable) to `Neuron`. |
| `backend/app/config.py` | Added 10 integrity settings: `integrity_homeostasis_default_scale`, `integrity_homeostasis_floor_threshold`, `integrity_duplicate_threshold`, `integrity_completion_threshold`, `integrity_conflict_sim_min`, `integrity_conflict_sim_max`, `integrity_aging_regulatory_days`, `integrity_aging_operational_days`, `integrity_aging_default_days`, `integrity_max_scan_neurons` |
| `backend/app/services/neuron_service.py` | Sets `neuron.last_accessed_at` on every firing (in the `record_firing` function, ~line 906) |
| `backend/app/routers/proposals.py` | Added `_apply_rescale_item()`, `_apply_link_item()`, `_apply_merge_item()` handlers. Updated `apply_proposal()` to dispatch these new action types and invalidate adjacency cache after edge modifications. |
| `backend/app/main.py` | Registered `integrity.router` |

### Database Changes (Migration 005)

- Table `integrity_scans`: id, scan_type, scope, status, parameters_json, findings_count, initiated_by, started_at, completed_at, created_at
- Table `integrity_findings`: id, scan_id (FK), finding_type, severity, priority_score, description, detail_json, neuron_ids_json, edge_ids_json, status, resolution, proposal_id (FK), resolved_by, resolved_at, created_at
- Column `neurons.last_accessed_at`: DateTime nullable — updated on each neuron firing

---

## API Endpoints (all under `/admin/integrity`)

### Scan Endpoints (POST, all dry-run)
- `POST /homeostasis/scan` — Body: `{scope, scale_factor, floor_threshold, initiated_by}`
- `POST /duplicates/scan` — Body: `{scope, similarity_threshold, max_pairs, cross_department_only, initiated_by}`
- `POST /connections/scan` — Body: `{scope, similarity_threshold, max_suggestions, exclude_same_parent, initiated_by}`
- `POST /conflicts/scan` — Body: `{scope, sim_min, sim_max, batch_size, max_pairs, initiated_by}` (calls LLM, has cost)
- `POST /aging/scan` — Body: `{scope, staleness_overrides, include_never_verified, min_invocations, initiated_by}`

### Homeostasis Apply
- `POST /homeostasis/{scan_id}/apply` — Body: `{reviewer}` → creates proposal for standard approve/apply workflow

### Finding Management
- `GET /scans` — Query: scan_type, status, limit
- `GET /scans/{scan_id}` — Full scan detail with all findings
- `GET /findings` — Query: finding_type, status, severity, limit
- `GET /findings/{finding_id}` — Detail with full neuron content loaded
- `POST /findings/{finding_id}/resolve` — Body: `{resolution, reviewer, notes}`
- `POST /findings/{finding_id}/dismiss` — Body: `{reviewer, notes}`
- `POST /findings/bulk-resolve` — Body: `{finding_ids, resolution, reviewer, notes}`

### Dashboard
- `GET /dashboard` — Returns: `{open_findings_total, open_by_type, open_by_severity, recent_scans}`

---

## Frontend Work Needed

### New Page: Integrity (`IntegrityPage.tsx` or similar)

Accessible from the admin area. Four sections:

#### 1. Dashboard Tab
- **Endpoint**: `GET /admin/integrity/dashboard`
- Show open finding counts by type (5 categories) as cards or a summary bar
- Severity breakdown (info/warning/critical) — could be a simple color-coded count
- Recent scans list (last 10) with type, scope, findings count, timestamp

#### 2. Scan Tab
- One sub-section per process type (tabs or accordion)
- Each has a form with the configurable parameters (scope dropdown, threshold sliders/inputs)
- "Run Scan" button calls the corresponding POST endpoint
- Results appear inline: findings count + list of findings with severity indicators
- **Homeostasis special**: show before/after weight distribution stats (the scan response includes `before` and `after` distribution objects with mean, median, percentiles). A histogram chart would be ideal but a stats comparison table works too. Include an "Apply" button that calls `/homeostasis/{scan_id}/apply`.

#### 3. Findings Queue Tab
- **Endpoint**: `GET /admin/integrity/findings?status=open`
- Sortable/filterable table: finding_type, severity, priority_score, description, neuron IDs, created_at
- Click a finding to see detail view (`GET /findings/{id}`) which loads full neuron content
- Action buttons vary by finding type:
  - **Duplicates**: "Merge" / "Differentiate" / "Dismiss"
  - **Missing Connections**: "Link" / "Dismiss"
  - **Contradictions**: "A Correct" / "B Correct" / "Add Context" / "Flag Expert" / "Dismiss"
  - **Stale Content**: "Mark Reviewed" / "Flag for Update" / "Dismiss"
- Bulk action toolbar: select multiple findings, bulk-resolve or bulk-dismiss
- Resolution calls `POST /findings/{id}/resolve` with the chosen resolution string

#### 4. Integration with Existing Pages
- **Proposal Queue**: Integrity proposals already appear there (they use the standard `AutopilotProposal` model with `gap_source` values like `integrity_homeostasis`, `integrity_duplicate`, etc.). No changes needed — they just show up.
- **Neuron Detail** (optional enhancement): Could show a badge or alert if there are open integrity findings referencing that neuron. Query: `GET /findings?status=open` and filter client-side by neuron ID, or add a dedicated endpoint later.

### UI Patterns to Follow
- The scan forms should match the existing admin UI patterns (the autopilot config form, the document ingest upload form)
- The findings queue should feel similar to the proposal queue — same table/card layout, same approve/reject interaction pattern
- The dashboard should be lightweight — it's a status overview, not an analytics deep-dive

### Resolution Strings (for the `resolution` field in resolve requests)
- `merged` — duplicate was merged into survivor
- `differentiated` — distinguishing context added to both
- `linked` — new edge created between neurons
- `a_correct` — neuron A is correct, B will be corrected
- `b_correct` — neuron B is correct, A will be corrected
- `context_added` — both correct, added distinguishing context
- `reviewed` — stale content confirmed still accurate
- `dismissed` — acknowledged, no action needed
- `rescaled` — homeostasis weights applied

---

## What Was NOT Built (Shelved by Design)

- **Synaptic Pruning**: Not implementing. Documentation can be relevant for years without being accessed (e.g., certification renewals on 5-year cycles). Single-user testing would bias what looks "stale."
- **Lateral Inhibition**: Shelved. The graph is too small (thousands to maybe a million neurons) compared to the brain (billions). Suppressing second-best matches would hide knowledge rather than sharpen signals at this scale.
