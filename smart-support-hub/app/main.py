# file: smart-support-hub/app/main.py
import sys
from pathlib import Path
from datetime import datetime
import streamlit as st

PKG_ROOT = Path(__file__).resolve().parent.parent
if str(PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(PKG_ROOT))

from app.config import load_settings, missing_keys
from app.ui.styles import inject_css
from app.ui.components import not_configured
from app.auth.basic_auth import require_login
from app.services.sheets_client import ensure_sheets_and_headers, get_user_role, append_log_row, upsert_user
from app.dashboards.lead_dashboard import render as render_dashboard
from app.ui.pages import main_page

st.set_page_config(page_title="Smart Support Hub", page_icon="🛠️", layout="wide")
inject_css()

settings = load_settings()
miss = missing_keys(settings)
if miss:
    not_configured(miss)
    st.stop()

# === HARD REQUIREMENT: Basic login only ===
user = require_login()  # blocks until success

# First-time setup + register user + log the login
try:
    ensure_sheets_and_headers()
    upsert_user(user["email"], user["name"])
    if not st.session_state.get("_login_logged"):
        append_log_row({
            "ticket_id": "",
            "user_email": user["email"],
            "prompt": "Login",
            "model_response": "Login OK",
            "result_status": "Login",
            "missing_sections": "",
            "compliance_score": "",
            "created_at": datetime.utcnow().isoformat(),
        })
        st.session_state["_login_logged"] = True
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
