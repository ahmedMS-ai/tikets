
from __future__ import annotations

DEFAULT_ROLE = "agent"
ADMIN_ROLE = "lead"

def can_view_dashboard(role: str) -> bool:
    return role in (ADMIN_ROLE, DEFAULT_ROLE)

def can_admin(role: str) -> bool:
    return role == ADMIN_ROLE
