# file: smart-support-hub/app/auth/basic_auth.py
from __future__ import annotations
import streamlit as st
from typing import Optional, Dict

def _get_creds() -> Dict[str, str]:
    """
    Reads [basic_auth] from st.secrets as username=password pairs.
    Fallback to {"1": "1"} for quick tests.
    """
    creds = {}
    try:
        raw = st.secrets.get("basic_auth", {})
        if isinstance(raw, dict):
            creds = {str(k): str(v) for k, v in raw.items()}
    except Exception:
        pass
    return creds or {"1": "1"}

def require_login() -> dict:
    """
    Hard requirement: block the app until user logs in.
    Returns a dict {email, name, username} on success.
    """
    if "user" in st.session_state:
        return st.session_state["user"]

    st.title("🔐 Sign in to continue")
    st.caption("Local login (temporary). Configure users in [basic_auth] secrets.")
    u = st.text_input("Username", key="ba_user")
    p = st.text_input("Password", type="password", key="ba_pass")
    e = st.text_input("Email (used in logs)", value=f"{u or 'user'}@local", key="ba_email")

    if st.button("Sign in"):
        creds = _get_creds()
        if u in creds and p == creds[u]:
            user = {"email": (e or f"{u}@local").strip(), "name": u, "username": u}
            st.session_state["user"] = user
            return user
        st.error("Invalid credentials.")
    st.stop()
