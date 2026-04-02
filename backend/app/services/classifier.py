"""Stage 1: Intent classification via LLM provider."""

import json
import logging

from app.services.claude_cli import claude_chat as llm_chat
from app.tenant import tenant

logger = logging.getLogger(__name__)


async def classify_query(message: str) -> dict:
    """Call Claude CLI to classify a user query. Returns classification dict and token counts."""
    result = await llm_chat(tenant.classify_system_prompt, message, max_tokens=300, model="haiku")

    raw_text = result["text"].strip()
    logger.info(f"Classifier raw response ({len(raw_text)} chars): {raw_text[:300]}")
    # Parse JSON response
    try:
        classification = json.loads(raw_text)
    except (json.JSONDecodeError, ValueError):
        # Try to extract JSON from markdown code blocks
        try:
            if "```" in raw_text:
                json_str = raw_text.split("```")[1]
                if json_str.startswith("json"):
                    json_str = json_str[4:]
                classification = json.loads(json_str.strip())
            else:
                raise ValueError("No JSON found")
        except (json.JSONDecodeError, ValueError, IndexError):
            logger.warning(f"Classifier fallback: could not parse response: {raw_text[:200]}")
            classification = {
                "intent": "general_query",
                "departments": [],
                "role_keys": [],
                "keywords": [],
            }

    return {
        "classification": classification,
        "input_tokens": result["input_tokens"],
        "output_tokens": result["output_tokens"],
        "cost_usd": result.get("cost_usd", 0),
    }
