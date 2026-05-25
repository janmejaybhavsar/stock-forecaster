import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

import time

import streamlit as st

from src.dashboard.components.charts import equity_curve_chart
from src.dashboard.components.sidebar import render_page_controls
from src.dashboard.components.theme import COLORS, metric_card, section_header
from src.dashboard.components.ui_helpers import empty_state, error_card

st.markdown(f"<h1 style='color:{COLORS['text_primary']}; margin:0 0 4px 0; font-weight:800; font-size:1.8rem;'>Backtesting</h1>", unsafe_allow_html=True)
params = render_page_controls(show_ticker=True, show_dates=True, show_model=True)

from src.dashboard.components.auth_helper import API_BASE

# Configuration
st.markdown(section_header("Configuration"), unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
with col1:
    train_window = st.number_input("Training Window (days)", 60, 504, 252)
with col2:
    test_window = st.number_input("Test Window (days)", 5, 63, 21)
with col3:
    step_size = st.number_input("Step Size (days)", 5, 63, 21)

run_btn = st.button("Run Backtest", type="primary")

if run_btn:
    import httpx

    with st.spinner(f"Running backtest for {params['ticker']} with {params['model'].upper()}..."):
        try:
            r = httpx.post(f"{API_BASE}/backtests/run", json={
                "ticker": params["ticker"],
                "model_name": params["model"],
                "train_window": train_window,
                "test_window": test_window,
                "step_size": step_size,
            }, timeout=30)
            job = r.json()

            for _ in range(180):
                r = httpx.get(f"{API_BASE}/backtests/{job['id']}", timeout=30)
                result = r.json()
                if result["status"] != "running":
                    break
                time.sleep(2)

            if result["status"] == "completed":
                st.session_state["backtest_result"] = result
            elif result["status"] == "failed":
                error_card("Backtest Failed", result.get("error", "Unknown error"), "Try a different model or adjust the training window.")
            else:
                error_card("Backtest Timed Out", "The model took too long to respond.", "Try reducing the training window or use a faster model like ARIMA.")
        except Exception as e:
            error_card("Request Error", str(e), "Check that the API server is running.")

st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

if "backtest_result" in st.session_state:
    result = st.session_state["backtest_result"]

    # Performance Metrics
    if result.get("metrics"):
        st.markdown(section_header("Performance Metrics", "How well the model predicted historical prices"), unsafe_allow_html=True)
        metrics = result["metrics"]

        mc1, mc2, mc3, mc4 = st.columns(4)
        with mc1:
            st.markdown(metric_card("MAE", f"{metrics.get('mae', 0):.4f}"), unsafe_allow_html=True)
        with mc2:
            st.markdown(metric_card("RMSE", f"{metrics.get('rmse', 0):.4f}"), unsafe_allow_html=True)
        with mc3:
            st.markdown(metric_card("MAPE", f"{metrics.get('mape', 0):.2f}%"), unsafe_allow_html=True)
        with mc4:
            acc = metrics.get("directional_accuracy", 0)
            acc_color = "green" if acc >= 55 else "red" if acc < 45 else "yellow"
            st.markdown(metric_card("Direction Acc.", f"{acc:.1f}%", delta_color=acc_color), unsafe_allow_html=True)

    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

    # Equity Curve
    if result.get("equity_curve"):
        st.markdown(section_header("Equity Curve", "Simulated portfolio value over the backtest period"), unsafe_allow_html=True)
        fig = equity_curve_chart(result["equity_curve"])
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor=COLORS["bg_secondary"],
            font_color=COLORS["text_secondary"],
            xaxis=dict(gridcolor=COLORS["border"], zerolinecolor=COLORS["border"]),
            yaxis=dict(gridcolor=COLORS["border"], zerolinecolor=COLORS["border"]),
            margin=dict(l=0, r=0, t=10, b=0),
        )
        st.plotly_chart(fig, use_container_width=True)

    # Predictions table
    if result.get("predictions"):
        st.markdown(section_header("Backtest Predictions"), unsafe_allow_html=True)
        import pandas as pd
        st.dataframe(pd.DataFrame(result["predictions"]), use_container_width=True)
else:
    empty_state("🧪", "Click 'Run Backtest' to evaluate model performance", "Adjust training window, test window, and step size above")
