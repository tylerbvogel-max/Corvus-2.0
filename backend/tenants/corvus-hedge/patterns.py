"""Reference detection patterns for investment analysis domain."""

import re

REGULATORY_PATTERNS: tuple[tuple[str, re.Pattern], ...] = (
    # SEC regulations (Title 17 CFR)
    ("SEC Rule",    re.compile(r'\bSEC\s+Rule\s+\d+', re.IGNORECASE)),
    ("Reg NMS",     re.compile(r'\bReg(?:ulation)?\s+NMS\b', re.IGNORECASE)),
    ("Reg SHO",     re.compile(r'\bReg(?:ulation)?\s+SHO\b', re.IGNORECASE)),
    ("Reg FD",      re.compile(r'\bReg(?:ulation)?\s+FD\b', re.IGNORECASE)),
    ("10-K",        re.compile(r'\b10-K\b')),
    ("10-Q",        re.compile(r'\b10-Q\b')),
    ("8-K",         re.compile(r'\b8-K\b')),
    ("S-1",         re.compile(r'\bS-1\b')),
    ("13F",         re.compile(r'\b13-?F\b')),
    ("DEF 14A",     re.compile(r'\bDEF\s*14A\b', re.IGNORECASE)),
    # FASB / Accounting
    ("GAAP",        re.compile(r'\bGAAP\b')),
    ("FASB ASC",    re.compile(r'\bFASB\s+ASC\s+\d+', re.IGNORECASE)),
    ("IFRS",        re.compile(r'\bIFRS\s+\d+', re.IGNORECASE)),
    # Federal Reserve
    ("FOMC",        re.compile(r'\bFOMC\b')),
    ("Fed Funds",   re.compile(r'\bFed(?:eral)?\s+Funds?\b', re.IGNORECASE)),
)

TECHNICAL_PATTERNS: tuple[tuple[str, re.Pattern], ...] = (
    # Financial metrics
    ("P/E",         re.compile(r'\bP/?E\s+ratio\b', re.IGNORECASE)),
    ("EV/EBITDA",   re.compile(r'\bEV/?EBITDA\b', re.IGNORECASE)),
    ("DCF",         re.compile(r'\bDCF\b')),
    ("WACC",        re.compile(r'\bWACC\b')),
    ("FCF",         re.compile(r'\bFCF\b|free\s+cash\s+flow', re.IGNORECASE)),
    ("EPS",         re.compile(r'\bEPS\b')),
    ("ROE",         re.compile(r'\bROE\b')),
    # Options
    ("Greeks",      re.compile(r'\b(?:delta|gamma|theta|vega|rho)\b', re.IGNORECASE)),
    ("IV",          re.compile(r'\bIV\b|implied\s+volatility', re.IGNORECASE)),
    ("LEAPS",       re.compile(r'\bLEAPS?\b')),
    ("Black-Scholes", re.compile(r'\bBlack[- ]Scholes\b', re.IGNORECASE)),
    # Macro indicators
    ("CPI",         re.compile(r'\bCPI\b')),
    ("PCE",         re.compile(r'\bPCE\b')),
    ("GDP",         re.compile(r'\bGDP\b')),
    ("NFP",         re.compile(r'\bNFP\b|nonfarm\s+payrolls', re.IGNORECASE)),
    ("PMI",         re.compile(r'\bPMI\b')),
    ("VIX",         re.compile(r'\bVIX\b')),
    # Platforms
    ("Bloomberg",   re.compile(r'\bBloomberg\b', re.IGNORECASE)),
    ("FRED",        re.compile(r'\bFRED\b')),
    ("EDGAR",       re.compile(r'\bEDGAR\b')),
)
