import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import base64

import streamlit as st

st.set_page_config(
    page_title="StockForecaster",
    page_icon=":material/trending_up:",
    layout="wide",
    initial_sidebar_state="expanded",
)

from src.dashboard.components.theme import inject_custom_css, COLORS
from src.dashboard.components.fintech_ui import inject_keyboard_shortcuts, inject_pnl_animation_css

# --- Inject global CSS + keyboard shortcuts ---
inject_custom_css()
inject_pnl_animation_css()
inject_keyboard_shortcuts()

# --- App Logo (renders above navigation in sidebar) ---
_logo_svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 220 44">
  <defs>
    <linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#00d4aa"/>
      <stop offset="100%" stop-color="#00b894"/>
    </linearGradient>
  </defs>
  <rect x="0" y="4" width="36" height="36" rx="9" fill="url(#g)"/>
  <text x="10" y="29" font-family="Arial,sans-serif" font-weight="800" font-size="16" fill="#0a0e17">SF</text>
  <text x="44" y="20" font-family="Arial,sans-serif" font-weight="800" font-size="15" fill="{COLORS['text_primary']}">StockForecaster</text>
  <text x="44" y="36" font-family="Arial,sans-serif" font-weight="600" font-size="8" fill="{COLORS['text_muted']}" letter-spacing="0.8">PORTFOLIO GROWTH COACH</text>
</svg>'''

_icon_svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 44">
  <defs>
    <linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#00d4aa"/>
      <stop offset="100%" stop-color="#00b894"/>
    </linearGradient>
  </defs>
  <rect x="2" y="4" width="36" height="36" rx="9" fill="url(#g)"/>
  <text x="12" y="29" font-family="Arial,sans-serif" font-weight="800" font-size="16" fill="#0a0e17">SF</text>
</svg>'''

_logo_b64 = base64.b64encode(_logo_svg.encode()).decode()
_icon_b64 = base64.b64encode(_icon_svg.encode()).decode()
st.logo(
    f"data:image/svg+xml;base64,{_logo_b64}",
    icon_image=f"data:image/svg+xml;base64,{_icon_b64}",
)

# --- Navigation ---
analysis_pages = [
    st.Page("pages/1_Overview.py", title="Overview", icon=":material/monitoring:", default=True),
    st.Page("pages/2_Forecast.py", title="Forecast", icon=":material/trending_up:"),
    st.Page("pages/3_Model_Comparison.py", title="Compare Models", icon=":material/compare_arrows:"),
    st.Page("pages/4_Backtesting.py", title="Backtesting", icon=":material/history:"),
    st.Page("pages/5_Sentiment.py", title="Sentiment", icon=":material/mood:"),
]

portfolio_pages = [
    st.Page("pages/6_Portfolio.py", title="Portfolio", icon=":material/account_balance_wallet:"),
    st.Page("pages/7_Signals.py", title="Signals", icon=":material/notifications_active:"),
    st.Page("pages/8_Daily_Briefing.py", title="Daily Briefing", icon=":material/newspaper:"),
]

coach_pages = [
    st.Page("pages/9_AI_Coach.py", title="AI Coach", icon=":material/smart_toy:"),
    st.Page("pages/10_Learning_Path.py", title="Learning Path", icon=":material/school:"),
]

account_pages = [
    st.Page("pages/0_Login.py", title="Account", icon=":material/person:"),
]

pg = st.navigation({
    "Analysis": analysis_pages,
    "Portfolio": portfolio_pages,
    "Coach": coach_pages,
    "Account": account_pages,
})

# --- Sidebar: User Info (after nav) ---
if st.session_state.get("auth_token"):
    user = st.session_state.get("auth_user", {})
    initial = user.get("username", "U")[0].upper()
    username = user.get("username", "User")
    st.sidebar.markdown(f"""
    <div style="
        display:flex; align-items:center; gap:10px;
        padding:8px 10px; background:{COLORS['bg_card']};
        border:1px solid {COLORS['border']}; border-radius:8px;
        margin: 4px 0 4px 0;
    ">
        <div style="
            width:30px; height:30px; border-radius:50%;
            background:linear-gradient(135deg, {COLORS['accent']}, #00b894);
            display:flex; align-items:center; justify-content:center;
            font-weight:700; color:#0a0e17; font-size:0.8rem; flex-shrink:0;
        ">{initial}</div>
        <div style="flex:1; min-width:0;">
            <div style="color:{COLORS['text_primary']}; font-weight:600; font-size:0.8rem; line-height:1.2;">{username}</div>
            <div style="color:{COLORS['accent']}; font-size:0.6rem; font-weight:500;">Active</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    if st.sidebar.button("Logout", key="_app_logout_btn", use_container_width=True):
        st.session_state.pop("auth_token", None)
        st.session_state.pop("auth_user", None)
        st.rerun()

# --- Run selected page ---
pg.run()
