
import streamlit as st
from typing import List

def not_configured(missing: List[str]):
    st.title("🔧 Smart Support Hub")
    st.error("This app is not fully configured.")
    st.write("Missing keys:")
    st.code("\n".join(missing))
    st.info("Provide values via Streamlit secrets or a local .env file. See README for setup.")

def header(user_name: str, user_email: str):
    st.markdown(f"**Signed in as:** {user_name} `<{user_email}>`")

def checklist():
    c1, c2 = st.columns(2)
    with c1:
        p = st.checkbox("Problem Statement", value=False, key="ck_problem")
        r = st.checkbox("Root Cause / Findings", value=False, key="ck_cause")
        i = st.checkbox("Investigation Steps", value=False, key="ck_steps")
    with c2:
        w = st.checkbox("Resolution / Workaround", value=False, key="ck_resolution")
        x = st.checkbox("Cross-team Involvement", value=False, key="ck_cross")
    return dict(problem=p, cause=r, steps=i, resolution=w, cross=x)
