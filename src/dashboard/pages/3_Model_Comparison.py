import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

import plotly.graph_objects as go
import streamlit as st

from src.dashboard.components.sidebar import render_page_controls
from src.dashboard.components.theme import COLORS, section_header
from src.dashboard.components.ui_helpers import empty_state, error_card

st.markdown(f"<h1 style='color:{COLORS['text_primary']}; margin:0 0 4px 0; font-weight:800; font-size:1.8rem;'>Compare Models</h1>", unsafe_allow_html=True)
params = render_page_controls(show_ticker=True, show_dates=True, show_horizon=True)

from src.dashboard.components.auth_helper import API_BASE

# Model selection
models_to_compare = st.multiselect(
    "Select models to compare",
    ["arima", "xgboost", "lstm", "transformer", "prophet"],
    default=["arima", "xgboost"],
)

compare_btn = st.button("Compare Models", type="primary")

if compare_btn:
    if len(models_to_compare) < 2:
        st.warning("Select at least 2 models to compare.")
    else:
        import httpx

        with st.spinner(f"Running {len(models_to_compare)} models in parallel..."):
            try:
                r = httpx.post(f"{API_BASE}/forecasts/compare", json={
                    "ticker": params["ticker"],
                    "models": models_to_compare,
                    "horizon": params["horizon"],
                }, timeout=300)
                r.raise_for_status()
                compare_data = r.json()

                results = {}
                for model_name, model_result in compare_data["results"].items():
                    if model_result["status"] == "completed":
                        results[model_name] = model_result
                    else:
                        st.warning(f"{model_name.upper()} failed: {model_result.get('error', 'Unknown')}")

                if results:
                    st.session_state["comparison_results"] = results
                    st.session_state["comparison_params"] = params.copy()
            except Exception as e:
                error_card("Comparison Failed", str(e), "Check that the API server is running.")

st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

if "comparison_results" in st.session_state:
    results = st.session_state["comparison_results"]
    cp = st.session_state["comparison_params"]

    st.markdown(section_header("Forecast Overlay", f"{len(results)} models for {cp['ticker']}"), unsafe_allow_html=True)

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
            line=dict(color=COLORS["blue"], width=2),
        ))

        model_colors = [COLORS["accent"], COLORS["yellow"], COLORS["red"], COLORS["purple"], "#26c6da"]
        for i, (model, result) in enumerate(results.items()):
            preds = result["predictions"]
            fig.add_trace(go.Scatter(
                x=[p["date"] for p in preds],
                y=[p["predicted_close"] for p in preds],
                mode="lines+markers", name=model.upper(),
                line=dict(color=model_colors[i % len(model_colors)], width=2, dash="dash"),
            ))

        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor=COLORS["bg_secondary"],
            font_color=COLORS["text_secondary"],
            height=500,
            yaxis_title="Price ($)",
            xaxis=dict(gridcolor=COLORS["border"], zerolinecolor=COLORS["border"]),
            yaxis=dict(gridcolor=COLORS["border"], zerolinecolor=COLORS["border"]),
            legend=dict(
                bgcolor=COLORS["bg_card"],
                bordercolor=COLORS["border"],
                font=dict(color=COLORS["text_primary"]),
            ),
            margin=dict(l=0, r=0, t=10, b=0),
        )
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        error_card("Chart Error", str(e), "Check that the API server is running.")

    st.markdown(section_header("Prediction Details"), unsafe_allow_html=True)
    import pandas as pd

    tabs = st.tabs([m.upper() for m in results.keys()])
    for tab, (model, result) in zip(tabs, results.items()):
        with tab:
            st.dataframe(pd.DataFrame(result["predictions"]), use_container_width=True)
else:
    empty_state("🔬", "Select models above and click 'Compare Models'", "Forecasts will be displayed side by side for easy comparison")
