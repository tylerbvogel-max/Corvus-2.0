"""Deterministic external reference detector.

Scans neuron content/summary for citations to regulatory standards and
technical APIs. Returns structured reference objects for storage in the
neuron's external_references JSON field.
"""

from dataclasses import dataclass

from app.tenant import tenant

REGULATORY_PATTERNS = tenant.regulatory_patterns
TECHNICAL_PATTERNS = tenant.technical_patterns


@dataclass
class DetectedReference:
    pattern: str       # The matched text (e.g., "FAR 31.205-6")
    domain: str        # "regulatory" or "technical"
    family: str        # Citation family (e.g., "FAR", "PySpark")


def detect_references(text: str) -> list[DetectedReference]:
    """Scan text for external references. Returns deduplicated list."""
    if not text:
        return []

    seen: set[str] = set()
    results: list[DetectedReference] = []

    for family, pattern in REGULATORY_PATTERNS:
        for match in pattern.finditer(text):
            matched = match.group(0).strip()
            if matched not in seen:
                seen.add(matched)
                results.append(DetectedReference(
                    pattern=matched,
                    domain="regulatory",
                    family=family,
                ))

    for family, pattern in TECHNICAL_PATTERNS:
        for match in pattern.finditer(text):
            matched = match.group(0).strip()
            if matched not in seen:
                seen.add(matched)
                results.append(DetectedReference(
                    pattern=matched,
                    domain="technical",
                    family=family,
                ))

    return results


def detect_neuron_references(content: str | None, summary: str | None) -> list[dict]:
    """Scan neuron content + summary and return references as JSON-serializable dicts."""
    combined = ""
    if content:
        combined += content + "\n"
    if summary:
        combined += summary

    refs = detect_references(combined)
    return [
        {
            "pattern": r.pattern,
            "domain": r.domain,
            "family": r.family,
            "resolved_neuron_id": None,
            "resolved_at": None,
        }
        for r in refs
    ]
