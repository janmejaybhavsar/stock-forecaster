"""
Smart Notifications Generator.
Produces proactive insights for portfolio holdings.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, timedelta

logger = logging.getLogger(__name__)


@dataclass
class Notification:
    type: str  # price_alert, signal_change, portfolio_risk, earnings, opportunity, milestone
    ticker: str | None
    message: str
    priority: str  # high, medium, low
    icon: str


def generate_notifications(
    holdings: list[dict],
    summary: dict,
    signals: list[dict] | None = None,
) -> list[Notification]:
    """Generate smart notifications based on portfolio state."""
    notifications: list[Notification] = []

    if not holdings:
        return notifications

    total_value = summary.get("total_value", 0)

    # --- 1. Price Alerts (significant daily moves) ---
    from src.data_layer.provider_factory import get_provider
    provider = get_provider()

    for h in holdings:
        try:
            end = date.today()
            start = end - timedelta(days=10)
            df = provider.get_historical(h["ticker"], start, end)
            if len(df) >= 2:
                prev_close = float(df["Close"].iloc[-2])
                curr_close = float(df["Close"].iloc[-1])
                change_pct = (curr_close - prev_close) / prev_close * 100

                if abs(change_pct) >= 3:
                    direction = "up" if change_pct > 0 else "down"
                    notifications.append(Notification(
                        type="price_alert",
                        ticker=h["ticker"],
                        message=f"{h['ticker']} moved {change_pct:+.1f}% ({direction}) — current price ${curr_close:,.2f}",
                        priority="high" if abs(change_pct) >= 5 else "medium",
                        icon="\U0001f4c8" if change_pct > 0 else "\U0001f4c9",
                    ))

                # 52-week high/low check
                if len(df) >= 200:
                    high_52w = float(df["High"].tail(252).max())
                    low_52w = float(df["Low"].tail(252).min())
                    if curr_close >= high_52w * 0.98:
                        notifications.append(Notification(
                            type="price_alert",
                            ticker=h["ticker"],
                            message=f"{h['ticker']} is near its 52-week high (${high_52w:,.2f}) — watch for potential resistance",
                            priority="medium",
                            icon="\U0001f3d4️",
                        ))
                    elif curr_close <= low_52w * 1.02:
                        notifications.append(Notification(
                            type="price_alert",
                            ticker=h["ticker"],
                            message=f"{h['ticker']} is near its 52-week low (${low_52w:,.2f}) — potential opportunity or further decline",
                            priority="high",
                            icon="⚠️",
                        ))
        except Exception as e:
            logger.warning(f"Price alert check failed for {h['ticker']}: {e}")

    # --- 2. Signal-based Notifications ---
    if signals:
        for sig in signals:
            label = sig.get("signal_label", "HOLD")
            confidence = sig.get("confidence", 0)
            ticker = sig.get("ticker", "")

            if label == "STRONG BUY" and confidence > 60:
                notifications.append(Notification(
                    type="opportunity",
                    ticker=ticker,
                    message=f"{ticker} has a Strong Buy signal with {confidence:.0f}% confidence — consider increasing your position",
                    priority="high",
                    icon="\U0001f7e2",
                ))
            elif label == "STRONG SELL" and confidence > 60:
                notifications.append(Notification(
                    type="signal_change",
                    ticker=ticker,
                    message=f"{ticker} has a Strong Sell signal with {confidence:.0f}% confidence — consider taking profits or reducing exposure",
                    priority="high",
                    icon="\U0001f534",
                ))

    # --- 3. Portfolio Risk Notifications ---
    if total_value > 0:
        for h in holdings:
            weight = h.get("market_value", 0) / total_value * 100
            if weight > 60:
                notifications.append(Notification(
                    type="portfolio_risk",
                    ticker=h["ticker"],
                    message=f"{h['ticker']} is {weight:.0f}% of your portfolio — consider diversifying to manage risk",
                    priority="high",
                    icon="⚠️",
                ))
            elif weight > 40:
                notifications.append(Notification(
                    type="portfolio_risk",
                    ticker=h["ticker"],
                    message=f"{h['ticker']} is {weight:.0f}% of your portfolio — getting concentrated",
                    priority="medium",
                    icon="\U0001f7e1",
                ))

    # --- 4. P&L Milestones ---
    total_pnl_pct = summary.get("total_pnl_pct", 0)
    if total_pnl_pct >= 10:
        notifications.append(Notification(
            type="milestone",
            ticker=None,
            message=f"Your portfolio is up {total_pnl_pct:.1f}%! Great performance!",
            priority="low",
            icon="\U0001f389",
        ))
    elif total_pnl_pct <= -10:
        notifications.append(Notification(
            type="milestone",
            ticker=None,
            message=f"Your portfolio is down {abs(total_pnl_pct):.1f}% — review your holdings and consider rebalancing",
            priority="high",
            icon="\U0001f6a8",
        ))

    # Individual holding milestones
    for h in holdings:
        pnl_pct = h.get("pnl_pct", 0)
        if pnl_pct >= 50:
            notifications.append(Notification(
                type="milestone",
                ticker=h["ticker"],
                message=f"{h['ticker']} is up {pnl_pct:.0f}%! Consider taking some profits to lock in gains",
                priority="medium",
                icon="\U0001f4b0",
            ))
        elif pnl_pct <= -30:
            notifications.append(Notification(
                type="milestone",
                ticker=h["ticker"],
                message=f"{h['ticker']} is down {abs(pnl_pct):.0f}% — review if your thesis still holds",
                priority="high",
                icon="\U0001f6a8",
            ))

    # --- 5. Earnings Upcoming ---
    for h in holdings:
        try:
            import yfinance as yf
            cal = yf.Ticker(h["ticker"]).calendar
            if cal is not None and isinstance(cal, dict) and "Earnings Date" in cal:
                earnings_dates = cal["Earnings Date"]
                if earnings_dates:
                    next_earnings = earnings_dates[0] if isinstance(earnings_dates, list) else earnings_dates
                    if hasattr(next_earnings, 'date'):
                        next_earnings = next_earnings.date()
                    days_until = (next_earnings - date.today()).days
                    if 0 <= days_until <= 7:
                        notifications.append(Notification(
                            type="earnings",
                            ticker=h["ticker"],
                            message=f"{h['ticker']} earnings in {days_until} day(s) ({next_earnings}) — expect increased volatility",
                            priority="high",
                            icon="\U0001f4c5",
                        ))
                    elif 7 < days_until <= 14:
                        notifications.append(Notification(
                            type="earnings",
                            ticker=h["ticker"],
                            message=f"{h['ticker']} earnings coming up on {next_earnings}",
                            priority="low",
                            icon="\U0001f4c5",
                        ))
        except Exception:
            continue

    # Sort by priority
    priority_order = {"high": 0, "medium": 1, "low": 2}
    notifications.sort(key=lambda n: priority_order.get(n.priority, 99))

    return notifications
