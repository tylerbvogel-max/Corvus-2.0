"""Risk category patterns and grounding reference pattern for investment analysis domain."""

import re

RISK_CATEGORIES: dict[str, list[tuple[re.Pattern, str]]] = {
    "concentration_risk": [
        (re.compile(r"\b(concentrat|overweight|all[- ]in|single[- ]stock|undiversif)", re.I),
         "References portfolio concentration or single-position risk"),
        (re.compile(r"\b(correlated|correlation\s+risk|sector\s+exposure|factor\s+tilt)", re.I),
         "References correlated position or factor exposure risk"),
    ],
    "leverage_risk": [
        (re.compile(r"\b(margin\s+call|leverage|levered|borrowed|margin\s+requirement)", re.I),
         "References leverage or margin risk"),
        (re.compile(r"\b(LEAPS|long[- ]?dated\s+(?:call|put|option)|time\s+decay|theta\s+burn)", re.I),
         "References options leverage or time decay exposure"),
    ],
    "macro_risk": [
        (re.compile(r"\b(recession|stagflation|rate\s+(?:hike|shock|surprise)|credit\s+crunch|systemic)", re.I),
         "References macroeconomic risk scenario"),
        (re.compile(r"\b(black\s+swan|tail\s+risk|fat\s+tail|crisis|crash|contagion)", re.I),
         "References extreme tail risk or crisis scenario"),
    ],
    "speculative": [
        (re.compile(r"\b(I\s+think|I\s+believe|probably|possibly|might\s+be|could\s+be|not\s+(?:entirely\s+)?sure)\b", re.I),
         "Contains hedging or speculative language"),
        (re.compile(r"\b(not\s+(?:investment|financial)\s+advice|disclaimer|consult\s+(?:a|an|your)\s+(?:advisor|professional))", re.I),
         "Contains disclaimer language"),
    ],
    "regulatory_risk": [
        (re.compile(r"\b(insider|material\s+non[- ]?public|MNPI|front[- ]?run|wash\s+(?:trade|sale))", re.I),
         "References insider trading or regulatory violation risk"),
    ],
}

GROUNDING_REF_PATTERN = re.compile(
    r'\b(?:10-[KQ]|8-K|13-?F|SEC|EDGAR|FRED|FOMC|CPI|PCE|GDP|NFP|'
    r'FASB\s+ASC\s+\d+|P/?E|EV/?EBITDA|DCF|WACC|VIX|LEAPS)\b', re.I
)
