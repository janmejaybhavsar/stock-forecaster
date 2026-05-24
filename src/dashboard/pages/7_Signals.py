import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

import httpx
import plotly.graph_objects as go
import streamlit as st

from src.dashboard.components.sidebar import render_sidebar

st.set_page_config(page_title="Signals - Stock Forecaster", layout="wide")
params = render_sidebar()

API_BASE = "http://localhost:8000/api/v1"

st.header("Buy / Sell / Hold Signals")
st.caption("Composite analysis combining technical indicators, ML model consensus, and news sentiment")

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
    run_signal = st.button("Analyze Signal", type="primary", use_container_width=True)

if run_signal:
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
            st.error(f"Signal analysis failed: {e}")
            st.stop()

# Display stored result
if "_signal_result" in st.session_state:
    data = st.session_state["_signal_result"]

    st.markdown("---")

    # --- Big Signal Badge ---
    col_badge, col_gauge, col_price = st.columns([2, 2, 1])

    with col_badge:
        label = data["signal_label"]
        color = data["color"]
        score = data["composite_score"]

        st.markdown(
            f"""
            <div style="
                background: {color}20;
                border: 3px solid {color};
                border-radius: 16px;
                padding: 30px;
                text-align: center;
            ">
                <div style="font-size: 42px; font-weight: bold; color: {color};">
                    {label}
                </div>
                <div style="font-size: 18px; color: #aaa; margin-top: 8px;">
                    Composite Score: {score:+.2f}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_gauge:
        confidence = data["confidence"]
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=confidence,
            title={"text": "Confidence", "font": {"size": 18, "color": "#ccc"}},
            number={"suffix": "%", "font": {"size": 36, "color": "#fff"}},
            gauge={
                "axis": {"range": [0, 100], "tickcolor": "#666"},
                "bar": {"color": color},
                "bgcolor": "#1a1a2e",
                "steps": [
                    {"range": [0, 33], "color": "#2d1b1b"},
                    {"range": [33, 66], "color": "#2d2d1b"},
                    {"range": [66, 100], "color": "#1b2d1b"},
                ],
            },
        ))
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=220,
            margin=dict(t=60, b=10, l=30, r=30),
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_price:
        st.metric("Current Price", f"${data['current_price']:,.2f}")
        st.metric("Ticker", data["ticker"])

    st.markdown("---")

    # --- Reasoning Bullets ---
    st.markdown("### Why This Signal?")
    for reason in data.get("reasoning", []):
        # Color-code based on content
        if any(word in reason.lower() for word in ["bullish", "positive", "upside", "oversold", "bounce", "golden"]):
            icon = "\U0001f7e2"
        elif any(word in reason.lower() for word in ["bearish", "negative", "downside", "overbought", "death", "pullback", "extended"]):
            icon = "\U0001f534"
        else:
            icon = "\U0001f7e1"
        st.markdown(f"- {icon} {reason}")

    st.markdown("---")

    # --- Breakdown Cards ---
    st.markdown("### Signal Breakdown")
    col_tech, col_model, col_sent = st.columns(3)

    with col_tech:
        tech = data.get("technical", {})
        tech_sig = tech.get("signal", 0)
        tech_color = "#00C851" if tech_sig > 0.1 else "#FF5252" if tech_sig < -0.1 else "#FFB300"
        st.markdown(
            f"""
            <div style="border: 1px solid {tech_color}; border-radius: 12px; padding: 20px;">
                <h4 style="color: {tech_color}; margin: 0;">Technical Analysis</h4>
                <div style="font-size: 28px; font-weight: bold; color: {tech_color}; margin: 10px 0;">
                    {tech_sig:+.2f}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        details = tech.get("details", {})
        if "rsi_14" in details:
            st.caption(f"RSI(14): {details['rsi_14']}")
        if "macd" in details:
            st.caption(f"MACD: {details['macd']:.4f}")
        if "bb_position" in details:
            st.caption(f"BB Position: {details['bb_position']:.0%}")
        if "sma_50" in details:
            st.caption(f"SMA 50/200: {details['sma_50']:.2f} / {details.get('sma_200', 0):.2f}")

        for r in tech.get("reasoning", []):
            st.markdown(f"<small style='color:#888;'>- {r}</small>", unsafe_allow_html=True)

    with col_model:
        consensus = data.get("model_consensus", {})
        con_sig = consensus.get("signal", 0)
        con_color = "#00C851" if con_sig > 0.1 else "#FF5252" if con_sig < -0.1 else "#FFB300"
        st.markdown(
            f"""
            <div style="border: 1px solid {con_color}; border-radius: 12px; padding: 20px;">
                <h4 style="color: {con_color}; margin: 0;">Model Consensus</h4>
                <div style="font-size: 28px; font-weight: bold; color: {con_color}; margin: 10px 0;">
                    {con_sig:+.2f}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        con_details = consensus.get("details", {})
        if "total_models" in con_details:
            st.caption(f"Models: {con_details.get('bullish_models', 0)} bullish / {con_details.get('bearish_models', 0)} bearish / {con_details.get('neutral_models', 0)} neutral")
        if "avg_predicted_return_pct" in con_details:
            st.caption(f"Avg predicted return: {con_details['avg_predicted_return_pct']:+.2f}%")

        per_model = con_details.get("per_model", {})
        for model_name, verdict in per_model.items():
            st.markdown(f"<small style='color:#888;'>- {model_name}: {verdict}</small>", unsafe_allow_html=True)

    with col_sent:
        sent = data.get("sentiment", {})
        sent_sig = sent.get("signal", 0)
        sent_color = "#00C851" if sent_sig > 0.1 else "#FF5252" if sent_sig < -0.1 else "#FFB300"
        st.markdown(
            f"""
            <div style="border: 1px solid {sent_color}; border-radius: 12px; padding: 20px;">
                <h4 style="color: {sent_color}; margin: 0;">News Sentiment</h4>
                <div style="font-size: 28px; font-weight: bold; color: {sent_color}; margin: 10px 0;">
                    {sent_sig:+.2f}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        sent_details = sent.get("details", {})
        if "total_headlines" in sent_details:
            st.caption(f"Headlines: {sent_details.get('positive_count', 0)} pos / {sent_details.get('negative_count', 0)} neg / {sent_details.get('neutral_count', 0)} neutral")

        top_headlines = sent_details.get("top_headlines", [])
        for h in top_headlines[:3]:
            emoji = {"positive": "+", "negative": "-", "neutral": "~"}.get(h["sentiment"], "~")
            st.markdown(f"<small style='color:#888;'>[{emoji}] {h['headline'][:60]}...</small>", unsafe_allow_html=True)

    # --- Weights Used ---
    st.markdown("---")
    weights = data.get("weights_used", {})
    if weights:
        w_cols = st.columns(3)
        with w_cols[0]:
            st.caption(f"Technical weight: {weights.get('technical', 0):.0%}")
        with w_cols[1]:
            st.caption(f"Model weight: {weights.get('consensus', 0):.0%}")
        with w_cols[2]:
            st.caption(f"Sentiment weight: {weights.get('sentiment', 0):.0%}")

# --- Portfolio Signals Section ---
st.markdown("---")
st.markdown("### Portfolio Signals")

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
                st.error(f"Portfolio scan failed: {e}")

    if "_portfolio_signals" in st.session_state:
        port_data = st.session_state["_portfolio_signals"]
        signals_list = port_data.get("signals", [])

        if signals_list:
            for sig in signals_list:
                color = sig["color"]
                with st.container(border=True):
                    c1, c2, c3, c4 = st.columns([2, 1.5, 1.5, 3])
                    with c1:
                        st.markdown(f"**{sig['ticker']}**")
                        st.caption(f"${sig['current_price']:,.2f}")
                    with c2:
                        st.markdown(
                            f"<span style='color:{color}; font-weight:bold; font-size:18px;'>{sig['signal_label']}</span>",
                            unsafe_allow_html=True,
                        )
                    with c3:
                        st.metric("Confidence", f"{sig['confidence']:.0f}%")
                    with c4:
                        if sig.get("reasoning"):
                            st.caption(sig["reasoning"][0])
        else:
            st.info("No holdings in portfolio. Add some on the Portfolio page!")
else:
    st.info("Log in to scan signals for your entire portfolio.")
    st.page_link("pages/0_Login.py", label="Go to Login", icon="🔑")
