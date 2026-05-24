import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

import httpx
import streamlit as st

from src.dashboard.components.sidebar import render_page_controls
from src.dashboard.components.theme import COLORS, section_header

st.markdown(f"<h1 style='color:{COLORS['text_primary']}; margin:0 0 4px 0; font-weight:800; font-size:1.8rem;'>AI Coach</h1>", unsafe_allow_html=True)
params = render_page_controls(show_ticker=True)

API_BASE = "http://localhost:8000/api/v1"

# --- Auth Check ---
if not st.session_state.get("auth_token"):
    st.markdown(f"""
    <div style="background:{COLORS['bg_card']}; border:1px solid {COLORS['border']}; border-radius:12px; padding:32px; text-align:center;">
        <p style="color:{COLORS['text_secondary']}; font-size:1.1rem;">Please log in to use the AI Coach</p>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/0_Login.py", label="Go to Login", icon="\U0001f511")
    st.stop()

headers = {"Authorization": f"Bearer {st.session_state.auth_token}"}

# --- Load saved LLM settings from server ---
if "_coach_settings_loaded" not in st.session_state:
    try:
        r = httpx.get(f"{API_BASE}/user/settings", headers=headers, timeout=10)
        if r.status_code == 200:
            saved = r.json()
            st.session_state["_coach_provider"] = saved.get("llm_provider", "gemini")
            st.session_state["_coach_api_key"] = saved.get("llm_api_key", "")
    except Exception:
        pass
    st.session_state["_coach_settings_loaded"] = True

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

    # Auto-save settings when changed
    col_save, col_status = st.columns([1, 3])
    with col_save:
        if st.button("Save Key", type="primary", use_container_width=True):
            try:
                r = httpx.put(
                    f"{API_BASE}/user/settings",
                    json={"llm_provider": llm_provider, "llm_api_key": llm_api_key},
                    headers=headers,
                    timeout=10,
                )
                if r.status_code == 200:
                    st.success("Settings saved!")
                else:
                    st.error("Failed to save settings")
            except Exception as e:
                st.error(f"Save failed: {e}")
    with col_status:
        if llm_api_key:
            st.markdown(f"<div style='padding-top:8px; color:{COLORS['green']}; font-size:0.8rem;'>Key configured — click Save to remember across sessions</div>", unsafe_allow_html=True)

    if not llm_api_key:
        st.markdown(f"""
        <div style="background:{COLORS['blue_soft']}; border:1px solid {COLORS['blue']}30; border-radius:8px; padding:12px 16px; margin-top:8px;">
            <span style="color:{COLORS['text_secondary']}; font-size:0.85rem;">
                Get a <strong style="color:{COLORS['accent']}">free</strong> Gemini key at
                <a href="https://aistudio.google.com/apikey" target="_blank" style="color:{COLORS['accent']}">Google AI Studio</a>
                or a free Groq key at
                <a href="https://console.groq.com" target="_blank" style="color:{COLORS['accent']}">console.groq.com</a>
            </span>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

# --- Quick Actions ---
st.markdown(section_header("Quick Actions"), unsafe_allow_html=True)
qa_cols = st.columns(4)

with qa_cols[0]:
    if st.button("Analyze Portfolio", use_container_width=True, disabled=not llm_api_key):
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
    if st.button("Explain Signals", use_container_width=True, disabled=not llm_api_key):
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
    if st.button("Rebalancing Tips", use_container_width=True, disabled=not llm_api_key):
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
    if st.button("Clear Chat", use_container_width=True):
        st.session_state["_coach_messages"] = []
        st.rerun()

st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

# --- Chat Interface ---
st.markdown(section_header("Chat"), unsafe_allow_html=True)

# Initialize chat history
if "_coach_messages" not in st.session_state:
    st.session_state["_coach_messages"] = []

# Display chat messages
for msg in st.session_state["_coach_messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input
if prompt := st.chat_input("Ask your AI coach anything...", disabled=not llm_api_key):
    st.session_state["_coach_messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                history = st.session_state["_coach_messages"][-10:]

                r = httpx.post(
                    f"{API_BASE}/coach/ask",
                    json={
                        "question": prompt,
                        "provider": llm_provider,
                        "api_key": llm_api_key,
                        "chat_history": history[:-1],
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

# Empty state
if not st.session_state["_coach_messages"]:
    st.markdown(f"""
    <div style="text-align:center; padding:48px; background:{COLORS['bg_card']}; border:1px solid {COLORS['border']}; border-radius:12px;">
        <div style="font-size:3rem; margin-bottom:16px;">🤖</div>
        <p style="color:{COLORS['text_primary']}; font-size:1.2rem; font-weight:600; margin:0;">Your AI Portfolio Coach is ready!</p>
        <p style="color:{COLORS['text_secondary']}; margin-top:8px;">Try a quick action above or ask a question below</p>
        <div style="margin-top:20px; color:{COLORS['text_muted']}; font-size:0.85rem;">
            <p style="margin:4px 0;">"Is my portfolio too risky?"</p>
            <p style="margin:4px 0;">"Should I buy more {params['ticker']}?"</p>
            <p style="margin:4px 0;">"What stocks should I add for diversification?"</p>
            <p style="margin:4px 0;">"Explain what RSI means for my stocks"</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
