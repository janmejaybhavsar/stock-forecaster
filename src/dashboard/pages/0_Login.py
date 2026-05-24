import sys
from pathlib import Path

_root = str(Path(__file__).resolve().parent.parent.parent.parent)
if _root not in sys.path:
    sys.path.insert(0, _root)

import httpx
import streamlit as st

from src.dashboard.components.sidebar import render_sidebar

st.set_page_config(page_title="Login - Stock Forecaster", layout="wide")
render_sidebar()

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
    st.header(f"Welcome, {user.get('username', 'User')}!")
    st.success("You are logged in.")

    st.markdown("### Quick Links")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.page_link("pages/6_Portfolio.py", label="My Portfolio", icon="💼")
    with col2:
        st.page_link("pages/2_Forecast.py", label="Run Forecast", icon="📈")
    with col3:
        st.page_link("pages/1_Overview.py", label="Overview", icon="🏠")

    st.markdown("---")
    if st.button("Logout", type="secondary"):
        st.session_state.pop("auth_token", None)
        st.session_state.pop("auth_user", None)
        st.rerun()
else:
    st.header("Account")

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
