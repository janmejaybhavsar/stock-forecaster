import sys
from pathlib import Path

_root = str(Path(__file__).resolve().parent.parent.parent.parent)
if _root not in sys.path:
    sys.path.insert(0, _root)

import importlib

import streamlit as st

from src.dashboard.components.sidebar import render_page_controls
from src.dashboard.components.theme import COLORS, section_header

st.markdown(f"<h1 style='color:{COLORS['text_primary']}; margin:0 0 4px 0; font-weight:800; font-size:1.8rem;'>Learning Path</h1>", unsafe_allow_html=True)
render_page_controls()

# Import modules
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

st.markdown(f"""
<div style="background:{COLORS['bg_card']}; border:1px solid {COLORS['border']}; border-radius:12px; padding:20px 24px; margin-bottom:24px;">
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
        <span style="color:{COLORS['text_primary']}; font-weight:700;">Overall Progress</span>
        <span style="color:{COLORS['accent']}; font-weight:700;">{done_count}/{total} steps ({progress:.0%})</span>
    </div>
    <div style="background:{COLORS['border']}; border-radius:6px; height:8px; overflow:hidden;">
        <div style="background:linear-gradient(90deg, {COLORS['accent']}, #00b894); width:{progress*100}%; height:100%; border-radius:6px; transition:width 0.3s;"></div>
    </div>
</div>
""", unsafe_allow_html=True)

if done_count == total:
    st.balloons()
    st.markdown(f"""
    <div style="background:{COLORS['green_soft']}; border:1px solid {COLORS['green']}40; border-radius:12px; padding:24px; text-align:center; margin-bottom:24px;">
        <div style="font-size:2rem; margin-bottom:8px;">🎉</div>
        <p style="color:{COLORS['green']}; font-weight:700; font-size:1.1rem; margin:0;">Congratulations! You've completed the entire Learning Path!</p>
        <p style="color:{COLORS['text_secondary']}; margin-top:4px;">You're now a confident investor</p>
    </div>
    """, unsafe_allow_html=True)

# --- Modules ---
for module in MODULES:
    module_steps_done = sum(1 for s in module.steps if f"{module.id}:{s.id}" in completed)
    module_total = len(module.steps)
    module_complete = module_steps_done == module_total

    badge = f" {module.badge}" if module_complete else ""
    status_text = "Complete" if module_complete else f"{module_steps_done}/{module_total}"

    with st.expander(
        f"{module.icon} **{module.title}** — {module.description} [{status_text}]{badge}",
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
                    st.markdown(f"""
                    <div style="opacity:0.6;">
                        <span style="color:{COLORS['green']}; font-weight:700;">Step {i+1}: {step.title}</span>
                        <span style="color:{COLORS['green']}; margin-left:8px;">✓</span>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"**Step {i+1}: {step.title}**")

                st.markdown(f"<span style='color:{COLORS['text_secondary']}; font-size:0.9rem;'>{step.description}</span>", unsafe_allow_html=True)

                if step.page_link and not is_done:
                    col_action, col_link = st.columns([3, 1])
                    with col_action:
                        st.markdown(f"""
                        <div style="background:{COLORS['accent']}10; border:1px solid {COLORS['accent']}30; border-radius:8px; padding:8px 14px; margin-top:4px;">
                            <span style="color:{COLORS['accent']}; font-size:0.85rem;">{step.action_text}</span>
                        </div>
                        """, unsafe_allow_html=True)
                    with col_link:
                        st.page_link(step.page_link, label="Go →", use_container_width=True)
                elif not is_done:
                    st.markdown(f"""
                    <div style="background:{COLORS['accent']}10; border:1px solid {COLORS['accent']}30; border-radius:8px; padding:8px 14px; margin-top:4px;">
                        <span style="color:{COLORS['accent']}; font-size:0.85rem;">{step.action_text}</span>
                    </div>
                    """, unsafe_allow_html=True)

        if module_complete:
            st.markdown(f"""
            <div style="background:{COLORS['green_soft']}; border-radius:8px; padding:10px 16px; margin-top:8px;">
                <span style="color:{COLORS['green']}; font-weight:600;">{module.badge} Module complete! Great job!</span>
            </div>
            """, unsafe_allow_html=True)

st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

# --- Persist info ---
if st.session_state.get("auth_token"):
    st.markdown(f"<div style='color:{COLORS['text_muted']}; font-size:0.8rem;'>Progress saved in session. Logged in as {st.session_state.get('auth_user', {}).get('username', 'User')}.</div>", unsafe_allow_html=True)
else:
    st.markdown(f"<div style='color:{COLORS['text_muted']}; font-size:0.8rem;'>Log in to save your progress across sessions.</div>", unsafe_allow_html=True)
    st.page_link("pages/0_Login.py", label="Login", icon="\U0001f511")

st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

# --- Tips Section ---
st.markdown(section_header("Quick Tips", "Essential investing wisdom"), unsafe_allow_html=True)

tips = [
    ("Never invest money you can't afford to lose", COLORS["red"]),
    ("Diversify across different stocks, sectors, and markets", COLORS["blue"]),
    ("Check signals before making buy/sell decisions", COLORS["accent"]),
    ("Use backtesting to see how models perform before trusting them", COLORS["yellow"]),
    ("Review your portfolio at least weekly using the Daily Briefing", COLORS["purple"]),
]

for tip, color in tips:
    st.markdown(f"""
    <div style="display:flex; align-items:center; gap:12px; padding:8px 0;">
        <div style="width:6px; height:6px; border-radius:50%; background:{color}; flex-shrink:0;"></div>
        <span style="color:{COLORS['text_secondary']}; font-size:0.9rem;">{tip}</span>
    </div>
    """, unsafe_allow_html=True)
