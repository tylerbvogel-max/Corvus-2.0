"""Coordination and synthesis of agent results.

Takes a list of AgentResult from parallel domain agents, decides whether to
escalate to Opus, builds a synthesis prompt, and executes the final LLM call.
Optionally runs verification agent in parallel (Session 3+).
"""

import asyncio
import time
from app.services.agent_dispatcher import AgentResult, AgentExecution, VerificationResult, _dispatch_verification_agent
from app.services.agent_templates import build_coordinator_prompt
from app.services.llm_provider import llm_chat as claude_chat
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


async def _execute_coordinator_phase(
    coordinator_prompt: str,
    user_message: str,
    agent_results: list[AgentResult],
    coordinator_model: str,
) -> dict:
    """Execute coordinator with fallback chain (JPL-4: extract helper to keep coordinate() under 100 lines)."""
    try:
        response = await claude_chat(
            system_prompt=coordinator_prompt,
            user_message=user_message,
            max_tokens=2000,
            model=coordinator_model,
        )
        return {
            "synthesis": response.get("text", ""),
            "input_tokens": response.get("input_tokens", 0),
            "output_tokens": response.get("output_tokens", 0),
            "cost_usd": response.get("cost_usd", 0),
            "error": False,
            "model": coordinator_model,
        }
    except Exception as e:
        # Option 1 fallback: re-run agent findings through Sonnet
        try:
            non_error_findings = [r for r in agent_results if not r.error]
            if not non_error_findings:
                best_agent = max(agent_results, key=lambda r: r.confidence)
                non_error_findings = [best_agent]

            findings_summary = "\n".join([
                f"**{r.role} ({r.domain_key})**: {r.findings}"
                for r in non_error_findings
            ])

            fallback_prompt = f"""Synthesize these expert findings into a single coherent answer:

{findings_summary}

Lead with the most important finding. Surface all [RISK], [AUDIT], [CRITICAL] flags.
Note any conflicts between experts. State your confidence level."""

            fallback_response = await claude_chat(
                system_prompt="You are a synthesis expert. Integrate the findings below.",
                user_message=fallback_prompt,
                max_tokens=2000,
                model="sonnet",
            )

            return {
                "synthesis": fallback_response.get("text", ""),
                "input_tokens": fallback_response.get("input_tokens", 0),
                "output_tokens": fallback_response.get("output_tokens", 0),
                "cost_usd": fallback_response.get("cost_usd", 0),
                "error": False,
                "model": "sonnet-fallback",
            }
        except Exception as fallback_e:
            best_agent = max(agent_results, key=lambda r: r.confidence)
            return {
                "synthesis": f"[Coordinator & Sonnet fallback both failed. Using best agent finding ({best_agent.role})]\n{best_agent.findings}",
                "input_tokens": 0,
                "output_tokens": 0,
                "cost_usd": 0,
                "error": True,
                "model": "fallback",
            }


async def coordinate(
    agent_results: list[AgentResult],
    query: str,
    intent: str,
    escalation_threshold: float = 0.7,
    on_stage: callable = None,
    base_model: str = "haiku",
) -> AgentExecution:
    """Synthesize agent results. Single-domain uses agent findings directly; multi-domain coordinates."""
    assert agent_results, "agent_results must be non-empty"
    assert query, "query must be non-empty"

    start_time = time.time()

    # Single-domain shortcut: use agent's findings directly
    if len(agent_results) == 1:
        result = agent_results[0]
        return AgentExecution(
            agent_results=agent_results,
            synthesis=result.findings,
            coordinator_model=base_model,
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
    coordinator_model = "opus" if should_escalate else base_model

    if on_stage:
        await on_stage("agent_coordination", {
            "domain_count": len(agent_results),
            "coordinator_model": coordinator_model,
            "escalated": should_escalate,
        })

    # Build coordinator prompt
    coordinator_prompt = build_coordinator_prompt(
        [r.__dict__ for r in agent_results],
        query,
        intent,
    )

    # Coordinator user message: request synthesis
    user_message = """Given the above agent findings, synthesize them into a single coherent answer.

Lead with the most actionable finding. Surface all [RISK], [AUDIT], [CRITICAL] flags.
Cite which agent provided each key claim. Note any conflicts between agents.
State your overall confidence level."""

    # Run coordinator and verification agent in parallel
    tasks = [asyncio.create_task(
        _execute_coordinator_phase(coordinator_prompt, user_message, agent_results, coordinator_model)
    )]
    if settings.agent_verification_enabled:
        tasks.append(asyncio.create_task(
            _dispatch_verification_agent(agent_results, "", query, intent, model=base_model)
        ))

    results = await asyncio.gather(*tasks)
    coord_result, verification_result = results[0], (results[1] if len(results) > 1 else None)
    if "model" in coord_result:
        coordinator_model = coord_result["model"]

    total_cost = sum(r.cost_usd for r in agent_results) + coord_result["cost_usd"]
    if verification_result:
        total_cost += verification_result.cost_usd

    return AgentExecution(
        agent_results=agent_results,
        synthesis=coord_result["synthesis"],
        coordinator_model=coordinator_model,
        escalated_to_opus=should_escalate,
        domains_active=[r.domain_key for r in agent_results],
        total_agents_dispatched=len(agent_results),
        coordinator_input_tokens=coord_result["input_tokens"],
        coordinator_output_tokens=coord_result["output_tokens"],
        coordinator_cost_usd=coord_result["cost_usd"],
        total_cost_usd=total_cost,
        verification_result=verification_result,
    )
