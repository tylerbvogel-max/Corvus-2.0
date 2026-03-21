"""Concept neuron definitions for plumbing domain."""

CONCEPT_DEFINITIONS: list[dict] = [
    {
        "label": "Diagnostic Reasoning",
        "summary": "Systematic troubleshooting method: observe symptoms, isolate variables, test hypotheses, verify fix across all plumbing specialties",
        "content": (
            "Diagnostic reasoning in plumbing follows a systematic process: (1) gather symptoms "
            "from customer description and visual observation, (2) determine scope — single "
            "fixture vs. branch vs. main line, (3) form hypotheses ranked by probability, "
            "(4) test each hypothesis with minimally invasive methods first (pressure test, "
            "camera inspection, smoke test, dye test), (5) confirm root cause before opening "
            "walls or excavating. Common diagnostic traps: treating symptoms instead of root "
            "cause (e.g., clearing a drain repeatedly without addressing root intrusion), "
            "assuming the most expensive fix first, and not checking the simplest cause (is the "
            "shutoff valve fully open?). Every department applies this: DWV uses camera and "
            "snake diagnostics, Water Supply uses pressure/flow testing, Gas uses electronic "
            "leak detection, and Fixtures uses component-level inspection."
        ),
        "direct_patterns": ["%diagnos%"],
        "content_patterns": ["%diagnos%", "%troubleshoot%", "%root cause%", "%symptom%"],
    },
    {
        "label": "Code Compliance Navigation",
        "summary": "Understanding the layered code jurisdiction: model code (IPC/UPC) -> state adoption -> local amendments -> manufacturer requirements",
        "content": (
            "Plumbing code compliance operates in layers: (1) Model codes — IPC (International "
            "Plumbing Code) or UPC (Uniform Plumbing Code) provide the base requirements, "
            "(2) State adoption — states adopt a specific edition with amendments, "
            "(3) Local amendments — cities/counties may add further restrictions, "
            "(4) Manufacturer requirements — installation must follow manufacturer instructions "
            "which may exceed code minimums. When codes conflict, the most restrictive applies. "
            "Common pitfalls: assuming IPC applies when the jurisdiction uses UPC (or vice versa), "
            "using an outdated code edition, missing local amendments (e.g., PEX restrictions, "
            "water conservation mandates), and confusing 'code minimum' with 'best practice.' "
            "Always verify: which code, which edition, which local amendments."
        ),
        "direct_patterns": ["%code%compliance%", "%code%requirement%"],
        "content_patterns": ["%ipc%", "%upc%", "%code%section%", "%local%amendment%", "%jurisdiction%"],
    },
    {
        "label": "Fixture Unit Method",
        "summary": "Universal sizing methodology: convert fixtures to standardized units (DFU/WSFU) for pipe sizing across DWV and water supply",
        "content": (
            "The fixture unit method is the fundamental sizing tool in plumbing engineering. "
            "Each fixture type is assigned a standardized unit value representing its probable "
            "demand on the system. DFU (Drainage Fixture Units) size drain piping — IPC Table "
            "709.1 assigns values (WC=4, lavatory=1, shower=2). WSFU (Water Supply Fixture "
            "Units) size supply piping — IPC Table 604.3. The conversion from fixture units to "
            "actual flow (GPM) uses probability curves that account for diversity of use — not "
            "all fixtures operate simultaneously. This method bridges all departments: DWV "
            "specialists use DFU for drain/vent sizing, Water Supply uses WSFU for pipe sizing, "
            "Engineers use both for system design, and Estimators use fixture counts for cost "
            "estimation. Understanding fixture units is the single most important calculation "
            "skill in plumbing."
        ),
        "direct_patterns": ["%fixture unit%"],
        "content_patterns": ["%dfu%", "%wsfu%", "%fixture unit%", "%pipe siz%"],
    },
    {
        "label": "Backflow Prevention Hierarchy",
        "summary": "Cross-connection control: hazard assessment -> device selection -> installation -> annual testing across water supply and code compliance",
        "content": (
            "Backflow prevention protects potable water from contamination. The hierarchy: "
            "(1) Air gap — most reliable, required for high-hazard where feasible, "
            "(2) RPZ (Reduced Pressure Zone) — for high-hazard continuous pressure connections "
            "(ASSE 1013), (3) DCVA (Double Check Valve Assembly) — for low-hazard connections "
            "(ASSE 1015), (4) PVB/AVB — for non-continuous pressure applications. "
            "Selection is driven by IPC Table 608.1 based on degree of hazard (health vs. "
            "non-health) and type of backflow (backpressure vs. backsiphonage). Annual testing "
            "by certified tester is required for RPZ, DCVA, PVB, and SPVB assemblies. "
            "This concept spans Water Supply (device selection and installation), Code "
            "Compliance (IPC 608 requirements), and Estimating (device and testing costs)."
        ),
        "direct_patterns": ["%backflow%"],
        "content_patterns": ["%backflow%", "%cross.connection%", "%rpz%", "%asse 1013%"],
    },
    {
        "label": "Trap Seal Protection",
        "summary": "Fundamental DWV principle: every fixture needs a trap, every trap needs a vent to maintain its water seal",
        "content": (
            "The trap-vent relationship is the core principle of DWV systems. Traps (P-traps) "
            "create a water seal (2-4 inches per IPC 1002.4) that blocks sewer gas from "
            "entering occupied spaces. Vents protect this seal by allowing air into the system "
            "to prevent siphonage (negative pressure pulling water out of the trap) and back-"
            "pressure (positive pressure pushing through the seal). Without proper venting, "
            "draining one fixture can siphon the trap of an adjacent fixture. Critical "
            "distances (IPC Table 906.1) define maximum trap arm lengths before a vent is "
            "required. This concept underlies everything in DWV: drain sizing, vent sizing, "
            "fixture installation, and most code violations encountered during inspection."
        ),
        "direct_patterns": ["%trap seal%", "%trap arm%"],
        "content_patterns": ["%trap%", "%vent%", "%siphon%", "%p-trap%", "%s-trap%"],
    },
    {
        "label": "Safety-First Gas Work",
        "summary": "Gas piping safety protocol: leak detection, pressure testing, venting categories, combustion air, and CO prevention",
        "content": (
            "Gas piping work requires a safety-first mindset because failures are immediately "
            "life-threatening. Key principles: (1) Never use flame for leak detection — use "
            "electronic detectors or approved leak detection fluid. (2) Always pressure test "
            "new piping at 3+ psi with air/nitrogen before introducing gas (IFGC 406.4). "
            "(3) Verify combustion air supply for all gas appliances — insufficient air causes "
            "incomplete combustion and carbon monoxide production. (4) Understand vent "
            "categories (I-IV) and match vent material to appliance type — a Category IV "
            "condensing furnace vents with PVC, not B-vent. (5) CSST bonding is mandatory "
            "(IFGC 310.1.1) to protect against lightning-induced perforation. "
            "Gas work spans Gas Piping (installation), Code Compliance (NFPA 54/IFGC), "
            "and Fixtures & Appliances (appliance connection and venting)."
        ),
        "direct_patterns": ["%gas leak%", "%gas pip%"],
        "content_patterns": ["%gas%", "%nfpa 54%", "%ifgc%", "%combustion air%", "%carbon monoxide%"],
    },
    {
        "label": "Water Quality and Lead Safety",
        "summary": "Potable water safety: lead-free requirements (SDWA 1417), NSF certification, testing protocols, and remediation options",
        "content": (
            "Potable water quality in plumbing centers on lead safety and material "
            "certification. The Safe Drinking Water Act Section 1417 (amended 2014) defines "
            "lead-free as 0.25% weighted average for wetted surfaces. All potable water "
            "components must be NSF/ANSI 61 (contaminant extraction) and NSF/ANSI 372 "
            "(lead content) certified. Pre-1986 homes may have lead solder joints; pre-2014 "
            "fixtures may exceed current lead-free thresholds. EPA action level is 15 ppb "
            "at the tap. Remediation options range from point-of-use filtration (NSF 53 "
            "certified for lead) to full re-pipe. This concept connects Water Supply "
            "(material selection), Code Compliance (EPA/SDWA requirements), Fixtures & "
            "Appliances (NSF-certified products), and Estimating (re-pipe cost analysis)."
        ),
        "direct_patterns": ["%lead free%", "%lead-free%"],
        "content_patterns": ["%lead%", "%nsf%61%", "%nsf%372%", "%sdwa%", "%potable%"],
    },
    {
        "label": "Pressure Management",
        "summary": "Water pressure control: PRV, expansion tanks, thermal expansion, water hammer arrestors across supply systems",
        "content": (
            "Water pressure management prevents both equipment damage and safety hazards. "
            "Key components: (1) PRV (Pressure Reducing Valve) — required when static pressure "
            "exceeds 80 psi (IPC 604.8). (2) Expansion tank — required when a PRV or check "
            "valve creates a closed system, to absorb thermal expansion (IPC 607.3.2). "
            "(3) Water hammer arrestors (ASSE 1010) — required at quick-closing valves to "
            "absorb pressure surges. (4) T&P relief valve — safety device on water heaters "
            "that opens if temperature exceeds 210F or pressure exceeds 150 psi. "
            "Pressure problems cascade: high street pressure without a PRV damages fixtures, "
            "a PRV without an expansion tank causes T&P valve discharge, and quick-closing "
            "valves without arrestors cause pipe noise and joint stress."
        ),
        "direct_patterns": ["%pressure%"],
        "content_patterns": ["%pressure%", "%prv%", "%expansion tank%", "%water hammer%", "%thermal expansion%"],
    },
    {
        "label": "Service Business Operations",
        "summary": "Plumbing business management: call triage, flat-rate pricing, estimating methods, permit workflow, and customer communication",
        "content": (
            "Running a plumbing service business requires operational systems beyond technical "
            "skill. Call triage: prioritize emergencies (active flooding, gas leaks, no water) "
            "over standard service (dripping faucet, running toilet). Pricing models: "
            "time-and-materials (transparent but unpredictable for customer), flat-rate "
            "(predictable for customer, requires good estimating), or diagnostic fee + quoted "
            "repair. Estimating: residential rough-in by fixture count, service work by task "
            "complexity, commercial by engineering calculation. Permit workflow: determine if "
            "work requires permit, pull permit before starting, schedule inspections at required "
            "stages, receive final approval. Customer communication: explain the problem in "
            "non-technical terms, present options (repair vs. replace, temporary vs. permanent), "
            "provide written estimate before starting work."
        ),
        "direct_patterns": ["%estimat%", "%pric%"],
        "content_patterns": ["%estimat%", "%flat rate%", "%service call%", "%permit%", "%dispatch%"],
        "role_filters": ["estimator", "dispatcher"],
    },
]
