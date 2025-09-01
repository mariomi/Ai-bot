from pydantic import BaseModel, Field
from typing import List, Optional

class QueryRequest(BaseModel):
    question: str
    k: int = 8
    mailbox_upn: Optional[str] = None
    since_iso: Optional[str] = None
    until_iso: Optional[str] = None

class SummarizeRequest(BaseModel):
    scope: str = "last_24h"
    k: int = 20
    instruction: str = "Riassumi in 8 bullet azionabili."

class AssistantChatRequest(BaseModel):
    upn: Optional[str] = None
    message: str
    k_email: int = 6
    k_kb: int = 6

class TaskCreate(BaseModel):
    upn: str
    title: str
    due_at: Optional[str] = None
    priority: str = Field(default="medium")
