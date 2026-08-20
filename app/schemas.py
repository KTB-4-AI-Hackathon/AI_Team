from datetime import datetime

from pydantic import BaseModel


class Message(BaseModel):
    speaker: str
    timestamp: datetime
    text: str


class ScoreResult(BaseModel):
    scores: dict[str, int]
    risk_components: list[str]
    evidence: dict[str, str]


class Evidence(BaseModel):
    component: str
    score: int
    summary: str


class AnalysisWarning(BaseModel):
    code: str
    message: str


class AnalysisResponse(BaseModel):
    analysisId: str
    modelVersion: str
    promptVersion: str
    processedMessageCount: int
    components: dict[str, int]
    evidences: list[Evidence]
    warnings: list[AnalysisWarning]
    completedAt: datetime


class ErrorDetail(BaseModel):
    code: str
    message: str
    retryable: bool
    requestId: str


class ErrorResponse(BaseModel):
    error: ErrorDetail
