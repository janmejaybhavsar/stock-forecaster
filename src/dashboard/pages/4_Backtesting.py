import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

import time

import streamlit as st

from src.dashboard.components.charts import equity_curve_chart
from src.dashboard.components.sidebar import render_sidebar

st.set_page_config(page_title="Backtesting - Stock Forecaster", layout="wide")
params = render_sidebar()

st.header("Backtesting")

st.markdown("### Backtest Configuration")
col1, col2, col3 = st.columns(3)
with col1:
    train_window = st.number_input("Training Window (days)", 60, 504, 252)
with col2:
    test_window = st.number_input("Test Window (days)", 5, 63, 21)
with col3:
    step_size = st.number_input("Step Size (days)", 5, 63, 21)

API_BASE = "http://localhost:8000/api/v1"

if st.button("Run Backtest", type="primary"):
    import httpx

    with st.spinner(f"Running backtest for {params['ticker']} with {params['model']}..."):
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
                st.error(f"Backtest failed: {result.get('error', 'Unknown')}")
            else:
                st.warning("Backtest timed out.")
        except Exception as e:
            st.error(f"Error: {e}")
            st.info("Make sure the API server is running.")

if "backtest_result" in st.session_state:
    result = st.session_state["backtest_result"]

    st.subheader("Performance Metrics")
    if result.get("metrics"):
        metrics = result["metrics"]
        cols = st.columns(4)
        cols[0].metric("MAE", f"{metrics.get('mae', 0):.4f}")
        cols[1].metric("RMSE", f"{metrics.get('rmse', 0):.4f}")
        cols[2].metric("MAPE", f"{metrics.get('mape', 0):.2f}%")
        cols[3].metric("Directional Acc.", f"{metrics.get('directional_accuracy', 0):.1f}%")

    if result.get("equity_curve"):
        st.subheader("Equity Curve")
        fig = equity_curve_chart(result["equity_curve"])
        st.plotly_chart(fig, use_container_width=True)

    if result.get("predictions"):
        st.subheader("Backtest Predictions")
        import pandas as pd
        st.dataframe(pd.DataFrame(result["predictions"]), use_container_width=True)
else:
    st.info("Click 'Run Backtest' to evaluate model performance on historical data.")
