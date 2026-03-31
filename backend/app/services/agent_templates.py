"""Static, cacheable agent system prompts and prompt builders.

All static persona sections end with DYNAMIC_CONTEXT_DELIMITER on their own line
to establish the explicit prompt caching boundary (Claude Code architecture pattern).
"""

from types import MappingProxyType
from app.models import Neuron
from app.services.scoring_engine import NeuronScoreBreakdown

# Cache boundary delimiter — signals where static (cacheable) portion ends
DYNAMIC_CONTEXT_DELIMITER: str = "=== DYNAMIC CONTEXT STARTS HERE ==="

# ═══════════════════════════════════════════════════════════════════
# Static Coordinator Agent Prompt
# ═══════════════════════════════════════════════════════════════════

COORDINATOR_PROMPT: str = """You are a synthesis coordinator for an aerospace defense knowledge system.
Your role is to integrate findings from N specialized domain agents into a single coherent answer.

## Synthesis Rules

1. Lead with the single most actionable finding (inverted pyramid: conclusion first, evidence second)
2. Surface all [RISK], [AUDIT], and [CRITICAL] flags first before other content
3. When agents conflict or disagree, note the conflict explicitly and cite which agents disagree
4. Cite the specific agent domain for each key claim (e.g. "Finance Agent found...", "Compliance Agent flagged...")
5. If overall confidence across agents is low (<0.6), explicitly state your confidence level
6. Never fabricate regulation numbers or standard citations not present in agent findings
7. Prefer agent findings that have [citations] to those without
8. If an agent encountered an error, acknowledge it and work with findings from other agents

## Output Structure

Begin with: [Most important finding, 1-2 sentences]
Then: [RISK]/[AUDIT]/[CRITICAL] flags from all agents
Then: [Key supporting evidence from agents, domain-specific]
Then: [Recommended action]
Finally: [Confidence assessment if not HIGH]

{}"""

# ═══════════════════════════════════════════════════════════════════
# Static Verification Agent Prompt
# ═══════════════════════════════════════════════════════════════════

VERIFICATION_AGENT_PROMPT: str = """You are a verification agent. Your role is to challenge and rigorously examine the findings of a primary domain agent.

## Verification Mandate

Look for:
1. Claims that lack citations or evidence
2. Regulation/standard references that appear imprecise, incorrect, or outdated
3. Risks or edge cases the primary agent may have understated
4. Missing qualifications or uncertainty statements ("if...", "may depend on...")
5. Overconfidence given the complexity of the domain

## Output Structure

If findings are sound: Confirm concisely with your rationale (1-2 sentences).
If gaps found: List them (1 per line) with severity: CRITICAL / HIGH / MEDIUM / LOW.
If citations missing: Note which claims need evidence.

Be direct. Do not repeat the primary agent's findings.

{}"""

# ═══════════════════════════════════════════════════════════════════
# Fallback Agent Template
# ═══════════════════════════════════════════════════════════════════

GENERIC_AGENT_TEMPLATE: str = """You are a domain specialist expert. Your role is to provide precise, well-cited guidance.

## Response Rules

1. Lead with your key recommendation or finding (1-2 sentences)
2. Support it with specific citations, regulation numbers, or standard references
3. Include any [RISK] or [AUDIT] flags that apply
4. Explain when to use this approach vs alternatives (trade-offs)
5. State your confidence level (HIGH/MEDIUM/LOW)
6. If uncertain about a fact, say so explicitly rather than guessing

## Output Format

Respond in JSON:
{{
  "findings": "Your key finding, then evidence",
  "citations": ["Citation 1", "Citation 2"],
  "confidence": 0.85,
  "flags": ["[RISK]", "[AUDIT]"]
}}

{}"""

# ═══════════════════════════════════════════════════════════════════
# Agent Role Templates (domain-agnostic defaults)
# ═══════════════════════════════════════════════════════════════════

AGENT_ROLE_TEMPLATES: MappingProxyType[str, str] = MappingProxyType({
    "cost_accounting": """You are a defense contractor cost accountant. Expertise: CAS, FAR Part 31, DCAA, indirect rates.

## Response Rules

1. State the cost treatment or accounting approach
2. Cite applicable FAR/CAS clause with section numbers (e.g. FAR 31.205-6, CAS 401)
3. Flag [AUDIT] if high-risk or [COMPLIANCE] if requires documentation
4. Explain the compliance or audit implication

{}""",

    "compliance": """You are a FAR/DFARS compliance specialist. Expertise: FAR, DFARS, CAS, DCAA, ITAR, EAR.

## Response Rules

1. State compliance requirement or exposure directly
2. Cite applicable regulation clause with exact numbers (e.g. FAR 52.215-2)
3. Flag [RISK] if compliance exposure or audit trigger exists
4. State the recommended action to achieve/maintain compliance

{}""",

    "far_dfars": """You are a FAR/DFARS procurement and contract specialist.

## Response Rules

1. State the FAR/DFARS requirement or procedure
2. Cite specific clause numbers (e.g. FAR 15.2, DFARS 252.227-7013)
3. Explain applicability (when, to whom, under what conditions)
4. Flag [RISK] if non-compliance has contract or regulatory consequences

{}""",

    "itar_ear": """You are an ITAR/EAR export control specialist. Expertise: USML, EAR99, 15 CFR, 22 CFR.

## Response Rules

1. State export control status or requirement
2. Cite ITAR/EAR clause or category (e.g. 22 CFR 121.1, 15 CFR 730)
3. Flag [CRITICAL] if unauthorized export/re-export could trigger penalties
4. Recommend required licensing, notifications, or compliance steps

{}""",

    "data_engineer": """You are a senior data engineer. Expertise: Databricks, Spark, Delta Lake, ETL patterns.

## Response Rules

1. Recommend the approach with specific tools/APIs
2. Include code example if applicable (Python, SQL, Scala)
3. Explain when to use this vs alternatives (trade-offs, performance)
4. Flag common pitfalls or failure modes

{}""",

    "general": """You are a knowledgeable domain expert in aerospace defense.

## Response Rules

1. Provide your key recommendation or finding
2. Support with specific references or examples
3. Flag any risks or uncertainties
4. State your confidence level

{}""",
})


# ═══════════════════════════════════════════════════════════════════
# Prompt Builder Functions
# ═══════════════════════════════════════════════════════════════════

def build_agent_system_prompt(
    role_key: str,
    department: str,
    tenant_personas: dict[str, str] | None = None,
) -> str:
    """Build the static persona section of an agent's system prompt.

    Tries tenant-specific personas first, falls back to AGENT_ROLE_TEMPLATES,
    falls back to GENERIC_AGENT_TEMPLATE.
    Always ends with DYNAMIC_CONTEXT_DELIMITER on its own line.

    Args:
        role_key: e.g. "cost_accounting", "compliance"
        department: e.g. "Finance", "Regulatory"
        tenant_personas: optional dict of overrides from tenant config

    Returns:
        Static persona prompt ending with delimiter
    """
    assert role_key, "role_key must be non-empty"
    assert department, "department must be non-empty"

    # Try tenant override first
    if tenant_personas and role_key in tenant_personas:
        persona = tenant_personas[role_key]
    # Fall back to template
    elif role_key in AGENT_ROLE_TEMPLATES:
        persona = AGENT_ROLE_TEMPLATES[role_key]
    # Generic fallback
    else:
        persona = GENERIC_AGENT_TEMPLATE

    # Inject delimiter
    if not persona.endswith(DYNAMIC_CONTEXT_DELIMITER):
        persona = persona.format(DYNAMIC_CONTEXT_DELIMITER)
    return persona.rstrip() + "\n" + DYNAMIC_CONTEXT_DELIMITER


def build_agent_dynamic_section(
    neurons: list[tuple[NeuronScoreBreakdown, Neuron]],
    query: str,
    intent: str,
    closing_instruction: str,
    token_budget: int = 3000,
) -> str:
    """Build the dynamic neuron content section of an agent's prompt.

    Packs neurons sorted by combined score descending.
    Includes the query, intent, and closing instruction.

    Args:
        neurons: list of (score, neuron) tuples
        query: user query string
        intent: classified intent (e.g. "compliance_risk_review")
        closing_instruction: intent-specific output format instruction
        token_budget: max tokens for this section (rough estimate)

    Returns:
        Dynamic section string (neurons + closing instruction)
    """
    assert neurons is not None, "neurons list must not be None"
    assert query, "query must be non-empty"
    assert closing_instruction, "closing_instruction must be non-empty"

    parts = []
    parts.append(f"\n## Query: {query}")
    parts.append(f"Intent: {intent}\n")

    # Pack neurons sorted by score descending
    parts.append("## Reference Knowledge\n")
    for score, neuron in neurons:
        if neuron.content:
            # Format: [N-{id}] label with metadata for traceability
            dept_info = f" | Dept: {neuron.department}" if neuron.department else ""
            role_info = f" | Role: {neuron.role_key}" if neuron.role_key else ""
            lookup_hint = f" | DB lookup: SELECT * FROM neurons WHERE id = {neuron.id}"
            entry = f"**[N-{neuron.id}] {neuron.label}**\nLayer: {neuron.layer}{dept_info}{role_info}\nScore: {score.combined:.2f}{lookup_hint}\n{neuron.content}"
        elif neuron.summary:
            entry = f"- [N-{neuron.id}] {neuron.summary} (score: {score.combined:.2f})"
        else:
            continue
        parts.append(entry)

    # Closing instruction
    closing_with_citation = f"{closing_instruction}\n\nCite referenced neurons by their [N-{{id}}] identifier inline with your findings."
    parts.append(f"\n{closing_with_citation}")

    return "\n".join(parts)


def build_coordinator_prompt(
    agent_results: list,  # AgentResult list — avoid circular import
    query: str,
    intent: str,
) -> str:
    """Build coordinator synthesis prompt from agent results.

    Args:
        agent_results: list of AgentResult dicts
        query: user query
        intent: classified intent

    Returns:
        Full coordinator system prompt + dynamic section
    """
    assert agent_results, "agent_results must be non-empty"
    assert query, "query must be non-empty"

    # Build static portion
    static = COORDINATOR_PROMPT.format(DYNAMIC_CONTEXT_DELIMITER)

    # Build dynamic section with agent findings
    dynamic_parts = []
    dynamic_parts.append(f"\nQuery: {query}")
    dynamic_parts.append(f"Intent: {intent}\n")
    dynamic_parts.append("## Agent Findings\n")

    for i, result in enumerate(agent_results, 1):
        domain = result.get("domain_key", "Unknown")
        findings = result.get("findings", "")
        confidence = result.get("confidence", 0)
        flags = result.get("flags", [])
        error = result.get("error", False)

        if error:
            dynamic_parts.append(f"{i}. [{domain}] ERROR: {result.get('error_message', 'Unknown error')}")
        else:
            flag_str = " ".join(flags) if flags else ""
            dynamic_parts.append(f"{i}. [{domain}] (confidence: {confidence:.2f}) {flag_str}")
            dynamic_parts.append(f"   {findings}\n")

    dynamic_parts.append("\nNow synthesize the above findings into a single coherent response.")

    return static.rstrip() + "\n" + "\n".join(dynamic_parts)


def build_verification_prompt(
    primary_findings: str,
    domain_key: str,
    query: str,
) -> str:
    """Build verification agent prompt to challenge primary findings.

    Args:
        primary_findings: the primary agent's findings string
        domain_key: which domain was being verified (for context)
        query: the user query (for context)

    Returns:
        Full verification system prompt + dynamic section
    """
    assert primary_findings, "primary_findings must be non-empty"
    assert domain_key, "domain_key must be non-empty"
    assert query, "query must be non-empty"

    # Build static portion
    static = VERIFICATION_AGENT_PROMPT.format(DYNAMIC_CONTEXT_DELIMITER)

    # Build dynamic section with findings to verify
    dynamic_parts = []
    dynamic_parts.append(f"\nQuery: {query}")
    dynamic_parts.append(f"Domain Agent: {domain_key}\n")
    dynamic_parts.append("## Findings to Verify\n")
    dynamic_parts.append(primary_findings)
    dynamic_parts.append("\n\nVerify the above findings. Identify gaps, imprecision, or missing uncertainty.")

    return static.rstrip() + "\n" + "\n".join(dynamic_parts)
