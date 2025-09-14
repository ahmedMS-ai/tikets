
import pandas as pd
import streamlit as st
from utils.gsheets import read_df

st.title("📈 Reports & Analytics")

col1, col2, col3 = st.columns(3)

try:
    df_t = read_df("tickets")
    df_e = read_df("evaluations")
except Exception as e:
    st.error(f"Cannot read Google Sheets: {e}")
    st.stop()

with col1:
    st.metric("Total Tickets", len(df_t))
with col2:
    sev_mix = df_t["severity"].value_counts() if not df_t.empty else pd.Series(dtype=int)
    st.metric("Top Severity", sev_mix.index[0] if not sev_mix.empty else "—")
with col3:
    pass_rate = 100.0 * (df_e["pass"].astype(str).str.upper().eq("TRUE").mean()) if not df_e.empty else 0.0
    st.metric("Evaluator Pass Rate", f"{pass_rate:.1f}%")

st.divider()

st.subheader("Severity Mix")
if not df_t.empty:
    st.bar_chart(df_t["severity"].value_counts())
else:
    st.info("No tickets yet.")

st.subheader("Scores Distribution")
if not df_e.empty:
    df_e["raw_score"] = pd.to_numeric(df_e["raw_score"], errors="coerce")
    st.bar_chart(df_e["raw_score"])
else:
    st.info("No evaluations yet.")

st.subheader("Recent Activity")
c1, c2 = st.columns(2)
with c1:
    st.write("**Latest Tickets**")
    st.dataframe(df_t.tail(20), use_container_width=True)
with c2:
    st.write("**Latest Evaluations**")
    st.dataframe(df_e.tail(20), use_container_width=True)
