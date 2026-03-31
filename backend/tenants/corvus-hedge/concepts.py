"""Concept neuron definitions for investment analysis domain."""

CONCEPT_DEFINITIONS: tuple[dict, ...] = (
    {
        "label": "LEAPS Strategy Framework",
        "summary": "Long-term equity anticipation securities — 12-24 month call options as leveraged equity exposure with defined risk",
        "content": (
            "LEAPS are long-dated options (typically 12-24 months to expiration) used as leveraged equity "
            "exposure with defined maximum loss. Key evaluation criteria: (1) intrinsic value vs premium "
            "paid — deep ITM LEAPS have high delta (0.70-0.85) and behave like stock with leverage, "
            "(2) implied volatility relative to historical — buying when IV is low captures vol expansion, "
            "(3) time decay profile — theta is minimal at 12+ months but accelerates inside 6 months, "
            "(4) break-even analysis — stock price at expiration that recovers the premium, "
            "(5) delta exposure — how much stock-equivalent exposure per dollar of capital. "
            "Risk management: max loss is the premium paid. Position sizing should reflect the leveraged "
            "nature — a LEAPS position controlling 100 shares costs less than the shares but the "
            "percentage loss on premium can be 100%. Roll decisions: evaluate at 6-month mark whether "
            "to close, roll to next expiration, or let run."
        ),
        "direct_patterns": ["%leaps%"],
        "content_patterns": ["%leaps%", "%long-dated%", "%long dated%", "%12 month call%", "%24 month call%"],
    },
    {
        "label": "DCF Valuation Framework",
        "summary": "Discounted cash flow analysis — projecting free cash flows and discounting to present value for intrinsic value estimation",
        "content": (
            "DCF valuation projects future free cash flows and discounts them to present value using WACC. "
            "Key inputs: (1) revenue growth rate — based on historical trend, TAM analysis, and management "
            "guidance, (2) operating margin trajectory — expansion or compression and why, (3) capex and "
            "working capital needs, (4) discount rate (WACC) — risk-free rate + equity risk premium adjusted "
            "for company beta, (5) terminal value — typically 15-25x terminal FCF or perpetuity growth model. "
            "Sensitivity analysis is critical: test +/- 2% on growth rate and +/- 1% on discount rate. "
            "Margin of safety: buy when market price is 20-40% below intrinsic value estimate. "
            "Limitations: garbage in = garbage out. DCF is only as good as the growth and margin assumptions. "
            "For high-growth tech companies, revenue growth rate is the dominant sensitivity."
        ),
        "direct_patterns": ["%dcf%", "%discounted cash flow%"],
        "content_patterns": ["%dcf%", "%intrinsic value%", "%wacc%", "%free cash flow%", "%margin of safety%"],
    },
    {
        "label": "Macro Cycle Positioning",
        "summary": "Economic cycle phase identification and sector rotation strategy based on leading indicators",
        "content": (
            "The economic cycle has four phases with different sector leadership: "
            "(1) Early expansion — rates low, earnings recovering. Cyclicals, small caps, and tech lead. "
            "Indicators: ISM PMI rising above 50, initial claims declining, yield curve steepening. "
            "(2) Mid expansion — growth broadening, earnings strong. Industrials, materials, energy join. "
            "Indicators: capacity utilization rising, wage growth steady, credit expanding. "
            "(3) Late expansion — inflation rising, Fed tightening. Defensives and energy outperform. "
            "Indicators: yield curve flattening, wage growth accelerating, credit standards tightening. "
            "(4) Recession — earnings falling, rates peaking then falling. Utilities, healthcare, staples. "
            "Indicators: ISM below 50, rising unemployment, inverted yield curve. "
            "For a LEAPS portfolio: early/mid expansion is ideal — long-dated calls benefit from rising "
            "earnings + low/stable rates. Late expansion increases risk — IV may be low (cheap entry) but "
            "the cycle is aging."
        ),
        "direct_patterns": ["%cycle%", "%rotation%"],
        "content_patterns": ["%economic cycle%", "%sector rotation%", "%early expansion%", "%recession%", "%pmi%"],
    },
    {
        "label": "Options Greeks Risk Management",
        "summary": "Understanding and managing delta, gamma, theta, vega, and rho exposure across an options portfolio",
        "content": (
            "Greeks measure sensitivity of option value to underlying variables: "
            "Delta: change in option price per $1 move in underlying. LEAPS calls typically 0.60-0.85 delta. "
            "Portfolio delta = sum of position deltas = stock-equivalent exposure. "
            "Gamma: rate of change of delta. Low for LEAPS (far from expiration), high near-term options. "
            "Theta: daily time decay. LEAPS lose ~$0.01-0.05/day at 12+ months. Accelerates inside 90 days. "
            "Vega: sensitivity to implied volatility. LEAPS have high vega — a 1-point IV increase can add "
            "2-5% to LEAPS value. Buying when IV is low (VIX < 15) and selling when high is an edge. "
            "Rho: sensitivity to interest rates. LEAPS calls benefit from rate cuts (rho is positive). "
            "Portfolio management: total delta tells you directional exposure. Total vega tells you vol "
            "exposure. If both are large and positive, you need the market to go up AND volatility to not "
            "crush — watch for vol-of-vol risk."
        ),
        "direct_patterns": ["%greek%", "%delta%", "%gamma%", "%theta%", "%vega%"],
        "content_patterns": ["%greek%", "%delta%", "%gamma%", "%theta%", "%vega%", "%implied volatility%"],
    },
    {
        "label": "Filing Surveillance Methodology",
        "summary": "Systematic approach to monitoring SEC filings for material changes, red flags, and investment-relevant signals",
        "content": (
            "Filing surveillance is the systematic review of SEC filings to detect material changes. "
            "Priority items in 10-Q/10-K review: (1) Revenue recognition changes — ASC 606 policy shifts, "
            "deferred revenue trends, contract asset/liability movements. (2) Risk factor additions — new "
            "risk factors or expanded language signal management awareness of emerging threats. "
            "(3) Guidance changes — raised/lowered/withdrawn guidance and the language around it. "
            "(4) Insider transactions (via 13F, Form 4) — cluster selling by multiple insiders is a "
            "stronger signal than single transactions. (5) Accounting policy changes — new estimates, "
            "restatements, auditor changes. (6) Segment reporting changes — new segments may signal "
            "strategic shifts; collapsed segments may hide underperformance. (7) Related party transactions "
            "— new or expanded related party dealings. (8) Subsequent events — post-period material events "
            "disclosed in notes. 8-K filings are the most time-sensitive — they report material events "
            "within 4 business days. Key 8-K items: leadership changes, asset sales, material agreements, "
            "bankruptcy, delisting notices."
        ),
        "direct_patterns": ["%filing%", "%10-q%", "%10-k%", "%8-k%"],
        "content_patterns": ["%filing%", "%10-q%", "%10-k%", "%8-k%", "%risk factor%", "%revenue recognition%"],
    },
    {
        "label": "Risk Intuition Framework",
        "summary": "Experienced-based pattern recognition for position sizing, timing, and correlation awareness beyond quantitative models",
        "content": (
            "Risk intuition is the experienced investor's ability to sense when something 'feels wrong' "
            "about a position or market before quantitative signals confirm it. Key patterns: "
            "(1) Position sizing discipline — conviction should scale with position size, but max single "
            "position rarely exceeds 10-15% of portfolio regardless of conviction. Oversizing is the "
            "#1 portfolio killer. (2) Correlation awareness — in a crisis, correlations go to 1. A "
            "tech-heavy portfolio that 'looks diversified' across 15 names may have 0.8+ correlation in "
            "a sell-off. True diversification requires different factor exposures, not just different tickers. "
            "(3) Timing humility — being right about direction but wrong about timing is indistinguishable "
            "from being wrong. LEAPS mitigate this (12-24 months of time) but don't eliminate it. "
            "(4) Liquidity risk — options on smaller names may have wide bid-ask spreads. Getting into a "
            "LEAPS position is easy; exiting at a fair price during stress may not be. "
            "(5) Regime change detection — when the macro environment shifts (rate cycle turn, credit "
            "event, geopolitical shock), historical correlations and patterns break down. The first signal "
            "is usually something that 'shouldn't happen' — an unexpected correlation break or a move "
            "that doesn't match the narrative."
        ),
        "direct_patterns": ["%risk intuition%", "%position siz%"],
        "content_patterns": ["%position siz%", "%correlation%", "%timing%", "%liquidity risk%", "%regime change%"],
    },
)
