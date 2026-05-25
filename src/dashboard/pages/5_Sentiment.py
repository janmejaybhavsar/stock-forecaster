import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

import streamlit as st
import plotly.graph_objects as go

from src.dashboard.components.sidebar import render_page_controls
from src.dashboard.components.theme import COLORS, section_header
from src.dashboard.components.ui_helpers import empty_state, error_card

st.markdown(f"<h1 style='color:{COLORS['text_primary']}; margin:0 0 4px 0; font-weight:800; font-size:1.8rem;'>Sentiment</h1>", unsafe_allow_html=True)
params = render_page_controls(show_ticker=True)

if st.button("Analyze Sentiment", type="primary"):
    with st.spinner("Analyzing news sentiment..."):
        try:
            from src.features.sentiment import SentimentAnalyzer

            analyzer = SentimentAnalyzer()
            headlines = analyzer.fetch_headlines(params["ticker"], days=14)

            if headlines:
                st.session_state["sentiment_data"] = headlines
                scored = analyzer.score_headlines(headlines)
                st.session_state["sentiment_scored"] = scored
            else:
                error_card("No Headlines Found", f"No recent news articles found for {params['ticker']}.", "Try a more popular ticker like AAPL or MSFT.")
        except Exception as e:
            error_card("Sentiment Analysis Failed", str(e), "This usually means the FinBERT model is still loading. Try again in a moment.")

st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

if "sentiment_scored" in st.session_state:
    scored = st.session_state["sentiment_scored"]
    import pandas as pd

    df = pd.DataFrame(scored)

    # Summary stats
    if "sentiment" in df.columns:
        counts = df["sentiment"].value_counts()
        pos = counts.get("positive", 0)
        neg = counts.get("negative", 0)
        neu = counts.get("neutral", 0)
        total = len(df)

        col_stats, col_chart = st.columns([2, 3])

        with col_stats:
            st.markdown(section_header("Sentiment Summary"), unsafe_allow_html=True)
            st.markdown(f"""
            <div style="background:{COLORS['bg_card']}; border:1px solid {COLORS['border']}; border-radius:12px; padding:24px;">
                <div style="margin-bottom:16px;">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                        <span style="color:{COLORS['text_secondary']};">Positive</span>
                        <span style="color:{COLORS['green']}; font-weight:700;">{pos} ({pos/total*100:.0f}%)</span>
                    </div>
                    <div style="background:{COLORS['border']}; border-radius:4px; height:6px;">
                        <div style="background:{COLORS['green']}; width:{pos/total*100 if total else 0}%; height:100%; border-radius:4px;"></div>
                    </div>
                </div>
                <div style="margin-bottom:16px;">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                        <span style="color:{COLORS['text_secondary']};">Negative</span>
                        <span style="color:{COLORS['red']}; font-weight:700;">{neg} ({neg/total*100:.0f}%)</span>
                    </div>
                    <div style="background:{COLORS['border']}; border-radius:4px; height:6px;">
                        <div style="background:{COLORS['red']}; width:{neg/total*100 if total else 0}%; height:100%; border-radius:4px;"></div>
                    </div>
                </div>
                <div>
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                        <span style="color:{COLORS['text_secondary']};">Neutral</span>
                        <span style="color:{COLORS['text_muted']}; font-weight:700;">{neu} ({neu/total*100:.0f}%)</span>
                    </div>
                    <div style="background:{COLORS['border']}; border-radius:4px; height:6px;">
                        <div style="background:{COLORS['text_muted']}; width:{neu/total*100 if total else 0}%; height:100%; border-radius:4px;"></div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col_chart:
            st.markdown(section_header("Distribution"), unsafe_allow_html=True)
            fig = go.Figure(data=[go.Pie(
                labels=["Positive", "Negative", "Neutral"],
                values=[pos, neg, neu],
                hole=0.5,
                marker_colors=[COLORS["green"], COLORS["red"], COLORS["text_muted"]],
                textinfo="label+percent",
                textfont=dict(color=COLORS["text_primary"]),
            )])
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                height=300,
                margin=dict(t=20, b=20, l=20, r=20),
                showlegend=False,
                font=dict(color=COLORS["text_secondary"]),
            )
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

    # Headlines list
    st.markdown(section_header("Recent Headlines", f"{len(df)} articles analyzed"), unsafe_allow_html=True)

    for _, row in df.iterrows():
        sentiment = row.get("sentiment", "neutral")
        score = row.get("score", 0)

        if sentiment == "positive":
            border_color = COLORS["green"]
            badge_bg = COLORS["green_soft"]
            badge_text = COLORS["green"]
        elif sentiment == "negative":
            border_color = COLORS["red"]
            badge_bg = COLORS["red_soft"]
            badge_text = COLORS["red"]
        else:
            border_color = COLORS["border"]
            badge_bg = f"{COLORS['text_muted']}20"
            badge_text = COLORS["text_muted"]

        st.markdown(f"""
        <div style="
            display:flex; align-items:center; justify-content:space-between;
            background:{COLORS['bg_card']}; border:1px solid {COLORS['border']};
            border-left:3px solid {border_color}; border-radius:8px;
            padding:12px 16px; margin-bottom:6px;
        ">
            <span style="color:{COLORS['text_primary']}; font-size:0.9rem; flex:1;">{row.get('headline', '')}</span>
            <div style="display:flex; align-items:center; gap:12px; margin-left:16px;">
                <span style="
                    background:{badge_bg}; color:{badge_text};
                    padding:3px 10px; border-radius:12px; font-size:0.7rem;
                    font-weight:700; text-transform:uppercase;
                ">{sentiment}</span>
                <span style="color:{COLORS['text_muted']}; font-size:0.8rem;">{score:.2f}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

else:
    empty_state("📰", "Click 'Analyze Sentiment' to fetch and analyze recent news", "Uses FinBERT to classify news headlines as positive, negative, or neutral")
