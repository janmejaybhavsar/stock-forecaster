import sys
from pathlib import Path

_root = str(Path(__file__).resolve().parent.parent.parent.parent)
if _root not in sys.path:
    sys.path.insert(0, _root)

import httpx
import streamlit as st

from src.dashboard.components.sidebar import render_page_controls
from src.dashboard.components.theme import COLORS, section_header

render_page_controls()

API_BASE = "http://localhost:8000/api/v1"


def _login(email: str, password: str) -> tuple[bool, str]:
    try:
        r = httpx.post(f"{API_BASE}/auth/login", json={"email": email, "password": password}, timeout=10)
        if r.status_code == 200:
            st.session_state.auth_token = r.json()["access_token"]
            me = httpx.get(f"{API_BASE}/auth/me", headers={"Authorization": f"Bearer {st.session_state.auth_token}"}, timeout=10)
            if me.status_code == 200:
                st.session_state.auth_user = me.json()
            return True, "Login successful!"
        return False, r.json().get("detail", "Login failed")
    except Exception as e:
        return False, str(e)


def _register(email: str, username: str, password: str) -> tuple[bool, str]:
    try:
        r = httpx.post(f"{API_BASE}/auth/register", json={
            "email": email, "username": username, "password": password
        }, timeout=10)
        if r.status_code == 201:
            return True, "Account created! Please log in."
        return False, r.json().get("detail", "Registration failed")
    except Exception as e:
        return False, str(e)


if st.session_state.get("auth_token"):
    user = st.session_state.get("auth_user", {})

    st.markdown(f"""
    <div style="text-align:center; padding:40px 0;">
        <div style="
            width:80px; height:80px; border-radius:50%;
            background:linear-gradient(135deg, {COLORS['accent']}, #00b894);
            display:inline-flex; align-items:center; justify-content:center;
            font-size:2rem; font-weight:800; color:#0a0e17;
            margin-bottom:16px;
        ">{user.get('username', 'U')[0].upper()}</div>
        <h2 style="color:{COLORS['text_primary']}; margin:0;">Welcome back, {user.get('username', 'User')}!</h2>
        <p style="color:{COLORS['text_muted']}; margin-top:4px;">You are logged in and ready to go</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(section_header("Quick Links"), unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.page_link("pages/6_Portfolio.py", label="My Portfolio", icon="\U0001f4bc")
    with col2:
        st.page_link("pages/2_Forecast.py", label="Run Forecast", icon="\U0001f4c8")
    with col3:
        st.page_link("pages/8_Daily_Briefing.py", label="Daily Briefing", icon="\U0001f4cb")

    st.markdown(f"<p style='color:{COLORS['text_muted']}; font-size:0.85rem; text-align:center; margin-top:32px;'>Use the Logout button in the sidebar to sign out</p>", unsafe_allow_html=True)
else:
    st.markdown(f"""
    <div style="text-align:center; padding:24px 0 32px 0;">
        <h1 style="color:{COLORS['text_primary']}; margin:0; font-weight:800;">Account</h1>
        <p style="color:{COLORS['text_muted']}; margin-top:4px;">Sign in or create an account to unlock portfolio features</p>
    </div>
    """, unsafe_allow_html=True)

    tab_login, tab_register = st.tabs(["Login", "Register"])

    with tab_login:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login", type="primary", use_container_width=True)

            if submitted:
                if not email or not password:
                    st.error("Please fill in all fields.")
                else:
                    ok, msg = _login(email, password)
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

    with tab_register:
        with st.form("register_form"):
            reg_email = st.text_input("Email", key="reg_email")
            reg_username = st.text_input("Username", key="reg_username")
            reg_password = st.text_input("Password", type="password", key="reg_password")
            reg_confirm = st.text_input("Confirm Password", type="password", key="reg_confirm")
            reg_submitted = st.form_submit_button("Create Account", type="primary", use_container_width=True)

            if reg_submitted:
                if not reg_email or not reg_username or not reg_password:
                    st.error("Please fill in all fields.")
                elif reg_password != reg_confirm:
                    st.error("Passwords do not match.")
                elif len(reg_password) < 6:
                    st.error("Password must be at least 6 characters.")
                else:
                    ok, msg = _register(reg_email, reg_username, reg_password)
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)

    st.markdown(f"""
    <div style="text-align:center; margin-top:32px; padding:20px; background:{COLORS['bg_card']}; border:1px solid {COLORS['border']}; border-radius:12px;">
        <p style="color:{COLORS['text_secondary']}; font-size:0.85rem; margin:0;">
            Unlock portfolio tracking, AI coaching, signals, daily briefings, and more
        </p>
    </div>
    """, unsafe_allow_html=True)
