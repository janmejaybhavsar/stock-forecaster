import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

import httpx
import plotly.graph_objects as go
import streamlit as st

from src.dashboard.components.sidebar import render_page_controls
from src.dashboard.components.theme import COLORS, section_header, metric_card
from src.dashboard.components.ui_helpers import error_card, loading_skeleton

st.markdown(f"<h1 style='color:{COLORS['text_primary']}; margin:0 0 4px 0; font-weight:800; font-size:1.8rem;'>Signals</h1>", unsafe_allow_html=True)
params = render_page_controls(show_ticker=True, show_horizon=True)

from src.dashboard.components.auth_helper import API_BASE

# --- Signal for Current Ticker ---
ticker = params["ticker"]
horizon = params["horizon"]

col_settings, col_run = st.columns([3, 1])
with col_settings:
    include_sentiment = st.checkbox(
        "Include Sentiment Analysis",
        value=False,
        help="Adds FinBERT news sentiment — takes longer to compute",
    )
with col_run:
    st.markdown("<br>", unsafe_allow_html=True)
    run_signal = st.button(f"Analyze {ticker}", type="primary", use_container_width=True)

if run_signal:
    loading_skeleton(lines=5, height="1.4rem")
    with st.spinner(f"Analyzing {ticker}... Running models and computing signals"):
        try:
            r = httpx.get(
                f"{API_BASE}/signals/{ticker}",
                params={"horizon": horizon, "include_sentiment": str(include_sentiment).lower()},
                timeout=120,
            )
            r.raise_for_status()
            signal_data = r.json()
            st.session_state["_signal_result"] = signal_data
        except Exception as e:
            error_card("Signal Analysis Failed", str(e), "This may be caused by missing dependencies or API issues. Try again.")
            st.stop()

# Display stored result
if "_signal_result" in st.session_state:
    data = st.session_state["_signal_result"]

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # --- Top Row: Signal Badge + Confidence + Price ---
    col_badge, col_gauge, col_info = st.columns([2.5, 2, 1.5])

    with col_badge:
        label = data["signal_label"]
        color = data["color"]
        score = data["composite_score"]

        st.markdown(f"""
        <div style="
            background: {color}10;
            border: 2px solid {color};
            border-radius: 16px;
            padding: 32px;
            text-align: center;
            box-shadow: 0 0 40px {color}15;
        ">
            <div style="font-size: 2.5rem; font-weight: 800; color: {color}; letter-spacing: 2px;">
                {label}
            </div>
            <div style="font-size: 1rem; color: {COLORS['text_muted']}; margin-top: 8px;">
                Score: <span style="color:{color}; font-weight:600;">{score:+.3f}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_gauge:
        confidence = data["confidence"]
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=confidence,
            title={"text": "CONFIDENCE", "font": {"size": 12, "color": COLORS["text_muted"]}},
            number={"suffix": "%", "font": {"size": 42, "color": COLORS["text_primary"]}},
            gauge={
                "axis": {"range": [0, 100], "tickcolor": COLORS["border"], "tickfont": {"color": COLORS["text_muted"]}},
                "bar": {"color": color, "thickness": 0.8},
                "bgcolor": COLORS["bg_card"],
                "bordercolor": COLORS["border"],
                "steps": [
                    {"range": [0, 33], "color": "rgba(255,71,87,0.08)"},
                    {"range": [33, 66], "color": "rgba(255,167,38,0.08)"},
                    {"range": [66, 100], "color": "rgba(0,212,170,0.08)"},
                ],
            },
        ))
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=200,
            margin=dict(t=50, b=0, l=30, r=30),
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_info:
        st.markdown(metric_card("Price", f"${data['current_price']:,.2f}"), unsafe_allow_html=True)
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        st.markdown(metric_card("Horizon", f"{horizon} days"), unsafe_allow_html=True)

    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

    # --- Reasoning ---
    st.markdown(section_header("Signal Reasoning", "Key factors driving this signal"), unsafe_allow_html=True)

    for reason in data.get("reasoning", []):
        if any(word in reason.lower() for word in ["bullish", "positive", "upside", "oversold", "bounce", "golden"]):
            icon_color = COLORS["green"]
            icon = "↑"
        elif any(word in reason.lower() for word in ["bearish", "negative", "downside", "overbought", "death", "pullback", "extended"]):
            icon_color = COLORS["red"]
            icon = "↓"
        else:
            icon_color = COLORS["yellow"]
            icon = "•"

        st.markdown(f"""
        <div style="display:flex; align-items:center; gap:12px; padding:10px 16px; background:{COLORS['bg_card']}; border-radius:8px; margin-bottom:6px; border-left:3px solid {icon_color};">
            <span style="color:{icon_color}; font-weight:800; font-size:1.1rem;">{icon}</span>
            <span style="color:{COLORS['text_primary']}; font-size:0.9rem;">{reason}</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

    # --- Breakdown Cards ---
    st.markdown(section_header("Signal Breakdown", "Individual component scores"), unsafe_allow_html=True)
    col_tech, col_model, col_sent = st.columns(3)

    def _breakdown_card(title: str, signal_val: float, details: dict, reasonings: list):
        sig_color = COLORS["green"] if signal_val > 0.1 else COLORS["red"] if signal_val < -0.1 else COLORS["yellow"]
        card_html = f"""
        <div style="
            background: {COLORS['bg_card']};
            border: 1px solid {COLORS['border']};
            border-top: 3px solid {sig_color};
            border-radius: 12px;
            padding: 24px;
            height: 100%;
        ">
            <div style="color:{COLORS['text_muted']}; font-size:0.75rem; text-transform:uppercase; letter-spacing:0.5px;">{title}</div>
            <div style="color:{sig_color}; font-size:2rem; font-weight:800; margin:8px 0;">{signal_val:+.2f}</div>
        """
        for key, val in list(details.items())[:4]:
            if key not in ("per_model", "top_headlines"):
                card_html += f'<div style="color:{COLORS["text_secondary"]}; font-size:0.8rem; margin:2px 0;">{key}: <span style="color:{COLORS["text_primary"]}">{val}</span></div>'
        if reasonings:
            card_html += f'''
            <div style="margin-top:12px; color:{COLORS["text_muted"]}; font-size:0.72rem; text-transform:uppercase; letter-spacing:0.4px;">Reasoning</div>
            '''
            for reason in reasonings[:3]:
                card_html += f'<div style="color:{COLORS["text_secondary"]}; font-size:0.8rem; margin:4px 0 0 0;">• {reason}</div>'
        card_html += "</div>"
        return card_html

    with col_tech:
        tech = data.get("technical", {})
        st.markdown(_breakdown_card(
            "Technical Analysis",
            tech.get("signal", 0),
            tech.get("details", {}),
            tech.get("reasoning", []),
        ), unsafe_allow_html=True)

    with col_model:
        consensus = data.get("model_consensus", {})
        st.markdown(_breakdown_card(
            "Model Consensus",
            consensus.get("signal", 0),
            consensus.get("details", {}),
            consensus.get("reasoning", []),
        ), unsafe_allow_html=True)

    with col_sent:
        sent = data.get("sentiment", {})
        st.markdown(_breakdown_card(
            "News Sentiment",
            sent.get("signal", 0),
            sent.get("details", {}),
            sent.get("reasoning", []),
        ), unsafe_allow_html=True)

st.markdown("<div style='height:32px'></div>", unsafe_allow_html=True)

# --- Portfolio Signals Section ---
st.markdown(section_header("Portfolio Signals", "Scan all your holdings at once"), unsafe_allow_html=True)

if st.session_state.get("auth_token"):
    headers = {"Authorization": f"Bearer {st.session_state.auth_token}"}

    if st.button("Scan All Holdings", use_container_width=True):
        with st.spinner("Scanning portfolio... This may take a minute"):
            try:
                r = httpx.get(
                    f"{API_BASE}/signals/portfolio/all",
                    params={"horizon": horizon},
                    headers=headers,
                    timeout=300,
                )
                r.raise_for_status()
                st.session_state["_portfolio_signals"] = r.json()
            except Exception as e:
                error_card("Portfolio Scan Failed", str(e), "This scans all holdings — ensure you have a stable connection.")

    if "_portfolio_signals" in st.session_state:
        port_data = st.session_state["_portfolio_signals"]
        signals_list = port_data.get("signals", [])

        if signals_list:
            for sig in signals_list:
                color = sig["color"]
                st.markdown(f"""
                <div style="
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    background: {COLORS['bg_card']};
                    border: 1px solid {COLORS['border']};
                    border-left: 4px solid {color};
                    border-radius: 10px;
                    padding: 16px 24px;
                    margin-bottom: 8px;
                ">
                    <div>
                        <span style="color:{COLORS['text_primary']}; font-weight:700; font-size:1.1rem;">{sig['ticker']}</span>
                        <span style="color:{COLORS['text_muted']}; margin-left:12px;">${sig['current_price']:,.2f}</span>
                    </div>
                    <div style="display:flex; align-items:center; gap:24px;">
                        <span style="color:{color}; font-weight:800; font-size:1rem;">{sig['signal_label']}</span>
                        <span style="color:{COLORS['text_secondary']}; font-size:0.85rem;">{sig['confidence']:.0f}%</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No holdings in portfolio. Add some on the Portfolio page!")
else:
    st.markdown(f"""
    <div style="background:{COLORS['bg_card']}; border:1px solid {COLORS['border']}; border-radius:12px; padding:24px; text-align:center;">
        <p style="color:{COLORS['text_secondary']};">Log in to scan signals for your entire portfolio</p>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/0_Login.py", label="Go to Login", icon="\U0001f511")
