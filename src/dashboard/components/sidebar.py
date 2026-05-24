"""Sidebar utilities and page-level controls."""

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


def _ensure_defaults():
    for k, v in _DEFAULTS.items():
        if k not in st.session_state:
            st.session_state[k] = v


def render_sidebar() -> dict:
    """Backward-compatible: returns params from session_state."""
    _ensure_defaults()
    if "_sidebar_params" in st.session_state:
        return st.session_state["_sidebar_params"]
    return {
        "ticker": st.session_state._saved_ticker,
        "start_date": st.session_state._saved_start_date,
        "end_date": st.session_state._saved_end_date,
        "model": st.session_state._saved_model,
        "horizon": st.session_state._saved_horizon,
        "include_sentiment": st.session_state._saved_sentiment,
    }


def render_page_controls(
    *,
    show_ticker: bool = True,
    show_dates: bool = False,
    show_model: bool = False,
    show_horizon: bool = False,
    show_sentiment: bool = False,
) -> dict:
    """Render compact inline controls at the top of a page.

    Returns the same params dict as render_sidebar().
    Only shows controls relevant to the current page.
    """
    from src.dashboard.components.theme import COLORS

    _ensure_defaults()

    # Build columns based on what's shown
    specs = []
    if show_ticker:
        specs.append(("ticker", 1.5))
    if show_dates:
        specs.append(("dates", 2.5))
    if show_model:
        specs.append(("model", 1.2))
    if show_horizon:
        specs.append(("horizon", 1.2))
    if show_sentiment:
        specs.append(("sentiment", 0.8))

    if not specs:
        _ensure_defaults()
        params = {
            "ticker": st.session_state._saved_ticker,
            "start_date": st.session_state._saved_start_date,
            "end_date": st.session_state._saved_end_date,
            "model": st.session_state._saved_model,
            "horizon": st.session_state._saved_horizon,
            "include_sentiment": st.session_state._saved_sentiment,
        }
        st.session_state["_sidebar_params"] = params
        return params

    # Toolbar container
    st.markdown(f"""
    <style>
        div[data-testid="stColumns"] > div {{
            padding: 0 4px;
        }}
        .toolbar-label {{
            color: {COLORS['text_muted']};
            font-size: 0.6rem;
            text-transform: uppercase;
            letter-spacing: 0.8px;
            font-weight: 600;
            margin-bottom: 2px;
        }}
    </style>
    """, unsafe_allow_html=True)

    cols = st.columns([s[1] for s in specs])
    col_map = {s[0]: c for s, c in zip(specs, cols)}

    if "ticker" in col_map:
        with col_map["ticker"]:
            st.markdown('<div class="toolbar-label">Symbol</div>', unsafe_allow_html=True)
            ticker = st.text_input(
                "Symbol",
                value=st.session_state._saved_ticker,
                max_chars=20,
                label_visibility="collapsed",
                placeholder="e.g. AAPL",
            ).upper().strip()
            st.session_state._saved_ticker = ticker
    else:
        ticker = st.session_state._saved_ticker

    if "dates" in col_map:
        with col_map["dates"]:
            st.markdown('<div class="toolbar-label">Date Range</div>', unsafe_allow_html=True)
            dc1, dc2 = st.columns(2)
            with dc1:
                start_date = st.date_input("Start", value=st.session_state._saved_start_date, label_visibility="collapsed")
            with dc2:
                end_date = st.date_input("End", value=st.session_state._saved_end_date, label_visibility="collapsed")
            st.session_state._saved_start_date = start_date
            st.session_state._saved_end_date = end_date
    else:
        start_date = st.session_state._saved_start_date
        end_date = st.session_state._saved_end_date

    if "model" in col_map:
        with col_map["model"]:
            st.markdown('<div class="toolbar-label">Model</div>', unsafe_allow_html=True)
            available_models = ["arima", "xgboost", "lstm", "transformer", "prophet", "ensemble"]
            model_index = available_models.index(st.session_state._saved_model)
            selected_model = st.selectbox(
                "Model",
                available_models,
                index=model_index,
                label_visibility="collapsed",
            )
            st.session_state._saved_model = selected_model
    else:
        selected_model = st.session_state._saved_model

    if "horizon" in col_map:
        with col_map["horizon"]:
            st.markdown('<div class="toolbar-label">Horizon</div>', unsafe_allow_html=True)
            horizon = st.selectbox(
                "Horizon",
                options=[1, 3, 5, 7, 10, 14, 21, 30],
                index=[1, 3, 5, 7, 10, 14, 21, 30].index(st.session_state._saved_horizon) if st.session_state._saved_horizon in [1, 3, 5, 7, 10, 14, 21, 30] else 2,
                format_func=lambda x: f"{x}d",
                label_visibility="collapsed",
            )
            st.session_state._saved_horizon = horizon
    else:
        horizon = st.session_state._saved_horizon

    if "sentiment" in col_map:
        with col_map["sentiment"]:
            st.markdown('<div class="toolbar-label">&nbsp;</div>', unsafe_allow_html=True)
            include_sentiment = st.checkbox(
                "Sentiment",
                value=st.session_state._saved_sentiment,
            )
            st.session_state._saved_sentiment = include_sentiment
    else:
        include_sentiment = st.session_state._saved_sentiment

    # Thin divider after toolbar
    st.markdown(f"<div style='border-bottom:1px solid {COLORS['border']}; margin: 8px 0 20px 0;'></div>", unsafe_allow_html=True)

    params = {
        "ticker": ticker,
        "start_date": start_date,
        "end_date": end_date,
        "model": selected_model,
        "horizon": horizon,
        "include_sentiment": include_sentiment,
    }
    st.session_state["_sidebar_params"] = params
    return params


def render_sidebar_settings() -> dict:
    """Legacy: still available if needed but prefer render_page_controls."""
    return render_page_controls(
        show_ticker=True,
        show_dates=True,
        show_model=True,
        show_horizon=True,
        show_sentiment=True,
    )
