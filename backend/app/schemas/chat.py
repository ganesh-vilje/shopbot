from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None


class MessageOut(BaseModel):
    id: str
    role: str
    content: str
    intent: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationOut(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    messages: list[MessageOut] = []

    class Config:
        from_attributes = True


class ConversationListItem(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
