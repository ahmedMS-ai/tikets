
import streamlit as st
from utils.gsheets import open_sheets, HEADERS

st.title("🔧 Admin Checks")

st.write("Validate worksheets and headers in the connected Google Sheet.")

if st.button("Run Checks"):
    try:
        _, ws_map = open_sheets()
        st.success(f"Found worksheets: {', '.join(ws_map.keys())}")
        for name, headers in HEADERS.items():
            ws = ws_map[name]
            row1 = ws.row_values(1)
            if row1[:len(headers)] == headers:
                st.write(f"✅ {name} headers OK")
            else:
                st.error(f"❌ {name} headers mismatch. Expected: {headers} | Found: {row1}")
    except Exception as e:
        st.error(f"Error: {e}")
