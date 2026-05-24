from datetime import date, timedelta

import streamlit as st

_DEFAULTS = {
    "_saved_ticker": "AAPL",
    "_saved_start_date": date.today() - timedelta(days=730),
    "_saved_end_date": date.today(),
    "_saved_model": "arima",
    "_saved_horizon": 5,
    "_saved_sentiment": False,
}


def render_sidebar() -> dict:
    st.sidebar.title("Stock Forecaster")

    if st.session_state.get("auth_token"):
        user = st.session_state.get("auth_user", {})
        st.sidebar.markdown(f"**{user.get('username', 'User')}**")
        if st.sidebar.button("Logout", key="_logout_btn", use_container_width=True):
            st.session_state.pop("auth_token", None)
            st.session_state.pop("auth_user", None)
            st.rerun()
    else:
        st.sidebar.page_link("pages/0_Login.py", label="Login / Register", icon="🔑")

    st.sidebar.markdown("---")

    for k, v in _DEFAULTS.items():
        if k not in st.session_state:
            st.session_state[k] = v

    ticker = st.sidebar.text_input(
        "Ticker Symbol",
        value=st.session_state._saved_ticker,
        max_chars=20,
        help="Enter a stock ticker (e.g. AAPL, MSFT, RELIANCE.NS)",
    ).upper().strip()
    st.session_state._saved_ticker = ticker

    st.sidebar.markdown("### Date Range")
    col1, col2 = st.sidebar.columns(2)
    with col1:
        start_date = st.date_input("Start", value=st.session_state._saved_start_date)
    with col2:
        end_date = st.date_input("End", value=st.session_state._saved_end_date)
    st.session_state._saved_start_date = start_date
    st.session_state._saved_end_date = end_date

    st.sidebar.markdown("### Model Settings")
    available_models = ["arima", "xgboost", "lstm", "transformer", "prophet", "ensemble"]
    model_index = available_models.index(st.session_state._saved_model)
    selected_model = st.sidebar.selectbox("Model", available_models, index=model_index)
    st.session_state._saved_model = selected_model

    horizon = st.sidebar.slider(
        "Forecast Horizon (days)", 1, 30, value=st.session_state._saved_horizon
    )
    st.session_state._saved_horizon = horizon

    include_sentiment = st.sidebar.checkbox(
        "Include Sentiment", value=st.session_state._saved_sentiment
    )
    st.session_state._saved_sentiment = include_sentiment

    return {
        "ticker": ticker,
        "start_date": start_date,
        "end_date": end_date,
        "model": selected_model,
        "horizon": horizon,
        "include_sentiment": include_sentiment,
    }
