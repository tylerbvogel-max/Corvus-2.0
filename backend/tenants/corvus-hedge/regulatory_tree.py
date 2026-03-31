"""Regulatory seed data structure for investment analysis domain."""

import json


def _cross_ref(depts: list[str]) -> str:
    """Serialize department cross-references as JSON string."""
    return json.dumps(depts)


DEPARTMENT = "Regulatory & Compliance"

REGULATORY_TREE = (
    # ── SEC Reporting Requirements ──
    ("SEC Reporting Requirements", "sec_reporting",
     ["Equity Research", "Portfolio Analysis"],
     "2025-01-01",
     [
        ("10-K Annual Report", "Comprehensive annual financial and operational disclosure",
         "Form 10-K filed within 60 days (large accelerated filer) or 90 days (others) of fiscal "
         "year end. Contains: audited financial statements, MD&A, risk factors, business description, "
         "legal proceedings, executive compensation. Key sections for investors: Item 1A (Risk Factors), "
         "Item 7 (MD&A), Item 8 (Financial Statements). Compare year-over-year for material changes.",
         None, []),
        ("10-Q Quarterly Report", "Interim financial statements and management discussion",
         "Form 10-Q filed within 40 days (large accelerated) or 45 days (others) of quarter end. "
         "Contains: unaudited financial statements, MD&A update, quantitative/qualitative market risk "
         "disclosures. Shorter than 10-K but critical for tracking quarterly trajectory. Watch for "
         "guidance updates, margin trends, and changes in risk factor language.",
         None, []),
        ("8-K Current Report", "Material event disclosure within 4 business days",
         "Form 8-K filed within 4 business days of a material event. Triggering events include: "
         "entry into material agreements, bankruptcy, leadership changes, asset acquisitions/dispositions, "
         "delisting, unregistered equity sales. Most time-sensitive filing — 8-K items often move stock "
         "price before the market fully digests the information.",
         None, []),
     ]),

    # ── SEC Trading Rules ──
    ("SEC Trading Rules", "sec_trading",
     ["Options & Derivatives", "Risk Management"],
     "2025-01-01",
     [
        ("Regulation FD — Fair Disclosure", "Prohibits selective disclosure of material nonpublic information",
         "Reg FD requires that when a public company discloses material nonpublic information to certain "
         "individuals (analysts, institutional investors), it must simultaneously or promptly disclose "
         "that information publicly. Investment implication: all investors get information at the same "
         "time — edge comes from analysis speed and interpretation quality, not information access.",
         None, []),
        ("Insider Trading Rules", "Prohibitions on trading based on material nonpublic information",
         "Section 10(b) of the Securities Exchange Act and Rule 10b-5 prohibit trading on material "
         "nonpublic information. Form 4 filings track insider transactions — cluster selling by "
         "multiple insiders is a stronger negative signal than single transactions. Watch for "
         "10b5-1 plan adoptions (scheduled selling programs) vs open-market sales.",
         None, []),
     ]),

    # ── Options Regulations ──
    ("Options Exchange Rules", "options_rules",
     ["Options & Derivatives"],
     "2025-01-01",
     [
        ("OCC Exercise and Settlement", "Options clearing, exercise, and settlement procedures",
         "Options Clearing Corporation handles all listed options clearing. American-style options "
         "(including equity LEAPS) can be exercised any time before expiration. Auto-exercise at "
         "expiration if in-the-money by $0.01 or more. Assignment risk for short options is real — "
         "early exercise most likely near ex-dividend dates for ITM calls. LEAPS expiration: "
         "January of the expiration year, third Friday.",
         None, []),
     ]),
)
