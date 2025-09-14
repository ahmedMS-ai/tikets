
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime

class Ticket(BaseModel):
    ticket_id: str = Field(..., description="Client-provided or auto-generated ticket ID")
    title: str
    description: str
    severity: str = Field(..., description="S0/S1/S2/S3")
    product: str = ""
    module: str = ""
    locale: str = "en"
    reporter: str = ""
    attachments: List[str] = []
    status: str = "New"

class Evaluation(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    ticket_id: str
    draft_len: int
    rubric_version: str = "v1"
    model: str = ""
    raw_score: float
    passed: bool
    verdict: str
    rationale: str
    failures: List[str] = []
    evaluator_latency_ms: Optional[int] = None
