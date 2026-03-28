"""Engram seed definitions for plumbing trade tenant.

Each engram is a retrieval index pointing to a specific CFR section.
Note: IPC/UPC plumbing codes are NOT in the CFR (they're ICC/IAPMO copyrighted
standards). Engrams here cover the federal regulations that do apply to plumbing:
OSHA safety, EPA water quality, and DOT hazmat transport.
"""

ENGRAM_SEEDS: tuple[dict, ...] = (
    # ── OSHA Excavation Safety (Title 29) ──
    {
        "label": "29 CFR 1926.652: Requirements for Protective Systems (Excavation)",
        "summary": "Protective system requirements for excavations including sloping, shoring, and shield systems for trenching work",
        "content": "excavation trench protective system sloping shoring shield benching soil classification Type A B C competent person plumbing sewer water main",
        "cfr_title": 29,
        "cfr_part": "1926",
        "cfr_section": "652",
        "authority_level": "regulatory",
        "issuing_body": "Department of Labor / OSHA",
    },
    {
        "label": "29 CFR 1910.146: Permit-Required Confined Spaces",
        "summary": "Entry requirements for permit-required confined spaces including atmospheric testing and rescue provisions",
        "content": "confined space permit entry atmospheric testing oxygen LEL H2S CO ventilation attendant rescue manhole sewer vault",
        "cfr_title": 29,
        "cfr_part": "1910",
        "cfr_section": "146",
        "authority_level": "regulatory",
        "issuing_body": "Department of Labor / OSHA",
    },
    {
        "label": "29 CFR 1926.1153: Respirable Crystalline Silica (Construction)",
        "summary": "Silica exposure limits and control measures for cutting concrete or masonry during construction",
        "content": "silica exposure PEL concrete cutting core drill masonry saw dust control wet method HEPA vacuum respirator plumbing penetration",
        "cfr_title": 29,
        "cfr_part": "1926",
        "cfr_section": "1153",
        "authority_level": "regulatory",
        "issuing_body": "Department of Labor / OSHA",
    },
    # ── EPA Safe Drinking Water (Title 40) ──
    {
        "label": "40 CFR 141.80: Lead and Copper Rule — General Requirements",
        "summary": "Lead and Copper Rule requirements including action levels and treatment technique requirements for public water systems",
        "content": "lead copper rule action level 15 ppb potable water public system corrosion control treatment technique lead service line SDWA",
        "cfr_title": 40,
        "cfr_part": "141",
        "cfr_section": "80",
        "authority_level": "regulatory",
        "issuing_body": "Environmental Protection Agency",
    },
    # ── EPA Underground Injection (Title 40) — relevant to well plumbing ──
    {
        "label": "40 CFR 144.12: Prohibition of Unauthorized Injection",
        "summary": "Prohibition of underground injection that may contaminate underground sources of drinking water",
        "content": "underground injection prohibition well contamination drinking water source USDW plumbing cross-connection backflow",
        "cfr_title": 40,
        "cfr_part": "144",
        "cfr_section": "12",
        "authority_level": "regulatory",
        "issuing_body": "Environmental Protection Agency",
    },
)
