# file: smart-support-hub/app/services/ticket_parser.py
from __future__ import annotations
import re
from typing import Dict, List

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
    for pat in [
        r"\bT[_\- ]?(\d{4,})\b",  # T_2123860
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
    lines = [l.strip("•- ").strip() for l in block.splitlines() if l.strip()]
    clean = []
    for l in lines:
        if re.match(r"^\d+\)", l):
            break
        if l.lower().startswith(("link ticket", "created:", "last update")):
            break
        clean.append(l)
    return [x for x in clean if x and len(x) < 80]


def _status_from_text(text: str) -> str:
    s = text.lower()
    if any(x in s for x in ("solution approved", "solved", "fixed", "resolved")):
        return "Resolved"
    return "Open"


def parse_ticket_text(raw: str) -> Dict[str, str]:
    """
    Parse pasted ticket block into our form fields.
    Returns keys (optional if not found):
    id, title, issue_type, description, links_attachments, involved_teams_people,
    requester, status, notes
    """
    text = (raw or "").replace("\u00A0", " ").strip()

    title = _find(r"Service Title\s*:\s*(.+)", text) or _find(r"^\s*(.+)$", text)

    stype = _find(r"Please select service type\s*:\s*(.+)", text)
    issue_type = _guess_issue_type((stype or "") + " " + (title or "") + " " + text)

    m = re.search(
        r"3\)\s*Description\s*:\s*(.+?)(?:\n\s*4\)|\n\s*5\)|\n\s*Created:|\Z)",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if m:
        desc = _clean(m.group(1))
    else:
        m2 = re.search(r"Description\s*:\s*(.+)", text, flags=re.IGNORECASE | re.DOTALL)
        desc = _clean(m2.group(1)) if m2 else ""

    urls = list(dict.fromkeys(_URL_RE.findall(text)))
    attaches = []
    if re.search(r"Attachment\\?s\s*:\s*Attached document", text, re.IGNORECASE):
        attaches.append("Attached document")
    if re.search(r"Attachment\\?s\s*:\s*No attached document", text, re.IGNORECASE):
        attaches.append("No attached document")
    files = _find_all(r"File extension\s+(.+)", text)
    links_attachments = "; ".join(attaches + files + urls)

    m_obs = re.search(
        r"Please select observer\s*:\s*(.+?)(?:\n\s*\d+\)|\n\s*Created:|\Z)",
        text,
        re.IGNORECASE | re.DOTALL,
    )
    observers = _extract_observers(m_obs.group(1)) if m_obs else []
    involved = "; ".join(observers)

    requester = _find(r"Created:\s*.+?\s*by\s*(.+)", text)
    if requester:
        requester = requester.split("\n")[0].strip()

    id_guess = _extract_id(text)
    status = _status_from_text(text)

    convo = []
    for line in text.splitlines():
        low = line.strip().lower()
        if low.startswith(("created:", "last update", "link to", "link ticket")):
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
