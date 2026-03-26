"""Reference detection patterns for presidential behavioral modeling."""

import re

REGULATORY_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("Executive Order",  re.compile(r'\bE\.?O\.?\s*\d{5}', re.IGNORECASE)),
    ("Executive Order",  re.compile(r'\bExecutive\s+Order\s+\d+', re.IGNORECASE)),
    ("Presidential Memo", re.compile(r'\bPresidential\s+Memor', re.IGNORECASE)),
    ("IEEPA",           re.compile(r'\bIEEPA\b')),
    ("NDAA",            re.compile(r'\bNDAA\s+\d{4}', re.IGNORECASE)),
    ("Tariff Act",      re.compile(r'\bSection\s+30[12]\b', re.IGNORECASE)),
    ("JCPOA",           re.compile(r'\bJCPOA\b', re.IGNORECASE)),
    ("AUMF",            re.compile(r'\bAUMF\b', re.IGNORECASE)),
    ("War Powers",      re.compile(r'\bWar\s+Powers\b', re.IGNORECASE)),
    ("Logan Act",       re.compile(r'\bLogan\s+Act\b', re.IGNORECASE)),
    ("Insurrection Act", re.compile(r'\bInsurrection\s+Act\b', re.IGNORECASE)),
]

TECHNICAL_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("Truth Social",    re.compile(r'\bTruth\s+Social\b', re.IGNORECASE)),
    ("Tweet",           re.compile(r'\btweet(?:ed|s|ing)?\b', re.IGNORECASE)),
    ("Rally",           re.compile(r'\brall(?:y|ies)\b', re.IGNORECASE)),
    ("Press Conference", re.compile(r'\bpress\s+(?:conference|briefing)\b', re.IGNORECASE)),
    ("Executive Order", re.compile(r'\bexecutive\s+order\b', re.IGNORECASE)),
    ("Sanctions",       re.compile(r'\bsanction(?:s|ed|ing)?\b', re.IGNORECASE)),
    ("Tariff",          re.compile(r'\btariff(?:s)?\b', re.IGNORECASE)),
    ("Summit",          re.compile(r'\bsummit\b', re.IGNORECASE)),
    ("NATO",            re.compile(r'\bNATO\b')),
    ("UN",              re.compile(r'\bU\.?N\.?\b')),
]
