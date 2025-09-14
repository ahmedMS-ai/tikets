# file: smart-support-hub/pages/1_Reports.py
import streamlit as st
import pandas as pd

from app.services.sheets_client import ensure_sheets_and_headers, _open  # type: ignore


st.set_page_config(page_title="Reports", page_icon="📈", layout="wide")
st.title("📈 Reports / Analytics")

try:
    ensure_sheets_and_headers()
    sh = _open()
    df = pd.DataFrame(sh.worksheet("tickets").get_all_records())
except Exception as e:
    st.error(f"Cannot load tickets yet: {e}")
    st.stop()

# Adapt from our schema -> page's expected schema
expected = [
    "timestamp", "ticket_id", "title", "description",
    "severity", "product", "module", "locale",
    "reporter", "attachments", "status",
]

df_out = pd.DataFrame()
df_out["timestamp"] = df.get("created_at", "")
df_out["ticket_id"] = df.get("id", "")
df_out["title"] = df.get("title", "")
df_out["description"] = df.get("description", "")
df_out["severity"] = df.get("issue_type", "")        # map
df_out["product"] = "TMS"                            # default
df_out["module"] = ""                                # unknown
df_out["locale"] = ""                                # unknown
df_out["reporter"] = df.get("requester", "")
df_out["attachments"] = df.get("links_attachments", "")
df_out["status"] = df.get("status", "")

df_out = df_out[expected]

st.subheader("Mix by severity (mapped from issue_type)")
if df_out.empty:
    st.info("No tickets yet.")
else:
    sev_mix = df_out["severity"].value_counts()
    st.bar_chart(sev_mix)

st.subheader("Raw (mapped) view")
st.dataframe(df_out.tail(200), use_container_width=True)
