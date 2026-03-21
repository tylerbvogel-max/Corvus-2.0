"""Reference detection patterns for plumbing domain."""

import re

REGULATORY_PATTERNS: list[tuple[str, re.Pattern]] = [
    # Plumbing codes
    ("IPC",      re.compile(r'\bIPC\s+\d+', re.IGNORECASE)),
    ("UPC",      re.compile(r'\bUPC\s+\d+', re.IGNORECASE)),
    ("IFGC",     re.compile(r'\bIFGC\s+\d+', re.IGNORECASE)),
    ("IRC",      re.compile(r'\bIRC\s+[PM]\d+', re.IGNORECASE)),
    # Fire/gas standards
    ("NFPA",     re.compile(r'\bNFPA\s+\d+', re.IGNORECASE)),
    # Product/safety standards
    ("ASSE",     re.compile(r'\bASSE\s+\d+', re.IGNORECASE)),
    ("NSF",      re.compile(r'\bNSF(?:/ANSI)?\s+\d+', re.IGNORECASE)),
    ("CSA",      re.compile(r'\bCSA\s+[A-Z]\d+', re.IGNORECASE)),
    # General standards that apply to plumbing
    ("ASME",     re.compile(r'\bASME\s+[A-Z]\d+', re.IGNORECASE)),
    ("ASTM",     re.compile(r'\bASTM\s+[A-Z]\d+', re.IGNORECASE)),
    ("ISO",      re.compile(r'\bISO\s+\d+', re.IGNORECASE)),
    # Federal regulations
    ("CFR",      re.compile(r'\b\d+\s+CFR\s+\d+', re.IGNORECASE)),
    ("OSHA",     re.compile(r'\bOSHA\s+\d+\.\d+', re.IGNORECASE)),
    ("EPA",      re.compile(r'\bEPA\s+(?:Section|§)\s*\d+', re.IGNORECASE)),
    ("SDWA",     re.compile(r'\bSDWA\s+(?:Section|§)\s*\d+', re.IGNORECASE)),
    # Material/pipe standards
    ("SDR",      re.compile(r'\bSDR[- ]?\d+', re.IGNORECASE)),
    ("SCH",      re.compile(r'\bSchedule\s+\d+', re.IGNORECASE)),
]

TECHNICAL_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("PySpark",     re.compile(r'\b(?:DataFrame|SparkSession|pyspark\.sql\.functions)\.\w+\s*\(')),
    ("SQLAlchemy",  re.compile(r'\b(?:select|Session|mapped_column|Mapped)\s*[\(\[]')),
    ("FastAPI",     re.compile(r'\b(?:Depends|APIRouter|@router\.)\w*')),
    ("React",       re.compile(r'\buse[A-Z]\w+\s*\(')),
    ("Delta Lake",  re.compile(r'\b(?:DeltaTable\.\w+|MERGE\s+INTO|OPTIMIZE|VACUUM)\b', re.IGNORECASE)),
    ("Python",      re.compile(r'\b(?:asyncio|dataclasses|typing|collections|functools|itertools)\.\w+')),
]
