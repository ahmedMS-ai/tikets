
import os, time
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

HEADERS = {
    "tickets": ["timestamp","ticket_id","title","description","severity","product","module","locale","reporter","attachments","status"],
    "evaluations": ["timestamp","ticket_id","draft_len","rubric_version","model","raw_score","pass","verdict","rationale","failures","evaluator_latency_ms"],
}

def _get_creds_from_streamlit():
    try:
        import streamlit as st
        if "gcp_service_account" in st.secrets:
            info = dict(st.secrets["gcp_service_account"])
            return Credentials.from_service_account_info(info, scopes=SCOPE)
    except Exception:
        pass
    return None

def _get_creds_from_env():
    sa_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    if not sa_json:
        return None
    import json
    info = json.loads(sa_json)
    return Credentials.from_service_account_info(info, scopes=SCOPE)

def get_gspread_client():
    creds = _get_creds_from_streamlit() or _get_creds_from_env()
    if not creds:
        raise RuntimeError("Google Service Account credentials not found. Provide via Streamlit secrets 'gcp_service_account' or env var GOOGLE_SERVICE_ACCOUNT_JSON.")
    return gspread.authorize(creds)

def get_sheet_id():
    try:
        import streamlit as st
        sid = st.secrets["GSHEETS"]["sheet_id"]
        if sid:
            return sid
    except Exception:
        pass
    sid = os.getenv("GSHEETS_SHEET_ID")
    if not sid:
        raise RuntimeError("Google Sheet ID not found. Set Streamlit secret GSHEETS.sheet_id or env GSHEETS_SHEET_ID.")
    return sid

def ensure_worksheets(sh):
    existing = {ws.title for ws in sh.worksheets()}
    for name, headers in HEADERS.items():
        if name not in existing:
            ws = sh.add_worksheet(title=name, rows=2000, cols=len(headers)+5)
            ws.append_row(headers)
    return {ws.title: ws for ws in sh.worksheets()}

def open_sheets():
    gc = get_gspread_client()
    sheet_id = get_sheet_id()
    sh = gc.open_by_key(sheet_id)
    ws_map = ensure_worksheets(sh)
    return sh, ws_map

def append_ticket(ticket_row):
    _, ws = open_sheets()
    ws_t = ws["tickets"]
    ws_t.append_row(ticket_row, value_input_option="USER_ENTERED")

def append_evaluation(eval_row):
    _, ws = open_sheets()
    ws_e = ws["evaluations"]
    ws_e.append_row(eval_row, value_input_option="USER_ENTERED")

def read_df(name: str) -> pd.DataFrame:
    _, ws = open_sheets()
    ws_n = ws[name]
    data = ws_n.get_all_records()
    if not data:
        return pd.DataFrame(columns=HEADERS[name])
    return pd.DataFrame(data)
