"""Domain-based agent dispatching and parallel execution.

Partitions scored neurons by (department, role_key), dispatches concurrent
claude_chat calls for each domain agent, returns structured AgentResult list.
"""

import asyncio
import json
import time
from dataclasses import dataclass, field
from app.models import Neuron
from app.services.scoring_engine import NeuronScoreBreakdown
from app.services.claude_cli import claude_chat
from app.services.agent_templates import build_agent_system_prompt, build_agent_dynamic_section
from app.config import settings

# ═══════════════════════════════════════════════════════════════════
# Data Structures
# ═══════════════════════════════════════════════════════════════════

@dataclass
class AgentResult:
    """Result from a single domain agent execution."""

    domain_key: str           # "Finance::cost_accounting"
    department: str
    role_key: str
    role: str                 # display name
    findings: str             # inverted pyramid: conclusion first, evidence after
    citations: list[str] = field(default_factory=list)
    confidence: float = 0.0   # 0.0–1.0 (agent self-reported)
    flags: list[str] = field(default_factory=list)  # [RISK], [AUDIT], [CRITICAL]
    neuron_ids: list[int] = field(default_factory=list)
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    duration_ms: int = 0
    error: bool = False
    error_message: str = ""


@dataclass
class AgentExecution:
    """Result from the full agent dispatch and coordination."""

    agent_results: list[AgentResult] = field(default_factory=list)
    synthesis: str = ""
    coordinator_model: str = "haiku"
    escalated_to_opus: bool = False
    domains_active: list[str] = field(default_factory=list)
    coordinator_input_tokens: int = 0
    coordinator_output_tokens: int = 0
    coordinator_cost_usd: float = 0.0
    total_agents_dispatched: int = 0
    total_cost_usd: float = 0.0
    verification_result: "VerificationResult | None" = None


@dataclass
class VerificationResult:
    """Result from verification agent critique (Session 3)."""

    critique: str
    gaps: list[str] = field(default_factory=list)
    confidence_adjustment: float = 0.0  # -0.3 to +0.1 (negative = less confident)
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    error: bool = False
    error_message: str = ""


# ═══════════════════════════════════════════════════════════════════
# Partition Logic
# ═══════════════════════════════════════════════════════════════════

def partition_neurons_by_domain(
    all_scored: list[NeuronScoreBreakdown],
    neuron_map: dict[int, Neuron],
    confidence_threshold: float = 0.5,
    max_neurons_per_domain: int = 12,
    min_neurons_per_domain: int = 2,
) -> dict[str, list[tuple[NeuronScoreBreakdown, Neuron]]]:
    """Partition scored neurons by (department, role_key) domain key.

    Groups neurons by their domain. Structural neurons (L0–L2, no content) are
    excluded. Neurons below confidence_threshold are excluded.
    Domains with fewer than min_neurons_per_domain are merged into "General::general".

    Args:
        all_scored: list of NeuronScoreBreakdown from scoring pipeline
        neuron_map: dict[neuron_id -> Neuron] from prepare_context
        confidence_threshold: minimum combined score to include neuron (default 0.5)
        max_neurons_per_domain: cap neurons per domain (for token budget)
        min_neurons_per_domain: minimum neurons to activate a domain agent

    Returns:
        dict keyed by "Department::role_key", values are [(score, neuron), ...]
        sorted by combined score descending within each domain
    """
    assert all_scored is not None, "all_scored must not be None"
    assert neuron_map is not None, "neuron_map must not be None"
    assert 0.0 <= confidence_threshold <= 1.0, f"confidence_threshold must be in [0.0, 1.0], got {confidence_threshold}"
    assert max_neurons_per_domain > 0, "max_neurons_per_domain must be positive"
    assert min_neurons_per_domain > 0, "min_neurons_per_domain must be positive"

    # Group by domain
    domains: dict[str, list[tuple[NeuronScoreBreakdown, Neuron]]] = {}

    for score in all_scored:
        # Filter by confidence threshold
        if score.combined < confidence_threshold:
            continue

        neuron = neuron_map.get(score.neuron_id)
        if not neuron:
            continue

        # Skip structural neurons without content
        if not neuron.content and not neuron.summary:
            continue

        # Build domain key
        dept = neuron.department or "General"
        role = neuron.role_key or "general"
        domain_key = f"{dept}::{role}"

        # Add to domain group (capped at max_neurons_per_domain)
        if domain_key not in domains:
            domains[domain_key] = []
        if len(domains[domain_key]) < max_neurons_per_domain:
            domains[domain_key].append((score, neuron))

    # Sort each domain by score descending
    for domain_key in domains:
        domains[domain_key].sort(key=lambda x: x[0].combined, reverse=True)

    # Merge thin domains into General::general
    general_key = "General::general"
    thin_domains = [k for k, v in domains.items() if len(v) < min_neurons_per_domain and k != general_key]

    for thin_key in thin_domains:
        if general_key not in domains:
            domains[general_key] = []
        domains[general_key].extend(domains.pop(thin_key))

    # Re-sort general if it grew
    if general_key in domains:
        domains[general_key].sort(key=lambda x: x[0].combined, reverse=True)

    # Sort dict by neuron count descending (prioritize larger domains)
    return dict(sorted(domains.items(), key=lambda x: len(x[1]), reverse=True))


# ═══════════════════════════════════════════════════════════════════
# Agent Response Parsing (JPL-4: extracted helper)
# ═══════════════════════════════════════════════════════════════════

async def _timed_agent_wrapper(
    domain_key: str, dept: str, role_key: str, coro,
) -> AgentResult:
    """Wrap agent dispatch with timeout (JPL-4: extracted to trim dispatch_agents)."""
    try:
        return await asyncio.wait_for(coro, timeout=settings.agent_timeout_seconds)
    except asyncio.TimeoutError:
        domain_display = role_key.replace("_", " ").title()
        return AgentResult(
            domain_key=domain_key, department=dept, role_key=role_key,
            role=domain_display, findings="", error=True,
            error_message=f"Timed out after {settings.agent_timeout_seconds}s",
            flags=["[AGENT_TIMEOUT]"], confidence=0.0,
        )


def _parse_agent_response(
    text: str, domain_key: str, department: str, role_key: str,
    domain_display: str, neurons: list, response: dict, start_time: float,
) -> AgentResult:
    """Parse agent JSON response with error handling (JPL-4: keep _dispatch_single_agent under 100 lines)."""
    # Strip markdown code blocks if LLM wrapped response in ```json...```
    # Also handle trailing text after closing backticks
    json_text = text.strip()
    if json_text.startswith("```json"):
        json_text = json_text[7:].lstrip("\n")
        # Find closing backticks and take only what's before them
        if "```" in json_text:
            json_text = json_text[:json_text.index("```")].rstrip()
    elif json_text.startswith("```"):
        json_text = json_text[3:].lstrip("\n")
        if "```" in json_text:
            json_text = json_text[:json_text.index("```")].rstrip()

    try:
        parsed = json.loads(json_text)
    except json.JSONDecodeError as e:
        return AgentResult(
            domain_key=domain_key,
            department=department,
            role_key=role_key,
            role=domain_display,
            findings=text,
            confidence=0.5,
            neuron_ids=[s.neuron_id for s, _ in neurons],
            input_tokens=response.get("input_tokens", 0),
            output_tokens=response.get("output_tokens", 0),
            cost_usd=response.get("cost_usd", 0),
            duration_ms=int((time.time() - start_time) * 1000),
            error=True,
            error_message=f"JSON parse error: {str(e)[:100]}",
        )

    findings = parsed.get("findings", "")
    citations = parsed.get("citations", [])
    if not isinstance(citations, list):
        citations = []
    confidence = parsed.get("confidence", 0.5)
    flags = list(parsed.get("flags", []))
    if not isinstance(flags, list):
        flags = []

    if not neurons:
        flags.insert(0, "[DOMAIN_CONTEXT_EMPTY]")

    return AgentResult(
        domain_key=domain_key,
        department=department,
        role_key=role_key,
        role=domain_display,
        findings=findings,
        citations=citations,
        confidence=float(confidence) if confidence else 0.5,
        flags=flags,
        neuron_ids=[s.neuron_id for s, _ in neurons],
        input_tokens=response.get("input_tokens", 0),
        output_tokens=response.get("output_tokens", 0),
        cost_usd=response.get("cost_usd", 0),
        duration_ms=int((time.time() - start_time) * 1000),
        error=False,
    )


# ═══════════════════════════════════════════════════════════════════
# Single Agent Dispatch
# ═══════════════════════════════════════════════════════════════════

async def _dispatch_single_agent(
    domain_key: str,
    department: str,
    role_key: str,
    neurons: list[tuple[NeuronScoreBreakdown, Neuron]],
    query: str,
    intent: str,
    closing_instruction: str,
    agent_token_budget: int,
    tenant_personas: dict[str, str] | None = None,
    model: str = "haiku",
) -> AgentResult:
    """Execute domain agent with error handling (all errors → AgentResult.error)."""
    assert domain_key, "domain_key must be non-empty"
    assert neurons is not None, "neurons list must not be None"
    assert query, "query must be non-empty"

    start_time = time.time()
    domain_display = role_key.replace("_", " ").title()

    try:
        # Build system prompt
        system_prompt = build_agent_system_prompt(role_key, department, tenant_personas)

        # Build dynamic section (handles empty neurons case)
        if neurons:
            dynamic_section = build_agent_dynamic_section(
                neurons, query, intent, closing_instruction, agent_token_budget
            )
        else:
            # Domain context empty — still fire agent but note it
            confidence_threshold = 0.5  # default from config
            dynamic_section = f"""
## Query: {query}
Intent: {intent}

## Reference Knowledge
[DOMAIN_CONTEXT_EMPTY] No neurons met confidence threshold (θ={confidence_threshold:.2f}) for {domain_key}.
Proceeding without domain context — findings below may surface unincorporated knowledge.

{closing_instruction}
"""
        full_prompt = system_prompt + "\n" + dynamic_section

        # User message requesting JSON output
        user_message = f"""Query: {query}

Please respond in JSON format:
{{
  "findings": "Lead with key conclusion. Then evidence.",
  "citations": ["FAR 31.205-6", "CAS 401"],
  "confidence": 0.85,
  "flags": ["[AUDIT]"]
}}"""

        # Execute agent via claude_chat
        response = await claude_chat(
            system_prompt=full_prompt,
            user_message=user_message,
            max_tokens=1000,
            model=model,
        )

        text = response.get("text", "")
        return _parse_agent_response(
            text, domain_key, department, role_key, domain_display,
            neurons, response, start_time,
        )
    except Exception as e:
        return AgentResult(
            domain_key=domain_key,
            department=department,
            role_key=role_key,
            role=domain_display,
            findings="",
            neuron_ids=[s.neuron_id for s, _ in neurons],
            error=True,
            error_message=f"Agent error: {str(e)[:100]}",
            duration_ms=int((time.time() - start_time) * 1000),
        )


# ═══════════════════════════════════════════════════════════════════
# Concurrent Agent Dispatch
# ═══════════════════════════════════════════════════════════════════

async def dispatch_agents(
    all_scored: list[NeuronScoreBreakdown],
    neuron_map: dict[int, Neuron],
    query: str,
    intent: str,
    closing_instruction: str,
    agent_token_budget: int,
    confidence_threshold: float = 0.5,
    tenant_personas: dict[str, str] | None = None,
    model: str = "haiku",
    on_stage: callable = None,
) -> list[AgentResult]:
    """Partition neurons into domains and dispatch concurrent agents.

    Executes all domain agents in parallel via asyncio.gather.
    Never raises — all errors are captured in AgentResult.error fields.

    Args:
        all_scored: list of NeuronScoreBreakdown from scoring pipeline
        neuron_map: dict[neuron_id -> Neuron]
        query: user query
        intent: classified intent
        closing_instruction: intent-specific output instruction
        agent_token_budget: token budget per agent (will be divided by domain count)
        confidence_threshold: minimum neuron combined score to include (default 0.5)
        tenant_personas: optional tenant role personas override
        model: "haiku" or "opus"
        on_stage: optional callback for progress events

    Returns:
        list of AgentResult (one per activated domain)
    """
    assert all_scored is not None, "all_scored must not be None"
    assert neuron_map is not None, "neuron_map must not be None"
    assert query, "query must be non-empty"
    assert agent_token_budget > 0, "agent_token_budget must be positive"
    assert 0.0 <= confidence_threshold <= 1.0, f"confidence_threshold must be in [0.0, 1.0], got {confidence_threshold}"

    # Partition neurons by domain
    domains = partition_neurons_by_domain(
        all_scored,
        neuron_map,
        confidence_threshold=confidence_threshold,
        max_neurons_per_domain=settings.agent_max_neurons_per_domain,
        min_neurons_per_domain=settings.agent_min_neurons_per_domain,
    )

    if not domains:
        return []

    if on_stage:
        await on_stage("agent_dispatch", {
            "domains_active": list(domains.keys()),
            "domain_count": len(domains),
        })

    # Divide token budget across domains
    per_domain_budget = max(2000, agent_token_budget // len(domains))

    # Create concurrent tasks for all agents with timeout wrapper
    tasks = []
    for domain_key, neurons in domains.items():
        dept, role_key = domain_key.split("::")
        coro = _dispatch_single_agent(
            domain_key=domain_key,
            department=dept,
            role_key=role_key,
            neurons=neurons,
            query=query,
            intent=intent,
            closing_instruction=closing_instruction,
            agent_token_budget=per_domain_budget,
            tenant_personas=tenant_personas,
            model=model,
        )
        task = _timed_agent_wrapper(domain_key, dept, role_key, coro)
        tasks.append(task)

    # Execute all agents concurrently
    results = await asyncio.gather(*tasks)

    return list(results)


async def _dispatch_verification_agent(
    agent_results: list[AgentResult],
    synthesis: str,
    query: str,
    intent: str,
    model: str = "haiku",
) -> VerificationResult:
    """Execute verification agent to critique findings (parallel with coordinator)."""
    assert agent_results, "agent_results must be non-empty"
    assert synthesis, "synthesis must be non-empty"
    assert query, "query must be non-empty"

    from app.services.agent_templates import VERIFICATION_AGENT_PROMPT, DYNAMIC_CONTEXT_DELIMITER
    start_time = time.time()

    try:
        # Build verification prompt
        static_prompt = VERIFICATION_AGENT_PROMPT.format(DYNAMIC_CONTEXT_DELIMITER)

        # Dynamic section: agent findings + synthesis
        dynamic_parts = [f"\n## Coordinator Synthesis\n{synthesis}\n"]
        dynamic_parts.append("## Agent Findings (for verification)\n")
        for ar in agent_results:
            dynamic_parts.append(f"**{ar.role} ({ar.domain_key})**: {ar.findings[:200]}...")
            if ar.flags:
                dynamic_parts.append(f"Flags: {', '.join(ar.flags)}")
        dynamic_section = "\n".join(dynamic_parts)
        full_prompt = static_prompt + dynamic_section

        # User message requesting JSON output
        user_message = f"""Query: {query}
Intent: {intent}

Please respond in JSON format:
{{
  "critique": "Summary of gaps or confirmations",
  "gaps": ["Gap 1", "Gap 2"],
  "confidence_adjustment": -0.1
}}"""

        # Execute verification call
        response = await claude_chat(
            system_prompt=full_prompt,
            user_message=user_message,
            max_tokens=800,
            model=model,
        )

        # Parse response JSON
        text = response.get("text", "")
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as e:
            return VerificationResult(
                critique=text,
                error=True,
                error_message=f"JSON parse error: {str(e)[:100]}",
                input_tokens=response.get("input_tokens", 0),
                output_tokens=response.get("output_tokens", 0),
                cost_usd=response.get("cost_usd", 0),
            )

        # Extract fields
        critique = parsed.get("critique", "")
        gaps = parsed.get("gaps", [])
        if not isinstance(gaps, list):
            gaps = []
        confidence_adjustment = float(parsed.get("confidence_adjustment", 0.0))
        # Clamp confidence adjustment to [-0.3, +0.1]
        confidence_adjustment = max(-0.3, min(0.1, confidence_adjustment))

        return VerificationResult(
            critique=critique,
            gaps=gaps,
            confidence_adjustment=confidence_adjustment,
            input_tokens=response.get("input_tokens", 0),
            output_tokens=response.get("output_tokens", 0),
            cost_usd=response.get("cost_usd", 0),
            error=False,
        )

    except Exception as e:
        return VerificationResult(
            critique="",
            error=True,
            error_message=str(e)[:200],
        )
