import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st

st.set_page_config(
    page_title="Stock Forecaster",
    page_icon="chart_with_upwards_trend",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .stMetric {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        padding: 15px;
        border-radius: 10px;
        border-left: 4px solid #42a5f5;
    }
    .stMetric:hover { border-left-color: #ffa726; }
    div[data-testid="stSidebarContent"] { background: #0e1117; }
</style>
""", unsafe_allow_html=True)

st.title("Stock Price Forecaster")
st.markdown("Multi-model ML forecasting with backtesting and sentiment analysis")
st.markdown("---")
st.markdown("Use the sidebar to navigate between pages.")
