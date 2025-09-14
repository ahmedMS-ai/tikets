# file: smart-support-hub/app/main.py
import sys
from pathlib import Path
import streamlit as st

PKG_ROOT = Path(__file__).resolve().parent.parent
if str(PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(PKG_ROOT))

from app.config import load_settings, missing_keys
from app.ui.styles import inject_css
from app.ui.components import not_configured
from app.auth.oauth import login_button, handle_callback, enforce_allowlist
from app.auth.basic_auth import basic_login_ui
from app.services.sheets_client import ensure_sheets_and_headers, get_user_role
from app.dashboards.lead_dashboard import render as render_dashboard
from app.ui.pages import main_page

st.set_page_config(page_title="Smart Support Hub", page_icon="🛠️", layout="wide")
inject_css()

settings = load_settings()
miss = missing_keys(settings)
if miss:
    not_configured(miss)
    st.stop()

# ---- Sign-in options (Google OAuth OR Local Basic) ----
if "user" not in st.session_state:
    t1, t2 = st.tabs(["🔐 Google Sign-in", "🧪 Local Login"])
    with t1:
        st.write("Sign in with Google")
        login_button()
        u = handle_callback()
        if u:
            st.session_state["user"] = u
    with t2:
        u = basic_login_ui()
        if u:
            st.session_state["user"] = u

if "user" not in st.session_state:
    st.stop()

user = st.session_state["user"]
# Enforce domain allowlist only for Google users (skip for local basic)
if "@local" not in user.get("email", "") and not enforce_allowlist(user):
    st.error("Your email domain is not allowed.")
    st.stop()

# Ensure sheets exist and register user
try:
    ensure_sheets_and_headers()
except Exception as e:
    st.error(f"Sheets configuration error: {e}")
    st.stop()

role = get_user_role(user["email"])

st.sidebar.title("Navigation")
page = st.sidebar.selectbox("Go to", ["Tickets", "Dashboard"])
if page == "Dashboard":
    render_dashboard()
else:
    main_page(user)
