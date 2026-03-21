"""Risk category patterns and grounding reference pattern for aerospace domain."""

import re

RISK_CATEGORIES: dict[str, list[tuple[re.Pattern, str]]] = {
    "safety_critical": [
        (re.compile(r"\b(structural\s+failure|fatigue\s+crack|catastrophic|life[- ]?threatening|crash\s+worthiness)", re.I),
         "References safety-critical failure mode"),
        (re.compile(r"\b(single\s+point\s+of\s+failure|redundancy\s+requirement|fail[- ]?safe)", re.I),
         "References safety-critical design requirement"),
    ],
    "dual_use": [
        (re.compile(r"\b(munitions|ITAR\s+controlled|classified|export[- ]?controlled|weapons?\s+system)", re.I),
         "References export-controlled or dual-use content"),
        (re.compile(r"\b(explosiv|detonat|warhead|guidance\s+system|targeting)", re.I),
         "References weapons-related content"),
    ],
    "speculative": [
        (re.compile(r"\b(I\s+think|I\s+believe|it\s+(?:seems?|appears?)\s+(?:that|like)|probably|possibly|might\s+be|could\s+be|not\s+(?:entirely\s+)?sure)\b", re.I),
         "Contains hedging/speculative language"),
        (re.compile(r"\b(disclaimer|not\s+(?:a\s+)?(?:legal|professional)\s+advice|consult\s+(?:a|an|your)\s+)", re.I),
         "Contains disclaimer language"),
    ],
}

GROUNDING_REF_PATTERN = re.compile(
    r'\b(?:FAR|DFARS|MIL-STD|AS\d+|NADCAP|ISO\s*\d+|AMS\s*\d+|SAE\s+\w+)\b[\s\-]?[\d.]*', re.I
)
