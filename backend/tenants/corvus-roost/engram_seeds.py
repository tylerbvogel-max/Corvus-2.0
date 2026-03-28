"""Engram seed definitions for real estate property management tenant.

Each engram is a retrieval index pointing to a specific CFR section.
The actual regulatory text is fetched at query time from the eCFR API.
Content field contains retrieval cues (key terms) that make the engram
findable by the scoring engine — NOT the regulation text itself.
"""

ENGRAM_SEEDS: tuple[dict, ...] = (
    # ── ADA (Title 28, Part 36 — Nondiscrimination on the Basis of Disability) ──
    {
        "label": "28 CFR 36.304: Removal of Barriers in Existing Facilities",
        "summary": "Requires removal of architectural barriers in existing commercial facilities when readily achievable",
        "content": "ADA barrier removal existing facilities readily achievable commercial property accessibility wheelchair ramp entrance",
        "cfr_title": 28,
        "cfr_part": "36",
        "cfr_section": "304",
        "authority_level": "regulatory",
        "issuing_body": "Department of Justice",
    },
    {
        "label": "28 CFR 36.402: Alterations — Path of Travel",
        "summary": "When altering a commercial facility, an accessible path of travel to the altered area must be provided",
        "content": "ADA alterations path of travel accessible route tenant build-out renovation commercial 20 percent cost",
        "cfr_title": 28,
        "cfr_part": "36",
        "cfr_section": "402",
        "authority_level": "regulatory",
        "issuing_body": "Department of Justice",
    },
    # ── EPA Environmental (Title 40) ──
    {
        "label": "40 CFR 61.145: Asbestos — Standard for Demolition and Renovation",
        "summary": "Notification and work practice requirements for asbestos during demolition or renovation of buildings",
        "content": "asbestos NESHAP demolition renovation notification abatement ACM friable building inspection survey pre-renovation",
        "cfr_title": 40,
        "cfr_part": "61",
        "cfr_section": "145",
        "authority_level": "regulatory",
        "issuing_body": "Environmental Protection Agency",
    },
    {
        "label": "40 CFR 745.85: Lead — Work Practice Standards for Renovation",
        "summary": "EPA RRP Rule work practice standards for renovation in pre-1978 target housing and child-occupied facilities",
        "content": "lead paint RRP renovation repair painting pre-1978 building containment cleaning verification EPA lead-safe certified firm",
        "cfr_title": 40,
        "cfr_part": "745",
        "cfr_section": "85",
        "authority_level": "regulatory",
        "issuing_body": "Environmental Protection Agency",
    },
    # ── OSHA Workplace Safety (Title 29) ──
    {
        "label": "29 CFR 1910.147: Control of Hazardous Energy (Lockout/Tagout)",
        "summary": "LOTO procedures for servicing and maintenance of machines and equipment in building operations",
        "content": "lockout tagout LOTO hazardous energy maintenance servicing equipment HVAC electrical building engineer safety",
        "cfr_title": 29,
        "cfr_part": "1910",
        "cfr_section": "147",
        "authority_level": "regulatory",
        "issuing_body": "Department of Labor / OSHA",
    },
    {
        "label": "29 CFR 1910.1001: Asbestos — General Industry",
        "summary": "OSHA asbestos exposure limits and requirements for general industry including building maintenance workers",
        "content": "asbestos OSHA PEL exposure limit building maintenance custodial floor tile pipe insulation abatement medical surveillance",
        "cfr_title": 29,
        "cfr_part": "1910",
        "cfr_section": "1001",
        "authority_level": "regulatory",
        "issuing_body": "Department of Labor / OSHA",
    },
    # ── Fair Housing (Title 24) ──
    {
        "label": "24 CFR 100.204: Reasonable Modifications for Persons with Disabilities",
        "summary": "Fair Housing Act requirements for allowing reasonable modifications to rental housing for persons with disabilities",
        "content": "fair housing reasonable modification disability rental residential tenant accommodation alteration expense restoration",
        "cfr_title": 24,
        "cfr_part": "100",
        "cfr_section": "204",
        "authority_level": "regulatory",
        "issuing_body": "Department of Housing and Urban Development",
    },
    {
        "label": "24 CFR 100.65: Discrimination in Terms and Conditions of Rental",
        "summary": "Prohibits discrimination in terms, conditions, or privileges of rental based on protected class",
        "content": "fair housing discrimination rental terms conditions privileges race color religion sex familial status disability national origin screening criteria",
        "cfr_title": 24,
        "cfr_part": "100",
        "cfr_section": "65",
        "authority_level": "regulatory",
        "issuing_body": "Department of Housing and Urban Development",
    },
    # ── EPA Refrigerant Management (Title 40) ──
    {
        "label": "40 CFR 82.156: Required Practices for Refrigerant Management",
        "summary": "EPA Section 608 requirements for HVAC refrigerant recovery, recycling, and reclamation",
        "content": "refrigerant recovery reclamation HVAC Section 608 CFC HCFC HFC certified technician leak repair venting prohibition building chiller",
        "cfr_title": 40,
        "cfr_part": "82",
        "cfr_section": "156",
        "authority_level": "regulatory",
        "issuing_body": "Environmental Protection Agency",
    },
    # ── Fire Safety (OSHA Title 29) ──
    {
        "label": "29 CFR 1910.38: Emergency Action Plans",
        "summary": "Requirements for emergency action plans in workplaces including evacuation procedures and fire prevention",
        "content": "emergency action plan evacuation fire alarm reporting procedures rescue medical duties employee training exit routes assembly point",
        "cfr_title": 29,
        "cfr_part": "1910",
        "cfr_section": "38",
        "authority_level": "regulatory",
        "issuing_body": "Department of Labor / OSHA",
    },
)
