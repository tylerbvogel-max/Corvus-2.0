"""Risk category patterns and grounding reference pattern for plumbing domain."""

import re

RISK_CATEGORIES: dict[str, list[tuple[re.Pattern, str]]] = {
    "safety_critical": [
        (re.compile(r"\b(gas\s+leak|carbon\s+monoxide|scald|burn\s+risk|flooding|water\s+damage|sewer\s+gas|hydrogen\s+sulfide)", re.I),
         "References safety-critical plumbing hazard"),
        (re.compile(r"\b(cross[- ]?connection|backflow|contamination|potable\s+water\s+supply)", re.I),
         "References potable water safety concern"),
    ],
    "code_violation": [
        (re.compile(r"\b(code\s+violation|not\s+to\s+code|non[- ]?compliant|failed\s+inspection|unpermitted)", re.I),
         "References code compliance issue"),
        (re.compile(r"\b(unlicensed|without\s+permit|no\s+permit)", re.I),
         "References permit/licensing concern"),
    ],
    "speculative": [
        (re.compile(r"\b(I\s+think|I\s+believe|it\s+(?:seems?|appears?)\s+(?:that|like)|probably|possibly|might\s+be|could\s+be|not\s+(?:entirely\s+)?sure)\b", re.I),
         "Contains hedging/speculative language"),
        (re.compile(r"\b(disclaimer|not\s+(?:a\s+)?(?:legal|professional)\s+advice|consult\s+(?:a|an|your)\s+)", re.I),
         "Contains disclaimer language"),
    ],
}

GROUNDING_REF_PATTERN = re.compile(
    r'\b(?:IPC|UPC|NFPA|ASSE|NSF|ASME|ASTM|CSA|ANSI|EPA|OSHA|CFR)\b[\s/\-]?[\d.]*', re.I
)
