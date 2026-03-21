"""Regulatory seed data structure for plumbing domain."""

import json


def _cross_ref(depts: list[str]) -> str:
    return json.dumps(depts)


DEPARTMENT = "Code Compliance"

REGULATORY_TREE = (
    # -- IPC (International Plumbing Code) --
    ("IPC — International Plumbing Code", "ipc",
     ["Drain/Waste/Vent", "Water Supply", "Gas Piping", "Fixtures & Appliances", "Estimating & Business"],
     "2024-01-01",
     [
        ("IPC Chapter 3 — General Regulations", "Permits, inspections, workmanship standards",
         "IPC Chapter 3 establishes general requirements: plumbing work requires permit except minor repairs and like-for-like replacements (303.3). All plumbing must be installed in a workmanlike manner per applicable codes. Protection of pipes required during construction. Testing required before concealment — water test or air test per Section 312. Existing plumbing may remain if safe and sanitary, but additions must comply with current code.",
         None, [
            ("312 Testing", "Required testing methods for DWV and water supply",
             "DWV water test: fill system to highest opening, maintain 15 min, inspect all joints — no leaks. DWV air test: 5 psi for 15 min, no drop allowed. Water supply: typically 100 psi for minimum 15 min (varies by jurisdiction). Test medium must be water or air — no other gases. Existing piping: test new sections connected to existing system. Final test: run all fixtures, verify drainage, check for leaks at connections."),
        ]),
        ("IPC Chapter 4 — Fixtures, Faucets, and Fixture Fittings", "Fixture requirements and installation",
         "IPC Chapter 4 covers: approved fixtures (NSF/ANSI 61 for potable water contact), fixture clearances (405.3.1: 15\" min WC center to wall, 21\" clear in front), water conservation (604.4: showerheads max 2.5 GPM, lavatory faucets max 2.2 GPM, WC max 1.6 GPF), anti-scald protection (424.3: shower valves must be pressure-balanced or thermostatic, max 120°F), and accessibility requirements per ICC A117.1.",
         None, [
            ("405.3.1 Fixture Clearances", "Minimum spacing for plumbing fixtures",
             "Water closet: 15\" minimum center to side wall or obstruction, 21\" clearance in front. Lavatory: 4\" minimum from side wall, 21\" clearance in front. Urinal: 12\" center to side wall. Shower: minimum 30\"x30\" interior dimension, 24\" minimum opening. Bathtub: access panel required for concealed trap and piping connections."),
            ("424.3 Anti-Scald Requirements", "Shower valve temperature and pressure requirements",
             "Shower and tub-shower valves must be pressure-balanced, thermostatic mixing, or combination type conforming to ASSE 1016 or CSA B125.3. Maximum hot water temperature at shower = 120°F. Valves must limit outlet temperature to not more than 120°F when subjected to pressure fluctuations."),
        ]),
        ("IPC Chapter 6 — Water Supply and Distribution", "Potable water system requirements",
         "IPC Chapter 6 covers: sizing (604.3 — WSFU method), minimum/maximum pressure (604.8 — 8 psi minimum at fixture, 80 psi maximum static), pressure reducing valves (604.8), thermal expansion control (607.3.2), hot water systems (607 — max 140°F at source, 120°F at fixtures), and water supply pipe sizing procedures (Appendix E).",
         None, [
            ("604.3 Water Supply Sizing", "Water supply fixture unit method for pipe sizing",
             "Size water supply per Section 604.3 using procedures in Appendix E. Steps: determine total WSFU, convert to GPM demand using Table E103.3(3), calculate available pressure (street pressure minus static head minus minimum fixture pressure), determine allowable friction loss, size pipe to deliver required flow within allowable friction loss. Minimum pipe sizes: 3/4\" building supply, 1/2\" fixture branch."),
            ("607.1 Hot Water Temperature", "Maximum temperatures for hot water distribution",
             "Hot water storage: minimum 120°F recommended (Legionella control). Maximum at point of use: 120°F for bathing fixtures (anti-scald). Hospitals/nursing facilities: additional thermostatic mixing valve requirements per ASSE 1017. Recirculation systems: required where wait time exceeds designated threshold or per energy code."),
            ("607.3.2 Thermal Expansion", "Expansion control in closed water supply systems",
             "When a PRV, check valve, or backflow preventer creates a closed system, thermal expansion must be controlled. Approved methods: expansion tank (ASSE 1013 or manufacturer listed), T&P relief valve alone is NOT sufficient for expansion control. Tank sizing: based on water heater capacity and supply pressure. Install on cold supply side, upstream of water heater."),
        ]),
        ("IPC Chapter 6 — Section 608 Backflow Prevention", "Cross-connection control requirements",
         "IPC 608 requires protection of potable water supply from contamination. Air gaps (608.13.1) preferred. Table 608.1 maps applications to acceptable device types. Annual testing required for testable assemblies (608.17). Devices must be accessible for testing/maintenance. Water purveyor may impose additional requirements. High-hazard connections require RPZ minimum.",
         None, [
            ("608.1 Cross-Connection Control", "General requirements and device selection",
             "Potable water supply must be protected from contamination. Air gap is most reliable. Device selection based on: degree of hazard (high=health risk, low=non-health), backpressure vs. backsiphonage, continuous vs. non-continuous pressure. Key devices: air gap, RPZ (ASSE 1013), DCVA (ASSE 1015), PVB (ASSE 1020), AVB (ASSE 1001), hose bibb vacuum breaker (ASSE 1011)."),
        ]),
        ("IPC Chapter 7 — Sanitary Drainage", "Drain pipe sizing, materials, and installation",
         "IPC Chapter 7 covers: approved materials (PVC, ABS, cast iron, copper DWV — per Section 702), pipe sizing by DFU method (Table 710.1), minimum slopes (704.1: 1/4\"/ft for 3\" and smaller, 1/8\"/ft for 4\" and larger), cleanout requirements (708: accessible, every 100' in 4\"+, at direction changes >45°), proper fitting usage (706: no double sanitary tee for horizontal drainage), and indirect waste requirements (801-803).",
         None, [
            ("708 Cleanout Requirements", "Location and spacing of cleanouts",
             "Required at: upper end of each horizontal drain, each aggregate change of direction >135° (>45° from straight), every 100' in pipes 4\" and larger, accessible from outside or through a cleanout access. Cleanout size: same nominal size as pipe served, minimum 1.5\", maximum 4\" required. Full-size cleanouts preferred for main building drains."),
            ("706 Fittings", "Proper fitting selection for drainage applications",
             "Horizontal to vertical: sanitary tee permitted. Horizontal to horizontal: wye + 1/8 bend (or combination wye-bend), NEVER sanitary tee. Vertical to horizontal: long-turn 90 (1/4 bend) or two 1/8 bends. No double sanitary tees on horizontal drainage where both inlets receive drainage. Short-turn 90s (vent 90s) only permitted on vent piping."),
        ]),
        ("IPC Chapter 9 — Vents", "Vent system requirements and sizing",
         "IPC Chapter 9 covers: vent sizing (Table 916.1 — based on drain size and developed vent length), vent types (individual, common, wet, circuit, island, AAV), critical distances (Table 906.1: max distance from trap weir to vent), termination requirements (903.1: 6\" above roof, 10' from openable window/air intake at same elevation), and air admittance valves (917: allowed in specific conditions, not as sole vent for building drain).",
         None, [
            ("906.1 Trap-to-Vent Distance", "Maximum distance from trap to vent by pipe size",
             "Maximum distances (IPC Table 906.1): 1.25\" trap arm=30\", 1.5\"=42\" (3.5'), 2\"=60\" (5'), 3\"=72\" (6'), 4\"=120\" (10'). If distance exceeded, S-trap condition occurs (self-siphoning risk). Trap arm must maintain minimum slope (1/4\"/ft). Vent connection must be above centerline of trap arm."),
            ("903.1 Vent Termination", "Vent pipe termination requirements",
             "Vents must terminate: minimum 6\" above roof surface, minimum 10' from any openable window/air intake at same or lower elevation (unless 3' above), minimum 10' from lot line (some jurisdictions). In areas with snow: extend vent to anticipated snow depth or use increased size (2\" minimum in cold climates). Vent cap/screen: not required by IPC but may be required locally."),
        ]),
        ("IPC Chapter 10 — Traps and Interceptors", "Trap requirements and grease/oil interceptors",
         "IPC Chapter 10: every fixture must have a trap (1002.1). Trap seal minimum 2\" maximum 4\" (1002.4). P-traps required (no S-traps, bell traps, or drum traps for new work). Grease interceptors required for food service establishments (1003 — sized per PDI G101 or flow rate method). Oil/sand interceptors for vehicle service, parking structures.",
         None, []),
     ]),

    # -- UPC (Uniform Plumbing Code) --
    ("UPC — Uniform Plumbing Code", "upc",
     ["Drain/Waste/Vent", "Water Supply", "Fixtures & Appliances"],
     "2024-01-01",
     [
        ("Key UPC Differences from IPC", "Areas where UPC and IPC diverge significantly",
         "UPC adopted in western states (CA, WA, OR, ID, MT, etc.) and internationally. Key differences from IPC: (1) Wet venting — UPC more restrictive on allowable configurations, (2) AAVs — UPC 2021 added limited allowance (previously prohibited), (3) Trap arm lengths — different calculation method, (4) Fixture unit values — slightly different tables, (5) Pipe support spacing — some differences, (6) UPC traditionally requires licensed plumber for all work. UPC Chapter 7 (DWV sizing) uses Table 7-3 vs. IPC Table 710.1.",
         None, []),
        ("UPC Chapter 6 — Water Supply", "UPC water supply requirements and differences",
         "UPC uses Water Supply Fixture Unit (WSFU) method similar to IPC but with different table values. Key provisions: minimum 15 psi at fixture (vs. IPC 8 psi), maximum 80 psi. UPC 610.10: pipe sizing per Appendix A. Water hammer: UPC 609.10 requires arrestors at quick-closing valves. Thermal expansion: UPC 608.3 requires expansion control on closed systems.",
         None, []),
        ("UPC Chapter 9 — DWV Sizing", "UPC drainage system sizing and requirements",
         "UPC Table 7-3: drainage fixture unit table (different values from IPC). UPC slope requirements match IPC: 1/4\"/ft for 3\" and smaller, 1/8\"/ft for 4\" and larger. Cleanout spacing: every 100' (same as IPC). Fitting requirements: similar to IPC but UPC explicitly defines fitting DFU equivalents for sizing. UPC Chapter 9 covers venting with more restrictive wet vent provisions than IPC.",
         None, []),
     ]),

    # -- NFPA Standards --
    ("NFPA — National Fire Protection Association", "nfpa",
     ["Gas Piping", "Water Supply"],
     None,
     [
        ("NFPA 54 / IFGC — National Fuel Gas Code", "Installation of gas piping and appliances",
         "NFPA 54 (also published as IFGC) covers: gas pipe sizing (Chapter 4 — longest-length or branch-length method), approved materials (black steel, CSST, copper for gas, PE underground only), testing (406.4: 3 psi for 10 min for new installations), appliance venting (Chapter 5 — Categories I-IV), combustion air (Chapter 3), and CSST bonding (310.1.1: bonding to grounding electrode system).",
         None, [
            ("NFPA 54 Section 406.4 Gas Pressure Testing", "Testing requirements for fuel gas piping",
             "New installations: test at not less than 3 psi (using air or nitrogen, NEVER combustible gas) for not less than 10 minutes. No pressure drop allowed. Existing systems being reconnected: test at operating pressure using gas — soap bubble test all connections. High-pressure systems (>14\" WC): test at 1.5x operating pressure. Provide test gauge with minimum 10 psi range. Isolate appliance controls and regulators during high-pressure tests."),
            ("NFPA 54 Section 310.1.1 CSST Bonding", "Bonding requirements for corrugated stainless steel tubing",
             "CSST must be bonded to the grounding electrode system. Bonding conductor: minimum 6 AWG copper. Bond at point before CSST enters building or at manifold. Purpose: protect against lightning-induced perforation of CSST (thin-wall tubing is susceptible to electrical arcing from nearby lightning strikes). Some jurisdictions require direct bond to each section of CSST."),
        ]),
        ("NFPA 13D — Residential Sprinkler Systems", "Sprinkler systems for one- and two-family dwellings",
         "NFPA 13D covers sprinkler systems for one- and two-family dwellings and manufactured homes. Design criteria: 2 sprinklers flowing simultaneously, 7 psi minimum at most remote head, 10-minute water supply duration. Multipurpose systems (combined domestic/fire supply) allowed. Pipe sizing: hydraulic calculation or pipe schedule (Table 6.3.2.4). Head placement per listing, typically 12'-16' coverage.",
         None, []),
        ("NFPA 13/13R — Commercial Sprinkler Systems", "Fire sprinkler requirements for commercial and residential buildings",
         "NFPA 13: standard for all occupancies — hazard classification (light, ordinary, extra), design densities, pipe sizing by hydraulic calculation, head types (pendent, upright, sidewall, ESFR). NFPA 13R: residential occupancies up to 4 stories — reduced coverage requirements (sprinklers not required in balconies, attics, closets <24 sq ft, bathrooms <55 sq ft). Both reference NFPA 25 for inspection/testing/maintenance of existing systems.",
         None, []),
     ]),

    # -- EPA Regulations --
    ("EPA — Environmental Protection Agency", "epa_regulations",
     ["Water Supply", "Fixtures & Appliances"],
     "2024-01-01",
     [
        ("Safe Drinking Water Act — Lead-Free Requirements", "Lead-free requirements for potable water components",
         "SDWA Section 1417 (amended 2014, Reduction of Lead in Drinking Water Act): Lead-free means ≤0.25% weighted average lead for wetted surfaces of pipes/fittings/fixtures, ≤0.2% for solder and flux. Applies to all potable water system components. NSF/ANSI 372 certification verifies compliance. NSF/ANSI 61 covers extraction of contaminants from drinking water system components. Violations: fines up to $25,000/day.",
         None, [
            ("Lead Testing and Remediation", "Testing for lead in drinking water and mitigation options",
             "EPA action level: 15 ppb (parts per billion) at the tap. Lead sources in plumbing: pre-1986 lead solder, lead service lines (street to house), brass fixtures with >0.25% lead (pre-2014). Testing: first-draw sample (water sitting 6+ hours) from kitchen cold tap. If >15 ppb: options include point-of-use filter (NSF 53 certified for lead), full re-pipe to eliminate lead solder joints, service line replacement. Flushing cold water for 2+ minutes reduces lead levels as interim measure."),
        ]),
        ("WaterSense Program", "EPA water efficiency labeling for plumbing products",
         "WaterSense is EPA's voluntary program for water-efficient products. Certified products use at least 20% less water while meeting performance criteria. Key categories: toilets (1.28 GPF vs. 1.6 GPF standard), lavatory faucets (1.5 GPM vs. 2.2 GPM), showerheads (2.0 GPM vs. 2.5 GPM), urinals (0.5 GPF vs. 1.0 GPF). Many jurisdictions now mandate WaterSense fixtures in new construction. Utility rebates commonly available for WaterSense products.",
         None, []),
     ]),

    # -- OSHA for Plumbing --
    ("OSHA — Plumbing Contractor Safety", "osha_plumbing",
     ["Estimating & Business", "Drain/Waste/Vent"],
     "2024-01-01",
     [
        ("29 CFR 1926 Subpart P — Excavation", "Excavation and trenching safety requirements",
         "Applies to all excavation/trenching for sewer, water, and gas piping. Trenches 5'+ deep require protective system: sloping/benching (Table B-1), shoring (timber, aluminum hydraulic, or pneumatic), or trench box/shield. Competent person must inspect daily and after rain/vibration/other hazards. Access: ladder, ramp, or steps within 25' of lateral travel for trenches 4'+ deep. Spoil pile: minimum 2' from edge of excavation. Underground utilities: locate before excavation (call 811).",
         None, [
            ("Trench Safety Requirements", "Specific requirements for plumbing excavation work",
             "Type A soil: 3/4:1 slope ratio (53°) or equivalent shoring. Type B: 1:1 (45°). Type C: 1.5:1 (34°). Default to Type C if soil classification is uncertain. Trench box: must extend at least 18\" above surrounding grade. Workers not permitted under loads being handled by excavating equipment. Daily inspections documented. Water accumulation: do not work in trenches with significant water unless adequate precautions taken (dewatering, safety harness for deep excavation)."),
        ]),
        ("29 CFR 1910.146 — Confined Spaces", "Confined space entry for sewer and underground work",
         "Permit-required confined spaces in plumbing: manholes, large-diameter sewer pipes, underground vaults, septic tanks. Requirements: atmospheric testing before entry (O2 19.5-23.5%, LEL <10%, H2S <10 ppm, CO <35 ppm), continuous monitoring, ventilation, attendant at entry, rescue plan, entry permit. Plumbing-specific hazards: hydrogen sulfide (sewer gas), methane (decomposition), oxygen deficiency, engulfment risk in flooded spaces.",
         None, []),
        ("Silica Exposure — 29 CFR 1926.1153", "Respirable crystalline silica when cutting concrete or cast iron",
         "Applies when cutting concrete (core drilling for pipe penetrations), cutting cast iron pipe, or demolishing concrete/masonry for pipe routing. PEL: 50 µg/m³ as 8-hour TWA. Table 1 controls: wet cutting with integrated water delivery, use vacuum-equipped saw, or supply HEPA-filtered respirator (APF 10 minimum). Medical surveillance required if exposed above action level (25 µg/m³) for 30+ days/year.",
         None, []),
     ]),

    # -- ASSE Standards --
    ("ASSE — Plumbing Product Standards", "state_amendments",
     ["Water Supply", "Fixtures & Appliances", "Code Compliance"],
     None,
     [
        ("ASSE 1010 — Water Hammer Arrestors", "Performance requirements for water hammer arrestors",
         "ASSE 1010 covers permanently installed water hammer arrestors (mini-riser, bellows, piston types). Sizing: based on fixture count served — Class A (1-11 fixture units), Class B (12-32), Class C (33-60), Class D (61-113), Class E (114-154), Class F (155-330). Installation: as close to quick-closing valve as possible, accessible. No periodic maintenance required for sealed units. PDI-WH 201 also referenced for sizing.",
         None, []),
        ("ASSE 1013 — RPZ Backflow Preventers", "Reduced pressure zone assembly performance standard",
         "ASSE 1013 covers RPZ assemblies for protection against both backpressure and backsiphonage at high-hazard connections. Relief valve must open before check valve differential drops below 2 psi. Annual testing required by certified tester. Common failure modes: fouled check valve (debris), relief valve weeping (worn disc), frozen/corroded internals. Installation: minimum 12\" above grade/flood level, accessible for testing, no conditions that would submerge relief valve.",
         None, []),
        ("ASSE 1016 — Anti-Scald Devices", "Performance requirements for automatic temperature limiting valves",
         "ASSE 1016 covers pressure-balanced and thermostatic mixing valves for individual fixtures (showers, tubs). Must limit outlet temperature to not more than 120°F when cold supply is interrupted. Response time: must compensate within 2-3 seconds. Required by IPC 424.3 and UPC for all shower and tub-shower valves. Also covers point-of-use thermostatic mixing valves per ASSE 1070 (for healthcare and institutional).",
         None, []),
        ("ASSE 1017 — Temperature Actuated Mixing Valves", "Master thermostatic mixing valves for distribution",
         "ASSE 1017 covers master thermostatic mixing valves installed at water heater outlet to control distribution temperature. Allows water heater storage at 140°F+ (Legionella control) while delivering 120°F to fixtures. Sizing based on flow demand. Not a substitute for point-of-use ASSE 1016 valves at showers. Healthcare applications: ASSE 1070 valves at each point of use in addition to ASSE 1017 at source.",
         None, []),
        ("NSF/ANSI 61 and 372", "Drinking water system component health effects and lead content",
         "NSF/ANSI 61: evaluates contaminants that leach from products into drinking water — covers pipes, fittings, coatings, joining materials, mechanical devices, and distribution system components. NSF/ANSI 372: verifies lead content ≤0.25% weighted average for wetted surfaces (implements SDWA lead-free requirements). Both certifications required for products in contact with potable water. Look for NSF certification mark on all potable water components.",
         None, []),
     ]),
)
