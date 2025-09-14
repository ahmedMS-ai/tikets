
# Smart Support Hub (Streamlit)

A production-ready Streamlit app for a TMS Support **Smart Support Hub** with **STRICT evaluation (Gemini)** and **Google Sheets persistence**.

## Features
- 📥 Ticket intake & triage (severity, product/module, locale, attachments metadata)
- 🧠 Draft solution evaluator using **Google Gemini** with a strict rubric & pass/fail threshold
- 📊 Google Sheets persistence for tickets and evaluations (via Service Account)
- 📈 Reports dashboard (SLA trends, severity mix, evaluator pass rate)
- 🔐 Secure secrets via Streamlit `secrets.toml`

---

## Quickstart

### 1) Python env
```bash
python -m venv .venv
source .venv/bin/activate  # on Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2) Configure secrets
Create `.streamlit/secrets.toml` from the example below.

- Create a **Google Cloud Service Account** with **Google Sheets API** enabled.
- Share your target Google Sheet with the service account email.
- Put the full JSON key into `gcp_service_account` section.
- Set your Gemini API key (from Google AI Studio).
- Put your **Spreadsheet ID** (the long ID in its URL).

**.streamlit/secrets.toml (example)**:
```toml
# ==== Google Service Account (full JSON) ====
[gcp_service_account]
type = "service_account"
project_id = "YOUR_GCP_PROJECT"
private_key_id = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "your-sa@your-project.iam.gserviceaccount.com"
client_id = "1234567890"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/your-sa%40your-project.iam.gserviceaccount.com"

# ==== Google Sheets ====
[GSHEETS]
sheet_id = "YOUR_SHEET_ID"

# ==== Gemini ====
[GEMINI]
api_key = "YOUR_GEMINI_API_KEY"
model = "gemini-1.5-flash"
```

> Tip: You can also set these via environment variables; the app prefers Streamlit secrets if present.

### 3) Prepare the Sheet
The app will ensure the following worksheets exist (created if missing):
- `tickets` with headers:
  `timestamp, ticket_id, title, description, severity, product, module, locale, reporter, attachments, status`
- `evaluations` with headers:
  `timestamp, ticket_id, draft_len, rubric_version, model, raw_score, pass, verdict, rationale, failures, evaluator_latency_ms`

### 4) Run
```bash
streamlit run app.py
```

Open the local URL shown in your terminal.

---

## Configuration
- **Rubric**: edit `./evaluations/rubric.yaml` to tune criteria and weights.
- **Pass threshold**: configurable in the sidebar.
- **Model**: override via `secrets.toml` key `GEMINI.model` or environment `GEMINI_MODEL`.

## Notes
- The evaluator is **strict** by design. Drafts that skip root-cause, repro steps, or policy checks will fail.
- Attachments are stored as metadata only (filenames). Actual binary upload is not persisted to Sheets.

## Security
- Do not commit `.streamlit/secrets.toml`.
- Limit Google Sheet sharing to the service account.
- Rotate API keys regularly.

## License
MIT
