
import streamlit as st

def inject_css():
    st.markdown(
        """
        <style>
        .ok { color: #0a7f2e; font-weight: 600; }
        .bad { color: #b00020; font-weight: 600; }
        .muted { color: #6b7280; }
        .box { padding: .75rem 1rem; background:#f8fafc; border:1px solid #e5e7eb; border-radius: .5rem; }
        .mono { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace; }
        </style>
        """
        , unsafe_allow_html=True
    )
