# file: smart-support-hub/app/services/sheets_client.py
from __future__ import annotations
import string
import re
from typing import Dict, Any, List
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from app.config import load_settings
from app.auth.roles import DEFAULT_ROLE

TICKETS_HEADERS = [
    "id","date","requester","title","issue_type","description","links_attachments","involved_teams_people",
    "investigation_steps","resolution_workaround","owner","status","notes",
    "structured_summary_problem","structured_summary_cause","structured_summary_steps","structured_summary_resolution",
    "structured_summary_cross_team","compliance_score","created_by","created_at"
]
LOG_HEADERS = [
    "ticket_id","user_email","prompt","model_response","result_status","missing_sections","compliance_score","created_at"
]
USERS_HEADERS = ["email","name","role","active","created_at"]

SCOPE = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

def _client() -> gspread.Client:
    s = load_settings()
    info = s.gcp_service_account
    if not info:
        raise RuntimeError("Service Account not configured")
    creds = Credentials.from_service_account_info(info, scopes=SCOPE)
    return gspread.authorize(creds)

def _extract_sheet_id(sid_or_url: str) -> str:
    m = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", sid_or_url)
    return m.group(1) if m else sid_or_url

def _open() -> gspread.Spreadsheet:
    s = load_settings()
    sid = _extract_sheet_id(s.google_sheet_id or "")
    if not sid:
        raise RuntimeError("GOOGLE_SHEET_ID missing")
    return _client().open_by_key(sid)

def _ensure_headers(ws: gspread.Worksheet, headers: List[str]):
    values = ws.row_values(1)
    if not values:
        ws.append_row(headers)
        return
    # If headers exist but different, don't overwrite user sheet; keep as-is.

def ensure_sheets_and_headers():
    sh = _open()
    existing = {ws.title for ws in sh.worksheets()}
    if "tickets" not in existing:
        ws = sh.add_worksheet(title="tickets", rows=2000, cols=len(TICKETS_HEADERS) + 5)
        ws.append_row(TICKETS_HEADERS)
    else:
        _ensure_headers(sh.worksheet("tickets"), TICKETS_HEADERS)

    if "log" not in existing:
        ws = sh.add_worksheet(title="log", rows=2000, cols=len(LOG_HEADERS) + 5)
        ws.append_row(LOG_HEADERS)
    else:
        _ensure_headers(sh.worksheet("log"), LOG_HEADERS)

    if "users" not in existing:
        ws = sh.add_worksheet(title="users", rows=2000, cols=len(USERS_HEADERS) + 5)
        ws.append_row(USERS_HEADERS)
    else:
        _ensure_headers(sh.worksheet("users"), USERS_HEADERS)

def _append_row(sheet_name: str, headers: List[str], row_dict: Dict[str, Any]):
    sh = _open()
    ws = sh.worksheet(sheet_name)
    # Map by header name to preserve order; missing keys -> ""
    dest_headers = ws.row_values(1) or headers  # support custom/extra columns
    # If the worksheet has extra columns, we only fill the known ones in order
    write_headers = headers if headers else dest_headers
    row = [str(row_dict.get(h, "")) for h in write_headers]
    ws.append_row(row, value_input_option="USER_ENTERED")

def append_ticket_row(row_dict: Dict[str, Any]):
    _append_row("tickets", TICKETS_HEADERS, row_dict)

def append_log_row(row_dict: Dict[str, Any]):
    # stringify complex fields (dicts) for logging
    row_dict = dict(row_dict)
    for k in ("prompt", "model_response"):
        v = row_dict.get(k)
        if isinstance(v, (dict, list)):
            import json
            row_dict[k] = json.dumps(v, ensure_ascii=False)
    _append_row("log", LOG_HEADERS, row_dict)

def _header_index_map(ws: gspread.Worksheet) -> Dict[str, int]:
    """Return header -> 1-based column index map (robust to extra columns)."""
    hdrs = ws.row_values(1)
    return {h.strip(): i + 1 for i, h in enumerate(hdrs) if h.strip()}

def get_user_role(email: str) -> str:
    sh = _open()
    ws = sh.worksheet("users")
    # Robust: read as records; fallback to default
    data = ws.get_all_records()
    for r in data:
        if str(r.get("email", "")).lower() == email.lower():
            return str(r.get("role", DEFAULT_ROLE)) or DEFAULT_ROLE
    return DEFAULT_ROLE

def upsert_user(email: str, name: str, role: str = DEFAULT_ROLE, active: bool = True):
    sh = _open()
    ws = sh.worksheet("users")
    data = ws.get_all_records()
    # Try find existing row
    for idx, r in enumerate(data, start=2):  # header is row 1
        if str(r.get("email", "")).lower() == email.lower():
            # Update using header names to be safe with extra columns
            hmap = _header_index_map(ws)
            if "name" in hmap:
                ws.update_cell(idx, hmap["name"], name)
            if "role" in hmap:
                ws.update_cell(idx, hmap["role"], role)
            if "active" in hmap:
                ws.update_cell(idx, hmap["active"], "TRUE" if active else "FALSE")
            return

    # Not found → append new in canonical order (extra columns will stay empty)
    ws.append_row(
        [email, name, role, "TRUE" if active else "FALSE", pd.Timestamp.utcnow().isoformat()],
        value_input_option="USER_ENTERED",
    )
