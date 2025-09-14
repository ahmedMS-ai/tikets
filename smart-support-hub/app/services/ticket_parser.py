# file: smart-support-hub/app/services/ticket_parser.py
from __future__ import annotations
import re
from typing import Dict, List
from urllib.parse import urlparse

# --------- Utilities ---------
_URL_RE = re.compile(r"https?://\S+")
_WS = re.compile(r"[ \t]+")

def _clean(s: str) -> str:
    return _WS.sub(" ", (s or "").strip())

def _find(pattern: str, text: str, flags=re.IGNORECASE | re.MULTILINE) -> str | None:
    m = re.search(pattern, text, flags)
    return _clean(m.group(1)) if m else None

def _find_all(pattern: str, text: str, flags=re.IGNORECASE | re.MULTILINE) -> List[str]:
    return [_clean(x) for x in re.findall(pattern, text, flags)]

def _guess_issue_type(src: str) -> str:
    s = src.lower()
    if "access issue" in s or "access" in s:
        return "Access"
    if "sync" in s:
        return "Sync"
    if "enhancement" in s or "feature" in s:
        return "Enhancement"
    if "report a problem" in s or "error" in s or "bug" in s or "urgent" in s:
        return "Bug"
    if "complain" in s or "complaint" in s:
        return "Other"
    return "Other"

def _extract_id(text: str) -> str | None:
    # Try common patterns
    for pat in [
        r"\bT[_\- ]?(\d{4,})\b",             # T_2123860
        r"\bticket(?: number)?[ :#]*(\d{3,})\b",
        r"\btask(?: id)?[ :#]*(\d{3,})\b",
        r"\bjob(?: id)?[ :#]*(\d{3,})\b",
        r"\bTP[- ]?(\d{3,})\b",
    ]:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            return m.group(1)
    return None

def _extract_observers(block: str) -> List[str]:
    # Lines after "Please select observer :" until a numbered section/Created/blank
    lines = [l.strip("•- ").strip() for l in block.splitlines() if l.strip()]
    # Remove generic words
    clean = []
    for l in lines:
        if re.match(r"^\d+\)", l): break
        if l.lower().startswith("link ticket"): break
        if l.lower().startswith("created:"): break
        if l.lower().startswith("last update"): break
        clean.append(l)
    return [x for x in clean if x and len(x) < 80]

def _status_from_text(text: str) -> str:
    s = text.lower()
    if "solution approved" in s or "solved" in s or "fixed" in s or "resolved" in s:
        return "Resolved"
    return "Open"

# --------- Main parser ---------
def parse_ticket_text(raw: str) -> Dict[str, str]:
    """
    Heuristic parser for pasted ticket text (examples provided).
    Returns a dict ready to pre-fill the Streamlit form fields.
    Keys returned (all optional if not found):
      id, title, issue_type, description, links_attachments, involved_teams_people,
      requester, status, notes
    """
    text = raw or ""
    text = text.replace("\u00A0", " ").strip()

    # Title
    title = _find(r"Service Title\s*:\s*(.+)", text) or _find(r"^\s*(.+)$", text)

    # Issue type (from "Please select service type : ...")
    stype = _find(r"Please select service type\s*:\s*(.+)", text)
    issue_type = _guess_issue_type((stype or "") + " " + (title or "") + " " + text)

    # Description block (#3)
    # Capture lines after "3) Description :" until we hit "4) Attachment" or "5) Please select observer" or "Created:"
    desc = ""
    m = re.search(
        r"3\)\s*Description\s*:\s*(.+?)(?:\n\s*4\)|\n\s*5\)|\n\s*Created:|\Z)",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if m:
        desc = _clean(m.group(1))
    else:
        # fallback: take paragraph after "Description :" keyword
        m2 = re.search(r"Description\s*:\s*(.+)", text, flags=re.IGNORECASE | re.DOTALL)
        if m2:
            desc = _clean(m2.group(1))

    # Links & attachments
    urls = _URL_RE.findall(text)
    urls = list(dict.fromkeys(urls))  # dedupe, preserve order
    attaches = []
    if re.search(r"Attachment\\?s\s*:\s*Attached document", text, re.IGNORECASE):
        attaches.append("Attached document")
    if re.search(r"Attachment\\?s\s*:\s*No attached document", text, re.IGNORECASE):
        attaches.append("No attached document")
    # file lines like "File extension Screenshot ..."
    files = _find_all(r"File extension\s+(.+)", text)
    links_attachments = "; ".join(attaches + files + urls)

    # Observers → involved_teams_people
    m_obs = re.search(r"Please select observer\s*:\s*(.+?)(?:\n\s*\d+\)|\n\s*Created:|\Z)", text, re.IGNORECASE | re.DOTALL)
    observers = _extract_observers(m_obs.group(1)) if m_obs else []
    involved = "; ".join(observers)

    # Requester from first "Created: ... by NAME"
    requester = _find(r"Created:\s*.+?\s*by\s*(.+)", text)
    if requester:
        requester = requester.split("\n")[0].strip()

    # Id guesses
    id_guess = _extract_id(text)

    # Status guess
    status = _status_from_text(text)

    # Notes: keep the conversation after Description (Created: ... lines)
    convo = []
    for line in text.splitlines():
        if line.strip().lower().startswith("created:") or line.strip().lower().startswith("last update"):
            convo.append(_clean(line))
        elif line.strip().lower().startswith("link to") or line.strip().lower().startswith("link ticket"):
            convo.append(_clean(line))
    notes = "\n".join(convo[:50])

    return {
        "id": id_guess or "",
        "title": title or "",
        "issue_type": issue_type,
        "description": desc or "",
        "links_attachments": links_attachments,
        "involved_teams_people": involved,
        "requester": requester or "",
        "status": status,
        "notes": notes,
    }
