
from __future__ import annotations
import streamlit as st
import pandas as pd
from app.services.sheets_client import ensure_sheets_and_headers, _open

def render():
    st.header("📊 Lead Dashboard")

    try:
        ensure_sheets_and_headers()
        sh = _open()
        tdf = pd.DataFrame(sh.worksheet("tickets").get_all_records())
        ldf = pd.DataFrame(sh.worksheet("log").get_all_records())
    except Exception as e:
        st.error(f"Sheets error: {e}")
        return

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Tickets", len(tdf))
    c2.metric("Accepted Logs", (ldf["result_status"]=="Accepted").sum() if not ldf.empty else 0)
    c3.metric("Rejected Logs", (ldf["result_status"]=="Rejected").sum() if not ldf.empty else 0)

    st.subheader("Recent Tickets")
    st.dataframe(tdf.tail(20), use_container_width=True)

    st.subheader("Recent Log")
    st.dataframe(ldf.tail(20), use_container_width=True)
