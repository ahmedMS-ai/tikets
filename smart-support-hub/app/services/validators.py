
from __future__ import annotations
import re

def sanitize_prompt_payload(text: str) -> str:
    # Remove obvious secrets/PII patterns in logs
    redacted = re.sub(r'[\w.+-]+@[\w-]+\.[\w.-]+', '<EMAIL>', text)
    redacted = re.sub(r'\b\+?\d[\d\s()-]{7,}\b', '<PHONE>', redacted)
    return redacted.strip()
