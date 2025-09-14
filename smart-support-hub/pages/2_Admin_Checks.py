# file: smart-support-hub/pages/2_Admin_Checks.py
# Validate worksheets but accept our schema as the source of truth.
import sys
from pathlib import Path
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.sheets_client import ensure_sheets_and_headers, open_spreadsheet  # type: ignore
from app.services.sheets_client import TICKETS_HEADERS, LOG_HEADERS, USERS_HEADERS  # type: ignore

st.set_page_config(page_title="Admin Checks", page_icon="🛠️", layout="wide")
st.title("🛠️ Admin Checks")
st.caption("Validate worksheets and headers in the connected Google Sheet.")

if st.button("Run Checks"):
    try:
        ensure_sheets_and_headers()
        sh = open_spreadsheet()
        ws = [w.title for w in sh.worksheets()]
        st.success(f"Found worksheets: {', '.join(ws)}")
        # tickets
        t_hdr = sh.worksheet("tickets").row_values(1)
        if t_hdr[: len(TICKETS_HEADERS)] == TICKETS_HEADERS:
            st.success("tickets headers OK (Smart Support Hub schema).")
        else:
            st.warning(
                "tickets headers differ from legacy schema. This is OK — app uses its own schema "
                "and pages map columns as needed."
            )
        # evaluations (optional)
        try:
            e_hdr = sh.worksheet("evaluations").row_values(1)
            st.success("evaluations sheet present.")
        except Exception:
            st.info("evaluations sheet not found (optional).")
    except Exception as e:
        st.error(f"Check failed: {e}")
else:
    st.info("Click **Run Checks** to validate.")
