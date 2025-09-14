
from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional

class User(BaseModel):
    email: str
    name: str
    role: str = "agent"
    active: bool = True

class EvalResult(BaseModel):
    ok: bool
    message: Optional[str] = None
    compliance_score: Optional[int] = None
    summary: Optional[dict] = None
    missing: Optional[list[str]] = None
