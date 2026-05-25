import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

import streamlit as st

from src.dashboard.components.charts import candlestick_chart
from src.dashboard.components.sidebar import render_page_controls
from src.dashboard.components.theme import COLORS, metric_card, section_header
from src.dashboard.components.ui_helpers import error_card

# Page header + inline controls
st.markdown(f"""
<div style="margin-bottom: 4px;">
    <h1 style="color:{COLORS['text_primary']}; margin:0; font-weight:800; font-size:1.8rem;">Overview</h1>
</div>
""", unsafe_allow_html=True)
params = render_page_controls(show_ticker=True, show_dates=True)

from src.dashboard.components.auth_helper import API_BASE


@st.cache_data(ttl=300)
def fetch_history(ticker: str, start: str, end: str) -> list[dict]:
    import httpx
    r = httpx.get(f"{API_BASE}/stocks/{ticker}/history", params={"start": start, "end": end}, timeout=30)
    r.raise_for_status()
    return r.json()


@st.cache_data(ttl=300)
def fetch_info(ticker: str) -> dict:
    import httpx
    r = httpx.get(f"{API_BASE}/stocks/{ticker}/info", timeout=30)
    r.raise_for_status()
    return r.json()


try:
    info = fetch_info(params["ticker"])
    name = info.get("name", "")
    sector = info.get("sector", "")
    industry = info.get("industry", "")
    current_price = info.get("current_price", 0)
    prev_close = info.get("previous_close", 0) or current_price
    change = current_price - prev_close if prev_close else 0
    change_pct = (change / prev_close * 100) if prev_close else 0
    change_color = COLORS["green"] if change >= 0 else COLORS["red"]

    st.markdown(f"""
    <div style="margin-bottom: 24px;">
        <div style="color:{COLORS['text_secondary']}; font-size:0.9rem; margin-bottom:8px;">{name} &nbsp;|&nbsp; {sector} &nbsp;|&nbsp; {industry}</div>
        <div style="display:flex; align-items:baseline; gap:16px;">
            <span style="font-size:2.5rem; font-weight:800; color:{COLORS['text_primary']};">${current_price:,.2f}</span>
            <span style="font-size:1.1rem; font-weight:600; color:{change_color};">{change:+.2f} ({change_pct:+.2f}%)</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Key metrics row
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(metric_card("Market Cap", f"${info.get('market_cap', 0)/1e9:.1f}B" if info.get('market_cap') else "N/A"), unsafe_allow_html=True)
    with c2:
        st.markdown(metric_card("52W High", f"${info.get('fifty_two_week_high', 0):,.2f}"), unsafe_allow_html=True)
    with c3:
        st.markdown(metric_card("52W Low", f"${info.get('fifty_two_week_low', 0):,.2f}"), unsafe_allow_html=True)
    with c4:
        vol = info.get("volume", 0)
        vol_str = f"{vol/1e6:.1f}M" if vol >= 1e6 else f"{vol/1e3:.0f}K" if vol >= 1e3 else str(vol)
        st.markdown(metric_card("Volume", vol_str), unsafe_allow_html=True)

except Exception as e:
    error_card("Stock Info Unavailable", str(e), "Check that the API server is running and the ticker is valid.")

st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

# Chart section
st.markdown(section_header("Price Chart"), unsafe_allow_html=True)

try:
    data = fetch_history(
        params["ticker"],
        str(params["start_date"]),
        str(params["end_date"]),
    )
    if data:
        fig = candlestick_chart(data, title="")
        # Apply dark theme to plotly chart
        fig.update_layout(
            paper_bgcolor=COLORS["bg_primary"],
            plot_bgcolor=COLORS["bg_secondary"],
            font_color=COLORS["text_secondary"],
            xaxis=dict(gridcolor=COLORS["border"], zerolinecolor=COLORS["border"]),
            yaxis=dict(gridcolor=COLORS["border"], zerolinecolor=COLORS["border"]),
            margin=dict(l=0, r=0, t=30, b=0),
        )
        st.plotly_chart(fig, use_container_width=True)

        # Last day stats
        last = data[-1]
        prev = data[-2] if len(data) > 1 else last
        day_change = last["close"] - prev["close"]
        day_pct = (day_change / prev["close"]) * 100 if prev["close"] else 0

        st.markdown(section_header("Latest Session"), unsafe_allow_html=True)
        lc1, lc2, lc3, lc4 = st.columns(4)
        with lc1:
            delta_color = "green" if day_change >= 0 else "red"
            st.markdown(metric_card("Close", f"${last['close']:,.2f}", f"{day_pct:+.2f}%", delta_color), unsafe_allow_html=True)
        with lc2:
            st.markdown(metric_card("Open", f"${last['open']:,.2f}"), unsafe_allow_html=True)
        with lc3:
            st.markdown(metric_card("High", f"${last['high']:,.2f}"), unsafe_allow_html=True)
        with lc4:
            st.markdown(metric_card("Low", f"${last['low']:,.2f}"), unsafe_allow_html=True)
    else:
        st.info("No data available for the selected range.")
except Exception as e:
    error_card("Chart Data Error", str(e), "Make sure the API server is running and try a different date range.")
