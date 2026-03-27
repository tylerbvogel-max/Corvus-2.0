"""Reference detection patterns for commercial real estate domain."""

import re

REGULATORY_PATTERNS: tuple[tuple[str, re.Pattern], ...] = (
    # NYC Local Laws
    ("LL97",     re.compile(r'\bLL\s?97\b', re.IGNORECASE)),
    ("LL152",    re.compile(r'\bLL\s?152\b', re.IGNORECASE)),
    ("LL84",     re.compile(r'\bLL\s?84\b', re.IGNORECASE)),
    ("LL87",     re.compile(r'\bLL\s?87\b', re.IGNORECASE)),
    ("LL11",     re.compile(r'\bLL\s?11\b', re.IGNORECASE)),
    ("LL26",     re.compile(r'\bLL\s?26\b', re.IGNORECASE)),
    # NYC agencies and codes
    ("DOB",      re.compile(r'\bDOB\b(?:\s+\u00a7?\d+)?')),
    ("HPD",      re.compile(r'\bHPD\b', re.IGNORECASE)),
    ("DHCR",     re.compile(r'\b(?:DHCR|HCR)\b', re.IGNORECASE)),
    ("RGB",      re.compile(r'\bRGB\b')),
    ("DOF",      re.compile(r'\bDOF\b')),
    # Property tax
    ("RPIE",     re.compile(r'\bRPIE\b', re.IGNORECASE)),
    # Zoning
    ("Zoning",   re.compile(r'\b(?:C[1-8]|M[1-3]|R[1-9])\b[-\d]*')),
    # Federal and state
    ("ADA",      re.compile(r'\bADA\b')),
    ("OSHA",     re.compile(r'\bOSHA\s+\d+\.\d+', re.IGNORECASE)),
    ("EPA",      re.compile(r'\bEPA\b')),
    ("SEQRA",    re.compile(r'\bSEQRA\b', re.IGNORECASE)),
    ("Fair Housing", re.compile(r'\bFair\s+Housing\s+Act\b', re.IGNORECASE)),
    # Connecticut specific
    ("CT CGS",   re.compile(r'\bCGS\s+\u00a7?\d+', re.IGNORECASE)),
    ("CT Fire",  re.compile(r'\bCT\s+Fire\s+(?:Code|Safety)', re.IGNORECASE)),
    # Arizona specific
    ("AZ ARS",   re.compile(r'\bARS\s+\u00a7?\d+', re.IGNORECASE)),
    # Building codes
    ("IBC",      re.compile(r'\bIBC\s+\d+', re.IGNORECASE)),
    ("NFPA",     re.compile(r'\bNFPA\s+\d+', re.IGNORECASE)),
    # Insurance
    ("AM Best",  re.compile(r"\bA\.?M\.?\s+Best\b", re.IGNORECASE)),
    # Credit reporting
    ("D&B",      re.compile(r'\bD&B\b|Dun\s*&\s*Bradstreet', re.IGNORECASE)),
    ("PAYDEX",   re.compile(r'\bPAYDEX\b', re.IGNORECASE)),
    # Accounting standards
    ("FASB ASC", re.compile(r'\bFASB\s+ASC\s+\d+', re.IGNORECASE)),
    ("BOMA",     re.compile(r'\bBOMA\b', re.IGNORECASE)),
)

TECHNICAL_PATTERNS: tuple[tuple[str, re.Pattern], ...] = (
    # Real estate terms
    ("LOI",         re.compile(r'\bLOI\b|letter\s+of\s+intent', re.IGNORECASE)),
    ("CAM",         re.compile(r'\bCAM\b|common\s+area\s+maintenance', re.IGNORECASE)),
    ("NOI",         re.compile(r'\bNOI\b|net\s+operating\s+income', re.IGNORECASE)),
    ("TI",          re.compile(r'\bTI\s+allowance|tenant\s+improvement', re.IGNORECASE)),
    ("Cap Rate",    re.compile(r'\bcap\s+rate\b', re.IGNORECASE)),
    ("DSCR",        re.compile(r'\bDSCR\b|debt\s+service\s+coverage', re.IGNORECASE)),
    ("NNN",         re.compile(r'\bNNN\b|triple\s+net', re.IGNORECASE)),
    ("FFO",         re.compile(r'\bFFO\b|funds\s+from\s+operations', re.IGNORECASE)),
    ("SNDA",        re.compile(r'\bSNDA\b|subordination.{0,20}non.?disturbance', re.IGNORECASE)),
    # Building systems
    ("HVAC",        re.compile(r'\bHVAC\b', re.IGNORECASE)),
    ("BMS",         re.compile(r'\bBMS\b|building\s+management\s+system', re.IGNORECASE)),
    ("CMMS",        re.compile(r'\bCMMS\b|computerized\s+maintenance', re.IGNORECASE)),
    # Market data platforms
    ("CoStar",      re.compile(r'\bCoStar\b', re.IGNORECASE)),
    ("CompStak",    re.compile(r'\bCompStak\b', re.IGNORECASE)),
    ("Placer",      re.compile(r'\bPlacer\.ai\b', re.IGNORECASE)),
    ("Megalytics",  re.compile(r'\bMegalytics\b', re.IGNORECASE)),
)
