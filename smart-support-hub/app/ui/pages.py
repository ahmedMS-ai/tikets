# file: smart-support-hub/app/ui/pages.py
from __future__ import annotations
import json
from typing import Dict, Any
from datetime import datetime
import streamlit as st

from app.ui.components import checklist, header
from app.services.validators import sanitize_prompt_payload
from app.services.gemini_client import evaluate_strict
from app.services.sheets_client import (
    ensure_sheets_and_headers,
    append_ticket_row,
    append_log_row,
    upsert_user,
)
from app.services.ticket_parser import parse_ticket_text


def _prefill_session(fields: Dict[str, Any]) -> None:
    for k, v in fields.items():
        st.session_state[f"form_{k}"] = v


def _get(key: str, default=""):
    return st.session_state.get(f"form_{key}", default)


def main_page(user: Dict[str, str]):
    header(user["name"], user["email"])

    # ---------- Paste & Parse ----------
    with st.expander("📋 Paste full ticket text → auto-fill the form", expanded=True):
        raw = st.text_area("Paste the ticket block here", height=220, key="raw_ticket_text")
        if st.button("Parse ticket"):
            try:
                ensure_sheets_and_headers()
                upsert_user(user["email"], user["name"])

                parsed = parse_ticket_text(raw or "")
                _prefill_session(parsed)

                append_log_row(
                    {
                        "ticket_id": parsed.get("id", "") or "N/A",
                        "user_email": user["email"],
                        "prompt": sanitize_prompt_payload((raw or "")[:5000]),
                        "model_response": json.dumps(parsed, ensure_ascii=False),
                        "result_status": "Parsed",
                        "missing_sections": "",
                        "compliance_score": "",
                        "created_at": datetime.utcnow().isoformat(),
                    }
                )
                st.success("Ticket parsed and form pre-filled.")
            except Exception as e:
                append_log_row(
                    {
                        "ticket_id": "",
                        "user_email": user["email"],
                        "prompt": sanitize_prompt_payload((raw or "")[:5000]),
                        "model_response": f"ParseError: {e}",
                        "result_status": "ParseError",
                        "missing_sections": "",
                        "compliance_score": "",
                        "created_at": datetime.utcnow().isoformat(),
                    }
                )
                st.error(f"Parse failed: {e}")

    # ---------- Strict Summary (Agent Journal) ----------
    st.sidebar.header("Strict Summary (Agent Journal)")
    draft = st.sidebar.text_area(
        "Write your investigation journal here (will be STRICT-evaluated)",
        height=260,
        key="draft_text",
    )
    with st.sidebar:
        checklist()

    # ---------- Form ----------
    st.title("Create / Update Ticket")

    with st.form("ticket_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            ticket_id = st.text_input("id", value=_get("id"), key="form_id")
            date = st.date_input("date")
            requester = st.text_input("requester", value=_get("requester"), key="form_requester")
        with c2:
            title = st.text_input("title", value=_get("title"), key="form_title")
            issue_type = st.selectbox(
                "issue_type",
                ["Access", "Sync", "Bug", "Report", "Enhancement", "Other"],
                index=["Access", "Sync", "Bug", "Report", "Enhancement", "Other"].index(
                    _get("issue_type", "Other")
                ),
                key="form_issue_type",
            )
            owner = st.text_input("owner", value=user["email"], key="form_owner")
        with c3:
            status = st.selectbox(
                "status",
                ["Open", "In Progress", "Waiting External", "Resolved", "Closed"],
                index=["Open", "In Progress", "Waiting External", "Resolved", "Closed"].index(
                    _get("status", "Open")
                ),
                key="form_status",
            )
            notes = st.text_area("notes", height=100, value=_get("notes"), key="form_notes")

        description = st.text_area("description", height=130, value=_get("description"), key="form_description")
        links_attachments = st.text_area(
            "links_attachments", height=80, value=_get("links_attachments"), key="form_links_attachments"
        )
        involved = st.text_input(
            "involved_teams_people", value=_get("involved_teams_people"), key="form_involved_teams_people"
        )
        inv_steps = st.text_area("investigation_steps", height=120, key="form_investigation_steps")
        resolution = st.text_area("resolution_workaround", height=120, key="form_resolution_workaround")

        left, right = st.columns(2)
        evaluate = left.form_submit_button("Evaluate (STRICT)")
        save = right.form_submit_button("Save Ticket", disabled=True)

    # ---------- Evaluate ----------
    if evaluate:
        if not user.get("email"):
            st.error("You must be logged in.")
            return
        if not ticket_id or not draft.strip():
            st.error("Ticket id and Draft are required.")
            return

        ensure_sheets_and_headers()
        upsert_user(user["email"], user["name"])
        payload = sanitize_prompt_payload(draft)

        append_log_row(
            {
                "ticket_id": ticket_id,
                "user_email": user["email"],
                "prompt": payload,
                "model_response": "",
                "result_status": "Pending",
                "missing_sections": "",
                "compliance_score": "",
                "created_at": datetime.utcnow().isoformat(),
            }
        )

        res = evaluate_strict(draft)

        if not res.get("ok"):
            st.error(f"Rejected — {res.get('message','Model error')}")
            missing = res.get("missing", [])
            if missing:
                st.info("Please include the following sections:")
                st.code("\n".join(missing))
            append_log_row(
                {
                    "ticket_id": ticket_id,
                    "user_email": user["email"],
                    "prompt": payload,
                    "model_response": json.dumps(res, ensure_ascii=False),
                    "result_status": "Rejected",
                    "missing_sections": "; ".join(missing) if missing else "",
                    "compliance_score": "",
                    "created_at": datetime.utcnow().isoformat(),
                }
            )
            return
        else:
            st.success("Accepted — structured summary ready.")
            st.json(res["summary"])
            st.session_state["can_save_ticket"] = True
            st.session_state["last_eval"] = res

            append_log_row(
                {
                    "ticket_id": ticket_id,
                    "user_email": user["email"],
                    "prompt": payload,
                    "model_response": json.dumps(res, ensure_ascii=False),
                    "result_status": "Accepted",
                    "missing_sections": "",
                    "compliance_score": res.get("compliance_score", 100),
                    "created_at": datetime.utcnow().isoformat(),
                }
            )

    # ---------- Save ----------
    if st.session_state.get("can_save_ticket") and st.session_state.get("last_eval"):
        if st.button("Confirm Save Ticket"):
            res = st.session_state["last_eval"]
            summary = res["summary"]
            append_ticket_row(
                {
                    "id": st.session_state.get("form_id", ticket_id),
                    "date": str(date),
                    "requester": st.session_state.get("form_requester", ""),
                    "title": st.session_state.get("form_title", ""),
                    "issue_type": st.session_state.get("form_issue_type", "Other"),
                    "description": st.session_state.get("form_description", ""),
                    "links_attachments": st.session_state.get("form_links_attachments", ""),
                    "involved_teams_people": st.session_state.get("form_involved_teams_people", ""),
                    "investigation_steps": st.session_state.get("form_investigation_steps", ""),
                    "resolution_workaround": st.session_state.get("form_resolution_workaround", ""),
                    "owner": st.session_state.get("form_owner", user["email"]),
                    "status": st.session_state.get("form_status", "Open"),
                    "notes": st.session_state.get("form_notes", ""),
                    "structured_summary_problem": summary.get("problem", ""),
                    "structured_summary_cause": summary.get("cause", ""),
                    "structured_summary_steps": summary.get("steps", ""),
                    "structured_summary_resolution": summary.get("resolution", ""),
                    "structured_summary_cross_team": summary.get("cross_team", ""),
                    "compliance_score": res.get("compliance_score", 100),
                    "created_by": user["email"],
                    "created_at": datetime.utcnow().isoformat(),
                }
            )
            st.toast(f"Ticket saved successfully. Thank you, {user['name']}.")
            st.session_state["can_save_ticket"] = False
            st.session_state["last_eval"] = None
