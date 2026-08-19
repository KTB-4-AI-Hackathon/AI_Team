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


class Metric(BaseModel):
    name: str
    currentValue: float
    previousValue: float
    unit: str
    period: str


class Evidence(BaseModel):
    component: str
    score: int
    summary: str
    metric: Metric | None = None


class RelationshipContext(BaseModel):
    relationshipType: str
    analyzedAt: datetime
    overallScore: int
    components: dict[str, int]
    evidences: list[Evidence]


class AnalysisResponse(BaseModel):
    analysisId: str
    modelVersion: str
    promptVersion: str
    processedMessageCount: int
    components: dict[str, int]
    evidences: list[Evidence]
    warnings: list[str]
    completedAt: datetime


class ConsultationMessage(BaseModel):
    role: str
    content: str


class ConsultationRequest(BaseModel):
    consultationId: str
    userMessage: str
    history: list[ConsultationMessage] = []
    relationshipContext: RelationshipContext


class ConsultationResponse(BaseModel):
    consultationId: str
    reply: str
    safetyType: str | None
    completedAt: datetime


class ErrorDetail(BaseModel):
    code: str
    message: str
    retryable: bool
    requestId: str


class ErrorResponse(BaseModel):
    error: ErrorDetail
