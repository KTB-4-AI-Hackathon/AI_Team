from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


PRQC_COMPONENT = Literal["satisfaction", "commitment", "intimacy", "trust", "passion", "love"]

ERROR_CODE = Literal[
    "INVALID_REQUEST",
    "AUTH_REQUIRED",
    "FORBIDDEN",
    "CONVERSATION_NOT_ACCESSIBLE",
    "IDEMPOTENCY_KEY_REUSED",
    "INSUFFICIENT_MESSAGES",
    "INVALID_CONVERSATION_DATA",
    "AI_RATE_LIMITED",
    "AI_INTERNAL_ERROR",
    "AI_PROVIDER_UNAVAILABLE",
    "AI_TIMEOUT",
]


class Message(StrictModel):
    speaker: str
    timestamp: datetime
    text: str


class Metric(StrictModel):
    name: str
    currentValue: float
    previousValue: float | None
    unit: str
    period: str


class ErrorDetail(StrictModel):
    code: ERROR_CODE
    message: str
    retryable: bool
    requestId: str
    details: dict | None = None


class ErrorResponse(StrictModel):
    error: ErrorDetail