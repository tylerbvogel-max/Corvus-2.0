"""Concept neuron definitions for presidential behavioral modeling.

These are cross-cutting behavioral heuristics observed across multiple
policy domains. Each concept spans departments and represents a recurring
pattern in presidential decision-making.
"""

CONCEPT_DEFINITIONS: list[dict] = [
    {
        "label": "Escalation Ladder",
        "summary": "Predictable escalation sequence: Truth Social → rally → media → sanctions/economic action → military posturing → direct action",
        "content": (
            "When confronted with a provocation or challenge, the president follows a "
            "predictable escalation sequence observed across multiple domains (foreign policy, "
            "domestic politics, trade disputes): (1) Truth Social post within hours — tests "
            "rhetoric and gauges reaction, (2) rally or media interview mention — elevates to "
            "public narrative, (3) formal press statement or spokesperson escalation, "
            "(4) economic/sanctions action — preferred tool over military, (5) military "
            "posturing — carrier groups, troop movements as signaling, (6) direct action — "
            "rare, requires perceived direct threat to American lives or interests. "
            "De-escalation typically occurs between steps 3-4 if counterparty signals willingness "
            "to negotiate. Observable across: Iran (2019-2020), North Korea (2017-2018), "
            "China trade war (2018-2019), domestic political opponents."
        ),
        "direct_patterns": ["%escalat%", "%ladder%"],
        "content_patterns": ["%escalat%", "%truth social%", "%rally%", "%postur%"],
    },
    {
        "label": "Dealmaker Framing",
        "summary": "Reframes any agreement as a 'win' regardless of concessions; pattern: escalate → negotiate → declare victory",
        "content": (
            "The dealmaker framing pattern follows a consistent three-phase structure: "
            "(1) Escalate — create pressure through rhetoric, tariffs, sanctions, or "
            "withdrawal threats to establish maximum leverage position, (2) Negotiate — "
            "engage in bilateral talks, often through personal relationship with counterpart "
            "leader, making tactical concessions while maintaining public hardline, "
            "(3) Declare victory — reframe any outcome as a historic deal regardless of "
            "objective concessions. Key indicators: use of 'the biggest deal,' 'nobody thought "
            "this was possible,' 'they never had a deal like this before.' Observable across: "
            "USMCA (reframed NAFTA with minimal changes as 'brand new'), Phase One China deal "
            "(partial rollback framed as historic), North Korea summits (no denuclearization "
            "achieved, framed as breakthrough), Abraham Accords (genuine achievement, also "
            "heavily framed). Critical insight: the declared victory rarely matches the "
            "objective outcome — track actual policy changes, not rhetoric."
        ),
        "direct_patterns": ["%deal%", "%negotiat%"],
        "content_patterns": ["%deal%", "%negotiat%", "%agreement%", "%win%"],
    },
    {
        "label": "Loyalty Test Pattern",
        "summary": "Personnel decisions driven by perceived loyalty; cycle: praise → disagreement → 'disloyal' label → removal",
        "content": (
            "Personnel decisions follow a loyalty-first evaluation framework rather than "
            "competence-based assessment. The observable cycle: (1) Initial appointment with "
            "lavish public praise ('the best,' 'tremendous,' 'nobody better'), (2) Honeymoon "
            "period where appointee has latitude, (3) First public disagreement or perceived "
            "disloyalty triggers suspicion, (4) Testing period — will they publicly realign? "
            "(5) If not: 'disloyal' label applied, often via Truth Social, (6) Removal — "
            "either forced resignation or public firing. Time from first disagreement to "
            "removal: typically 2-8 weeks. Observable across: Rex Tillerson (State), "
            "Jeff Sessions (AG), James Mattis (Defense), John Bolton (NSA), Mark Esper "
            "(Defense), Bill Barr (AG — partial pattern), HR McMaster (NSA). Exception: "
            "appointees who publicly realign can survive (Lindsey Graham pattern)."
        ),
        "direct_patterns": ["%loyal%", "%fire%", "%firing%"],
        "content_patterns": ["%loyal%", "%appoint%", "%cabinet%", "%fired%", "%resign%"],
    },
    {
        "label": "Strength Perception Sensitivity",
        "summary": "Responses calibrated to perceived strength of counterparty; strong leaders get respect, weak leaders get maximalist demands",
        "content": (
            "Presidential responses are heavily calibrated by whether the counterparty is "
            "perceived as 'strong' or 'weak.' Strong leaders (Xi Jinping, Putin, Kim Jong Un, "
            "Erdogan, MBS) receive: personal rapport-building, private negotiation channels, "
            "public expressions of respect ('very smart,' 'tough'), willingness to make "
            "concessions for relationship. Weak leaders (perceived) receive: public humiliation, "
            "maximalist demands, no private back-channel, used as examples. This extends to "
            "domestic politics: strong opponents (those who fight back) earn grudging respect; "
            "those who capitulate get contempt. Critical for prediction: identify whether the "
            "current counterparty falls into the 'strong' or 'weak' category, as this "
            "fundamentally changes the response pattern. Shift indicator: a leader can move "
            "from 'weak' to 'strong' by publicly standing up (Zelensky partial example)."
        ),
        "direct_patterns": ["%strong%leader%", "%respect%"],
        "content_patterns": ["%strong%", "%weak%", "%respect%", "%tough%"],
    },
    {
        "label": "Narrative Control Reflex",
        "summary": "When losing a news cycle, creates a new controversy to redirect media attention within 24-48 hours",
        "content": (
            "When the dominant media narrative is unfavorable, a new controversy or "
            "announcement is generated to redirect attention. This is not always strategic — "
            "it appears to be partly instinctive. Timing: typically within 24-48 hours of "
            "negative coverage reaching critical mass. Methods: provocative Truth Social post, "
            "surprise policy announcement, personal attack on a public figure, or leaked "
            "consideration of controversial action. The redirected topic does not need to be "
            "resolved — it only needs to dominate one news cycle. Observable across: "
            "both terms, dozens of instances. Prediction utility: when a negative story is "
            "building, expect a diversionary action within 48 hours. The nature of the "
            "diversion often reveals what topics the president considers high-leverage "
            "(immigration, trade, foreign policy drama tend to be the preferred redirects)."
        ),
        "direct_patterns": ["%distract%", "%narrative%", "%news cycle%"],
        "content_patterns": ["%distract%", "%narrative%", "%media%", "%redirect%", "%diversion%"],
    },
    {
        "label": "Economic Nationalism Trigger",
        "summary": "Trade deficits, job losses, or foreign competition trigger protectionist response regardless of advisor input",
        "content": (
            "Trade deficits, manufacturing job losses, and foreign economic competition are "
            "the most reliable triggers for policy action. This pattern is remarkably consistent "
            "across both terms and predates the presidency (1980s Japan rhetoric mirrors "
            "2018 China rhetoric almost verbatim). Key indicators: (1) trade deficit data "
            "release → public statement within days, (2) plant closure announcement → "
            "direct intervention via phone call or tweet, (3) foreign government subsidy → "
            "tariff threat within weeks. Advisor input has minimal impact on this trigger — "
            "Gary Cohn, Larry Kudlow, and others have all failed to moderate the protectionist "
            "instinct on this specific issue. The response is almost always tariffs as the "
            "first tool, followed by bilateral trade negotiation pressure. Observable across: "
            "China (2018-ongoing), EU (steel/aluminum), Canada (lumber, dairy), Japan (autos), "
            "Mexico (immigration-linked tariff threats). This is the single most predictable "
            "behavioral pattern in the repertoire."
        ),
        "direct_patterns": ["%tariff%", "%trade deficit%", "%protectionist%"],
        "content_patterns": ["%tariff%", "%trade%", "%deficit%", "%import%", "%manufacturing%"],
    },
    {
        "label": "Revenge/Reciprocity Principle",
        "summary": "Perceived slights receive proportional or disproportionate retaliation; response is near-certain, timing varies",
        "content": (
            "Perceived slights, betrayals, or public attacks trigger a retaliation response "
            "that is near-certain in occurrence but variable in timing. The retaliation is "
            "often disproportionate to the original slight. This applies across all domains: "
            "political opponents, media figures, foreign leaders, former allies, and "
            "institutions. Key characteristics: (1) the slight is never forgotten — retaliation "
            "may come months or years later, (2) the response is public and designed to be "
            "visible as punishment, (3) the severity often exceeds what a proportional response "
            "would warrant, (4) once labeled an enemy, rehabilitation is rare but possible "
            "(requires public submission). This pattern is documented in 'The Art of the Deal' "
            "as an explicit philosophy: 'When someone screws you, screw them back ten times "
            "harder.' Observable across: political opponents (too numerous to list), media "
            "(CNN, NYT, specific journalists), foreign relations (EU tariffs partly framed "
            "as response to trade 'unfairness'), former appointees (Sessions, Mattis, Bolton). "
            "Prediction utility: if a slight has occurred, retaliation is coming — the question "
            "is when and in what form, not whether."
        ),
        "direct_patterns": ["%reveng%", "%retaliat%", "%payback%"],
        "content_patterns": ["%reveng%", "%retaliat%", "%slight%", "%betray%", "%punch back%"],
    },
]
