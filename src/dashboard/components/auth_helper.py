import os

import httpx
import streamlit as st

API_BASE = os.environ.get("API_BASE_URL", "http://localhost:8000").rstrip("/") + "/api/v1"


def get_auth_headers() -> dict:
    token = st.session_state.get("auth_token")
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


def is_authenticated() -> bool:
    return bool(st.session_state.get("auth_token"))


def get_current_user() -> dict | None:
    headers = get_auth_headers()
    if not headers:
        return None
    try:
        r = httpx.get(f"{API_BASE}/auth/me", headers=headers, timeout=10)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None


def login(email: str, password: str) -> tuple[bool, str]:
    try:
        r = httpx.post(f"{API_BASE}/auth/login", json={"email": email, "password": password}, timeout=10)
        if r.status_code == 200:
            st.session_state.auth_token = r.json()["access_token"]
            user = get_current_user()
            if user:
                st.session_state.auth_user = user
            return True, "Login successful!"
        return False, r.json().get("detail", "Login failed")
    except Exception as e:
        return False, str(e)


def register(email: str, username: str, password: str) -> tuple[bool, str]:
    try:
        r = httpx.post(f"{API_BASE}/auth/register", json={
            "email": email, "username": username, "password": password
        }, timeout=10)
        if r.status_code == 201:
            return True, "Account created! Please log in."
        return False, r.json().get("detail", "Registration failed")
    except Exception as e:
        return False, str(e)


def logout():
    st.session_state.pop("auth_token", None)
    st.session_state.pop("auth_user", None)


def require_auth():
    if not is_authenticated():
        st.warning("Please log in to access this feature.")
        st.page_link("pages/0_Login.py", label="Go to Login", icon="🔑")
        st.stop()
