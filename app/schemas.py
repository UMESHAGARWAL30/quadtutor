from pydantic import BaseModel
from typing import Optional, Literal

class Whiteboard(BaseModel):
    action: Literal["add", "replace", "clear"]
    content: str
    highlight: Optional[str] = None

class TutorTurn(BaseModel):
    extracted_answer: Optional[str] = None
    intent: Literal["answer", "confused", "off_topic"]
    is_correct: Optional[bool] = None
    decision: Literal["advance", "reteach", "clarify"]
    reason: str
    speak: str
    whiteboard: Whiteboard