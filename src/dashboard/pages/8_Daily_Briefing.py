import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

import httpx
import streamlit as st

from src.dashboard.components.sidebar import render_page_controls
from src.dashboard.components.theme import COLORS, metric_card, section_header, notification_card, stat_row

st.markdown(f"<h1 style='color:{COLORS['text_primary']}; margin:0 0 4px 0; font-weight:800; font-size:1.8rem;'>Daily Briefing</h1>", unsafe_allow_html=True)
params = render_page_controls(show_horizon=True)

API_BASE = "http://localhost:8000/api/v1"

# --- Check auth ---
if not st.session_state.get("auth_token"):
    st.markdown(f"""
    <div style="background:{COLORS['bg_card']}; border:1px solid {COLORS['border']}; border-radius:12px; padding:32px; text-align:center; margin-bottom:24px;">
        <p style="color:{COLORS['text_secondary']}; font-size:1.1rem;">Log in to see your personalized daily briefing</p>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/0_Login.py", label="Go to Login", icon="\U0001f511")

    # Guest demo
    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
    st.markdown(section_header("Demo Briefing", "Guest preview using AAPL"), unsafe_allow_html=True)

    try:
        r = httpx.get(f"{API_BASE}/signals/AAPL", params={"horizon": 5}, timeout=120)
        if r.status_code == 200:
            sig = r.json()
            color = sig["color"]
            st.markdown(f"""
            <div style="
                display:flex; align-items:center; justify-content:space-between;
                background:{COLORS['bg_card']}; border:1px solid {COLORS['border']};
                border-left:4px solid {color}; border-radius:10px; padding:16px 24px;
            ">
                <div>
                    <span style="color:{COLORS['text_primary']}; font-weight:700; font-size:1.1rem;">AAPL</span>
                    <span style="color:{COLORS['text_muted']}; margin-left:12px;">${sig['current_price']:,.2f}</span>
                </div>
                <div style="display:flex; align-items:center; gap:16px;">
                    <span style="color:{color}; font-weight:800;">{sig['signal_label']}</span>
                    <span style="color:{COLORS['text_secondary']}; font-size:0.85rem;">{sig['confidence']:.0f}%</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            for reason in sig.get("reasoning", [])[:3]:
                st.markdown(f"""
                <div style="color:{COLORS['text_secondary']}; font-size:0.85rem; padding:4px 0 4px 20px;">• {reason}</div>
                """, unsafe_allow_html=True)
    except Exception:
        st.markdown(f"<p style='color:{COLORS['text_muted']}'>Unable to load demo signal</p>", unsafe_allow_html=True)

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
    st.markdown(f"""
    <div style="background:{COLORS['bg_card']}; border:1px solid {COLORS['border']}; border-radius:12px; padding:32px; text-align:center;">
        <p style="color:{COLORS['text_secondary']}; font-size:1.1rem;">Your portfolio is empty. Add holdings to get a personalized briefing!</p>
    </div>
    """, unsafe_allow_html=True)
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
            st.markdown(section_header(f"Notifications ({len(notifs)})", "Alerts and insights for your portfolio"), unsafe_allow_html=True)
            for n in notifs[:5]:
                st.markdown(notification_card(n["icon"], n["message"], n["priority"]), unsafe_allow_html=True)
            st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
except Exception:
    pass

# ========================================
# SECTION 1: Portfolio Snapshot
# ========================================
st.markdown(section_header("Portfolio Snapshot", "Current state of your holdings"), unsafe_allow_html=True)

pnl_color = "green" if summary["total_pnl"] >= 0 else "red"
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(metric_card("Total Value", f"${summary['total_value']:,.2f}"), unsafe_allow_html=True)
with c2:
    st.markdown(metric_card("Total Cost", f"${summary['total_cost']:,.2f}"), unsafe_allow_html=True)
with c3:
    st.markdown(metric_card("Total P&L", f"${summary['total_pnl']:,.2f}", f"{summary['total_pnl_pct']:+.1f}%", pnl_color), unsafe_allow_html=True)
with c4:
    st.markdown(metric_card("Holdings", str(summary["holdings_count"])), unsafe_allow_html=True)

st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

# ========================================
# SECTION 2: Yesterday's Moves
# ========================================
st.markdown(section_header("What Changed", "Recent price movements for your holdings"), unsafe_allow_html=True)

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
            prices = r.json()
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
        color = COLORS["green"] if ch["change_pct"] >= 0 else COLORS["red"]
        arrow = "↑" if ch["change_pct"] >= 0 else "↓"
        st.markdown(f"""
        <div style="
            display:flex; align-items:center; justify-content:space-between;
            background:{COLORS['bg_card']}; border:1px solid {COLORS['border']};
            border-radius:8px; padding:12px 20px; margin-bottom:6px;
        ">
            <div style="display:flex; align-items:center; gap:16px;">
                <span style="color:{COLORS['text_primary']}; font-weight:700;">{ch['ticker']}</span>
                <span style="color:{COLORS['text_muted']}; font-size:0.85rem;">${ch['prev']:.2f} → ${ch['curr']:.2f}</span>
            </div>
            <div style="display:flex; align-items:center; gap:20px;">
                <span style="color:{color}; font-weight:700;">{arrow} {ch['change_pct']:+.2f}%</span>
                <span style="color:{color}; font-size:0.85rem;">Impact: ${ch['impact']:+,.2f}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
else:
    st.markdown(f"<p style='color:{COLORS['text_muted']}'>No recent price data available</p>", unsafe_allow_html=True)

st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

# ========================================
# SECTION 3: Today's Signals
# ========================================
st.markdown(section_header("Today's Signals", "Buy/sell/hold signals for your holdings"), unsafe_allow_html=True)

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
        st.markdown(f"""
        <div style="
            display:flex; align-items:center; justify-content:space-between;
            background:{COLORS['bg_card']}; border:1px solid {COLORS['border']};
            border-left:4px solid {color}; border-radius:10px; padding:16px 24px; margin-bottom:8px;
        ">
            <div>
                <span style="color:{COLORS['text_primary']}; font-weight:700; font-size:1.1rem;">{sig['ticker']}</span>
                <span style="color:{COLORS['text_muted']}; margin-left:12px;">${sig['current_price']:,.2f}</span>
            </div>
            <div style="display:flex; align-items:center; gap:20px;">
                <span style="color:{color}; font-weight:800; font-size:1rem;">{sig['signal_label']}</span>
                <span style="color:{COLORS['text_secondary']}; font-size:0.85rem;">{sig['confidence']:.0f}%</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        reasons = sig.get("reasoning", [])[:2]
        for reason in reasons:
            st.markdown(f"<div style='color:{COLORS['text_secondary']}; font-size:0.8rem; padding:2px 0 2px 28px;'>• {reason}</div>", unsafe_allow_html=True)
else:
    st.markdown(f"<p style='color:{COLORS['text_muted']}; font-size:0.9rem;'>Click 'Refresh Signals' to generate buy/sell/hold signals for your holdings</p>", unsafe_allow_html=True)

st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

# ========================================
# SECTION 4: Action Items
# ========================================
st.markdown(section_header("Action Items", "Prioritized recommendations based on signals"), unsafe_allow_html=True)

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
                "priority": "low" if label == "STRONG BUY" else "medium",
                "icon": "↑",
                "message": f"Consider buying <strong>{ticker}</strong> — {first_reason}",
                "confidence": conf,
            })
        elif label in ("STRONG SELL", "SELL") and conf > 40:
            action_items.append({
                "priority": "high" if label == "STRONG SELL" else "medium",
                "icon": "↓",
                "message": f"Consider reducing <strong>{ticker}</strong> — {first_reason}",
                "confidence": conf,
            })

    # Concentration warnings
    if summary["total_value"] > 0:
        for h in holdings:
            weight = h["market_value"] / summary["total_value"] * 100
            if weight > 50:
                action_items.append({
                    "priority": "medium",
                    "icon": "⚠",
                    "message": f"<strong>{h['ticker']}</strong> is {weight:.0f}% of your portfolio — consider diversifying",
                    "confidence": 0,
                })

    if action_items:
        action_items.sort(key=lambda x: x["confidence"], reverse=True)
        for item in action_items:
            st.markdown(notification_card(item["icon"], item["message"], item["priority"]), unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="background:{COLORS['green_soft']}; border-left:4px solid {COLORS['green']}; padding:12px 16px; border-radius:8px;">
            <span style="color:{COLORS['text_primary']};">No urgent action items today. Your portfolio looks balanced!</span>
        </div>
        """, unsafe_allow_html=True)
else:
    st.markdown(f"<p style='color:{COLORS['text_muted']}; font-size:0.9rem;'>Refresh signals above to see personalized action items</p>", unsafe_allow_html=True)

st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

# ========================================
# SECTION 5: Portfolio Health
# ========================================
st.markdown(section_header("Portfolio Health", "Allocation, performance, and diversity analysis"), unsafe_allow_html=True)

health_cols = st.columns(3)

with health_cols[0]:
    st.markdown(f"<div style='color:{COLORS['text_primary']}; font-weight:700; margin-bottom:12px;'>Allocation</div>", unsafe_allow_html=True)
    for h in holdings:
        if summary["total_value"] > 0:
            weight = h["market_value"] / summary["total_value"] * 100
            bar_color = COLORS["red"] if weight > 50 else COLORS["yellow"] if weight > 30 else COLORS["green"]
            bar_width = min(weight, 100)
            st.markdown(f"""
            <div style="margin-bottom:8px;">
                <div style="display:flex; justify-content:space-between; margin-bottom:2px;">
                    <span style="color:{COLORS['text_secondary']}; font-size:0.8rem;">{h['ticker']}</span>
                    <span style="color:{bar_color}; font-size:0.8rem; font-weight:600;">{weight:.1f}%</span>
                </div>
                <div style="background:{COLORS['border']}; border-radius:4px; height:4px;">
                    <div style="background:{bar_color}; width:{bar_width}%; height:100%; border-radius:4px;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

with health_cols[1]:
    st.markdown(f"<div style='color:{COLORS['text_primary']}; font-weight:700; margin-bottom:12px;'>P&L by Holding</div>", unsafe_allow_html=True)
    for h in holdings:
        pnl_color = COLORS["green"] if h["pnl"] >= 0 else COLORS["red"]
        st.markdown(f"""
        <div style="display:flex; justify-content:space-between; padding:4px 0; border-bottom:1px solid {COLORS['border']}20;">
            <span style="color:{COLORS['text_secondary']}; font-size:0.85rem;">{h['ticker']}</span>
            <span style="color:{pnl_color}; font-size:0.85rem; font-weight:600;">${h['pnl']:+,.2f} ({h['pnl_pct']:+.1f}%)</span>
        </div>
        """, unsafe_allow_html=True)

with health_cols[2]:
    st.markdown(f"<div style='color:{COLORS['text_primary']}; font-weight:700; margin-bottom:12px;'>Market Diversity</div>", unsafe_allow_html=True)
    exchanges: dict[str, int] = {}
    for h in holdings:
        if "." in h["ticker"]:
            ex = h["ticker"].split(".")[-1]
        else:
            ex = "US"
        exchanges[ex] = exchanges.get(ex, 0) + 1

    for ex, count in exchanges.items():
        st.markdown(f"""
        <div style="display:flex; align-items:center; gap:8px; padding:6px 0;">
            <div style="width:8px; height:8px; border-radius:50%; background:{COLORS['accent']};"></div>
            <span style="color:{COLORS['text_secondary']}; font-size:0.85rem;">{ex}: {count} holding(s)</span>
        </div>
        """, unsafe_allow_html=True)

    if len(exchanges) == 1 and len(holdings) > 1:
        st.markdown(f"<div style='color:{COLORS['yellow']}; font-size:0.8rem; margin-top:8px;'>⚠ All in one market — consider diversifying internationally</div>", unsafe_allow_html=True)
    elif len(exchanges) > 1:
        st.markdown(f"<div style='color:{COLORS['green']}; font-size:0.8rem; margin-top:8px;'>Good international diversification</div>", unsafe_allow_html=True)
