"""
Daily Briefing Generator.
Builds a personalized daily summary for a user's portfolio.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date, timedelta

logger = logging.getLogger(__name__)


@dataclass
class BriefingData:
    # Portfolio snapshot
    total_value: float = 0.0
    total_cost: float = 0.0
    total_pnl: float = 0.0
    total_pnl_pct: float = 0.0
    holdings_count: int = 0

    # Yesterday's changes
    daily_changes: list[dict] = field(default_factory=list)
    top_gainer: dict | None = None
    top_loser: dict | None = None

    # Today's signals
    signals: list[dict] = field(default_factory=list)

    # Action items (ranked by confidence)
    action_items: list[dict] = field(default_factory=list)

    # Portfolio health
    concentration_warnings: list[str] = field(default_factory=list)
    sector_breakdown: dict = field(default_factory=dict)

    # Market context
    market_headlines: list[dict] = field(default_factory=list)

    # Earnings upcoming
    upcoming_earnings: list[dict] = field(default_factory=list)


def generate_briefing(
    holdings: list[dict],
    portfolio_summary: dict,
    include_signals: bool = True,
) -> BriefingData:
    """
    Generate a daily briefing for the user's portfolio.

    holdings: list of enriched holdings (with current_price, market_value, pnl, etc.)
    portfolio_summary: dict with total_value, total_cost, total_pnl, etc.
    """
    from src.data_layer.provider_factory import get_provider

    briefing = BriefingData(
        total_value=portfolio_summary.get("total_value", 0),
        total_cost=portfolio_summary.get("total_cost", 0),
        total_pnl=portfolio_summary.get("total_pnl", 0),
        total_pnl_pct=portfolio_summary.get("total_pnl_pct", 0),
        holdings_count=portfolio_summary.get("holdings_count", 0),
    )

    if not holdings:
        return briefing

    provider = get_provider()

    # --- Yesterday's Changes ---
    daily_changes = []
    for h in holdings:
        ticker = h["ticker"]
        try:
            end = date.today()
            start = end - timedelta(days=10)
            df = provider.get_historical(ticker, start, end)
            if len(df) >= 2:
                prev_close = float(df["Close"].iloc[-2])
                curr_close = float(df["Close"].iloc[-1])
                change = curr_close - prev_close
                change_pct = (change / prev_close) * 100
                daily_changes.append({
                    "ticker": ticker,
                    "prev_close": round(prev_close, 2),
                    "current_close": round(curr_close, 2),
                    "change": round(change, 2),
                    "change_pct": round(change_pct, 2),
                    "shares": h.get("shares", 0),
                    "impact": round(change * h.get("shares", 0), 2),
                })
        except Exception as e:
            logger.warning(f"Failed to get daily change for {ticker}: {e}")
            continue

    briefing.daily_changes = sorted(daily_changes, key=lambda x: x["change_pct"], reverse=True)

    if daily_changes:
        briefing.top_gainer = max(daily_changes, key=lambda x: x["change_pct"])
        briefing.top_loser = min(daily_changes, key=lambda x: x["change_pct"])

    # --- Signals ---
    if include_signals:
        try:
            from src.signals.engine import generate_portfolio_signals
            from dataclasses import asdict

            signal_results = generate_portfolio_signals(
                holdings=[{"ticker": h["ticker"]} for h in holdings],
                horizon=5,
                include_sentiment=False,
            )
            briefing.signals = [asdict(r) for r in signal_results]
        except Exception as e:
            logger.warning(f"Failed to generate signals: {e}")

    # --- Action Items ---
    action_items = []
    for sig in briefing.signals:
        label = sig.get("signal_label", "HOLD")
        confidence = sig.get("confidence", 0)
        ticker = sig.get("ticker", "")

        if label in ("STRONG BUY", "BUY") and confidence > 40:
            action_items.append({
                "ticker": ticker,
                "action": label,
                "confidence": confidence,
                "message": f"Consider buying {ticker} — {sig.get('reasoning', [''])[0]}",
                "priority": "high" if label == "STRONG BUY" else "medium",
            })
        elif label in ("STRONG SELL", "SELL") and confidence > 40:
            action_items.append({
                "ticker": ticker,
                "action": label,
                "confidence": confidence,
                "message": f"Consider selling {ticker} — {sig.get('reasoning', [''])[0]}",
                "priority": "high" if label == "STRONG SELL" else "medium",
            })

    # Sort by confidence descending
    briefing.action_items = sorted(action_items, key=lambda x: x["confidence"], reverse=True)

    # --- Concentration Warnings ---
    if holdings and briefing.total_value > 0:
        for h in holdings:
            weight = h.get("market_value", 0) / briefing.total_value * 100
            if weight > 50:
                briefing.concentration_warnings.append(
                    f"{h['ticker']} makes up {weight:.0f}% of your portfolio — consider diversifying"
                )

        # Sector-like grouping by exchange suffix
        exchange_groups: dict[str, float] = {}
        for h in holdings:
            ticker = h["ticker"]
            if "." in ticker:
                exchange = ticker.split(".")[-1]
            else:
                exchange = "US"
            exchange_groups[exchange] = exchange_groups.get(exchange, 0) + h.get("market_value", 0)

        for exchange, value in exchange_groups.items():
            pct = value / briefing.total_value * 100
            briefing.sector_breakdown[exchange] = round(pct, 1)
            if pct > 80 and len(exchange_groups) == 1 and len(holdings) > 1:
                briefing.concentration_warnings.append(
                    f"All holdings are in the {exchange} market — consider international diversification"
                )

    # --- Upcoming Earnings ---
    for h in holdings:
        try:
            import yfinance as yf
            info = yf.Ticker(h["ticker"]).calendar
            if info is not None and not (hasattr(info, 'empty') and info.empty):
                if isinstance(info, dict) and "Earnings Date" in info:
                    earnings_dates = info["Earnings Date"]
                    if earnings_dates:
                        next_earnings = earnings_dates[0] if isinstance(earnings_dates, list) else earnings_dates
                        if hasattr(next_earnings, 'date'):
                            next_earnings = next_earnings.date()
                        days_until = (next_earnings - date.today()).days
                        if 0 <= days_until <= 30:
                            briefing.upcoming_earnings.append({
                                "ticker": h["ticker"],
                                "date": str(next_earnings),
                                "days_until": days_until,
                            })
        except Exception:
            continue

    briefing.upcoming_earnings.sort(key=lambda x: x.get("days_until", 999))

    return briefing
