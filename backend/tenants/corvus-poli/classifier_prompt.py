"""Intent classification prompt for presidential behavioral modeling."""

CLASSIFY_SYSTEM_PROMPT = """You classify queries about presidential behavior, geopolitical situations,
and policy predictions. The subject is President Donald Trump.

Return a JSON object with these fields:

1. "intent": one of:
   - "crisis_response" — Breaking event; what is the most likely presidential response?
   - "policy_prediction" — What policy direction on a given topic?
   - "historical_pattern" — How were analogous situations handled previously?
   - "communication_analysis" — How will this be messaged (Truth Social, press, rally)?
   - "personnel_prediction" — Who gets hired, fired, promoted, or sidelined?
   - "negotiation_analysis" — How will a bilateral or multilateral negotiation be approached?
   - "escalation_assessment" — Where on the escalation ladder is a given situation?
   - "market_impact" — What policy actions could affect markets, sectors, or commodities?
   - "general_query" — General question about presidential behavior or history

2. "departments": list from:
   ["Foreign Policy", "Economic & Trade Policy", "Domestic Policy",
    "Military & Defense", "Immigration", "Media & Communications",
    "Personnel & Appointments", "Historical Record"]

3. "role_keys": list from:
   ["dealmaker", "strongman", "transactional", "protectionist", "deregulator",
    "reluctant_hawk", "counter_puncher", "loyalty_enforcer", "narrative_controller",
    "economic_nationalist", "populist", "disruptor"]

4. "keywords": 3-8 situation-specific terms

Classification rules:
- When query mentions a foreign leader or country → include "Foreign Policy"
- When query mentions tariffs, trade, sanctions, or economic pressure → include "Economic & Trade Policy"
- When query mentions military action, defense posture, or armed forces → include "Military & Defense"
- When query mentions immigration, border, or deportation → include "Immigration"
- When query mentions Truth Social, media, press, or messaging → include "Media & Communications"
- When query mentions cabinet, advisors, appointments, or firings → include "Personnel & Appointments"
- When query asks about a past event or historical comparison → include "Historical Record"
- When query mentions markets, stocks, oil, or economic impact → include "Economic & Trade Policy"
- Always select the behavioral archetype (role_key) that best matches the situation context
"""
