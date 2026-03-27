"""Concept neuron definitions for commercial real estate property management domain."""

CONCEPT_DEFINITIONS: tuple[dict, ...] = (
    {
        "label": "Tenant Credit Risk Lifecycle",
        "summary": "End-to-end tenant credit evaluation from initial screening through ongoing monitoring using D&B, Megalytics, and COSO ERM frameworks",
        "content": (
            "Tenant credit risk management spans the full lifecycle from initial screening to lease "
            "expiration. Initial screening uses D&B Viability Rating (1-9 scale, 9=highest risk), "
            "D&B Failure Score (predicts insolvency within 12 months), and PAYDEX Score (payment "
            "performance, 0-100). Megalytics provides AI-driven scoring using 200 components across "
            "financial statements, peer benchmarking, credit, background checks, industry risk, "
            "news, social media, and lease terms — achieving 12.7% prediction of negative client "
            "transitions and 67.6% loss prevention rate using Random Forest ML models. Equifax CRE "
            "Tenant Risk Assessment provides cloud-based real-time credit data and payment patterns. "
            "The COSO ERM framework adapted for real estate provides governance structure: risk "
            "appetite statements, systematic identification, assessment, response (accept/avoid/"
            "transfer/mitigate), and reporting. Risk response calibration depends on tenant industry "
            "category, lease term remaining, guarantor strength, and portfolio concentration."
        ),
        "direct_patterns": ["%credit risk%", "%tenant risk%"],
        "content_patterns": ["%credit%", "%d&b%", "%paydex%", "%megalytics%", "%viability%", "%risk score%"],
    },
    {
        "label": "LOI-to-Lease Pipeline",
        "summary": "Full lifecycle from property viewing through LOI negotiation to lease execution including counsel impact analysis",
        "content": (
            "The LOI-to-Lease pipeline follows a structured sequence: (1) Property viewing and "
            "preliminary conversations, (2) LOI preparation based on tenant requirements and market "
            "analysis, (3) LOI negotiation and signing (1-3 page document, generally non-binding on "
            "price terms but binding on confidentiality and exclusivity), (4) Due diligence period "
            "(30-120 days depending on property type), (5) Formal lease drafting and negotiation, "
            "(6) Execution and occupancy. Key LOI terms include base rent (typically 10-20% below "
            "asking in actual deals), annual escalations, CAM charges with caps (often 5% annual "
            "increase limit), TI allowances ($10-50+/sqft based on market and tenant credit), "
            "operating expense base year, lease term and renewal options, and security deposit. "
            "Counsel quality materially affects outcomes: tenants with institutional law firm "
            "representation negotiate stronger protections (contingency language, risk allocation, "
            "tenant-favorable defaults). Self-represented tenants typically achieve faster closings "
            "but accept more landlord-favorable terms. Counsel should be engaged before LOI "
            "submission to minimize deal-breaker misunderstandings. Market analysis from CoStar, "
            "CompStak, and vacancy/absorption data informs negotiating position. Total occupancy "
            "cost analysis (base rent represents only ~40% of true cost) is essential."
        ),
        "direct_patterns": ["%letter of intent%", "%loi%"],
        "content_patterns": ["%loi%", "%lease negotiat%", "%tenant improvement%", "%cam charge%", "%escalation%"],
    },
    {
        "label": "CAM Reconciliation Framework",
        "summary": "Operating expense allocation methodology covering calculations, exclusions, caps, audit rights, and year-end reconciliation",
        "content": (
            "CAM (Common Area Maintenance) reconciliation is the annual process of truing-up "
            "estimated operating expense charges to actual costs. Key components: (1) Allocation "
            "methodology — pro rata share based on rentable square footage (BOMA measurement "
            "standard ANSI/BOMA Z65.1), (2) Included expenses — insurance, utilities, janitorial, "
            "landscaping, security, management fees, repairs and maintenance, (3) Excluded expenses "
            "— capital improvements (amortized separately), landlord-specific costs, leasing "
            "commissions, above-standard tenant services, (4) Administrative fee — typically 10-15% "
            "of total CAM, (5) Cap structures — many leases include 5% annual increase caps on "
            "controllable expenses, (6) Gross-up provisions — adjusting expenses to reflect full "
            "occupancy (typically when building is below 95% occupied), (7) Tenant audit rights — "
            "most leases allow annual audit within 90-180 days of reconciliation delivery, with "
            "landlord reimbursement of audit costs if overcharge exceeds a threshold (commonly 3-5%). "
            "Common disputes arise from capital vs operating expense classification, management fee "
            "calculation base, and gross-up methodology."
        ),
        "direct_patterns": ["%cam reconcil%", "%common area maintenance%"],
        "content_patterns": ["%cam%", "%operating expense%", "%reconcil%", "%gross up%", "%audit right%"],
    },
    {
        "label": "Early Warning System for Tenant Distress",
        "summary": "Basel-style EWS adapted for CRE tenant monitoring using behavioral, financial, and public-record signals",
        "content": (
            "Early Warning Systems (EWS) adapted from banking credit risk management (Basel-style "
            "watchlist triggers) provide systematic detection of tenant distress before formal "
            "default. Behavioral signals: declining foot traffic (measured via infrared sensors, "
            "cameras, Wi-Fi/Bluetooth tracking), employee headcount reduction (visible through "
            "parking utilization, badge access patterns, or LinkedIn monitoring), abnormal utility "
            "usage changes (energy management system data indicating reduced operations), and "
            "payment pattern deterioration (slipping from on-time to 30/60/90+ days). Financial "
            "signals: negative macroeconomic events affecting tenant industry, increased debt "
            "levels, operating margin compression, significant revenue drops. Public record "
            "signals: UCC filings indicating new secured creditors (monitor across jurisdictions "
            "for competing liens), court filings (lawsuits, judgments), Abstract of Judgment liens, "
            "and bankruptcy watch (debtor name monitoring). Tools: D&B continuous monitoring "
            "alerts, Megalytics portfolio-level risk dashboard, Placer.ai foot traffic analytics, "
            "CoStar tenant health indicators. Response protocol: watchlist placement, enhanced "
            "monitoring cadence, proactive tenant engagement, retention strategy activation, or "
            "lease termination preparation."
        ),
        "direct_patterns": ["%early warning%", "%tenant distress%"],
        "content_patterns": ["%early warning%", "%watchlist%", "%foot traffic%", "%ucc filing%", "%payment pattern%"],
    },
    {
        "label": "LL97 Compliance Framework",
        "summary": "NYC Local Law 97 carbon emissions limits, penalty calculation, compliance pathways, and retrofit strategies",
        "content": (
            "Local Law 97 (part of NYC Climate Mobilization Act 2019) imposes building emissions "
            "limits on properties over 25,000 sqft. Period 1 (2024-2029) targets the top 20% "
            "emitters; Period 2 (2030+) implements 40% reduction with net-zero goal by 2050. "
            "Annual GHG reporting required starting May 1, 2025, certified by a registered design "
            "professional (RDP). Penalties: up to $268 per metric ton CO2 over the cap. Compliance "
            "pathways: (1) Energy efficiency upgrades — HVAC optimization, LED lighting, building "
            "envelope improvements, (2) Clean energy switching — electrification of heating (heat "
            "pumps replacing gas boilers), (3) Renewable energy credits (RECs), (4) Carbon offsets "
            "(limited to 10% of reduction requirement). NYC Accelerator provides free technical "
            "assistance for affordable housing. Relevant Grunberg properties: 928 Broadway (NYC) "
            "is directly subject; 66 W 77th St residential is subject. Hartford and Scottsdale "
            "properties are not subject to LL97 but may face analogous state/local requirements. "
            "Capital planning should integrate LL97 retrofit costs into 5-10 year projections."
        ),
        "direct_patterns": ["%ll97%", "%local law 97%"],
        "content_patterns": ["%ll97%", "%emissions%", "%carbon%", "%climate%mobilization%", "%greenhouse%"],
    },
    {
        "label": "Property Classification Matrix",
        "summary": "Class A/B/C office classification criteria and their impact on rents, TI expectations, tenant quality, and management intensity",
        "content": (
            "Office property classification drives management strategy, tenant expectations, and "
            "financial performance. Class A: newest, highest-quality construction, premium finishes, "
            "institutional ownership, highest rents, professional management, low vacancy in strong "
            "markets. Tenants expect high TI allowances, concierge services, modern amenities "
            "(fitness center, conference rooms), and responsive management. Examples in portfolio: "
            "280 Trumbull St (Hartford), 628 Hebron Ave (Glastonbury), 7975 N Hayden/8655 Via de "
            "Ventura (Scottsdale). Class B: older but well-maintained, functional space, competitive "
            "rents, typically privately owned. Grunberg value proposition: 'amenities, quality and "
            "service of modern office buildings at affordable rents' — repositioning Class B stock "
            "to deliver Class A experience. Example: 928 Broadway (pre-war loft conversion). "
            "Class C: older, minimal amenities, lowest rents, often value-add opportunities. "
            "Classification affects: asking rent ranges, TI budget expectations, management fee "
            "percentage, capital reserve requirements, tenant credit minimums, and marketing strategy."
        ),
        "direct_patterns": ["%class a%", "%class b%", "%property class%"],
        "content_patterns": ["%class%office%", "%classification%", "%repositioning%", "%amenities%"],
    },
    {
        "label": "Lease Escalation Structures",
        "summary": "Fixed percentage, CPI-indexed, and FMV reset escalation mechanisms and their impact on NOI growth and tenant retention",
        "content": (
            "Lease escalation structures determine revenue growth trajectory and significantly "
            "affect property valuation. Fixed percentage escalations (typically 2-3% annually) "
            "provide predictable NOI growth but may lag or exceed inflation. CPI-indexed escalations "
            "track actual inflation but introduce revenue uncertainty and are harder for tenants to "
            "budget. Fair market value (FMV) resets at renewal capture market appreciation but "
            "create re-leasing risk if market rents decline. Operating expense pass-throughs "
            "(base year or expense stop structure) shift variable costs to tenants but require "
            "annual reconciliation (see CAM Reconciliation). Government tenants (GSA, state "
            "agencies) often negotiate CPI-limited escalations with caps, reducing upside for "
            "landlords but providing credit stability. Portfolio strategy should balance escalation "
            "types: fixed escalations for cash flow predictability, CPI-indexed for inflation "
            "protection, and FMV resets for assets in appreciating markets. Each structure type "
            "affects property cap rate calculation differently — fixed escalations are capitalized "
            "directly; CPI/FMV require assumption modeling."
        ),
        "direct_patterns": ["%escalation%", "%rent increase%"],
        "content_patterns": ["%escalation%", "%cpi%index%", "%fair market value%", "%base year%", "%expense stop%"],
    },
    {
        "label": "Net Operating Income Waterfall",
        "summary": "NOI calculation from gross potential rent through vacancy and operating expenses — the fundamental property valuation metric",
        "content": (
            "Net Operating Income (NOI) is the primary metric for commercial property valuation "
            "and lender underwriting. The NOI waterfall: Gross Potential Rent (GPR — all units at "
            "market rent) minus Vacancy and Credit Loss (typically 5-10% for stabilized properties, "
            "higher for transitional) plus Other Income (parking, storage, antenna leases, late "
            "fees) equals Effective Gross Income (EGI). EGI minus Total Operating Expenses (property "
            "taxes, insurance, utilities, repairs, management fees, administrative, janitorial, "
            "landscaping, security) equals NOI. Capital expenditures are below the NOI line. Cap "
            "rate = NOI / property value. DSCR = NOI / annual debt service (lenders typically "
            "require 1.25x minimum). NOI is the input to both direct capitalization and discounted "
            "cash flow valuation. For Grunberg properties, NOI analysis should be run per-property "
            "and portfolio-wide, with sensitivity analysis on vacancy assumptions (US office "
            "vacancy averaging 20%+ in major markets)."
        ),
        "direct_patterns": ["%noi%", "%net operating income%"],
        "content_patterns": ["%noi%", "%cap rate%", "%dscr%", "%vacancy%", "%operating expense%", "%valuation%"],
    },
    {
        "label": "Multi-Jurisdiction Regulatory Navigation",
        "summary": "Managing compliance across NYC, CT, and AZ regulatory regimes simultaneously with deadline calendaring",
        "content": (
            "Grunberg properties span three regulatory jurisdictions with distinct requirements. "
            "NYC (928 Broadway, 66 W 77th St): LL97 emissions reporting (annual, May 1 deadline), "
            "LL152 gas piping inspection (4-year cycle by Community District), LL84 benchmarking "
            "(annual), LL87 energy audit (10-year cycle), RPIE property tax filing (June 1), HPD "
            "housing maintenance code (residential), rent stabilization compliance (66 W 77th if "
            "applicable), DOB permits and inspections, FISP facade inspection (5-year cycle). "
            "Connecticut (280 Trumbull, 628 Hebron): state building code (IBC-based), fire safety "
            "inspection, elevator inspection, CGS Title 47a landlord-tenant law, Hartford/Glastonbury "
            "municipal zoning. Arizona (7975 Hayden, 8655 Via de Ventura): Scottsdale zoning and "
            "development standards, AZ fire code, ARS Title 33 Chapter 10 commercial leasing, "
            "Maricopa County property tax assessment. Cross-cutting federal: ADA, OSHA, EPA "
            "(asbestos/lead), Fair Housing Act (residential). A compliance calendar should track "
            "all filing deadlines and inspection cycles across jurisdictions."
        ),
        "direct_patterns": ["%regulatory%", "%compliance calendar%"],
        "content_patterns": ["%jurisdiction%", "%filing deadline%", "%inspection cycle%", "%compliance%"],
    },
    {
        "label": "Government Tenant Risk Profile",
        "summary": "Unique risk characteristics of government tenants including appropriations risk, CPI limits, and sovereign immunity",
        "content": (
            "Government tenants (GSA/SBA at 280 Trumbull, CT Dept of Banking, CT Dept of Insurance, "
            "Access Health CT, Glastonbury Board of Education) present a unique risk profile distinct "
            "from private-sector tenants. Strengths: very strong credit quality (backed by taxing "
            "authority or federal budget), reliable payment (rarely delinquent), long-term occupancy "
            "tendency, and prestige/anchor tenant effect that attracts other tenants. Risks: "
            "appropriations risk (government funding may be reduced or eliminated, especially for "
            "state agencies during budget crises), CPI-limited escalations (government procurement "
            "rules cap annual increases, reducing NOI growth), extensive holdover provisions "
            "(government tenants may hold over at existing rent terms for extended periods without "
            "penalty), sovereign immunity considerations (limitations on landlord remedies in "
            "default scenarios), and specific space requirements (security clearance areas, "
            "public access requirements, ADA compliance at higher standards). GSA leases follow "
            "the PBS Leasing Desk Guide with standardized terms that limit landlord negotiating "
            "flexibility. Portfolio management should consider government tenant concentration "
            "risk — Grunberg has significant government exposure at 280 Trumbull and 628 Hebron."
        ),
        "direct_patterns": ["%government tenant%", "%gsa%"],
        "content_patterns": ["%government%", "%gsa%", "%state agency%", "%appropriation%", "%sovereign%"],
    },
)
