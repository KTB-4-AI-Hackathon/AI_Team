from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


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
    selfReportComparison: str
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


class CheckInAnswerContext(StrictModel):
    questionCode: Literal["RELATIONSHIP_FEELING", "CONVERSATION_COMFORT"]
    score: int = Field(ge=1, le=7)


class AnalysisCheckInContext(StrictModel):
    checkInId: UUID
    weekStart: date
    inputAt: datetime
    answers: list[CheckInAnswerContext] = Field(min_length=1)


class AnalysisUserContext(StrictModel):
    userId: UUID
    displayName: str = Field(min_length=1, max_length=100)
    timezone: str = Field(min_length=1, max_length=50)


class AnalysisRelationshipContext(StrictModel):
    relationshipId: UUID
    name: str = Field(min_length=1, max_length=100)
    relationshipType: Literal["ROMANTIC_PARTNER", "FRIEND", "FAMILY", "COWORKER", "OTHER"]
    status: str = Field(min_length=1)


class CurrentAnalysisContext(StrictModel):
    conversationFileId: UUID
    checkIn: AnalysisCheckInContext


class HistoricalConversationMessage(StrictModel):
    sender: Literal["SELF", "OTHER"]
    sentAt: datetime
    text: str = Field(min_length=1, max_length=20000)


class HistoricalConversationContext(StrictModel):
    conversationFileId: UUID
    messages: list[HistoricalConversationMessage]


class HistoricalEvidence(StrictModel):
    component: Literal["satisfaction", "commitment", "intimacy", "trust", "passion", "love"]
    score: int = Field(ge=0, le=100)
    summary: str = Field(min_length=1, max_length=1000)
    metric: Metric | None = None


class PrqcScoresContext(StrictModel):
    satisfaction: int = Field(ge=0, le=100)
    commitment: int = Field(ge=0, le=100)
    intimacy: int = Field(ge=0, le=100)
    trust: int = Field(ge=0, le=100)
    passion: int = Field(ge=0, le=100)
    love: int = Field(ge=0, le=100)


class PreviousAnalysisContext(StrictModel):
    reportId: UUID
    analyzedAt: datetime
    overallScore: int = Field(ge=0, le=100)
    scoreChange: int | None = Field(default=None, ge=-100, le=100)
    prqc: PrqcScoresContext
    evidences: list[HistoricalEvidence] = Field(min_length=1, max_length=12)


class HistoricalAnalysisContext(StrictModel):
    inputAt: datetime
    conversation: HistoricalConversationContext
    checkIn: AnalysisCheckInContext
    analysis: PreviousAnalysisContext


class AnalysisContext(StrictModel):
    user: AnalysisUserContext
    relationship: AnalysisRelationshipContext
    current: CurrentAnalysisContext
    history: list[HistoricalAnalysisContext]

    @model_validator(mode="after")
    def history_is_chronological(self):
        input_times = [item.inputAt for item in self.history]
        if input_times != sorted(input_times):
            raise ValueError("history must be ordered by inputAt ascending")
        if any(item.inputAt != item.checkIn.inputAt for item in self.history):
            raise ValueError("history inputAt must match the entry checkIn.inputAt")
        return self
