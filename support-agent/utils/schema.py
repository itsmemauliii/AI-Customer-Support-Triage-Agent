from pydantic import BaseModel
from typing import Literal


class TriageResult(BaseModel):
    urgency: Literal["low", "medium", "high"]
    category: str
    sentiment: Literal["calm", "neutral", "angry"]
    suggested_reply: str
    escalate: bool
    confidence: float
