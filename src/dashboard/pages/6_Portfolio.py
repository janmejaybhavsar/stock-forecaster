import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

import httpx
import plotly.graph_objects as go
import streamlit as st

from src.dashboard.components.sidebar import render_sidebar

st.set_page_config(page_title="Portfolio - Stock Forecaster", layout="wide")
params = render_sidebar()

API_BASE = "http://localhost:8000/api/v1"

if not st.session_state.get("auth_token"):
    st.warning("Please log in to access your portfolio.")
    st.page_link("pages/0_Login.py", label="Go to Login", icon="🔑")
    st.stop()

headers = {"Authorization": f"Bearer {st.session_state.auth_token}"}

st.header("My Portfolio")

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
try:
    r = httpx.get(f"{API_BASE}/portfolio/", headers=headers, timeout=30)
    r.raise_for_status()
    portfolio = r.json()
except Exception as e:
    st.error(f"Failed to load portfolio: {e}")
    st.stop()

holdings = portfolio["holdings"]
summary = portfolio["summary"]

if not holdings:
    st.info("Your portfolio is empty. Add holdings above to get started!")
    st.stop()

# --- Summary Cards ---
st.markdown("### Portfolio Summary")
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("Total Value", f"${summary['total_value']:,.2f}")
with c2:
    st.metric("Total Cost", f"${summary['total_cost']:,.2f}")
with c3:
    st.metric("Total P&L", f"${summary['total_pnl']:,.2f}", f"{summary['total_pnl_pct']:+.1f}%")
with c4:
    st.metric("Holdings", summary["holdings_count"])

st.markdown("---")

# --- Holdings Table and Chart ---
col_table, col_chart = st.columns([3, 2])

with col_table:
    st.markdown("### Holdings")
    for h in holdings:
        with st.container(border=True):
            tc1, tc2, tc3, tc4, tc5 = st.columns([2, 1.5, 1.5, 1.5, 0.5])
            with tc1:
                st.markdown(f"**{h['ticker']}**")
                st.caption(f"{h['shares']} shares @ ${h['avg_cost']:.2f}")
            with tc2:
                st.metric("Current", f"${h['current_price']:,.2f}")
            with tc3:
                st.metric("Value", f"${h['market_value']:,.2f}")
            with tc4:
                st.metric("P&L", f"${h['pnl']:,.2f}", f"{h['pnl_pct']:+.1f}%")
            with tc5:
                if st.button("X", key=f"del_{h['id']}", help="Remove holding"):
                    httpx.delete(f"{API_BASE}/portfolio/holdings/{h['id']}", headers=headers, timeout=10)
                    st.rerun()

with col_chart:
    st.markdown("### Allocation")
    labels = [h["ticker"] for h in holdings]
    values = [h["market_value"] for h in holdings]

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.4,
        textinfo="label+percent",
        marker=dict(colors=[
            "#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4",
            "#FFEAA7", "#DDA0DD", "#98D8C8", "#F7DC6F",
        ]),
    )])
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=400,
        margin=dict(t=20, b=20, l=20, r=20),
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)
