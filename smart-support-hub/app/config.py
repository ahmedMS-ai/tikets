
from __future__ import annotations
import os, json
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

try:
    import streamlit as st
except Exception:  # fallback during tests
    class _Dummy:
        secrets = {}
    st = _Dummy()

load_dotenv(override=False)

def _get_secret(key: str, default: Optional[str] = None) -> Optional[str]:
    # Prefer Streamlit secrets, fallback to env
    try:
        val = st.secrets.get(key)
        if isinstance(val, (str, int, float)):
            return str(val)
    except Exception:
        pass
    return os.getenv(key, default)

def _get_nested_secret(section: str, key: str) -> Optional[str]:
    try:
        sec = st.secrets.get(section, {})
        if isinstance(sec, dict):
            v = sec.get(key)
            return None if v is None else str(v)
    except Exception:
        pass
    return None

def get_sa_info() -> Optional[Dict[str, Any]]:
    # Only from Streamlit secrets (recommended). Fallback to env var containing full JSON text.
    try:
        info = st.secrets.get("gcp_service_account", None)
        if isinstance(info, dict):
            return dict(info)
    except Exception:
        pass
    sa_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "")
    if sa_json:
        try:
            return json.loads(sa_json)
        except Exception:
            return None
    return None

@dataclass
class Settings:
    gemini_api_key: Optional[str]
    oauth_client_id: Optional[str]
    oauth_client_secret: Optional[str]
    oauth_allowed_domains: List[str]
    google_sheet_id: Optional[str]
    gcp_service_account: Optional[Dict[str, Any]]

def load_settings() -> Settings:
    allowed = _get_secret("OAUTH_ALLOWED_DOMAINS", "gmail.com")
    domains = [d.strip().lower() for d in (allowed or "").split(",") if d.strip()]
    return Settings(
        gemini_api_key=_get_secret("GEMINI_API_KEY"),
        oauth_client_id=_get_secret("OAUTH_CLIENT_ID"),
        oauth_client_secret=_get_secret("OAUTH_CLIENT_SECRET"),
        oauth_allowed_domains=domains or ["gmail.com"],
        google_sheet_id=_get_secret("GOOGLE_SHEET_ID"),
        gcp_service_account=get_sa_info(),
    )

def missing_keys(s: Settings) -> list[str]:
    missing = []
    if not s.oauth_client_id: missing.append("OAUTH_CLIENT_ID")
    if not s.oauth_client_secret: missing.append("OAUTH_CLIENT_SECRET")
    if not s.gemini_api_key: missing.append("GEMINI_API_KEY")
    if not s.google_sheet_id: missing.append("GOOGLE_SHEET_ID")
    if not s.gcp_service_account: missing.append("gcp_service_account (service account JSON)")
    return missing
