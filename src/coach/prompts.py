"""
System prompts and context templates for the AI Portfolio Coach.
"""

SYSTEM_PROMPT = """You are an AI Portfolio Coach — a friendly, knowledgeable financial advisor helping users understand and grow their stock portfolio. You speak in plain English, avoid jargon unless you explain it, and always provide reasoning.

IMPORTANT DISCLAIMERS:
- You are NOT a licensed financial advisor. Always remind users that your analysis is educational and they should do their own research.
- Never guarantee returns or make promises about future performance.
- Encourage diversification and risk management.

Your personality:
- Supportive and encouraging, like a knowledgeable friend
- Uses analogies to explain complex concepts
- Highlights both risks and opportunities
- Gives specific, actionable suggestions (not vague advice)
- Breaks down complex analysis into simple bullet points
"""

PORTFOLIO_ANALYSIS_TEMPLATE = """Here is the user's current portfolio data. Use this to provide personalized analysis:

PORTFOLIO SUMMARY:
- Total Value: ${total_value:,.2f}
- Total Cost: ${total_cost:,.2f}
- Total P&L: ${total_pnl:,.2f} ({total_pnl_pct:+.1f}%)
- Number of Holdings: {holdings_count}

HOLDINGS:
{holdings_detail}

SIGNALS (Buy/Sell/Hold):
{signals_detail}

Based on this real data, provide your analysis.
"""

EXPLAIN_SIGNAL_TEMPLATE = """The user wants to understand the signal for {ticker}.

Current Price: ${current_price:,.2f}
Signal: {signal_label} (composite score: {composite_score:+.2f}, confidence: {confidence:.0f}%)

Technical Analysis (score: {tech_signal:+.2f}):
{tech_reasoning}

Model Consensus (score: {consensus_signal:+.2f}):
{consensus_reasoning}

Sentiment (score: {sentiment_signal:+.2f}):
{sentiment_reasoning}

Explain this signal in plain English. What does it mean? Should the user act on it? What are the risks?
"""

REBALANCING_TEMPLATE = """The user wants rebalancing suggestions for their portfolio:

PORTFOLIO:
{holdings_detail}

Total Value: ${total_value:,.2f}

Current Allocation:
{allocation_detail}

Suggest how they could improve diversification, manage risk, and potentially improve returns. Consider:
1. Sector/market concentration
2. Position sizing
3. Risk management
4. Growth vs value balance
"""

QUESTION_TEMPLATE = """The user has a question about their portfolio or investing in general.

PORTFOLIO CONTEXT:
{portfolio_context}

USER QUESTION: {question}

Answer the question using the portfolio data as context where relevant. Be specific and actionable.
"""


def build_portfolio_context(holdings: list[dict], summary: dict, signals: list[dict] | None = None) -> str:
    """Build a context string from portfolio data."""
    holdings_lines = []
    for h in holdings:
        line = (
            f"- {h['ticker']}: {h['shares']} shares @ ${h['avg_cost']:.2f}, "
            f"current ${h.get('current_price', 0):,.2f}, "
            f"value ${h.get('market_value', 0):,.2f}, "
            f"P&L ${h.get('pnl', 0):,.2f} ({h.get('pnl_pct', 0):+.1f}%)"
        )
        holdings_lines.append(line)
    holdings_detail = "\n".join(holdings_lines) if holdings_lines else "No holdings"

    signals_lines = []
    if signals:
        for s in signals:
            line = f"- {s.get('ticker', '?')}: {s.get('signal_label', 'N/A')} (confidence: {s.get('confidence', 0):.0f}%)"
            reasons = s.get("reasoning", [])
            if reasons:
                line += f" — {reasons[0]}"
            signals_lines.append(line)
    signals_detail = "\n".join(signals_lines) if signals_lines else "No signals computed yet"

    return PORTFOLIO_ANALYSIS_TEMPLATE.format(
        total_value=summary.get("total_value", 0),
        total_cost=summary.get("total_cost", 0),
        total_pnl=summary.get("total_pnl", 0),
        total_pnl_pct=summary.get("total_pnl_pct", 0),
        holdings_count=summary.get("holdings_count", 0),
        holdings_detail=holdings_detail,
        signals_detail=signals_detail,
    )


def build_signal_context(signal_data: dict) -> str:
    """Build context for explaining a signal."""
    tech = signal_data.get("technical", {})
    consensus = signal_data.get("model_consensus", {})
    sentiment = signal_data.get("sentiment", {})

    return EXPLAIN_SIGNAL_TEMPLATE.format(
        ticker=signal_data.get("ticker", "?"),
        current_price=signal_data.get("current_price", 0),
        signal_label=signal_data.get("signal_label", "N/A"),
        composite_score=signal_data.get("composite_score", 0),
        confidence=signal_data.get("confidence", 0),
        tech_signal=tech.get("signal", 0),
        tech_reasoning="\n".join(f"  - {r}" for r in tech.get("reasoning", [])),
        consensus_signal=consensus.get("signal", 0),
        consensus_reasoning="\n".join(f"  - {r}" for r in consensus.get("reasoning", [])),
        sentiment_signal=sentiment.get("signal", 0),
        sentiment_reasoning="\n".join(f"  - {r}" for r in sentiment.get("reasoning", [])),
    )
