"""Reference detection patterns for aerospace domain."""

import re

REGULATORY_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("FAR",      re.compile(r'\bFAR\s+\d+\.\d+', re.IGNORECASE)),
    ("DFARS",    re.compile(r'\bDFARS\s+\d+\.\d+', re.IGNORECASE)),
    ("ITAR",     re.compile(r'\bITAR\s+§?\d+\.\d+', re.IGNORECASE)),
    ("EAR",      re.compile(r'\bEAR\s+§?\d+\.\d+', re.IGNORECASE)),
    ("CFR",      re.compile(r'\b\d+\s+CFR\s+\d+', re.IGNORECASE)),
    ("NIST",     re.compile(r'\bNIST\s+SP\s+\d+-\d+', re.IGNORECASE)),
    ("MIL-STD",  re.compile(r'\bMIL-STD-\d+[A-Z]?\b', re.IGNORECASE)),
    ("MIL-SPEC", re.compile(r'\bMIL-[A-Z]+-\d+\b')),
    ("AS",       re.compile(r'\bAS\s?\d{4,}[A-Z]?\b')),
    ("DO",       re.compile(r'\bDO-\d+[A-Z]?\b', re.IGNORECASE)),
    ("ASME",     re.compile(r'\bASME\s+[A-Z]\d+', re.IGNORECASE)),
    ("NADCAP",   re.compile(r'\bNADCAP\s+[A-Z]+\d*', re.IGNORECASE)),
    ("ISO",      re.compile(r'\bISO\s+\d+', re.IGNORECASE)),
    ("SAE",      re.compile(r'\bSAE\s+(?:AS|AMS|ARP|J)\d+', re.IGNORECASE)),
    ("OSHA",     re.compile(r'\bOSHA\s+\d+\.\d+', re.IGNORECASE)),
    ("ASTM",     re.compile(r'\bASTM\s+[A-Z]\d+', re.IGNORECASE)),
    ("NAS",      re.compile(r'\bNAS\s?\d{3,}\b')),
    ("CMMC",     re.compile(r'\bCMMC\b', re.IGNORECASE)),
]

TECHNICAL_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("PySpark",     re.compile(r'\b(?:DataFrame|SparkSession|pyspark\.sql\.functions)\.\w+\s*\(')),
    ("SQLAlchemy",  re.compile(r'\b(?:select|Session|mapped_column|Mapped)\s*[\(\[]')),
    ("FastAPI",     re.compile(r'\b(?:Depends|APIRouter|@router\.)\w*')),
    ("React",       re.compile(r'\buse[A-Z]\w+\s*\(')),
    ("Delta Lake",  re.compile(r'\b(?:DeltaTable\.\w+|MERGE\s+INTO|OPTIMIZE|VACUUM)\b', re.IGNORECASE)),
    ("Python",      re.compile(r'\b(?:asyncio|dataclasses|typing|collections|functools|itertools)\.\w+')),
]
