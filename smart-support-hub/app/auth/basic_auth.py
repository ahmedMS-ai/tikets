# file: smart-support-hub/app/auth/basic_auth.py
from __future__ import annotations
import streamlit as st


def basic_login_ui() -> dict | None:
    """
    Minimal username/password form.
    - Reads optional [basic_auth] from st.secrets as username=password pairs.
    - Default fallback creds for testing: 1 / 1
    Returns a user dict {email, name} if success, else None.
    """
    st.subheader("Local Login (temporary)")
    u = st.text_input("Username", key="ba_user")
    p = st.text_input("Password", type="password", key="ba_pass")
    e = st.text_input("Email (for logging)", value=f"{u or 'user'}@local", key="ba_email")
    if st.button("Sign in", key="ba_btn"):
        creds = {}
        try:
            creds = dict(st.secrets.get("basic_auth", {}))
        except Exception:
            pass
        if not creds:
            creds = {"1": "1"}  # fallback demo
        if u in creds and p == str(creds[u]):
            return {"email": e.strip() or f"{u}@local", "name": u}
        st.error("Invalid credentials.")
    return None
