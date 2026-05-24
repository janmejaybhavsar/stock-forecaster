import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

import time

import streamlit as st

from src.dashboard.components.charts import comparison_bar_chart, forecast_chart
from src.dashboard.components.sidebar import render_sidebar

st.set_page_config(page_title="Model Comparison - Stock Forecaster", layout="wide")
params = render_sidebar()

st.header("Model Comparison")

API_BASE = "http://localhost:8000/api/v1"

models_to_compare = st.multiselect(
    "Select models to compare",
    ["arima", "xgboost", "lstm", "transformer", "prophet"],
    default=["arima", "xgboost"],
)

if st.button("Compare Models", type="primary"):
    if len(models_to_compare) < 2:
        st.warning("Select at least 2 models to compare.")
    else:
        import httpx

        results = {}
        progress = st.progress(0)

        for i, model in enumerate(models_to_compare):
            with st.spinner(f"Running {model}..."):
                try:
                    r = httpx.post(f"{API_BASE}/forecasts/run", json={
                        "ticker": params["ticker"],
                        "model_name": model,
                        "horizon": params["horizon"],
                        "include_sentiment": False,
                    }, timeout=30)
                    job = r.json()

                    for _ in range(120):
                        r = httpx.get(f"{API_BASE}/forecasts/{job['id']}", timeout=30)
                        result = r.json()
                        if result["status"] != "running":
                            break
                        time.sleep(2)

                    if result["status"] == "completed":
                        results[model] = result
                except Exception as e:
                    st.warning(f"{model} failed: {e}")

            progress.progress((i + 1) / len(models_to_compare))

        if results:
            st.session_state["comparison_results"] = results
            st.session_state["comparison_params"] = params.copy()

if "comparison_results" in st.session_state:
    results = st.session_state["comparison_results"]
    cp = st.session_state["comparison_params"]

    st.subheader("Forecast Overlay")
    import plotly.graph_objects as go
    import httpx

    try:
        r = httpx.get(f"{API_BASE}/stocks/{cp['ticker']}/history", params={
            "start": str(cp["start_date"]), "end": str(cp["end_date"]),
        }, timeout=30)
        historical = r.json()
        recent = historical[-60:] if len(historical) > 60 else historical

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=[d["date"] for d in recent],
            y=[d["close"] for d in recent],
            mode="lines", name="Historical",
            line=dict(color="#42a5f5", width=2),
        ))

        colors = ["#ffa726", "#66bb6a", "#ef5350", "#ab47bc", "#26c6da"]
        for i, (model, result) in enumerate(results.items()):
            preds = result["predictions"]
            fig.add_trace(go.Scatter(
                x=[p["date"] for p in preds],
                y=[p["predicted_close"] for p in preds],
                mode="lines+markers", name=model.upper(),
                line=dict(color=colors[i % len(colors)], width=2, dash="dash"),
            ))

        fig.update_layout(
            title=f"{cp['ticker']} — Model Comparison",
            template="plotly_dark", height=500,
            yaxis_title="Price ($)",
        )
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Error: {e}")

    st.subheader("Prediction Table")
    import pandas as pd
    for model, result in results.items():
        st.markdown(f"**{model.upper()}**")
        st.dataframe(pd.DataFrame(result["predictions"]), use_container_width=True)
