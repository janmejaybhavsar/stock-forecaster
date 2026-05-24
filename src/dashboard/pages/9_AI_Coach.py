import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

import httpx
import streamlit as st

from src.dashboard.components.sidebar import render_sidebar

st.set_page_config(page_title="AI Coach - Stock Forecaster", layout="wide")
params = render_sidebar()

API_BASE = "http://localhost:8000/api/v1"

st.header("\U0001f916 AI Portfolio Coach")
st.caption("Talk to your portfolio — get personalized analysis, explanations, and advice")

# --- Auth Check ---
if not st.session_state.get("auth_token"):
    st.warning("Please log in to use the AI Coach.")
    st.page_link("pages/0_Login.py", label="Go to Login", icon="\U0001f511")
    st.stop()

headers = {"Authorization": f"Bearer {st.session_state.auth_token}"}

# --- LLM Provider Settings ---
# Initialize defaults
if "_coach_provider" not in st.session_state:
    st.session_state["_coach_provider"] = "gemini"
if "_coach_api_key" not in st.session_state:
    st.session_state["_coach_api_key"] = ""

with st.expander("LLM Settings", expanded=not st.session_state.get("_coach_api_key")):
    provider_options = ["gemini", "groq", "openai", "anthropic"]
    col_prov, col_key = st.columns([1, 3])
    with col_prov:
        llm_provider = st.selectbox(
            "Provider",
            provider_options,
            key="_coach_provider",
            help="Gemini: free (need API key from Google AI Studio). Groq: free tier. OpenAI/Anthropic: paid.",
        )
    with col_key:
        llm_api_key = st.text_input(
            "API Key",
            type="password",
            key="_coach_api_key",
            placeholder="Enter your API key",
            help="Get free Gemini key at https://aistudio.google.com/apikey. Get free Groq key at https://console.groq.com",
        )

    if not llm_api_key:
        st.info(
            "You need an API key to use the AI Coach. "
            "Get a **free** Gemini API key at [Google AI Studio](https://aistudio.google.com/apikey) "
            "or a **free** Groq key at [console.groq.com](https://console.groq.com)"
        )

# --- Quick Actions ---
st.markdown("### Quick Actions")
qa_cols = st.columns(4)

with qa_cols[0]:
    if st.button("\U0001f4ca Analyze Portfolio", use_container_width=True, disabled=not llm_api_key):
        with st.spinner("Analyzing your portfolio..."):
            try:
                r = httpx.post(
                    f"{API_BASE}/coach/analyze",
                    json={"provider": llm_provider, "api_key": llm_api_key},
                    headers=headers,
                    timeout=120,
                )
                if r.status_code != 200:
                    detail = r.json().get("detail", r.text) if "json" in r.headers.get("content-type", "") else r.text
                    st.error(f"Analysis failed: {detail}")
                else:
                    data = r.json()
                    st.session_state.setdefault("_coach_messages", [])
                    st.session_state["_coach_messages"].append(
                        {"role": "user", "content": "Analyze my portfolio"}
                    )
                    st.session_state["_coach_messages"].append(
                        {"role": "assistant", "content": data["response"]}
                    )
                    st.rerun()
            except Exception as e:
                st.error(f"Analysis failed: {e}")

with qa_cols[1]:
    if st.button("\U0001f6a6 Explain Signals", use_container_width=True, disabled=not llm_api_key):
        ticker = params["ticker"]
        with st.spinner(f"Explaining {ticker} signal..."):
            try:
                r = httpx.post(
                    f"{API_BASE}/coach/explain",
                    json={"ticker": ticker, "provider": llm_provider, "api_key": llm_api_key},
                    headers=headers,
                    timeout=120,
                )
                r.raise_for_status()
                data = r.json()
                st.session_state.setdefault("_coach_messages", [])
                st.session_state["_coach_messages"].append(
                    {"role": "user", "content": f"Why is {ticker} a {data['signal']['signal_label']}?"}
                )
                st.session_state["_coach_messages"].append(
                    {"role": "assistant", "content": data["response"]}
                )
                st.rerun()
            except Exception as e:
                st.error(f"Explanation failed: {e}")

with qa_cols[2]:
    if st.button("⚖️ Rebalancing Tips", use_container_width=True, disabled=not llm_api_key):
        with st.spinner("Getting rebalancing suggestions..."):
            try:
                r = httpx.post(
                    f"{API_BASE}/coach/ask",
                    json={
                        "question": "How should I rebalance my portfolio for better diversification and risk management?",
                        "provider": llm_provider,
                        "api_key": llm_api_key,
                    },
                    headers=headers,
                    timeout=120,
                )
                r.raise_for_status()
                data = r.json()
                st.session_state.setdefault("_coach_messages", [])
                st.session_state["_coach_messages"].append(
                    {"role": "user", "content": "How should I rebalance my portfolio?"}
                )
                st.session_state["_coach_messages"].append(
                    {"role": "assistant", "content": data["response"]}
                )
                st.rerun()
            except Exception as e:
                st.error(f"Failed: {e}")

with qa_cols[3]:
    if st.button("\U0001f5d1️ Clear Chat", use_container_width=True):
        st.session_state["_coach_messages"] = []
        st.rerun()

st.markdown("---")

# --- Chat Interface ---
st.markdown("### Chat")

# Initialize chat history
if "_coach_messages" not in st.session_state:
    st.session_state["_coach_messages"] = []

# Display chat messages
for msg in st.session_state["_coach_messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input
if prompt := st.chat_input("Ask your AI coach anything...", disabled=not llm_api_key):
    # Add user message
    st.session_state["_coach_messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Get AI response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                # Build chat history (last 10 messages for context)
                history = st.session_state["_coach_messages"][-10:]

                r = httpx.post(
                    f"{API_BASE}/coach/ask",
                    json={
                        "question": prompt,
                        "provider": llm_provider,
                        "api_key": llm_api_key,
                        "chat_history": history[:-1],  # Exclude last user msg (it's the question)
                    },
                    headers=headers,
                    timeout=120,
                )
                if r.status_code != 200:
                    detail = r.json().get("detail", r.text) if r.headers.get("content-type", "").startswith("application/json") else r.text
                    raise Exception(f"API error ({r.status_code}): {detail}")
                data = r.json()
                response = data["response"]
                st.markdown(response)
                st.session_state["_coach_messages"].append(
                    {"role": "assistant", "content": response}
                )
            except Exception as e:
                error_msg = f"Sorry, I encountered an error: {e}"
                st.error(error_msg)
                st.session_state["_coach_messages"].append(
                    {"role": "assistant", "content": error_msg}
                )

# Footer
if not st.session_state["_coach_messages"]:
    st.markdown(
        """
        <div style="text-align: center; color: #666; padding: 40px;">
            <p style="font-size: 48px;">🤖</p>
            <p style="font-size: 18px;">Your AI Portfolio Coach is ready!</p>
            <p>Try a quick action above or ask a question below.</p>
            <p style="font-size: 14px; color: #888;">
                Example questions:<br>
                "Is my portfolio too risky?"<br>
                "Should I buy more AAPL?"<br>
                "What stocks should I add for diversification?"<br>
                "Explain what RSI means for my stocks"
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
