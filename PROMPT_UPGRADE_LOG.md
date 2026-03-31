# Corvus Prompt Engineering Upgrade — Implementation Log

**Date:** March 31, 2026  
**Tenant:** corvus-aero (Phase 1)  
**Status:** ✓ Complete and tested

## Changes Implemented

### 1. Enriched Voice Map (HIGHEST IMPACT)
**File:** `backend/tenants/corvus-aero/voices.py`

All 15 intent voices expanded from 1-line persona declarations to structured briefing blocks containing:
- Persona + domain authority framing
- Explicit `## Response structure` sections (4-part format per intent type)
- Worked examples showing correct/incorrect answers
- Uncertainty calibration notes

**Example transformation:**
```python
# BEFORE (1 line)
"compliance": "You are a compliance and regulatory expert. Respond with precision, cite specific regulations (FAR, DFARS, CAS), and flag any risk areas."

# AFTER (15+ lines per intent)
"compliance": """You are a compliance and regulatory expert with deep knowledge of FAR, DFARS, CAS, DCAA, ITAR, and EAR regulations.

## Response structure
1. Direct answer (1-2 sentences)
2. Applicable regulation(s) with clause numbers (e.g., FAR 31.205-6, DFARS 252.225-7001, CAS 401)
3. [RISK] flags if any compliance exposure or audit trigger points exist
4. Recommended action

## Example
Q: Does our subcontractor need DCAA-approved timekeeping?
A: Yes — required under FAR 52.215-2 and CAS 401 for cost-type contracts. [RISK] Non-compliant timekeeping triggers DCAA audit findings and potential cost disallowance. Require written attestation of approved system before contract award.

If uncertain about a specific clause number or applicability, state that explicitly rather than approximating."""
```

**Intent voices updated:** compliance, engineering, data_engineer, elt, databricks, pipeline, finance, procurement, proposal, program_management, hr, safety, it_security, executive, regulatory, general_query

---

### 2. Signal-Aware Query Briefing
**File:** `backend/app/services/prompt_assembler.py`

Added new function `_build_signal_briefing()` that injects context explaining why neurons were selected:

```
## Query Analysis
Intent: compliance_risk_review | Confidence: HIGH (max relevance ≥ 0.85)
Active neurons: 8 regulatory + 12 functional | Signals: relevance=0.85, impact=0.71
```

**Confidence levels:**
- `HIGH`: max relevance ≥ 0.8
- `MEDIUM`: max relevance 0.5–0.79
- `LOW`: max relevance < 0.5 (appends note: "State uncertainty explicitly rather than guessing")

This tells Haiku upfront:
- Why these specific neurons were selected (trust signal)
- How confident the pipeline is in the routing
- That low-confidence queries should hedge uncertainty

**Function location:** `prompt_assembler.py:_build_signal_briefing()` (~20 lines)

---

### 3. Intent-Specific Closing Instructions
**File:** `backend/app/services/prompt_assembler.py`

Added `CLOSING_INSTRUCTION_MAP` dict with 16 intent-keyed instructions that replace the generic single closing:

```python
CLOSING_INSTRUCTION_MAP = MappingProxyType({
    "compliance": "Answer with: (1) Direct answer, (2) Cited regulation clause numbers (FAR/DFARS/CAS/ITAR), (3) [RISK] flags if any compliance exposure, (4) Recommended action. Never fabricate regulation numbers — if uncertain, say so explicitly.",
    "engineering": "Answer with: (1) Technical recommendation, (2) Referenced standard with section number (MIL-STD, DO-178C, AS9100, ASME Y14.5, SAE), (3) Implementation steps (numbered, specific), (4) Verification method or acceptance criteria.",
    "data_engineer": "Answer with: (1) Recommended approach with specific tools, (2) Code example if applicable, (3) When to use this vs alternatives (tradeoffs), (4) Common pitfalls or failure modes.",
    # ... 13 more intents ...
})
```

Each intent's closing instruction specifies the exact output structure Haiku should follow, removing ambiguity about what "good" looks like.

**Function:** `_get_closing_instruction(intent, is_low_confidence)` (~15 lines) — matches intent prefix, falls back to `general_query`, optionally appends low-confidence note.

---

### 4. Classifier Prompt with Worked Examples
**File:** `backend/tenants/corvus-aero/classifier_prompt.py`

Appended 4 concrete worked examples to `CLASSIFY_SYSTEM_PROMPT`:
```
Example 1 (ITAR/Export Control):
Q: "What are our ITAR obligations for the LIDAR sensor component we're exporting?"
A: {"intent": "compliance_risk_review", "departments": ["Regulatory", "Contracts & Compliance"], "role_keys": ["itar_ear", "export_control"], "keywords": ["ITAR", "export control", "LIDAR", "EAR99", "USML"]}

Example 2 (Data Engineering/Databricks):
Q: "How do I write a Delta Lake merge statement that handles late-arriving data?"
A: {"intent": "data_pipeline_design", "departments": ["Engineering"], "role_keys": ["data_engineer", "sw_eng"], "keywords": ["Delta Lake", "merge", "late-arriving data", "upsert", "Databricks"]}

Example 3 (Finance/Cost Accounting):
Q: "What's the cost accounting treatment for IR&D expenses?"
A: {"intent": "cost_reporting", "departments": ["Finance", "Contracts & Compliance"], "role_keys": ["cost_accountant", "far_specialist"], "keywords": ["IR&D", "cost accounting", "CAS 420", "FAR 31.205-18", "indirect"]}

Example 4 (Proposal/SBIR):
Q: "We need to submit a proposal for the AFWERX SBIR topic — where do we start?"
A: {"intent": "proposal_development", "departments": ["Business Development", "Contracts & Compliance"], "role_keys": ["proposal_mgr", "capture_mgr", "contract_analyst"], "keywords": ["SBIR", "AFWERX", "proposal", "Section L", "Section M"]}
```

These are domain-specific edge cases where the classifier commonly misroutes. Haiku will now have concrete examples of correct classification.

---

### 5. Signal Rationale on High-Scoring Neurons
**File:** `backend/app/services/prompt_assembler.py`

Modified `_pack_neuron()` to surface why high-scoring neurons were selected:

```python
# BEFORE
**FAR 31.205-6 Compensation for Personal Services** [REGULATORY] (L3, score: 0.87)

# AFTER (when score.combined >= 0.8)
**FAR 31.205-6 Compensation for Personal Services** [REGULATORY] (L3) ← relevance, impact driver
```

The signal rationale (`← relevance, impact driver`) is built from the two strongest signals (relevance, impact, recency, burst) with values > 0.3. This shows Haiku at a glance why each neuron matters.

**Modified function:** `_pack_neuron()` (~40 lines, from 25)

---

## Integration Points

### Updated `assemble_prompt()` workflow:
1. `_build_prompt_header()` — voice header + authority legend
2. **NEW:** `_build_signal_briefing()` — Query Analysis briefing
3. `_pack_prior_context()` — conversation continuity
4. `_pack_functional_section()` — domain knowledge neurons (now with signal notes on high-scoring)
5. `_pack_regulatory_section()` — regulatory neurons (now with signal notes on high-scoring)
6. `_pack_resolved_regulations()` — live eCFR text
7. **NEW:** `_get_closing_instruction()` — intent-specific closing, optionally with low-confidence calibration

### Token efficiency:
- Voice map expansion: +~400–500 tokens per query (voices are 15–25 lines each, embedded once per prompt)
- Signal briefing: +~30–50 tokens (1-2 line summary)
- Closing instructions: +~20–40 tokens (intent-specific guidance)
- **Total overhead: ~450–600 tokens** out of 8000-token budget (5–7.5%) — well within tolerance

---

## NASA Lint Compliance

All new code adheres to CLAUDE.md NASA standards:

✓ **JPL-6** (no mutable globals): All module-level dicts use `MappingProxyType`  
✓ **JPL-4** (functions under 60 lines): New functions are 15–25 lines  
✓ **NPR-3** (no bare except): No bare `except` clauses  
✓ **JPL-5** (assertions): Input assumptions documented/asserted  
✓ Docstrings and comments preserved  

**Syntax validation:** `python -m py_compile` on all 3 modified files — passed

---

## Testing & Verification

### ✓ Syntax validation passed
```bash
python -m py_compile app/services/prompt_assembler.py \
  tenants/corvus-aero/voices.py \
  tenants/corvus-aero/classifier_prompt.py
```

### ✓ Import and functionality tests passed
- All 16 closing instructions loaded and matched correctly
- All 16 voice maps loaded with enriched structure
- Signal briefing generation works for HIGH/MEDIUM/LOW confidence levels
- Neuron signal rationale formatting correct
- Backward compatibility maintained (falls back to general_query on unknown intent)

### ✓ Dev server running
```
TENANT_ID=corvus-aero PORT=8002 uvicorn app.main:app --port 8002 --reload
```
Server is healthy and watching for hot-reload of Python files.

---

## Files Modified

| File | Lines Changed | Type |
|---|---|---|
| `backend/tenants/corvus-aero/voices.py` | +250 | Enhanced voices (structured briefings) |
| `backend/tenants/corvus-aero/classifier_prompt.py` | +20 | Added 4 worked examples |
| `backend/app/services/prompt_assembler.py` | +150 | Added 3 helper functions, updated 2 existing functions, added CLOSING_INSTRUCTION_MAP |

---

## Phase 2: Validation Plan

**Seed queries to test in Query Lab** (compare `haiku_neuron` vs `haiku_raw`):

1. "What are the key FAR compliance requirements for our prime contract?"
   - Expect: Specific clause numbers (FAR 31.xxx, FAR 52.xxx), [RISK] flags if pricing disputes
   
2. "Help me understand AS9100 document control requirements"
   - Expect: Section references (AS9100D 4.2.x), implementation steps, verification method
   
3. "What are ITAR restrictions on sharing technical data with foreign nationals?"
   - Expect: EAR/ITAR regulation numbers, [RISK] flags, compliance action
   
4. "Explain DCAA audit requirements for cost-type contracts"
   - Expect: FAR/CAS references, cost accounting standards, audit timing/scope
   
5. "What are the key RCA steps after a manufacturing nonconformance?"
   - Expect: Structured investigation steps, root cause definition, corrective action framework

**Success criteria:**
- Responses contain specific regulation/standard citations with clause numbers
- Responses follow the structured format defined in voices.py (4-part pattern per intent)
- Token count stays under 2000 (structured voices + query = reasonable overhead)
- `## Query Analysis` briefing appears in assembled prompt (check via `/context` endpoint)
- Low-confidence queries include uncertainty disclaimers (max relevance < 0.5)

---

## Phase 3: Rollout to Other Tenants

After aero validation, apply the same enrichment to:
- `backend/tenants/corvus-flow/voices.py` — plumbing domain (6 intents)
- `backend/tenants/corvus-flow/classifier_prompt.py` — plumbing-specific examples

The shared `prompt_assembler.py` changes (signal briefing, closing instructions, neuron signal notes) automatically apply to all tenants since they're domain-agnostic (intent key matching is prefix-based, falls back to `general_query`).

---

## References

- Plan: `/home/tylerbvogel/.claude/plans/jazzy-spinning-brooks.md`
- Corvus Status: `~/Projects/corvus/CORVUS-STATUS.md`
- NASA Lint Rules: `~/Projects/corvus/CLAUDE.md`
- Claude Code Source Insights: `src/` (extracted from `~/src.zip`)

---

**Implementation complete. Dev server running. Ready for validation phase.**
