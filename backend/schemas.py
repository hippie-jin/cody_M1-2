from datetime import date, datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class DataPointCreate(BaseModel):
    date: date
    value: float
    memo: Optional[str] = None


class DataPointUpdate(BaseModel):
    date: Optional[date] = None
    value: Optional[float] = None
    memo: Optional[str] = None


class DataPoint(BaseModel):
    id: str
    date: date
    value: float
    memo: Optional[str] = None


class SummaryMetrics(BaseModel):
    total: float
    average: float
    max: float
    min: float


class DataSummary(BaseModel):
    period: str
    count: int
    metrics: SummaryMetrics
    trend: str


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ConversationCreate(BaseModel):
    title: Optional[str] = None
    messages: List[ChatMessage]


class ConversationSummary(BaseModel):
    id: str
    title: str
    created_at: datetime
    message_count: int


class Conversation(BaseModel):
    id: str
    title: str
    created_at: datetime
    messages: List[ChatMessage]


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    reply: str
    conversation_id: str
