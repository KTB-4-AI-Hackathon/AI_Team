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
    self_report_comparison: str


class Metric(BaseModel):
    name: str
    currentValue: float
    previousValue: float | None
    unit: str
    period: str


class Evidence(BaseModel):
    component: str
    score: int
    summary: str
    metric: Metric | None = None


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


class ConsultationEvidenceContext(BaseModel):
    evidenceId: str
    component: str
    score: int
    summary: str


class ConsultationHistoryMessage(BaseModel):
    role: str
    content: str


class ConsultationAnswerRequest(BaseModel):
    reportId: str
    overallScore: int
    scoreChange: int | None = None
    prqc: dict[str, int]
    evidences: list[ConsultationEvidenceContext]
    recentMessages: list[ConsultationHistoryMessage]
    userMessage: str


class ConsultationEvidenceReference(BaseModel):
    evidenceId: str
    label: str


class ConsultationResourceQuery(BaseModel):
    category: str
    region: str = "KR"


class ConsultationSafetyNotice(BaseModel):
    type: str
    title: str
    message: str
    resourceQuery: ConsultationResourceQuery


class ConsultationAnswerResponse(BaseModel):
    content: str
    evidenceRefs: list[ConsultationEvidenceReference]
    safetyNotice: ConsultationSafetyNotice | None


class ErrorDetail(BaseModel):
    code: str
    message: str
    retryable: bool
    requestId: str
    details: dict | None = None


class ErrorResponse(BaseModel):
    error: ErrorDetail
