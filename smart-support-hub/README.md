
# Smart Support Hub (Streamlit + Gemini + Google Sheets)

A production-ready Streamlit app for TMS Support with:
- Google **OAuth (OIDC)** login with **domain allowlist**
- **Google Sheets** persistence via **Service Account**
- **STRICT** Gemini evaluation with an embedded prompt (no external files)
- Streamlit entrypoint at **`app/main.py`**

---

## 1) Prerequisites

- Google Cloud Project
  - **OAuth Client** (Web app). Authorized redirect URIs must include your Streamlit URL (e.g., `http://localhost:8501/` for local).
  - **Service Account** with **Google Sheets API** enabled. Download the JSON.
- **Google Sheet** to store data. Copy its URL or ID.

### Extracting the Google Sheet ID
From a URL like:
```
https://docs.google.com/spreadsheets/d/1AbCdEfGhIjKlMnOPQRsTUVWXYZ1234567890/edit#gid=0
```
The **Workbook ID** is the long value after `/d/` and before `/edit`:
```
1AbCdEfGhIjKlMnOPQRsTUVWXYZ1234567890
```

Share the sheet with your **Service Account email** (Editor).

---

## 2) Configure Secrets / Env

You can configure via **Streamlit Cloud → App Secrets** (preferred) or locally using a `.env` file.

### Streamlit secrets example (`.streamlit/secrets.toml`):
Copy from `.streamlit/secrets.toml.example` and fill in:
- `GEMINI_API_KEY`
- `OAUTH_CLIENT_ID`, `OAUTH_CLIENT_SECRET`, `OAUTH_ALLOWED_DOMAINS` (comma-separated)
- `GOOGLE_SHEET_ID`
- Full JSON of `[gcp_service_account]`

### Local env (`.env`):
Copy from `.env.example` and set values (Streamlit will also read `st.secrets` if present).

---

## 3) Run Locally

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app/main.py
```

Open `http://localhost:8501` and log in with Google. Only emails with allowed domains can proceed.

---

## 4) Deploy on Streamlit Cloud

- Set **Main file**: `app/main.py`
- Add **App secrets** using the example in `.streamlit/secrets.toml.example`
- Add your app URL to the Google OAuth Client **Authorized redirect URIs**

---

## 5) Troubleshooting

- **Not configured page**: Ensure required secrets are provided: `GEMINI_API_KEY`, `GOOGLE_SHEET_ID`, `OAUTH_CLIENT_ID`, `OAUTH_CLIENT_SECRET`, `OAUTH_ALLOWED_DOMAINS`, and `[gcp_service_account]`.
- **Sheets write/read fails**: Confirm the **Service Account email** has **Editor** access to the workbook; confirm `GOOGLE_SHEET_ID` is correct.
- **OAuth denied**: Verify the email domain is in `OAUTH_ALLOWED_DOMAINS`. Check redirect URIs in Google Cloud.
- **Gemini errors**: Verify `GEMINI_API_KEY` and that the model is accessible in your region.

---

## 6) Makefile shortcuts

```bash
make run     # streamlit run app/main.py
make format  # black + ruff
make lint    # ruff check
make test    # pytest -q
```

---

## Data Model (Google Sheets)

The app ensures three tabs with the exact headers and order:

### `tickets`
```
id, date, requester, title, issue_type, description, links_attachments, involved_teams_people,
investigation_steps, resolution_workaround, owner, status, notes,
structured_summary_problem, structured_summary_cause, structured_summary_steps, structured_summary_resolution,
structured_summary_cross_team, compliance_score, created_by, created_at
```

### `log`
```
ticket_id, user_email, prompt, model_response, result_status, missing_sections, compliance_score, created_at
```

### `users`
```
email, name, role, active, created_at
```

---

## License

MIT
