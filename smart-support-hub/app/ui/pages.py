
from __future__ import annotations
import streamlit as st
from typing import Dict, Any
from datetime import datetime

from app.ui.components import checklist, header
from app.services.validators import sanitize_prompt_payload
from app.services.gemini_client import evaluate_strict
from app.services.sheets_client import (
    ensure_sheets_and_headers,
    append_ticket_row,
    append_log_row,
    upsert_user,
)

def main_page(user: Dict[str, str]):
    header(user["name"], user["email"])

    st.sidebar.header("Strict Summary")
    draft = st.sidebar.text_area("Agent Draft (free text)", height=240, key="draft_text")
    checks = st.sidebar.container()
    with checks:
        flags = checklist()

    st.title("Create / Update Ticket")
    with st.form("ticket_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            ticket_id = st.text_input("id", placeholder="TCK-0001")
            date = st.date_input("date")
            requester = st.text_input("requester", placeholder="customer@domain.com")
        with c2:
            title = st.text_input("title")
            issue_type = st.selectbox("issue_type", ["Access","Sync","Bug","Report","Enhancement","Other"], index=2)
            owner = st.text_input("owner", value=user["email"])
        with c3:
            status = st.selectbox("status", ["Open","In Progress","Waiting External","Resolved","Closed"], index=0)
            notes = st.text_area("notes", height=100)
        description = st.text_area("description", height=130)
        links_attachments = st.text_area("links_attachments", height=80, placeholder="URLs, filenames...")
        involved = st.text_input("involved_teams_people", placeholder="SRE; DBA; Vendor")
        inv_steps = st.text_area("investigation_steps", height=120)
        resolution = st.text_area("resolution_workaround", height=120)

        left, right = st.columns(2)
        evaluate = left.form_submit_button("Evaluate (STRICT)")
        save = right.form_submit_button("Save Ticket", disabled=True)

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
        append_log_row({
            "ticket_id": ticket_id,
            "user_email": user["email"],
            "prompt": payload,
            "model_response": "",
            "result_status": "Pending",
            "missing_sections": "",
            "compliance_score": "",
            "created_at": datetime.utcnow().isoformat(),
        })

        res = evaluate_strict(draft)

        if not res.get("ok"):
            st.error(f"Rejected — {res.get('message','Model error')}")
            missing = res.get("missing", [])
            if missing:
                st.write("Missing sections:")
                st.code("\n".join(missing))
            append_log_row({
                "ticket_id": ticket_id,
                "user_email": user["email"],
                "prompt": payload,
                "model_response": res,
                "result_status": "Rejected",
                "missing_sections": "; ".join(missing) if missing else "",
                "compliance_score": "",
                "created_at": datetime.utcnow().isoformat(),
            })
            return
        else:
            st.success("Accepted — structured summary ready.")
            summary = res["summary"]
            st.json(summary)

            # Enable save button via session flag
            st.session_state["can_save_ticket"] = True
            st.session_state["last_eval"] = res

            append_log_row({
                "ticket_id": ticket_id,
                "user_email": user["email"],
                "prompt": payload,
                "model_response": res,
                "result_status": "Accepted",
                "missing_sections": "",
                "compliance_score": res.get("compliance_score", 100),
                "created_at": datetime.utcnow().isoformat(),
            })

    # Save ticket if allowed and last form was submitted with Save
    if st.session_state.get("can_save_ticket") and st.session_state.get("last_eval"):
        if st.button("Confirm Save Ticket"):
            res = st.session_state["last_eval"]
            summary = res["summary"]
            append_ticket_row({
                "id": st.session_state.get("id") or st.session_state.get("form_id") or ticket_id,
                "date": str(date),
                "requester": requester,
                "title": title,
                "issue_type": issue_type,
                "description": description,
                "links_attachments": links_attachments,
                "involved_teams_people": involved,
                "investigation_steps": inv_steps,
                "resolution_workaround": resolution,
                "owner": owner,
                "status": status,
                "notes": notes,
                "structured_summary_problem": summary.get("problem",""),
                "structured_summary_cause": summary.get("cause",""),
                "structured_summary_steps": summary.get("steps",""),
                "structured_summary_resolution": summary.get("resolution",""),
                "structured_summary_cross_team": summary.get("cross_team",""),
                "compliance_score": res.get("compliance_score", 100),
                "created_by": user["email"],
                "created_at": datetime.utcnow().isoformat(),
            })
            st.toast(f"Ticket saved successfully. Thank you, {user['name']}.")
            st.session_state["can_save_ticket"] = False
            st.session_state["last_eval"] = None
