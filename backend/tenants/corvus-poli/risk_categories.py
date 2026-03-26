"""Risk category patterns for presidential behavioral modeling."""

import re

RISK_CATEGORIES: dict[str, list[tuple[re.Pattern, str]]] = {
    "speculative": [
        (re.compile(r"\b(I\s+think|I\s+believe|it\s+(?:seems?|appears?)\s+(?:that|like)|probably|possibly|might\s+be|could\s+be|not\s+(?:entirely\s+)?sure)\b", re.I),
         "Contains hedging/speculative language"),
        (re.compile(r"\b(rumor|unconfirmed|anonymous\s+source|reportedly)\b", re.I),
         "References unconfirmed information"),
    ],
    "outdated_position": [
        (re.compile(r"\b(he\s+used\s+to|previously\s+(?:said|stated|believed)|in\s+(?:2015|2016|2017|2018|2019|2020)\s+he)\b", re.I),
         "References a potentially outdated position — verify against recent statements"),
        (re.compile(r"\b(first\s+term|before\s+(?:leaving|losing)\s+office|pre-(?:2024|presidency))\b", re.I),
         "References first-term position — may have evolved"),
    ],
    "private_deliberation": [
        (re.compile(r"\b(privately|behind\s+closed\s+doors|off\s+the\s+record|confidential(?:ly)?|insider\s+(?:says?|told|reports?))\b", re.I),
         "Claims knowledge of private deliberations — lower confidence"),
        (re.compile(r"\b(sources?\s+(?:say|told|report|indicate)|according\s+to\s+(?:people|officials|sources?)\s+familiar)\b", re.I),
         "Based on unnamed sources — may not reflect actual decision process"),
    ],
}

GROUNDING_REF_PATTERN = re.compile(
    r"\b(?:E\.?O\.?\s*\d{5}|Executive\s+Order\s+\d+|"
    r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}|"
    r"\d{1,2}/\d{1,2}/\d{4}|"
    r"Truth\s+Social\s+post|"
    r"press\s+conference|"
    r"(?:State\s+of\s+the\s+Union|SOTU|UN\s+General\s+Assembly|rally\s+in\s+\w+))\b",
    re.IGNORECASE,
)
