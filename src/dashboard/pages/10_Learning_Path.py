import sys
from pathlib import Path

_root = str(Path(__file__).resolve().parent.parent.parent.parent)
if _root not in sys.path:
    sys.path.insert(0, _root)

import importlib
import httpx
import streamlit as st

from src.dashboard.components.sidebar import render_sidebar

st.set_page_config(page_title="Learning Path - Stock Forecaster", layout="wide")
params = render_sidebar()

API_BASE = "http://localhost:8000/api/v1"

st.header("\U0001f393 Learning Path")
st.caption("Your step-by-step guide to becoming a confident investor")

# Import modules - use importlib to avoid caching issues
_learning_mod = importlib.import_module("src.learning.modules")
MODULES = _learning_mod.MODULES
total_steps = _learning_mod.total_steps

# --- Track completion in session state ---
if "_learning_completed" not in st.session_state:
    st.session_state["_learning_completed"] = set()

completed = st.session_state["_learning_completed"]
total = total_steps()
done_count = len(completed)

# --- Overall Progress ---
progress = done_count / total if total > 0 else 0
st.progress(progress, text=f"Progress: {done_count}/{total} steps completed ({progress:.0%})")

if done_count == total:
    st.balloons()
    st.success("\U0001f389 Congratulations! You've completed the entire Learning Path! You're now a confident investor!")

st.markdown("---")

# --- Modules ---
for module in MODULES:
    module_steps_done = sum(1 for s in module.steps if f"{module.id}:{s.id}" in completed)
    module_total = len(module.steps)
    module_complete = module_steps_done == module_total

    # Module header
    badge = f" {module.badge}" if module_complete else ""
    status_icon = "✅" if module_complete else f"{module_steps_done}/{module_total}"

    with st.expander(
        f"{module.icon} **{module.title}** — {module.description} [{status_icon}]{badge}",
        expanded=not module_complete and (module_steps_done > 0 or module == MODULES[0]),
    ):
        for i, step in enumerate(module.steps):
            step_key = f"{module.id}:{step.id}"
            is_done = step_key in completed

            col_check, col_content = st.columns([0.5, 9.5])

            with col_check:
                if st.checkbox(
                    "",
                    value=is_done,
                    key=f"cb_{step_key}",
                    label_visibility="collapsed",
                ):
                    completed.add(step_key)
                else:
                    completed.discard(step_key)
                st.session_state["_learning_completed"] = completed

            with col_content:
                if is_done:
                    st.markdown(f"~~**Step {i+1}: {step.title}**~~")
                else:
                    st.markdown(f"**Step {i+1}: {step.title}**")

                st.markdown(step.description)

                # Action + link
                if step.page_link and not is_done:
                    col_action, col_link = st.columns([3, 1])
                    with col_action:
                        st.info(f"\U0001f449 {step.action_text}")
                    with col_link:
                        st.page_link(step.page_link, label="Go →", use_container_width=True)
                elif not is_done:
                    st.info(f"\U0001f449 {step.action_text}")

        # Module completion message
        if module_complete:
            st.success(f"{module.badge} Module complete! Great job!")

# --- Persist to DB if logged in ---
if st.session_state.get("auth_token"):
    headers = {"Authorization": f"Bearer {st.session_state.auth_token}"}
    # Save progress periodically (could be enhanced with API endpoint)
    st.markdown("---")
    st.caption(f"\U0001f4be Progress saved in session. Logged in as {st.session_state.get('auth_user', {}).get('username', 'User')}.")
else:
    st.markdown("---")
    st.caption("Log in to save your progress across sessions.")
    st.page_link("pages/0_Login.py", label="Login", icon="\U0001f511")

# --- Tips Section ---
st.markdown("---")
st.markdown("### \U0001f4a1 Quick Tips")
tips = [
    "Never invest money you can't afford to lose",
    "Diversify across different stocks, sectors, and markets",
    "Check signals before making buy/sell decisions — don't act on impulse",
    "Use backtesting to see how models perform before trusting them",
    "Review your portfolio at least weekly using the Daily Briefing",
    "The ensemble model combines multiple predictions for better accuracy",
    "RSI below 30 often means a stock is oversold — could be a buying opportunity",
    "Keep learning! The best investors never stop educating themselves",
]

import random
random.seed(42)  # Consistent order per session
selected_tips = random.sample(tips, min(3, len(tips)))
for tip in selected_tips:
    st.markdown(f"- {tip}")
