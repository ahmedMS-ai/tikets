
from __future__ import annotations
import os, json, secrets, time, base64
from urllib.parse import urlencode
import requests
from authlib.integrations.requests_client import OAuth2Session
import streamlit as st
from app.config import load_settings

GOOGLE_DISCOVERY = {
    "authorization_endpoint": "https://accounts.google.com/o/oauth2/v2/auth",
    "token_endpoint": "https://oauth2.googleapis.com/token",
    "userinfo_endpoint": "https://openidconnect.googleapis.com/v1/userinfo",
}

SCOPES = ["openid", "email", "profile"]

def _this_base_url() -> str:
    # Heuristic: Streamlit sets browser URL. Fallback to localhost.
    try:
        # In Streamlit Cloud, base can be read from request, but here we use current page.
        params = st.query_params if hasattr(st, "query_params") else {}
        # Not reliable; instruct users to add exact URL in GCP.
    except Exception:
        pass
    # Return root path; Google allows trailing slash.
    return os.getenv("OAUTH_REDIRECT_BASE", "http://localhost:8501/")

def login_button():
    s = load_settings()
    client_id = s.oauth_client_id
    if not client_id:
        st.error("OAuth not configured. Missing OAUTH_CLIENT_ID / OAUTH_CLIENT_SECRET.")
        return

    # PKCE (simple)
    code_verifier = base64.urlsafe_b64encode(os.urandom(40)).rstrip(b"=").decode("utf-8")
    st.session_state["code_verifier"] = code_verifier

    redirect_uri = _this_base_url()
    auth_url_params = dict(
        client_id=client_id,
        response_type="code",
        redirect_uri=redirect_uri,
        scope=" ".join(SCOPES),
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    url = GOOGLE_DISCOVERY["authorization_endpoint"] + "?" + urlencode(auth_url_params)
    st.link_button("Sign in with Google", url)

def handle_callback() -> dict | None:
    s = load_settings()
    if not s.oauth_client_id or not s.oauth_client_secret:
        return None

    params = st.query_params if hasattr(st, "query_params") else {}
    code = params.get("code")
    if not code:
        return None

    redirect_uri = _this_base_url()
    data = {
        "code": code,
        "client_id": s.oauth_client_id,
        "client_secret": s.oauth_client_secret,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }
    resp = requests.post(GOOGLE_DISCOVERY["token_endpoint"], data=data, timeout=15)
    if resp.status_code != 200:
        st.error("OAuth token exchange failed.")
        return None
    tok = resp.json()

    # Get userinfo
    hdr = {"Authorization": f"Bearer {tok.get('access_token')}"}
    u = requests.get(GOOGLE_DISCOVERY["userinfo_endpoint"], headers=hdr, timeout=15)
    if u.status_code != 200:
        st.error("Failed fetching user info.")
        return None
    user = u.json()
    return {
        "email": user.get("email",""),
        "name": user.get("name", user.get("email","User")),
    }

def enforce_allowlist(user: dict) -> bool:
    from app.config import load_settings
    s = load_settings()
    if not user or not user.get("email"):
        return False
    domain = user["email"].split("@")[-1].lower()
    return domain in s.oauth_allowed_domains
