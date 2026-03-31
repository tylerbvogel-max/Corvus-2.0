"""Engram seed definitions for aerospace defense tenant.

Each engram is a retrieval index pointing to a specific CFR section.
The actual regulatory text is fetched at query time from the eCFR API.
"""

ENGRAM_SEEDS: tuple[dict, ...] = (
    # ── FAR Part 31 — Contract Cost Principles (Title 48) ──
    {
        "label": "FAR 31.205-6: Compensation for Personal Services",
        "summary": "Allowability criteria for employee compensation including salary, overtime, bonuses, deferred compensation, pension, and stock options on government contracts",
        "content": "compensation allowability personal services salary wages bonuses deferred ESOP pension overtime reasonableness allocability FAR 31.205-6",
        "cfr_title": 48,
        "cfr_part": "31",
        "cfr_section": "205-6",
        "authority_level": "regulatory",
        "issuing_body": "Federal Acquisition Regulation Council",
    },
    {
        "label": "FAR 31.205-18: Independent Research and Development / Bid and Proposal Costs",
        "summary": "Allowability of IR&D and B&P costs including allocation methodology and ceiling limitations",
        "content": "IR&D independent research development bid proposal B&P allowability allocation ceiling technical effort FAR 31.205-18",
        "cfr_title": 48,
        "cfr_part": "31",
        "cfr_section": "205-18",
        "authority_level": "regulatory",
        "issuing_body": "Federal Acquisition Regulation Council",
    },
    {
        "label": "FAR 31.205-14: Entertainment Costs",
        "summary": "Entertainment costs are unallowable including amusement, social activities, meals, and club memberships",
        "content": "entertainment costs unallowable amusement social dining club membership tickets meals lodging FAR 31.205-14",
        "cfr_title": 48,
        "cfr_part": "31",
        "cfr_section": "205-14",
        "authority_level": "regulatory",
        "issuing_body": "Federal Acquisition Regulation Council",
    },
    {
        "label": "FAR 15.404-1: Proposal Analysis Techniques",
        "summary": "Price and cost analysis techniques for evaluating contractor proposals including certified cost or pricing data",
        "content": "proposal analysis price cost evaluation certified pricing data comparison should-cost FAR 15.404-1 contracting officer",
        "cfr_title": 48,
        "cfr_part": "15",
        "cfr_section": "404-1",
        "authority_level": "regulatory",
        "issuing_body": "Federal Acquisition Regulation Council",
    },
    {
        "label": "FAR 31.201-2: Determining Allowability",
        "summary": "Five factors for determining allowability of costs: reasonableness, allocability, standards, terms, limitations",
        "content": "allowability reasonable allocable CAS GAAP contract terms statutory limitations FAR 31.201-2 cost principles",
        "cfr_title": 48,
        "cfr_part": "31",
        "cfr_section": "201-2",
        "authority_level": "regulatory",
        "issuing_body": "Federal Acquisition Regulation Council",
    },
    # ── ITAR (Title 22) ──
    {
        "label": "22 CFR 120.6: Defense Article",
        "summary": "Definition of defense article under ITAR including technical data, models, and items on the US Munitions List",
        "content": "ITAR defense article USML United States Munitions List technical data model mockup export control classification",
        "cfr_title": 22,
        "cfr_part": "120",
        "cfr_section": "6",
        "authority_level": "regulatory",
        "issuing_body": "Department of State / DDTC",
    },
    {
        "label": "22 CFR 125.4: Exemptions for Technical Data",
        "summary": "Exemptions to ITAR licensing requirements for export of unclassified technical data",
        "content": "ITAR exemption technical data export license fundamental research public domain basic marketing operations maintenance",
        "cfr_title": 22,
        "cfr_part": "125",
        "cfr_section": "4",
        "authority_level": "regulatory",
        "issuing_body": "Department of State / DDTC",
    },
    # ── FAA Airworthiness (Title 14) ──
    {
        "label": "14 CFR 25.571: Damage Tolerance and Fatigue Evaluation of Structure",
        "summary": "Damage tolerance evaluation requirements for transport category aircraft structure including inspection programs",
        "content": "damage tolerance fatigue evaluation structure crack growth residual strength inspection program transport aircraft airworthiness 14 CFR 25.571",
        "cfr_title": 14,
        "cfr_part": "25",
        "cfr_section": "571",
        "authority_level": "regulatory",
        "issuing_body": "Federal Aviation Administration",
    },
    # ── OSHA for Manufacturing (Title 29) ──
    {
        "label": "29 CFR 1910.147: Control of Hazardous Energy (Lockout/Tagout)",
        "summary": "LOTO procedures for servicing and maintenance of machines and equipment",
        "content": "lockout tagout LOTO hazardous energy maintenance servicing equipment machine manufacturing safety procedure",
        "cfr_title": 29,
        "cfr_part": "1910",
        "cfr_section": "147",
        "authority_level": "regulatory",
        "issuing_body": "Department of Labor / OSHA",
    },
    {
        "label": "29 CFR 1910.134: Respiratory Protection",
        "summary": "Respiratory protection program requirements including fit testing, medical evaluation, and permissible exposure limits",
        "content": "respiratory protection respirator fit test medical evaluation PEL APF IDLH atmosphere hazard N95 SCBA manufacturing",
        "cfr_title": 29,
        "cfr_part": "1910",
        "cfr_section": "134",
        "authority_level": "regulatory",
        "issuing_body": "Department of Labor / OSHA",
    },
)
