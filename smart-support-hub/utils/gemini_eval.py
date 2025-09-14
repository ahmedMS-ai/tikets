
import os, json, time
from typing import Dict, Any, List
from tenacity import retry, stop_after_attempt, wait_exponential

def _get_api_key_and_model():
    api_key = None
    model = None
    try:
        import streamlit as st
        api_key = st.secrets.get("GEMINI", {}).get("api_key")
        model = st.secrets.get("GEMINI", {}).get("model", "gemini-1.5-flash")
    except Exception:
        pass
    api_key = api_key or os.getenv("GEMINI_API_KEY")
    model = model or os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    if not api_key:
        raise RuntimeError("Gemini API key not found. Provide via Streamlit secret GEMINI.api_key or env GEMINI_API_KEY.")
    return api_key, model

SYSTEM_PROMPT = """
You are a STRICT support-response evaluator for a Translation Management System (TMS) vendor.
Score the proposed draft resolution against a rubric with clear criteria and weights.
Output ONLY a JSON object matching this schema:

{
  "raw_score": 0-100,
  "verdict": "PASS" | "FAIL",
  "rationale": "string",
  "failures": ["criterion1: reason", ...]
}

Rules:
- If reproduction steps or root cause are missing -> automatic FAIL.
- If any suggested step violates data-security or customer policy -> automatic FAIL.
- If the draft omits customer communications or SLA handling for S0/S1 -> heavy penalty.
- Fail if hallucinations (fabricated logs/IDs) are detected.
Be concise, objective, and harsh.
"""

EVAL_TEMPLATE = """
### Context
- Severity: {severity}
- Locale: {locale}
- Product: {product}
- Module: {module}

### Ticket
{ticket}

### Draft Response to Evaluate
{draft}

### Rubric (YAML)
{rubric}
"""

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
def evaluate_with_gemini(ticket: str, draft: str, rubric_yaml: str, severity: str, locale: str, product: str, module: str) -> Dict[str, Any]:
    api_key, model_name = _get_api_key_and_model()
    import google.generativeai as genai
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name, system_instruction=SYSTEM_PROMPT)
    prompt = EVAL_TEMPLATE.format(severity=severity, locale=locale, product=product, module=module, ticket=ticket, draft=draft, rubric=rubric_yaml)

    t0 = time.time()
    resp = model.generate_content(prompt, generation_config={
        "temperature": 0.1,
        "top_p": 0.3,
        "top_k": 32,
        "max_output_tokens": 1024,
        "response_mime_type": "application/json",
    })
    latency_ms = int((time.time() - t0) * 1000)

    text = resp.text if hasattr(resp, "text") else (resp.candidates[0].content.parts[0].text if resp.candidates else "{}")
    try:
        data = json.loads(text)
    except Exception:
        # attempt to extract JSON
        import re
        m = re.search(r"\{[\s\S]*\}", text)
        data = json.loads(m.group(0)) if m else {"raw_score": 0, "verdict": "FAIL", "rationale": "Non-JSON response", "failures": ["format"]}

    out = {
        "raw_score": float(data.get("raw_score", 0)),
        "verdict": str(data.get("verdict", "FAIL")).upper(),
        "rationale": data.get("rationale", ""),
        "failures": data.get("failures", []),
        "model": model_name,
        "latency_ms": latency_ms,
    }
    out["passed"] = out["verdict"] == "PASS"
    return out
