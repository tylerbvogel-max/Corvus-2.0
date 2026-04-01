"""Multi-provider LLM abstraction layer.

Unified interface for calling LLMs across providers: Anthropic, Google Gemini,
and Groq. All callers use display names from MODEL_REGISTRY.
Provider dispatch is automatic based on the model's registered provider.

Free-tier models are prioritized in the registry ordering for UI display.
"""

import logging
from dataclasses import dataclass
from types import MappingProxyType

from app.config import settings

logger = logging.getLogger(__name__)


# ── Model Registry ──

@dataclass(frozen=True)
class ModelInfo:
    display_name: str       # Short name used throughout the codebase
    provider: str           # "anthropic" | "google" | "groq"
    api_id: str             # Provider-specific model ID
    input_price: float      # USD per million input tokens
    output_price: float     # USD per million output tokens
    tier: str               # "frontier" | "free" — for UI grouping


MODEL_REGISTRY: MappingProxyType[str, ModelInfo] = MappingProxyType({
    # ── Frontier (paid, high-capability lab models) ──
    "haiku": ModelInfo(
        display_name="haiku",
        provider="anthropic",
        api_id="claude-haiku-4-5-20251001",
        input_price=0.80,
        output_price=4.00,
        tier="frontier",
    ),
    "sonnet": ModelInfo(
        display_name="sonnet",
        provider="anthropic",
        api_id="claude-sonnet-4-6",
        input_price=3.00,
        output_price=15.00,
        tier="frontier",
    ),
    "opus": ModelInfo(
        display_name="opus",
        provider="anthropic",
        api_id="claude-opus-4-6",
        input_price=15.00,
        output_price=75.00,
        tier="frontier",
    ),
    "gemini-pro": ModelInfo(
        display_name="gemini-pro",
        provider="google",
        api_id="gemini-2.5-pro",
        input_price=1.25,
        output_price=10.00,
        tier="frontier",
    ),
    # ── Free (generous free tiers, suitable for real usage) ──
    "gemini-flash": ModelInfo(
        display_name="gemini-flash",
        provider="google",
        api_id="gemini-2.0-flash",
        input_price=0.0,
        output_price=0.0,
        tier="free",
    ),
    "gemini-flash-lite": ModelInfo(
        display_name="gemini-flash-lite",
        provider="google",
        api_id="gemini-2.0-flash-lite",
        input_price=0.0,
        output_price=0.0,
        tier="free",
    ),
    "groq-llama-70b": ModelInfo(
        display_name="groq-llama-70b",
        provider="groq",
        api_id="llama-3.3-70b-versatile",
        input_price=0.0,
        output_price=0.0,
        tier="free",
    ),
    "groq-llama-8b": ModelInfo(
        display_name="groq-llama-8b",
        provider="groq",
        api_id="llama-3.1-8b-instant",
        input_price=0.0,
        output_price=0.0,
        tier="free",
    ),
    "groq-gemma-9b": ModelInfo(
        display_name="groq-gemma-9b",
        provider="groq",
        api_id="gemma2-9b-it",
        input_price=0.0,
        output_price=0.0,
        tier="free",
    ),
})

# No default — user must always select a model explicitly
DEFAULT_MODEL: str | None = None


# ── Provider availability ──

def _provider_available(provider: str) -> bool:
    """Check if a provider's API key is configured."""
    assert isinstance(provider, str), "provider must be a string"
    key_map = MappingProxyType({
        "anthropic": settings.anthropic_api_key,
        "google": settings.google_api_key,
        "groq": settings.groq_api_key,
    })
    key = key_map.get(provider, "")
    assert provider in key_map, f"Unknown provider: {provider}"
    return bool(key and key.strip())


def get_available_models() -> list[dict]:
    """Return list of models whose provider API key is configured."""
    result = []
    for name, info in MODEL_REGISTRY.items():
        if _provider_available(info.provider):
            result.append({
                "display_name": info.display_name,
                "provider": info.provider,
                "api_id": info.api_id,
                "tier": info.tier,
                "input_price": info.input_price,
                "output_price": info.output_price,
            })
    assert isinstance(result, list), "result must be a list"
    return result


def get_valid_model_names() -> set[str]:
    """Return set of model display names that are currently available."""
    return {
        name for name, info in MODEL_REGISTRY.items()
        if _provider_available(info.provider)
    }


# ── Provider implementations ──

async def _anthropic_chat(
    system_prompt: str, user_message: str, max_tokens: int, model_info: ModelInfo,
) -> dict:
    """Call Anthropic API via the official SDK."""
    import anthropic

    assert settings.anthropic_api_key, "ANTHROPIC_API_KEY not configured"
    assert len(user_message.strip()) > 0, "user_message must be non-empty"

    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    try:
        response = await client.messages.create(
            model=model_info.api_id,
            max_tokens=max_tokens,
            system=system_prompt if system_prompt else anthropic.NOT_GIVEN,
            messages=[{"role": "user", "content": user_message}],
        )
    finally:
        await client.close()

    text = response.content[0].text if response.content else ""
    usage = response.usage
    base_input = usage.input_tokens
    cache_create = getattr(usage, "cache_creation_input_tokens", 0) or 0
    cache_read = getattr(usage, "cache_read_input_tokens", 0) or 0
    output_tokens = usage.output_tokens

    cost = _estimate_cost_anthropic(
        model_info, base_input, cache_create, cache_read, output_tokens,
    )

    assert base_input >= 0, f"base_input must be non-negative, got {base_input}"
    assert output_tokens >= 0, f"output_tokens must be non-negative, got {output_tokens}"
    return {
        "text": text,
        "input_tokens": base_input,
        "cache_creation_tokens": cache_create,
        "cache_read_tokens": cache_read,
        "output_tokens": output_tokens,
        "cost_usd": cost,
        "model_version": response.model,
    }


async def _google_chat(
    system_prompt: str, user_message: str, max_tokens: int, model_info: ModelInfo,
) -> dict:
    """Call Google Gemini API via the google-generativeai SDK."""
    from google import genai

    assert settings.google_api_key, "GOOGLE_API_KEY not configured"
    assert len(user_message.strip()) > 0, "user_message must be non-empty"

    client = genai.Client(api_key=settings.google_api_key)
    config = genai.types.GenerateContentConfig(
        system_instruction=system_prompt if system_prompt else None,
        max_output_tokens=max_tokens,
    )
    response = await client.aio.models.generate_content(
        model=model_info.api_id,
        contents=user_message,
        config=config,
    )

    text = response.text or ""
    input_tokens = getattr(response.usage_metadata, "prompt_token_count", 0) or 0
    output_tokens = getattr(response.usage_metadata, "candidates_token_count", 0) or 0
    cost = estimate_cost(model_info.display_name, input_tokens, output_tokens)

    assert input_tokens >= 0, f"input_tokens must be non-negative, got {input_tokens}"
    assert output_tokens >= 0, f"output_tokens must be non-negative, got {output_tokens}"
    return {
        "text": text,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost_usd": cost,
        "model_version": model_info.api_id,
    }


async def _groq_chat(
    system_prompt: str, user_message: str, max_tokens: int, model_info: ModelInfo,
) -> dict:
    """Call Groq API via the groq SDK (OpenAI-compatible)."""
    from groq import AsyncGroq

    assert settings.groq_api_key, "GROQ_API_KEY not configured"
    assert len(user_message.strip()) > 0, "user_message must be non-empty"

    client = AsyncGroq(api_key=settings.groq_api_key)
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_message})

    try:
        response = await client.chat.completions.create(
            model=model_info.api_id,
            messages=messages,
            max_tokens=max_tokens,
        )
    finally:
        await client.close()

    text = response.choices[0].message.content if response.choices else ""
    usage = response.usage
    input_tokens = usage.prompt_tokens if usage else 0
    output_tokens = usage.completion_tokens if usage else 0
    cost = estimate_cost(model_info.display_name, input_tokens, output_tokens)

    assert input_tokens >= 0, f"input_tokens must be non-negative, got {input_tokens}"
    assert output_tokens >= 0, f"output_tokens must be non-negative, got {output_tokens}"
    return {
        "text": text or "",
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost_usd": cost,
        "model_version": response.model if response.model else model_info.api_id,
    }


# ── Provider dispatch ──

_PROVIDER_DISPATCH = MappingProxyType({
    "anthropic": _anthropic_chat,
    "google": _google_chat,
    "groq": _groq_chat,
})


async def llm_chat(
    system_prompt: str,
    user_message: str,
    max_tokens: int = 2048,
    model: str | None = None,
) -> dict:
    """Call an LLM and return {"text", "input_tokens", "output_tokens", "cost_usd", "model_version"}.

    `model` must be a MODEL_REGISTRY key (e.g. "haiku", "gemini-flash", "groq-llama-70b").
    No default model — caller must specify explicitly.
    """
    assert model is not None, "model must be specified — no default model selection"
    assert (system_prompt and system_prompt.strip()) or (user_message and user_message.strip()), \
        "llm_chat requires a non-empty system_prompt or user_message"

    model_info = MODEL_REGISTRY.get(model)
    if not model_info:
        raise ValueError(f"Unknown model: {model!r}. Available: {list(MODEL_REGISTRY.keys())}")

    if not _provider_available(model_info.provider):
        raise ValueError(
            f"Provider {model_info.provider!r} not configured. "
            f"Set the API key in .env to use model {model!r}."
        )

    handler = _PROVIDER_DISPATCH.get(model_info.provider)
    assert handler is not None, f"No handler for provider: {model_info.provider}"

    result = await handler(system_prompt, user_message, max_tokens, model_info)

    assert "text" in result and "input_tokens" in result and "output_tokens" in result, \
        "llm_chat result missing required keys"
    assert result["input_tokens"] >= 0, f"input_tokens must be non-negative, got {result['input_tokens']}"
    assert result["output_tokens"] >= 0, f"output_tokens must be non-negative, got {result['output_tokens']}"
    return result


# ── Cost estimation ──

def estimate_cost(model: str | None, input_tokens: int, output_tokens: int) -> float:
    """Estimate USD cost from token counts and model name (no cache differentiation)."""
    assert input_tokens >= 0, f"input_tokens must be non-negative, got {input_tokens}"
    assert output_tokens >= 0, f"output_tokens must be non-negative, got {output_tokens}"

    if not model:
        return 0.0
    info = MODEL_REGISTRY.get(model)
    if not info:
        return 0.0
    result = (input_tokens * info.input_price + output_tokens * info.output_price) / 1_000_000

    assert result >= 0, f"estimated cost must be non-negative, got {result}"
    return result


def _estimate_cost_anthropic(
    model_info: ModelInfo,
    base_input: int,
    cache_create: int,
    cache_read: int,
    output_tokens: int,
) -> float:
    """Estimate USD cost with Anthropic prompt caching rates."""
    assert base_input >= 0, f"base_input must be non-negative, got {base_input}"
    assert cache_create >= 0, f"cache_create must be non-negative, got {cache_create}"
    assert cache_read >= 0, f"cache_read must be non-negative, got {cache_read}"
    assert output_tokens >= 0, f"output_tokens must be non-negative, got {output_tokens}"

    input_cost = (
        base_input * model_info.input_price
        + cache_create * model_info.input_price * 1.25
        + cache_read * model_info.input_price * 0.10
    )
    output_cost = output_tokens * model_info.output_price
    result = (input_cost + output_cost) / 1_000_000

    assert result >= 0, f"estimated cost must be non-negative, got {result}"
    return result
