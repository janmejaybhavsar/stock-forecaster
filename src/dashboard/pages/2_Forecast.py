import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

import time

import streamlit as st

from src.dashboard.components.charts import forecast_chart
from src.dashboard.components.sidebar import render_sidebar

st.set_page_config(page_title="Forecast - Stock Forecaster", layout="wide")
params = render_sidebar()

st.header(f"{params['ticker']} Price Forecast")

API_BASE = "http://localhost:8000/api/v1"


@st.cache_data(ttl=300)
def fetch_history(ticker: str, start: str, end: str) -> list[dict]:
    import httpx
    r = httpx.get(f"{API_BASE}/stocks/{ticker}/history", params={"start": start, "end": end}, timeout=30)
    r.raise_for_status()
    return r.json()


def run_forecast(ticker: str, model: str, horizon: int, include_sentiment: bool) -> dict:
    import httpx
    r = httpx.post(f"{API_BASE}/forecasts/run", json={
        "ticker": ticker,
        "model_name": model,
        "horizon": horizon,
        "include_sentiment": include_sentiment,
    }, timeout=30)
    r.raise_for_status()
    return r.json()


def poll_forecast(forecast_id: str) -> dict:
    import httpx
    for _ in range(120):
        r = httpx.get(f"{API_BASE}/forecasts/{forecast_id}", timeout=30)
        result = r.json()
        if result["status"] != "running":
            return result
        time.sleep(2)
    return {"status": "timeout", "error": "Forecast timed out"}


if st.sidebar.button("Run Forecast", type="primary", use_container_width=True):
    with st.spinner(f"Running {params['model']} forecast for {params['ticker']}..."):
        try:
            result = run_forecast(
                params["ticker"], params["model"],
                params["horizon"], params["include_sentiment"],
            )
            forecast = poll_forecast(result["id"])

            if forecast["status"] == "completed" and forecast.get("predictions"):
                st.session_state["last_forecast"] = forecast
                st.session_state["last_forecast_params"] = params.copy()
            elif forecast["status"] == "failed":
                st.error(f"Forecast failed: {forecast.get('error', 'Unknown error')}")
            else:
                st.warning("Forecast timed out. Try again.")
        except Exception as e:
            st.error(f"Error: {e}")
            st.info("Make sure the API server is running.")

if "last_forecast" in st.session_state:
    forecast = st.session_state["last_forecast"]
    fp = st.session_state["last_forecast_params"]

    st.success(f"Forecast complete: {fp['model'].upper()} | {fp['ticker']} | {fp['horizon']}-day horizon")

    try:
        historical = fetch_history(fp["ticker"], str(fp["start_date"]), str(fp["end_date"]))
        recent = historical[-60:] if len(historical) > 60 else historical

        fig = forecast_chart(
            recent,
            forecast["predictions"],
            title=f"{fp['ticker']} — {fp['model'].upper()} Forecast",
        )
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Prediction Details")
        import pandas as pd
        pred_df = pd.DataFrame(forecast["predictions"])
        st.dataframe(pred_df, use_container_width=True)

    except Exception as e:
        st.error(f"Error rendering forecast: {e}")
else:
    st.info("Click 'Run Forecast' in the sidebar to generate predictions.")
