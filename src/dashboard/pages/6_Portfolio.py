import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

import httpx
import plotly.graph_objects as go
import streamlit as st

from src.dashboard.components.sidebar import render_page_controls
from src.dashboard.components.theme import COLORS, metric_card, section_header
from src.dashboard.components.ui_helpers import empty_state, error_card, loading_card_skeleton, responsive_columns

st.markdown(f"<h1 style='color:{COLORS['text_primary']}; margin:0 0 4px 0; font-weight:800; font-size:1.8rem;'>Portfolio</h1>", unsafe_allow_html=True)
params = render_page_controls()

from src.dashboard.components.auth_helper import API_BASE

if not st.session_state.get("auth_token"):
    st.markdown(f"""
    <div style="background:{COLORS['bg_card']}; border:1px solid {COLORS['border']}; border-radius:12px; padding:32px; text-align:center;">
        <p style="color:{COLORS['text_secondary']}; font-size:1.1rem;">Please log in to access your portfolio</p>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/0_Login.py", label="Go to Login", icon="\U0001f511")
    st.stop()

headers = {"Authorization": f"Bearer {st.session_state.auth_token}"}

# --- Add Holding Form ---
with st.expander("Add New Holding", expanded=False):
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    with col1:
        new_ticker = st.text_input("Ticker", placeholder="e.g. AAPL, RELIANCE.NS", key="new_ticker")
    with col2:
        new_shares = st.number_input("Shares", min_value=0.01, value=1.0, step=1.0, key="new_shares")
    with col3:
        new_cost = st.number_input("Avg Cost", min_value=0.01, value=100.0, step=1.0, key="new_cost")
    with col4:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Add", type="primary", use_container_width=True):
            if new_ticker:
                r = httpx.post(
                    f"{API_BASE}/portfolio/holdings",
                    json={"ticker": new_ticker.upper().strip(), "shares": new_shares, "avg_cost": new_cost},
                    headers=headers,
                    timeout=10,
                )
                if r.status_code == 200:
                    st.success(f"Added {new_ticker.upper()}")
                    st.rerun()
                else:
                    st.error(f"Failed: {r.text}")
            else:
                st.warning("Enter a ticker symbol")

# --- Load Portfolio ---
_portfolio_placeholder = st.empty()
with _portfolio_placeholder.container():
    loading_card_skeleton(count=4)

try:
    r = httpx.get(f"{API_BASE}/portfolio/", headers=headers, timeout=30)
    r.raise_for_status()
    portfolio = r.json()
    _portfolio_placeholder.empty()
except Exception as e:
    _portfolio_placeholder.empty()
    error_card("Portfolio Load Failed", str(e), "Check that the API server is running and you're logged in.")
    st.stop()

holdings = portfolio["holdings"]
summary = portfolio["summary"]

if not holdings:
    empty_state("📂", "Your portfolio is empty", "Add holdings above to get started!")
    st.stop()

# --- Summary Cards ---
st.markdown(section_header("Summary"), unsafe_allow_html=True)

pnl_color = "green" if summary["total_pnl"] >= 0 else "red"
cols = responsive_columns(4)
with cols[0]:
    st.markdown(metric_card("Total Value", f"${summary['total_value']:,.2f}"), unsafe_allow_html=True)
with cols[1]:
    st.markdown(metric_card("Total Cost", f"${summary['total_cost']:,.2f}"), unsafe_allow_html=True)
with cols[2]:
    st.markdown(metric_card("Total P&L", f"${summary['total_pnl']:,.2f}", f"{summary['total_pnl_pct']:+.1f}%", pnl_color), unsafe_allow_html=True)
with cols[3]:
    st.markdown(metric_card("Holdings", str(summary["holdings_count"])), unsafe_allow_html=True)

st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

# --- Holdings Table and Chart ---
col_table, col_chart = st.columns([3, 2])

with col_table:
    st.markdown(section_header("Holdings"), unsafe_allow_html=True)
    for h in holdings:
        pnl_color_h = COLORS["green"] if h["pnl"] >= 0 else COLORS["red"]
        st.markdown(f"""
        <div style="
            display:flex; align-items:center; justify-content:space-between;
            background:{COLORS['bg_card']}; border:1px solid {COLORS['border']};
            border-radius:10px; padding:16px 20px; margin-bottom:8px;
        ">
            <div>
                <div style="color:{COLORS['text_primary']}; font-weight:700; font-size:1.05rem;">{h['ticker']}</div>
                <div style="color:{COLORS['text_muted']}; font-size:0.8rem;">{h['shares']} shares @ ${h['avg_cost']:.2f}</div>
            </div>
            <div style="display:flex; align-items:center; gap:24px;">
                <div style="text-align:right;">
                    <div style="color:{COLORS['text_primary']}; font-weight:600;">${h['current_price']:,.2f}</div>
                    <div style="color:{COLORS['text_muted']}; font-size:0.75rem;">Current</div>
                </div>
                <div style="text-align:right;">
                    <div style="color:{COLORS['text_primary']}; font-weight:600;">${h['market_value']:,.2f}</div>
                    <div style="color:{COLORS['text_muted']}; font-size:0.75rem;">Value</div>
                </div>
                <div style="text-align:right;">
                    <div style="color:{pnl_color_h}; font-weight:700;">${h['pnl']:+,.2f}</div>
                    <div style="color:{pnl_color_h}; font-size:0.75rem;">{h['pnl_pct']:+.1f}%</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Delete button (separate so it doesn't break the HTML card)
        if st.button(f"Remove {h['ticker']}", key=f"del_{h['id']}", type="secondary"):
            httpx.delete(f"{API_BASE}/portfolio/holdings/{h['id']}", headers=headers, timeout=10)
            st.rerun()

with col_chart:
    st.markdown(section_header("Allocation"), unsafe_allow_html=True)
    labels = [h["ticker"] for h in holdings]
    values = [h["market_value"] for h in holdings]

    chart_colors = [COLORS["accent"], COLORS["blue"], COLORS["yellow"], COLORS["red"],
                    COLORS["purple"], "#26c6da", "#ff8a65", "#a5d6a7"]

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.5,
        textinfo="label+percent",
        textfont=dict(color=COLORS["text_primary"], size=12),
        marker=dict(colors=chart_colors[:len(labels)]),
    )])
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=400,
        margin=dict(t=20, b=20, l=20, r=20),
        showlegend=False,
        font=dict(color=COLORS["text_secondary"]),
    )
    st.plotly_chart(fig, use_container_width=True)
