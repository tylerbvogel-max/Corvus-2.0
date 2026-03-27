"""Regulatory seed data structure for commercial real estate property management domain."""

import json


def _cross_ref(depts: list[str]) -> str:
    """Serialize department cross-references as JSON string."""
    return json.dumps(depts)


DEPARTMENT = "Legal & Regulatory Compliance"

REGULATORY_TREE = (
    # ══════════════════════════════════════════════════════════════
    # NYC MULTI-FAMILY RESIDENTIAL
    # ══════════════════════════════════════════════════════════════
    ("NYC Multi-Family Residential", "nyc_multifamily",
     ["Property Operations", "Legal & Regulatory Compliance", "Finance & Accounting"],
     "2025-01-01",
     [
        ("Rent Stabilization", "Rent regulation framework for buildings with 6+ units built before 1974",
         "Rent stabilization applies to NYC buildings with 6+ units built before January 1, 1974. "
         "Administered by NYS Homes and Community Renewal (HCR) Division of Housing and Community "
         "Renewal (DHCR). Annual increases set by Rent Guidelines Board (RGB) — most recent Order #57 "
         "(October 2025-September 2026). Owners must register rents annually with HCR. Major Capital "
         "Improvement (MCI) increases capped at 6% annually. Individual Apartment Improvement (IAI) "
         "increases available for qualifying renovations. Applicable to 66 W 77th St if units are "
         "stabilized. Key compliance: annual registration, proper notice for increases, adherence to "
         "RGB order for lease renewals, proper vacancy lease procedures.",
         None, [
            ("RGB Annual Rent Adjustments", "Rent Guidelines Board orders set maximum annual increases",
             "RGB issues annual orders for 1-year and 2-year lease renewals. Owners must provide "
             "lease renewal offers 90-150 days before current lease expiry. Tenant has 60 days to "
             "accept. If no renewal offered, existing lease terms continue. MCI rent increases "
             "require DHCR application and approval — building-wide improvements only (roof, "
             "boiler, elevator, windows, plumbing, wiring). IAI increases for individual unit "
             "improvements have dollar caps per year."),
        ]),
        ("HPD Housing Maintenance Code", "NYC minimum housing standards and violation system",
         "NYC Housing Maintenance Code (Title 27 Chapter 2) establishes minimum standards for "
         "residential properties. Heat requirements: 68F daytime (6am-10pm) when outdoor temp "
         "below 55F, 62F nighttime, October 1 through May 31. Hot water: 120F minimum year-round. "
         "Pest control: sealing entry points, eliminating water sources, regular treatment. Mold: "
         "identify and remediate moisture source. Violation classes: Class A (non-hazardous, "
         "90 days to correct), Class B (hazardous, 30 days), Class C (immediately hazardous, "
         "24 hours), Class I (information). Penalties: $50 to $5,000+ per violation depending "
         "on class and repeat offender status.",
         None, [
            ("Lead Paint (Local Law 1)", "Lead-based paint hazard requirements for pre-1960 buildings",
             "Pre-1960 buildings with children under 6: annual inspection for lead paint hazards, "
             "safe work practices for any disturbance of lead paint, XRF testing or EPA-certified "
             "lab analysis, abatement or interim controls as required. Annual notice to tenants. "
             "HPD enforces through inspections and violation orders. Fines up to $1,000 per "
             "violation per day."),
            ("Window Guards and Safety", "Window guard requirements for residential buildings",
             "Window guards required in apartments where children 10 or under reside. Annual "
             "notice to all tenants asking about children in household. Guards must be installed "
             "within 30 days of request. Applies to all windows except fire escape windows "
             "(which get approved safety gates instead)."),
        ]),
        ("LL97 Emissions — Residential", "Building emissions limits for residential properties over 25K sqft",
         "Local Law 97 applies to residential buildings over 25,000 sqft. 66 W 77th St (36 units) "
         "must comply if over threshold. Period 1 (2024-2029): initial caps targeting top 20% "
         "emitters. Period 2 (2030+): 40% reduction target. Annual GHG reporting required starting "
         "May 1, 2025, certified by registered design professional. Penalties: up to $268 per "
         "metric ton CO2 over cap. Compliance pathways: energy efficiency upgrades (LED, insulation, "
         "high-efficiency heating), electrification (heat pumps replacing gas boilers), RECs, carbon "
         "offsets (up to 10%). NYC Accelerator provides free technical assistance.",
         None, []),
     ]),

    # ══════════════════════════════════════════════════════════════
    # NYC COMMERCIAL OFFICE
    # ══════════════════════════════════════════════════════════════
    ("NYC Commercial Office", "nyc_commercial_office",
     ["Property Operations", "Legal & Regulatory Compliance", "Finance & Accounting", "Executive & Asset Management"],
     "2025-01-01",
     [
        ("NYC Zoning — Commercial Districts", "Zoning Resolution Article IV governs commercial uses",
         "NYC Zoning Resolution Article IV defines permitted commercial uses by district. Use Groups "
         "reformed from numbers (1-18) to Roman numerals (I-X). Commercial Districts C1-C8 have "
         "specific allowances: S (size restriction), P (additional conditions), U (open use), "
         "special permit (requires City Planning Commission approval). 928 Broadway (Flatiron) is "
         "in a commercial district — verify current zoning designation for any change of use or "
         "tenant fit-out. Building use must match certificate of occupancy and zoning district.",
         None, [
            ("Certificate of Occupancy", "C of O requirements for commercial occupancy",
             "Certificate of Occupancy required before commercial space can be occupied. Issued "
             "by DOB. Must match actual building use. Temporary C of O available for partial "
             "occupancy during construction. Changes in use (e.g., office to retail, or different "
             "use group) require DOB application and potentially zoning analysis. Outstanding "
             "violations can prevent C of O issuance or renewal."),
        ]),
        ("ADA Compliance", "Americans with Disabilities Act requirements for commercial buildings",
         "2010 ADA Standards for Accessible Design apply to new construction and alterations. "
         "Existing facilities must remove architectural barriers when readily achievable. Key "
         "requirements: accessible entrances, accessible path of travel to tenant spaces, "
         "accessible restrooms, elevator access to all floors (exception: buildings under 3 "
         "stories or under 3,000 sqft per floor, excluding shopping centers, health care, "
         "transit, airports). Safe harbor for elements compliant with 1991 Standards if not "
         "altered since March 15, 2012. All tenant build-outs must include ADA compliance "
         "review as part of permit process.",
         None, []),
        ("LL152 — Gas Piping Inspection", "Periodic gas piping inspection on 4-year rotating schedule",
         "Local Law 152 requires periodic inspection of gas piping in buildings with gas service. "
         "Exempt: one- and two-family homes and R-3 occupancy. Inspection scope: exposed gas "
         "piping from point of entry including meters, piping in public/common spaces (hallways, "
         "mechanical rooms, boiler rooms). Does not include piping within individual tenant spaces. "
         "Four-year rotation by Community District: Districts 1,3,10 (2024/2028); Districts "
         "2,5,7,13,18 (2025/2029); Districts 4,6,8,9,16 (2026/2030); Districts 11,12,14,15,17 "
         "(2027/2031). Inspector: Licensed Master Plumber (LMP) or qualified individual under "
         "LMP supervision. Certification: GPS2 form signed and sealed by LMP, filed within "
         "60 days of inspection. Penalties: up to $10,000 per violation for non-compliance.",
         None, []),
        ("LL97 Emissions — Commercial", "Building emissions limits for commercial properties over 25K sqft",
         "Same LL97 framework applies to commercial buildings. 928 Broadway must comply. "
         "Commercial buildings typically have different emissions intensity limits than "
         "residential due to occupancy type and operating hours. Reporting requirements, "
         "penalty structure, and compliance pathways are identical. Consider electrification "
         "of HVAC, LED lighting upgrades, building envelope improvements, and renewable energy "
         "procurement. Capital planning must integrate LL97 compliance costs.",
         None, []),
        ("Fire Safety (LL26)", "Fire safety and emergency action plan requirements",
         "NYC Fire Code establishes requirements for fire prevention, emergency preparedness, "
         "and hazardous materials. Commercial office buildings require: Fire Safety Director "
         "(FSD) on premises during business hours, Emergency Action Plan (EAP) filed with "
         "FDNY, fire drills (minimum 2 per year for non-residential), fire alarm and sprinkler "
         "system maintenance and testing, means of egress maintenance and signage. LL26 "
         "specifically requires non-residential buildings to have emergency action plans.",
         None, []),
        ("FISP Facade Inspection (LL11)", "Facade Inspection Safety Program — 5-year inspection cycle",
         "Buildings over 6 stories require facade inspection every 5 years by a Qualified "
         "Exterior Wall Inspector (QEWI). Filing: Technical Report filed with DOB classifying "
         "each facade condition as Safe, Safe With Repair and Maintenance Program (SWARMP), "
         "or Unsafe. Unsafe conditions require immediate remediation (sidewalk shed/netting "
         "within 30 days). SWARMP conditions must be repaired within reporting cycle. "
         "Applicable to 928 Broadway (if over 6 stories) and 66 W 77th St.",
         None, []),
     ]),

    # ══════════════════════════════════════════════════════════════
    # NYC COMMERCIAL RETAIL
    # ══════════════════════════════════════════════════════════════
    ("NYC Commercial Retail", "nyc_commercial_retail",
     ["Leasing & Tenant Relations", "Legal & Regulatory Compliance", "Property Operations"],
     "2025-01-01",
     [
        ("Signage Requirements", "DOB sign permit requirements and zoning restrictions",
         "NYC DOB Construction Code 28-105.1 requires Sign Permit (SG) for displayed signage "
         "unless exempt. Exemptions: signs painted directly on exterior walls, wall signs 6 sqft "
         "or less. NYC Zoning Resolution governs sign location, size, illumination, and projection "
         "restrictions by zoning district. Non-compliant signs subject to removal orders and "
         "violations. Outstanding sign violations can complicate C of O and transactions. "
         "Relevant for ground-floor retail at 928 Broadway (Obica restaurant signage).",
         None, []),
        ("Use Clause Enforcement", "Tenant use restrictions in commercial leases",
         "Commercial leases define permitted use through use clauses. Use must align with "
         "zoning district classification and certificate of occupancy. Landlords monitor "
         "tenant use compliance for covenant violations. Exclusive use clauses prevent "
         "landlord from leasing to competing businesses in same property. Co-tenancy clauses "
         "may allow tenant rent reductions if anchor tenants vacate. Careful drafting prevents "
         "disputes over what constitutes permitted vs prohibited use.",
         None, []),
        ("Storefront Registration (RPIE Section S)", "Ground-floor commercial premises registration",
         "Properties with ground or second-floor commercial premises visible and accessible "
         "to the public must complete Section S of the RPIE form (Storefront Registration). "
         "Filed with NYC Department of Finance as part of annual RPIE submission. Reports "
         "on vacancy status, lease terms, and tenant information for retail spaces. Applicable "
         "to 928 Broadway ground-floor retail (Obica).",
         None, []),
     ]),

    # ══════════════════════════════════════════════════════════════
    # NYC CROSS-CUTTING REQUIREMENTS
    # ══════════════════════════════════════════════════════════════
    ("NYC Cross-Cutting Requirements", "nyc_cross_cutting",
     ["Finance & Accounting", "Legal & Regulatory Compliance", "Property Operations"],
     "2025-01-01",
     [
        ("RPIE Filing", "Real Property Income and Expense annual filing requirements",
         "RPIE filed annually with NYC Department of Finance. Required for owners of "
         "income-producing property with actual assessed value over $40,000. Commercial "
         "condo buildings and rented commercial/professional space in residential condos "
         "also must file. Large Property Addendum: properties with assessed value at or "
         "above $750,000 must include rent roll information. Storefront Registration: "
         "Section S required for ground/second-floor retail. Filing deadline: June 1 "
         "annually (RPIE-2025 due June 1, 2026 for calendar year 2025). Online-only "
         "filing. Penalties: up to 5% of actual assessed value for late filing. Both "
         "NYC Grunberg properties (928 Broadway, 66 W 77th St) must file.",
         None, []),
        ("LL84 Benchmarking", "Annual energy and water usage reporting",
         "Local Law 84 requires annual benchmarking of energy and water usage for buildings "
         "over 25,000 sqft using EPA Energy Star Portfolio Manager. Data reported to NYC "
         "and published publicly. Benchmarking scores help identify efficiency opportunities "
         "and inform LL97 compliance planning. Filing deadline: May 1 annually. Building "
         "owners must request utility data from providers. Results are public record.",
         None, []),
        ("LL87 Energy Audit", "Energy audit and retro-commissioning on 10-year cycle",
         "Local Law 87 requires buildings over 50,000 sqft to complete energy audit and "
         "retro-commissioning every 10 years. Audit identifies energy conservation measures "
         "(ECMs) with payback analysis. Retro-commissioning evaluates existing building "
         "systems for optimization opportunities without capital investment. Filed with "
         "DOB. Results inform LL97 compliance strategy and capital planning.",
         None, []),
        ("Insurance Requirements", "Commercial property and tenant insurance minimums",
         "Commercial tenant insurance requirements: minimum $1M general liability per "
         "occurrence, B+ or better A.M. Best carrier rating, landlord named as additional "
         "insured. Contractor requirements: $1M general liability minimum, workers "
         "compensation, disability benefits. Certificate of Insurance (COI) tracking: "
         "verify coverage currency, endorsements, and named insured status. NYC "
         "Administrative Code 28-105 and RCNY 101-08 govern permit-related insurance.",
         None, []),
     ]),

    # ══════════════════════════════════════════════════════════════
    # CONNECTICUT COMMERCIAL
    # ══════════════════════════════════════════════════════════════
    ("Connecticut Commercial", "ct_commercial",
     ["Property Operations", "Legal & Regulatory Compliance", "Leasing & Tenant Relations"],
     "2025-01-01",
     [
        ("CT Building Code", "State building code based on IBC/ICC with CT amendments",
         "Connecticut adopted the International Building Code (IBC) with state-specific "
         "amendments administered by CT Department of Administrative Services (DAS). Applies "
         "to 280 Trumbull St (Hartford) and 628 Hebron Ave (Glastonbury). Building permits "
         "issued by local building officials. Occupancy permits required for tenant fit-outs. "
         "Fire safety inspections coordinated with State Fire Marshal (CT DESPP). Elevator "
         "inspections per ASME A17.1 with CT amendments.",
         None, [
            ("Hartford Municipal Requirements", "Hartford-specific zoning and building requirements",
             "280 Trumbull St is in Hartford Central Business District. Hartford zoning permits "
             "office use in CBD. Building alterations and tenant fit-outs require city building "
             "permits. Fire safety compliance with Hartford Fire Department. Property tax "
             "assessed by Hartford Tax Assessor — commercial properties reassessed periodically."),
            ("Glastonbury Municipal Requirements", "Glastonbury-specific zoning and building requirements",
             "628 Hebron Ave is zoned for commercial office use. Glastonbury Planning and Zoning "
             "Commission oversees land use. Building permits through Glastonbury Building "
             "Department. Property tax assessed by Glastonbury Tax Assessor."),
        ]),
        ("CT Landlord-Tenant Law (CGS Title 47a)", "Connecticut statutory framework for commercial leasing",
         "Connecticut General Statutes Title 47a governs landlord-tenant relationships. "
         "Commercial lease provisions differ from residential. Key areas: security deposit "
         "requirements, lease termination procedures, landlord access rights, maintenance "
         "obligations (as defined by lease rather than habitability standards), and dispute "
         "resolution. CT does not have rent control for commercial properties. Eviction "
         "procedures through CT Superior Court.",
         None, []),
        ("CT Fire Safety", "Connecticut fire safety inspection and compliance",
         "CT Department of Emergency Services and Public Protection (DESPP) State Fire "
         "Marshal oversees fire safety compliance. Annual fire safety inspections for "
         "commercial buildings. Fire alarm and sprinkler system testing and maintenance "
         "requirements. High-rise buildings (280 Trumbull at 29 stories) have enhanced "
         "requirements: fire command center, emergency voice/alarm communication, smoke "
         "control systems, standpipe systems. Fire Safety Director designation may be "
         "required for high-rise occupancy.",
         None, []),
     ]),

    # ══════════════════════════════════════════════════════════════
    # ARIZONA COMMERCIAL
    # ══════════════════════════════════════════════════════════════
    ("Arizona Commercial", "az_commercial",
     ["Property Operations", "Legal & Regulatory Compliance", "Leasing & Tenant Relations"],
     "2025-01-01",
     [
        ("Scottsdale Zoning and Development", "Scottsdale zoning ordinance and building permits",
         "7975 N Hayden Rd and 8655 E Via de Ventura are in Scottsdale, AZ (McCormick Ranch "
         "area). Scottsdale Development Review Board oversees land use and development "
         "standards. Commercial office use is permitted in current zoning. Building permits "
         "through Scottsdale Building Safety Division. Scottsdale has specific signage "
         "ordinances, landscaping requirements (desert-compatible), and parking ratios. "
         "The McCormick Ranch area has CC&Rs that may impose additional restrictions.",
         None, [
            ("Scottsdale Parking Requirements", "Parking ratio and design standards",
             "Scottsdale commercial office parking typically requires 4 spaces per 1,000 sqft "
             "of leasable area. The Scottsdale Executive Office Park provides ample covered "
             "parking. Any modification to parking areas requires city approval. ADA accessible "
             "parking spaces must meet both federal ADA and Arizona state requirements."),
        ]),
        ("AZ Commercial Landlord-Tenant (ARS Title 33)", "Arizona statutory framework for commercial leasing",
         "Arizona Revised Statutes Title 33, Chapter 10 governs commercial leasing. Arizona "
         "is generally landlord-friendly with broad freedom of contract for commercial leases. "
         "Key provisions: landlord remedies upon tenant default (including lockout provisions "
         "per lease terms), security deposit handling, assignment and subletting rights as "
         "defined by lease. No rent control. Eviction through Maricopa County Superior Court "
         "or Justice Court depending on amount in controversy.",
         None, []),
        ("AZ Fire Code", "Arizona fire code based on IFC with state amendments",
         "Arizona adopted the International Fire Code (IFC) with state amendments. Scottsdale "
         "Fire Department enforces locally. Commercial buildings require: fire alarm system "
         "testing (NFPA 72), sprinkler system inspection (NFPA 25), fire extinguisher "
         "maintenance (NFPA 10), emergency egress maintenance. Annual fire safety inspection "
         "by Scottsdale Fire Prevention Bureau.",
         None, []),
        ("Maricopa County Property Tax", "Property tax assessment and appeal procedures",
         "Property tax assessed by Maricopa County Assessor. Commercial properties assessed "
         "at full cash value. Tax rate set by overlapping taxing jurisdictions (county, city, "
         "school district, special districts). Assessment appeals through Maricopa County "
         "Board of Equalization (must file within 60 days of notice of value). Property tax "
         "is a significant operating expense for the Scottsdale office park — monitor "
         "assessment values annually and appeal if overvalued.",
         None, []),
     ]),

    # ══════════════════════════════════════════════════════════════
    # FEDERAL REQUIREMENTS
    # ══════════════════════════════════════════════════════════════
    ("Federal Requirements", "federal",
     ["Legal & Regulatory Compliance", "Property Operations", "Risk Management"],
     "2025-01-01",
     [
        ("ADA — Americans with Disabilities Act", "Federal accessibility requirements for commercial properties",
         "ADA applies to all commercial properties (places of public accommodation and commercial "
         "facilities). 2010 Standards for Accessible Design govern new construction and alterations. "
         "Existing facilities must remove barriers when readily achievable. Key areas: accessible "
         "entrance and path of travel, accessible restrooms, elevator access (exceptions for small "
         "buildings), signage, parking. Tenant build-outs trigger compliance review for altered "
         "areas. Safe harbor for elements conforming to 1991 Standards if unaltered since March "
         "15, 2012. All Grunberg properties must comply.",
         None, []),
        ("OSHA — Workplace Safety", "Occupational safety requirements for building operations",
         "OSHA standards apply to building operations staff (engineers, maintenance technicians). "
         "Key areas: hazard communication (chemical labeling for cleaning products, maintenance "
         "chemicals), lockout/tagout (LOTO) for equipment maintenance, fall protection for roof "
         "access and elevated work, confined space entry (mechanical rooms, elevator pits), "
         "personal protective equipment. OSHA 300 log for recordable injuries. Worker complaint "
         "mechanism for unsafe conditions.",
         None, []),
        ("EPA — Environmental Compliance", "Environmental regulations for building operations",
         "EPA regulations relevant to property management: asbestos (NESHAP — National Emission "
         "Standards for Hazardous Air Pollutants) requires asbestos survey before renovation or "
         "demolition, trained workers for disturbance, proper disposal. Lead paint: EPA RRP Rule "
         "for renovation in pre-1978 buildings. Refrigerant management: EPA Section 608 requires "
         "certified technicians for HVAC refrigerant handling, leak repair requirements, proper "
         "recovery and disposal. PCB-containing ballasts in older fluorescent fixtures require "
         "proper disposal. Older buildings (280 Trumbull built 1984, 928 Broadway pre-war) may "
         "have asbestos-containing materials.",
         None, []),
        ("Fair Housing Act", "Federal anti-discrimination for residential properties",
         "Fair Housing Act prohibits discrimination in residential housing based on race, color, "
         "national origin, religion, sex, familial status, and disability. Applies to 66 W 77th "
         "St residential. Key areas: advertising (no discriminatory language), tenant screening "
         "(consistent criteria applied uniformly), reasonable accommodations for disability "
         "(service animals, accessibility modifications), no retaliation for fair housing "
         "complaints. NYC and NY State human rights laws add additional protected classes "
         "(source of income, gender identity, age, citizenship status).",
         None, []),
        ("FASB ASC 842 — Lease Accounting", "Lease accounting standards from landlord perspective",
         "FASB ASC 842 governs lease accounting for both lessors and lessees. From the landlord "
         "(lessor) perspective: classify leases as sales-type, direct financing, or operating. "
         "Most commercial property leases are operating leases from the lessor perspective. "
         "Revenue recognition: straight-line rental income over lease term (including free "
         "rent periods). Lease incentives (TI allowances) amortized over lease term. Variable "
         "lease payments (CAM, percentage rent) recognized when earned. Relevant for financial "
         "reporting and lender covenant compliance.",
         None, []),
     ]),
)
