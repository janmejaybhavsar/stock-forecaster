import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from src.dashboard.components.sidebar import render_sidebar

st.set_page_config(page_title="Sentiment - Stock Forecaster", layout="wide")
params = render_sidebar()

st.header(f"{params['ticker']} Sentiment Analysis")

API_BASE = "http://localhost:8000/api/v1"

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
                st.warning("No headlines found.")
        except Exception as e:
            st.error(f"Sentiment analysis not yet available: {e}")
            st.info("Sentiment features will be available after Phase 4 implementation.")

if "sentiment_scored" in st.session_state:
    scored = st.session_state["sentiment_scored"]
    import pandas as pd

    df = pd.DataFrame(scored)

    st.subheader("Recent Headlines")
    for _, row in df.iterrows():
        sentiment = row.get("sentiment", "neutral")
        color = {"positive": "green", "negative": "red"}.get(sentiment, "gray")
        score = row.get("score", 0)
        st.markdown(
            f":{color}[{sentiment.upper()}] ({score:.2f}) — {row.get('headline', '')}"
        )

    st.subheader("Sentiment Distribution")
    if "sentiment" in df.columns:
        counts = df["sentiment"].value_counts()
        fig = go.Figure(data=[go.Pie(
            labels=counts.index.tolist(),
            values=counts.values.tolist(),
            marker_colors=["#66bb6a", "#ef5350", "#bdbdbd"],
        )])
        fig.update_layout(template="plotly_dark", height=350)
        st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Click 'Analyze Sentiment' to fetch and analyze recent news headlines.")
    st.markdown("""
    This page uses **FinBERT** to analyze sentiment from financial news headlines.
    - Headlines are sourced from Google News RSS
    - Sentiment is classified as Positive, Negative, or Neutral
    - Scores indicate confidence level
    """)
