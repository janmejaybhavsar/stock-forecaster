import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

import streamlit as st

from src.dashboard.components.charts import candlestick_chart
from src.dashboard.components.metrics_cards import render_metric_cards
from src.dashboard.components.sidebar import render_sidebar

st.set_page_config(page_title="Overview - Stock Forecaster", layout="wide")
params = render_sidebar()

st.header(f"{params['ticker']} Overview")

API_BASE = "http://localhost:8000/api/v1"


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
    render_metric_cards(info)
    st.markdown(f"**{info.get('name', '')}** | {info.get('sector', '')} | {info.get('industry', '')}")
except Exception as e:
    st.warning(f"Could not load stock info: {e}")

st.markdown("---")

try:
    data = fetch_history(
        params["ticker"],
        str(params["start_date"]),
        str(params["end_date"]),
    )
    if data:
        fig = candlestick_chart(data, title=f"{params['ticker']} Price Chart")
        st.plotly_chart(fig, use_container_width=True)

        last = data[-1]
        prev = data[-2] if len(data) > 1 else last
        change = last["close"] - prev["close"]
        pct = (change / prev["close"]) * 100 if prev["close"] else 0

        col1, col2, col3 = st.columns(3)
        col1.metric("Last Close", f"${last['close']:,.2f}", f"{change:+.2f} ({pct:+.2f}%)")
        col2.metric("Day High", f"${last['high']:,.2f}")
        col3.metric("Day Volume", f"{last['volume']:,.0f}")
    else:
        st.info("No data available for the selected range.")
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.info("Make sure the API server is running: `uvicorn src.api.app:create_app --factory --port 8000`")
