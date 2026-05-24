import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

import httpx
import streamlit as st

from src.dashboard.components.sidebar import render_sidebar

st.set_page_config(page_title="Daily Briefing - Stock Forecaster", layout="wide")
params = render_sidebar()

API_BASE = "http://localhost:8000/api/v1"

st.header("\U0001f4cb Daily Briefing")
st.caption("Your personalized portfolio summary — what happened, what to watch, and what to do")

# --- Check auth ---
if not st.session_state.get("auth_token"):
    st.info("Log in to see your personalized daily briefing.")
    st.page_link("pages/0_Login.py", label="Go to Login", icon="\U0001f511")

    # Guest demo
    st.markdown("---")
    st.markdown("### Demo Briefing (AAPL)")
    st.caption("Log in to see your own portfolio briefing")

    try:
        r = httpx.get(f"{API_BASE}/signals/AAPL", params={"horizon": 5}, timeout=120)
        if r.status_code == 200:
            sig = r.json()
            color = sig["color"]
            st.markdown(
                f"**AAPL** — <span style='color:{color};font-weight:bold'>{sig['signal_label']}</span> "
                f"(confidence: {sig['confidence']:.0f}%)",
                unsafe_allow_html=True,
            )
            for reason in sig.get("reasoning", [])[:3]:
                st.markdown(f"- {reason}")
    except Exception:
        st.caption("Unable to load demo signal")

    st.stop()

headers = {"Authorization": f"Bearer {st.session_state.auth_token}"}

# --- Load Portfolio Data ---
@st.cache_data(ttl=300)
def load_portfolio(_headers_tuple):
    headers_dict = dict([_headers_tuple])
    r = httpx.get(f"{API_BASE}/portfolio/", headers=headers_dict, timeout=30)
    if r.status_code == 200:
        return r.json()
    return None

portfolio = load_portfolio(("Authorization", f"Bearer {st.session_state.auth_token}"))

if not portfolio or not portfolio.get("holdings"):
    st.info("Your portfolio is empty. Add holdings to get a personalized briefing!")
    st.page_link("pages/6_Portfolio.py", label="Go to Portfolio", icon="\U0001f4bc")
    st.stop()

holdings = portfolio["holdings"]
summary = portfolio["summary"]

# ========================================
# SECTION 0: Smart Notifications
# ========================================
try:
    nr = httpx.get(f"{API_BASE}/signals/portfolio/notifications", headers=headers, timeout=30)
    if nr.status_code == 200:
        notifs = nr.json().get("notifications", [])
        if notifs:
            st.markdown(f"### \U0001f514 Notifications ({len(notifs)})")
            for n in notifs[:5]:
                priority_style = {
                    "high": "background-color: #3d1515; border-left: 4px solid #FF5252;",
                    "medium": "background-color: #3d3415; border-left: 4px solid #FFB300;",
                    "low": "background-color: #153d15; border-left: 4px solid #00C851;",
                }
                style = priority_style.get(n["priority"], "")
                st.markdown(
                    f"<div style='{style} padding: 10px 15px; border-radius: 4px; margin-bottom: 8px;'>"
                    f"{n['icon']} {n['message']}"
                    f"</div>",
                    unsafe_allow_html=True,
                )
            st.markdown("---")
except Exception:
    pass  # Don't break briefing if notifications fail

# ========================================
# SECTION 1: Portfolio Snapshot
# ========================================
st.markdown("### \U0001f4ca Portfolio Snapshot")

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("Total Value", f"${summary['total_value']:,.2f}")
with c2:
    st.metric("Total Cost", f"${summary['total_cost']:,.2f}")
with c3:
    pnl_delta = f"{summary['total_pnl_pct']:+.1f}%"
    st.metric("Total P&L", f"${summary['total_pnl']:,.2f}", pnl_delta)
with c4:
    st.metric("Holdings", summary["holdings_count"])

st.markdown("---")

# ========================================
# SECTION 2: Yesterday's Moves
# ========================================
st.markdown("### \U0001f4c8 What Changed")

# Compute daily changes inline (faster than running full briefing engine)
changes = []
for h in holdings:
    try:
        from datetime import date, timedelta
        end = date.today()
        start = end - timedelta(days=10)
        r = httpx.get(
            f"{API_BASE}/stocks/{h['ticker']}/history",
            params={"start": str(start), "end": str(end)},
            timeout=15,
        )
        if r.status_code == 200:
            prices = r.json()  # returns list directly
            if len(prices) >= 2:
                prev = prices[-2]["close"]
                curr = prices[-1]["close"]
                change_pct = (curr - prev) / prev * 100
                changes.append({
                    "ticker": h["ticker"],
                    "prev": prev,
                    "curr": curr,
                    "change_pct": change_pct,
                    "impact": (curr - prev) * h["shares"],
                })
    except Exception:
        continue

if changes:
    changes.sort(key=lambda x: x["change_pct"], reverse=True)

    for ch in changes:
        color = "#00C851" if ch["change_pct"] >= 0 else "#FF5252"
        arrow = "↑" if ch["change_pct"] >= 0 else "↓"
        st.markdown(
            f"**{ch['ticker']}** &nbsp; "
            f"<span style='color:{color}'>{arrow} {ch['change_pct']:+.2f}%</span> &nbsp; "
            f"(${ch['prev']:.2f} → ${ch['curr']:.2f}) &nbsp; "
            f"Impact: <span style='color:{color}'>${ch['impact']:+,.2f}</span>",
            unsafe_allow_html=True,
        )
else:
    st.caption("No recent price data available")

st.markdown("---")

# ========================================
# SECTION 3: Today's Signals
# ========================================
st.markdown("### \U0001f6a6 Today's Signals")

if st.button("Refresh Signals", type="primary"):
    try:
        r = httpx.get(
            f"{API_BASE}/signals/portfolio/all",
            params={"horizon": params["horizon"]},
            headers=headers,
            timeout=300,
        )
        r.raise_for_status()
        st.session_state["_briefing_signals"] = r.json().get("signals", [])
    except Exception as e:
        st.error(f"Failed to load signals: {e}")

if "_briefing_signals" in st.session_state:
    sigs = st.session_state["_briefing_signals"]
    for sig in sigs:
        color = sig["color"]
        label = sig["signal_label"]
        conf = sig["confidence"]

        with st.container(border=True):
            sc1, sc2, sc3, sc4 = st.columns([1.5, 1, 1, 4])
            with sc1:
                st.markdown(f"**{sig['ticker']}**")
                st.caption(f"${sig['current_price']:,.2f}")
            with sc2:
                st.markdown(
                    f"<span style='color:{color};font-size:20px;font-weight:bold'>{label}</span>",
                    unsafe_allow_html=True,
                )
            with sc3:
                st.caption(f"Confidence: {conf:.0f}%")
            with sc4:
                reasons = sig.get("reasoning", [])
                if reasons:
                    st.caption(reasons[0])
                if len(reasons) > 1:
                    st.caption(reasons[1])
else:
    st.caption("Click 'Refresh Signals' to generate buy/sell/hold signals for your holdings")

st.markdown("---")

# ========================================
# SECTION 4: Action Items
# ========================================
st.markdown("### ✅ Action Items")

if "_briefing_signals" in st.session_state:
    sigs = st.session_state["_briefing_signals"]
    action_items = []

    for sig in sigs:
        label = sig.get("signal_label", "HOLD")
        conf = sig.get("confidence", 0)
        ticker = sig.get("ticker", "")
        reasons = sig.get("reasoning", [])
        first_reason = reasons[0] if reasons else ""

        if label in ("STRONG BUY", "BUY") and conf > 40:
            action_items.append({
                "priority": "\U0001f7e2" if label == "STRONG BUY" else "\U0001f7e1",
                "message": f"Consider buying **{ticker}** — {first_reason}",
                "confidence": conf,
            })
        elif label in ("STRONG SELL", "SELL") and conf > 40:
            action_items.append({
                "priority": "\U0001f534" if label == "STRONG SELL" else "\U0001f7e0",
                "message": f"Consider reducing **{ticker}** — {first_reason}",
                "confidence": conf,
            })

    # Concentration warnings
    if summary["total_value"] > 0:
        for h in holdings:
            weight = h["market_value"] / summary["total_value"] * 100
            if weight > 50:
                action_items.append({
                    "priority": "⚠️",
                    "message": f"**{h['ticker']}** is {weight:.0f}% of your portfolio — consider diversifying",
                    "confidence": 0,
                })

    if action_items:
        action_items.sort(key=lambda x: x["confidence"], reverse=True)
        for item in action_items:
            st.markdown(f"{item['priority']} {item['message']}")
    else:
        st.success("No urgent action items today. Your portfolio looks balanced!")
else:
    st.caption("Refresh signals above to see personalized action items")

st.markdown("---")

# ========================================
# SECTION 5: Portfolio Health
# ========================================
st.markdown("### \U0001f3e5 Portfolio Health")

health_cols = st.columns(3)

with health_cols[0]:
    st.markdown("**Allocation**")
    for h in holdings:
        if summary["total_value"] > 0:
            weight = h["market_value"] / summary["total_value"] * 100
            bar_color = "#FF5252" if weight > 50 else "#FFB300" if weight > 30 else "#00C851"
            st.markdown(
                f"{h['ticker']}: "
                f"<span style='color:{bar_color}'>{weight:.1f}%</span>",
                unsafe_allow_html=True,
            )

with health_cols[1]:
    st.markdown("**P&L by Holding**")
    for h in holdings:
        pnl_color = "#00C851" if h["pnl"] >= 0 else "#FF5252"
        st.markdown(
            f"{h['ticker']}: "
            f"<span style='color:{pnl_color}'>${h['pnl']:+,.2f} ({h['pnl_pct']:+.1f}%)</span>",
            unsafe_allow_html=True,
        )

with health_cols[2]:
    st.markdown("**Market Diversity**")
    exchanges: dict[str, int] = {}
    for h in holdings:
        if "." in h["ticker"]:
            ex = h["ticker"].split(".")[-1]
        else:
            ex = "US"
        exchanges[ex] = exchanges.get(ex, 0) + 1

    for ex, count in exchanges.items():
        st.markdown(f"{ex}: {count} holding(s)")

    if len(exchanges) == 1 and len(holdings) > 1:
        st.caption("⚠️ All in one market — consider diversifying internationally")
    elif len(exchanges) > 1:
        st.caption("✅ Good international diversification")
