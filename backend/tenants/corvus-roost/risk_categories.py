"""Risk category patterns and grounding reference pattern for commercial real estate domain."""

import re

RISK_CATEGORIES: dict[str, list[tuple[re.Pattern, str]]] = {
    "tenant_credit_risk": [
        (re.compile(r"\b(bankruptcy|chapter\s+(?:7|11)|insolven|default(?:ed)?|delinquen)", re.I),
         "References tenant credit or default risk"),
        (re.compile(r"\b(downsiz|layoff|headcount\s+(?:reduction|cut)|closing|shut(?:ting)?\s+down)", re.I),
         "References tenant operational decline"),
        (re.compile(r"\b(subleas|assign(?:ment)?|vacate|early\s+terminat)", re.I),
         "References potential tenant departure"),
    ],
    "regulatory_violation": [
        (re.compile(r"\b(violation|citation|penalty|fine|non.?compliance|DOB\s+violation)", re.I),
         "References regulatory violation or penalty exposure"),
        (re.compile(r"\b(LL97\s+(?:penalty|fine|exceed)|emissions?\s+(?:limit|exceedance))", re.I),
         "References LL97 emissions compliance risk"),
        (re.compile(r"\b(failed\s+inspection|unpermitted|without\s+permit)", re.I),
         "References permit or inspection failure"),
    ],
    "financial_exposure": [
        (re.compile(r"\b(vacancy\s+(?:rate|risk|exposure)|unleased|dark\s+space)", re.I),
         "References vacancy or revenue risk"),
        (re.compile(r"\b(debt\s+(?:service|covenant)|loan\s+(?:default|maturity)|refinanc)", re.I),
         "References debt or financing risk"),
        (re.compile(r"\b(cap(?:ital)?\s+(?:expenditure|call|reserve)|deferred\s+maintenance)", re.I),
         "References capital expenditure exposure"),
    ],
    "speculative": [
        (re.compile(r"\b(I\s+think|I\s+believe|probably|possibly|might\s+be|could\s+be|not\s+(?:entirely\s+)?sure)\b", re.I),
         "Contains hedging or speculative language"),
        (re.compile(r"\b(disclaimer|not\s+(?:legal|financial|professional)\s+advice|consult\s+(?:a|an|your)\s+)", re.I),
         "Contains disclaimer language"),
    ],
    "environmental_risk": [
        (re.compile(r"\b(asbestos|lead\s+paint|mold|radon|pcb|underground\s+(?:storage\s+)?tank)", re.I),
         "References environmental hazard"),
        (re.compile(r"\b(phase\s+[12]\s+(?:esa|environmental)|brownfield|contamination)", re.I),
         "References environmental assessment"),
    ],
}

GROUNDING_REF_PATTERN = re.compile(
    r'\b(?:LL\s?\d+|HPD|DOB|RPIE|RGB|DHCR|ADA|OSHA|BOMA|NFPA\s+\d+|'
    r'FASB\s+ASC\s+\d+|D&B|PAYDEX|Megalytics|CoStar|CompStak|Placer\.ai|'
    r'CGS\s+\u00a7?\d+|ARS\s+\u00a7?\d+|IBC\s+\d+|COSO\s+ERM)\b', re.I
)
