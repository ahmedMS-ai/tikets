
from __future__ import annotations
import streamlit as st
from app.config import load_settings, missing_keys
from app.ui.styles import inject_css
from app.ui.components import not_configured
from app.auth.oauth import login_button, handle_callback, enforce_allowlist
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

# OAuth flow
user = handle_callback()
if user:
    st.session_state["user"] = user

if "user" not in st.session_state:
    st.title("🛠️ Smart Support Hub")
    st.write("Sign in to continue")
    login_button()
    st.stop()

user = st.session_state["user"]
if not enforce_allowlist(user):
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
page = st.sidebar.selectbox("Go to", ["Tickets","Dashboard"])

if page == "Dashboard":
    render_dashboard()
else:
    main_page(user)
