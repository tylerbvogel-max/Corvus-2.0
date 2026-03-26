"""Historical record structure for presidential behavioral modeling.

This tenant has no regulatory framework per se — this file provides the
historical record department structure that the seeder expects.
"""

import json


def _cross_ref(depts: list[str]) -> str:
    return json.dumps(depts)


DEPARTMENT = "Historical Record"

REGULATORY_TREE = (
    ("Presidential Communication Patterns", "comm_patterns",
     ["Foreign Policy", "Economic & Trade Policy", "Domestic Policy", "Media & Communications"],
     "2017-01-20",
     [
        ("Truth Social / Twitter Communication", "Direct public communication patterns and timing analysis",
         "Presidential social media usage patterns: timing of posts relative to events, "
         "rhetorical escalation indicators, market-moving language patterns, and "
         "the relationship between social media rhetoric and subsequent policy action.",
         None, []),
     ]),
    ("Executive Action Record", "exec_actions",
     ["Foreign Policy", "Economic & Trade Policy", "Domestic Policy", "Military & Defense", "Immigration"],
     "2017-01-20",
     [
        ("First Term Executive Orders (2017-2021)", "Complete record of executive orders and presidential memoranda from first term",
         "Chronological record of executive actions including: travel bans, trade actions, "
         "deregulation orders, immigration enforcement directives, and emergency declarations. "
         "Each action is linked to the triggering event and communication sequence that preceded it.",
         None, []),
        ("Second Term Executive Orders (2025-present)", "Executive orders and actions from current term",
         "Ongoing record of second-term executive actions including policy reversals, "
         "new initiatives, and emergency declarations.",
         None, []),
     ]),
)
