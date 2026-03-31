"""Coordination and synthesis of agent results.

Takes a list of AgentResult from parallel domain agents, decides whether to
escalate to Opus, builds a synthesis prompt, and executes the final LLM call.
"""

import time
from app.services.agent_dispatcher import AgentResult, AgentExecution
from app.services.agent_templates import build_coordinator_prompt
from app.services.claude_cli import claude_chat
from app.config import settings


def _should_escalate_to_opus(
    agent_results: list[AgentResult],
    escalation_threshold: float = 0.7,
) -> bool:
    """Determine if coordination should use Opus instead of Haiku.

    Escalates to Opus if:
    1. ≥3 non-error domain agents AND avg confidence < escalation_threshold, OR
    2. Any agent returned a [CRITICAL] flag

    Args:
        agent_results: list of AgentResult from dispatch_agents()
        escalation_threshold: confidence threshold for escalation (default 0.7)

    Returns:
        True if Opus should be used, False if Haiku is sufficient
    """
    assert agent_results is not None, "agent_results must not be None"
    assert escalation_threshold > 0, "escalation_threshold must be positive"

    # Check for [CRITICAL] flags
    for result in agent_results:
        if "[CRITICAL]" in " ".join(result.flags):
            return True

    # Check domain count and confidence
    non_error_count = sum(1 for r in agent_results if not r.error)
    if non_error_count >= 3:
        avg_confidence = _compute_aggregate_confidence(agent_results)
        if avg_confidence < escalation_threshold:
            return True

    return False


def _compute_aggregate_confidence(
    agent_results: list[AgentResult],
) -> float:
    """Compute average confidence across all non-error agent results.

    Args:
        agent_results: list of AgentResult

    Returns:
        Average confidence (0.0–1.0), or 1.0 if no valid results
    """
    assert agent_results is not None, "agent_results must not be None"

    non_error_results = [r for r in agent_results if not r.error]
    if not non_error_results:
        return 1.0

    total_confidence = sum(r.confidence for r in non_error_results)
    return total_confidence / len(non_error_results)


async def coordinate(
    agent_results: list[AgentResult],
    query: str,
    intent: str,
    escalation_threshold: float = 0.7,
    on_stage: callable = None,
) -> AgentExecution:
    """Synthesize agent results into a final response.

    Single-domain shortcut: if len(agent_results)==1, returns that agent's findings
    directly without a coordinator LLM call.

    Multi-domain: decides Haiku vs Opus, builds coordinator prompt, executes synthesis.

    Args:
        agent_results: list of AgentResult from dispatch_agents()
        query: user query string
        intent: classified intent
        escalation_threshold: confidence threshold for Opus escalation
        on_stage: optional callback for progress events

    Returns:
        AgentExecution with synthesis text and full tracing
    """
    assert agent_results, "agent_results must be non-empty"
    assert query, "query must be non-empty"

    start_time = time.time()

    # Single-domain shortcut: use agent's findings directly
    if len(agent_results) == 1:
        result = agent_results[0]
        return AgentExecution(
            agent_results=agent_results,
            synthesis=result.findings,
            coordinator_model="haiku",
            escalated_to_opus=False,
            domains_active=[result.domain_key],
            total_agents_dispatched=1,
            coordinator_input_tokens=0,
            coordinator_output_tokens=0,
            coordinator_cost_usd=0,
            total_cost_usd=sum(r.cost_usd for r in agent_results),
        )

    # Multi-domain: decide escalation
    should_escalate = _should_escalate_to_opus(agent_results, escalation_threshold)
    coordinator_model = "opus" if should_escalate else "haiku"

    if on_stage:
        await on_stage("agent_coordination", {
            "domain_count": len(agent_results),
            "coordinator_model": coordinator_model,
            "escalated": should_escalate,
        })

    # Build coordinator prompt
    coordinator_prompt = build_coordinator_prompt(
        [r.__dict__ for r in agent_results],  # Convert to dicts for JSON serialization
        query,
        intent,
    )

    # Coordinator user message: request synthesis
    user_message = """Given the above agent findings, synthesize them into a single coherent answer.

Lead with the most actionable finding. Surface all [RISK], [AUDIT], [CRITICAL] flags.
Cite which agent provided each key claim. Note any conflicts between agents.
State your overall confidence level."""

    # Execute coordinator
    try:
        response = await claude_chat(
            system_prompt=coordinator_prompt,
            user_message=user_message,
            max_tokens=2000,
            model=coordinator_model,
        )

        synthesis = response.get("text", "")
        coord_input_tokens = response.get("input_tokens", 0)
        coord_output_tokens = response.get("output_tokens", 0)
        coord_cost_usd = response.get("cost_usd", 0)

    except Exception as e:
        # Graceful fallback: return best agent's findings if coordinator fails
        best_agent = max(agent_results, key=lambda r: r.confidence)
        synthesis = f"[Coordinator error: {str(e)[:50]}. Using best agent finding:]\n{best_agent.findings}"
        coord_input_tokens = 0
        coord_output_tokens = 0
        coord_cost_usd = 0

    total_agents = len(agent_results)
    total_cost = sum(r.cost_usd for r in agent_results) + coord_cost_usd

    return AgentExecution(
        agent_results=agent_results,
        synthesis=synthesis,
        coordinator_model=coordinator_model,
        escalated_to_opus=should_escalate,
        domains_active=[r.domain_key for r in agent_results],
        total_agents_dispatched=total_agents,
        coordinator_input_tokens=coord_input_tokens,
        coordinator_output_tokens=coord_output_tokens,
        coordinator_cost_usd=coord_cost_usd,
        total_cost_usd=total_cost,
    )
