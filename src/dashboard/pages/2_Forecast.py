import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

import time

import streamlit as st

from src.dashboard.components.charts import forecast_chart
from src.dashboard.components.sidebar import render_page_controls
from src.dashboard.components.theme import COLORS, section_header
from src.dashboard.components.ui_helpers import empty_state, error_card

st.markdown(f"<h1 style='color:{COLORS['text_primary']}; margin:0 0 4px 0; font-weight:800; font-size:1.8rem;'>Forecast</h1>", unsafe_allow_html=True)
params = render_page_controls(show_ticker=True, show_dates=True, show_model=True, show_horizon=True, show_sentiment=True)

from src.dashboard.components.auth_helper import API_BASE


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


run_btn = st.button("Run Forecast", type="primary")

if run_btn:
    with st.spinner(f"Running {params['model'].upper()} forecast for {params['ticker']}..."):
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
                error_card("Forecast Failed", forecast.get("error", "Unknown error"), "Try a different model or ticker.")
            else:
                error_card("Forecast Timed Out", "The model took too long to respond.", "Try a simpler model like ARIMA or reduce the horizon.")
        except Exception as e:
            error_card("Request Error", str(e), "Check that the API server is running.")

st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

if "last_forecast" in st.session_state:
    forecast = st.session_state["last_forecast"]
    fp = st.session_state["last_forecast_params"]

    # Success banner
    st.markdown(f"""
    <div style="background:{COLORS['green_soft']}; border:1px solid {COLORS['green']}40; border-radius:8px; padding:12px 20px; margin-bottom:16px;">
        <span style="color:{COLORS['green']}; font-weight:600;">Forecast complete</span>
        <span style="color:{COLORS['text_secondary']}; margin-left:12px;">{fp['model'].upper()} | {fp['ticker']} | {fp['horizon']}-day horizon</span>
    </div>
    """, unsafe_allow_html=True)

    try:
        historical = fetch_history(fp["ticker"], str(fp["start_date"]), str(fp["end_date"]))
        recent = historical[-60:] if len(historical) > 60 else historical

        fig = forecast_chart(
            recent,
            forecast["predictions"],
            title=f"{fp['ticker']} — {fp['model'].upper()} Forecast",
        )
        fig.update_layout(
            paper_bgcolor=COLORS["bg_primary"],
            plot_bgcolor=COLORS["bg_secondary"],
            font_color=COLORS["text_secondary"],
            xaxis=dict(gridcolor=COLORS["border"], zerolinecolor=COLORS["border"]),
            yaxis=dict(gridcolor=COLORS["border"], zerolinecolor=COLORS["border"]),
            margin=dict(l=0, r=0, t=30, b=0),
        )
        st.plotly_chart(fig, use_container_width=True)

        # Prediction details
        st.markdown(section_header("Prediction Details"), unsafe_allow_html=True)
        import pandas as pd
        pred_df = pd.DataFrame(forecast["predictions"])
        st.dataframe(pred_df, use_container_width=True)

    except Exception as e:
        error_card("Render Error", str(e), "The forecast data may be corrupted. Try running again.")
else:
    empty_state("📈", "Click 'Run Forecast' to generate predictions", "Configure model and horizon using the controls above")
