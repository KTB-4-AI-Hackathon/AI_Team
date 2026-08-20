from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import Field, model_validator

from app.schemas.common import PRQC_COMPONENT, Message, Metric, StrictModel


class ScoreResult(StrictModel):
    scores: dict[str, int]
    risk_components: list[str]
    evidence: dict[str, str]
    self_report_comparison: str


class Evidence(StrictModel):
    component: PRQC_COMPONENT
    score: int
    summary: str
    metric: Metric | None = None


class AnalysisWarning(StrictModel):
    code: Literal["LIMITED_DATE_RANGE", "LOW_MESSAGE_COUNT", "NO_STRUCTURED_EVIDENCE", "PARTIAL_ANALYSIS"]
    message: str


class AnalysisResponse(StrictModel):
    analysisId: str
    modelVersion: str
    promptVersion: str
    processedMessageCount: int
    components: dict[str, int]
    evidences: list[Evidence]
    warnings: list[AnalysisWarning]
    selfReportComparison: str
    completedAt: datetime


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
    component: PRQC_COMPONENT
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