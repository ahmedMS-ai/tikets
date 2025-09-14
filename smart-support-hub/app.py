
import os, io, time, json, yaml, uuid
import pandas as pd
import streamlit as st
from utils.schemas import Ticket, Evaluation
from utils.gsheets import append_ticket, append_evaluation, read_df
from utils.gsheets import HEADERS  # for column order
from utils.gemini_eval import evaluate_with_gemini

st.set_page_config(page_title="Smart Support Hub", page_icon="🛠️", layout="wide")

st.title("🛠️ Smart Support Hub — TMS Support")

with st.sidebar:
    st.header("Settings")
    # Load rubric
    default_rubric_path = os.path.join("evaluations", "rubric.yaml")
    with open(default_rubric_path, "r", encoding="utf-8") as f:
        default_rubric_yaml = f.read()
    rubric_yaml = st.text_area("Evaluation Rubric (YAML)", default_rubric_yaml, height=300)
    rubric = yaml.safe_load(rubric_yaml)
    pass_threshold = float(rubric.get("pass_threshold", 75))
    st.caption(f"Pass threshold: {pass_threshold}")

    st.divider()
    st.markdown("**Environment checks**")
    ok_gs = "✅" if ("gcp_service_account" in st.secrets or os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")) else "❌"
    ok_sid = "✅" if (st.secrets.get("GSHEETS", {}).get("sheet_id") if hasattr(st, "secrets") else os.getenv("GSHEETS_SHEET_ID")) else "❌"
    ok_gem = "✅" if (st.secrets.get("GEMINI", {}).get("api_key") if hasattr(st, "secrets") else os.getenv("GEMINI_API_KEY")) else "❌"
    st.write(f"Google Service Account: {ok_gs}  |  Sheet ID: {ok_sid}  |  Gemini Key: {ok_gem}")
    st.info("Provide missing secrets in `.streamlit/secrets.toml` or environment variables.")

tab1, tab2 = st.tabs(["📥 Ticket Intake", "🧪 Draft Evaluation"])

with tab1:
    st.subheader("Create / Log Support Ticket")
    with st.form(key="ticket_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            title = st.text_input("Title", placeholder="Customer cannot import TMX")
            severity = st.selectbox("Severity", ["S0","S1","S2","S3"], index=2)
            locale = st.text_input("Customer Locale", value="en")
        with col2:
            product = st.text_input("Product", value="TMS")
            module = st.text_input("Module", value="Connectors")
            reporter = st.text_input("Reporter (email)", value="")
        with col3:
            ticket_id = st.text_input("Ticket ID (optional, will auto-generate if empty)", value="")
            status = st.selectbox("Status", ["New","In Progress","Pending Customer","Resolved","Closed"], index=0)
            attachments = st.text_area("Attachment filenames (comma-separated)", placeholder="error.log, screenshot.png")

        submitted = st.form_submit_button("Save Ticket to Google Sheets")
        if submitted:
            if not title or not severity:
                st.error("Title and Severity are required.")
            else:
                tid = ticket_id.strip() or f"TCK-{uuid.uuid4().hex[:8].upper()}"
                att_list = [a.strip() for a in attachments.split(",") if a.strip()]
                t = Ticket(
                    ticket_id=tid,
                    title=title,
                    description=st.text_area if False else st.session_state.get("ticket_desc", ""),  # placeholder no-op
                    severity=severity,
                    product=product,
                    module=module,
                    locale=locale,
                    reporter=reporter,
                    attachments=att_list,
                    status=status,
                )
                # Build row in fixed order
                row = [
                    pd.Timestamp.utcnow().isoformat(),
                    t.ticket_id, t.title, st.session_state.get("ticket_desc",""), t.severity,
                    t.product, t.module, t.locale, t.reporter, ";".join(t.attachments), t.status
                ]
                try:
                    append_ticket(row)
                    st.success(f"Ticket saved: {t.ticket_id}")
                except Exception as e:
                    st.error(f"Failed to write to Google Sheets: {e}")

    st.markdown("#### Ticket Description")
    desc = st.text_area("Describe the issue (included in future saves)", key="ticket_desc", height=180, placeholder="Steps, expected vs actual, error messages...")

    st.divider()
    st.subheader("Recent Tickets")
    try:
        df_t = read_df("tickets")
        st.dataframe(df_t.tail(50), use_container_width=True)
    except Exception as e:
        st.warning(f"Cannot load tickets yet: {e}")

with tab2:
    st.subheader("Evaluate a Draft Response (STRICT)")
    colA, colB = st.columns(2)
    with colA:
        eval_ticket_id = st.text_input("Ticket ID (link evaluation to ticket)", value="")
        eval_severity = st.selectbox("Severity (for rubric context)", ["S0","S1","S2","S3"], index=2, key="sev_eval")
        eval_locale = st.text_input("Locale", value="en", key="loc_eval")
        eval_product = st.text_input("Product", value="TMS", key="prod_eval")
        eval_module = st.text_input("Module", value="Connectors", key="mod_eval")
        ticket_ctx = st.text_area("Paste ticket text / context", height=150)
    with colB:
        draft = st.text_area("Paste the draft support response to evaluate", height=230, placeholder="Proposed customer reply / solution...")

    run = st.button("Run Strict Evaluation with Gemini")
    if run:
        if not draft.strip():
            st.error("Please paste a draft response to evaluate.")
        else:
            with st.spinner("Evaluating with Gemini..."):
                try:
                    result = evaluate_with_gemini(
                        ticket=ticket_ctx,
                        draft=draft,
                        rubric_yaml=rubric_yaml,
                        severity=eval_severity,
                        locale=eval_locale,
                        product=eval_product,
                        module=eval_module,
                    )
                    passed = result["passed"]
                    raw = result["raw_score"]
                    verdict = result["verdict"]
                    rationale = result.get("rationale","")
                    failures = result.get("failures",[])
                    model = result.get("model","")
                    lat = result.get("latency_ms")

                    st.metric(label="Verdict", value=verdict)
                    st.metric(label="Raw Score", value=f"{raw:.1f}")
                    st.caption(f"Model: {model} | Latency: {lat} ms")
                    st.write("**Rationale**")
                    st.write(rationale)
                    if failures:
                        st.write("**Failures**")
                        st.write("\n".join(f"- {f}" for f in failures))

                    # Persist
                    row = [
                        pd.Timestamp.utcnow().isoformat(),
                        eval_ticket_id or "",
                        len(draft),
                        "v1",
                        model,
                        float(raw),
                        "TRUE" if passed else "FALSE",
                        verdict,
                        rationale,
                        "; ".join(failures),
                        int(lat) if lat is not None else ""
                    ]
                    try:
                        append_evaluation(row)
                        st.success("Evaluation saved to Google Sheets.")
                    except Exception as e:
                        st.error(f"Failed to save evaluation: {e}")
                except Exception as e:
                    st.error(f"Evaluation failed: {e}")

    st.divider()
    st.subheader("Recent Evaluations")
    try:
        df_e = read_df("evaluations")
        st.dataframe(df_e.tail(50), use_container_width=True)
    except Exception as e:
        st.warning(f"Cannot load evaluations yet: {e}")
