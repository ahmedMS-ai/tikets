
from __future__ import annotations
import json
from typing import Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential
import streamlit as st
import google.generativeai as genai
from app.config import load_settings
from app.services.gemini_prompts import STRICT_SYSTEM_PROMPT

def _configure_gemini():
    s = load_settings()
    if not s.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY not configured.")
    genai.configure(api_key=s.gemini_api_key)

@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=4))
def evaluate_strict(draft_text: str) -> Dict[str, Any]:
    try:
        _configure_gemini()
    except Exception:
        return {"ok": False, "message": "Model error", "missing": ["Unknown"]}

    model = genai.GenerativeModel("gemini-1.5-flash", system_instruction=STRICT_SYSTEM_PROMPT)
    try:
        resp = model.generate_content(draft_text, generation_config={
            "temperature": 0.0,
            "top_p": 0.2,
            "max_output_tokens": 800,
            "response_mime_type": "application/json",
        })
        text = getattr(resp, "text", None) or ""
        data = json.loads(text)
        # Validate minimal schema
        if "ok" not in data:
            return {"ok": False, "message": "Model error", "missing": ["Unknown"]}
        return data
    except Exception:
        return {"ok": False, "message": "Model error", "missing": ["Unknown"]}
