# file: smart-support-hub/pages/1_Reports.py
# Standalone page: robust imports + works with our ticket schema.
import sys
from pathlib import Path
import streamlit as st
import pandas as pd

# Ensure 'app' package is importable even if Streamlit spawns this page directly
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.sheets_client import ensure_sheets_and_headers, open_spreadsheet  # type: ignore

st.set_page_config(page_title="Reports", page_icon="📈", layout="wide")
st.title("📈 Reports / Analytics")

try:
    ensure_sheets_and_headers()
    sh = open_spreadsheet()
    df = pd.DataFrame(sh.worksheet("tickets").get_all_records())
except Exception as e:
    st.error(f"Cannot load tickets yet: {e}")
    st.stop()

if df.empty:
    st.info("No tickets yet.")
    st.stop()

# Map our columns -> legacy expected for charts (so مفيش KeyError تاني)
df_out = pd.DataFrame()
df_out["timestamp"]    = df.get("created_at", "")
df_out["ticket_id"]    = df.get("id", "")
df_out["title"]        = df.get("title", "")
df_out["description"]  = df.get("description", "")
df_out["severity"]     = df.get("issue_type", "")
df_out["product"]      = "TMS"
df_out["module"]       = ""
df_out["locale"]       = ""
df_out["reporter"]     = df.get("requester", "")
df_out["attachments"]  = df.get("links_attachments", "")
df_out["status"]       = df.get("status", "")

st.subheader("Mix by severity (mapped from issue_type)")
st.bar_chart(df_out["severity"].value_counts())

st.subheader("Recent tickets (mapped view)")
st.dataframe(df_out.tail(200), use_container_width=True)
