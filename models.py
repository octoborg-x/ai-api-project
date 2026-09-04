from typing import Literal
from pydantic import BaseModel


class ChatRequest(BaseModel):
    prompt: str


class ChatResponse(BaseModel):
    response: str
    prompt_tokens: int
    completion_tokens: int


class TicketExtraction(BaseModel):
    summary: str
    category: Literal["billing", "technical", "account", "other"]
    urgency: Literal["low", "medium", "high"]
    customer_sentiment: Literal["positive", "neutral", "negative"]
