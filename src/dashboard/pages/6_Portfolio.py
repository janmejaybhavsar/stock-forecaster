import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

import httpx
import streamlit as st

from src.dashboard.components.sidebar import render_page_controls
from src.dashboard.components.theme import COLORS, metric_card, section_header
from src.dashboard.components.ui_helpers import empty_state, error_card, loading_card_skeleton, responsive_columns
from src.dashboard.components.fintech_ui import (
    animated_pnl,
    donut_chart_svg,
    holding_row_html,
    inject_keyboard_shortcuts,
    inject_pnl_animation_css,
    onboarding_tour,
    sparkline_svg,
    toast,
)

st.markdown(f"<h1 style='color:{COLORS['text_primary']}; margin:0 0 4px 0; font-weight:800; font-size:1.8rem;'>Portfolio</h1>", unsafe_allow_html=True)
params = render_page_controls()

# Inject animations and keyboard shortcuts
inject_pnl_animation_css()
inject_keyboard_shortcuts()

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

# --- Onboarding Tour (first-time portfolio users) ---
onboarding_tour(
    steps=[
        {
            "icon": "📊",
            "title": "Welcome to your Portfolio",
            "description": "Track all your holdings in one place. Add stocks, see live P&L, and monitor allocation."
        },
        {
            "icon": "➕",
            "title": "Add Your Holdings",
            "description": "Click 'Add New Holding' below to add stocks. Enter the ticker (e.g., AAPL), number of shares, and your average cost."
        },
        {
            "icon": "🎯",
            "title": "Track Performance",
            "description": "See real-time profit/loss with color-coded indicators, sparkline charts, and allocation breakdowns."
        },
        {
            "icon": "⌨️",
            "title": "Pro Tips",
            "description": "Use Ctrl+K to quickly search tickers. Press '?' anytime to see all keyboard shortcuts."
        },
    ],
    key="portfolio_onboarding_complete",
)

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
                    toast(f"Added {new_ticker.upper()} to portfolio", type="success")
                    st.rerun()
                else:
                    toast(f"Failed to add: {r.text}", type="error")
            else:
                toast("Enter a ticker symbol", type="warning")

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

# --- Summary Cards with animated P&L ---
st.markdown(section_header("Summary"), unsafe_allow_html=True)

cols = responsive_columns(4)
with cols[0]:
    st.markdown(metric_card("Total Value", f"${summary['total_value']:,.2f}"), unsafe_allow_html=True)
with cols[1]:
    st.markdown(metric_card("Total Cost", f"${summary['total_cost']:,.2f}"), unsafe_allow_html=True)
with cols[2]:
    pnl_html = animated_pnl(summary["total_pnl"], summary["total_pnl_pct"], size="large")
    st.markdown(f"""
    <div style="
        background: {COLORS['bg_card']};
        border: 1px solid {COLORS['border']};
        border-radius: 12px;
        padding: 20px 24px;
    ">
        <div style="color:{COLORS['text_secondary']}; font-size:0.75rem; text-transform:uppercase; letter-spacing:0.5px; margin-bottom:8px;">Total P&L</div>
        {pnl_html}
    </div>
    """, unsafe_allow_html=True)
with cols[3]:
    st.markdown(metric_card("Holdings", str(summary["holdings_count"])), unsafe_allow_html=True)

st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

# --- Fetch sparkline data for each holding ---
# Get 7-day price history for sparklines
sparkline_data: dict[str, list[float]] = {}
tickers_to_fetch = list({h["ticker"] for h in holdings})

try:
    from datetime import date, timedelta
    for ticker in tickers_to_fetch[:10]:  # Limit to prevent too many requests
        spark_r = httpx.get(
            f"{API_BASE}/stocks/{ticker}/history",
            params={"start": (date.today() - timedelta(days=7)).isoformat(), "interval": "1d"},
            headers=headers,
            timeout=5,
        )
        if spark_r.status_code == 200:
            data = spark_r.json()
            # Handle both paginated and raw response
            records = data if isinstance(data, list) else data.get("data", [])
            sparkline_data[ticker] = [r["close"] for r in records]
except Exception:
    pass  # Sparklines are nice-to-have, don't block the page

# --- Holdings Table with Sparklines and Chart ---
col_table, col_chart = st.columns([3, 2])

with col_table:
    st.markdown(section_header("Holdings"), unsafe_allow_html=True)
    for h in holdings:
        spark_prices = sparkline_data.get(h["ticker"], [])
        st.markdown(
            holding_row_html(
                ticker=h["ticker"],
                shares=h["shares"],
                avg_cost=h["avg_cost"],
                current_price=h["current_price"],
                market_value=h["market_value"],
                pnl=h["pnl"],
                pnl_pct=h["pnl_pct"],
                sparkline_prices=spark_prices,
            ),
            unsafe_allow_html=True,
        )

        # Delete button
        if st.button(f"Remove {h['ticker']}", key=f"del_{h['id']}", type="secondary"):
            httpx.delete(f"{API_BASE}/portfolio/holdings/{h['id']}", headers=headers, timeout=10)
            toast(f"Removed {h['ticker']} from portfolio", type="info")
            st.rerun()

with col_chart:
    st.markdown(section_header("Allocation"), unsafe_allow_html=True)
    labels = [h["ticker"] for h in holdings]
    values = [h["market_value"] for h in holdings]

    # SVG donut chart
    donut_html = donut_chart_svg(
        labels=labels,
        values=values,
        size=260,
        center_value=f"${summary['total_value']:,.0f}",
        center_label="TOTAL VALUE",
    )
    st.markdown(donut_html, unsafe_allow_html=True)

    # Concentration warning
    if values:
        max_pct = max(values) / sum(values) * 100
        if max_pct > 50:
            max_ticker = labels[values.index(max(values))]
            st.markdown(f"""
            <div style="
                background:{COLORS['yellow_soft']};
                border: 1px solid {COLORS['yellow']}40;
                border-left: 4px solid {COLORS['yellow']};
                border-radius: 8px;
                padding: 10px 14px;
                margin-top: 16px;
            ">
                <span style="color:{COLORS['yellow']}; font-size:0.85rem;">
                    ⚠️ {max_ticker} is {max_pct:.0f}% of your portfolio — consider diversifying.
                </span>
            </div>
            """, unsafe_allow_html=True)
