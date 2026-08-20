from typing import Literal

from app.schemas.common import PRQC_COMPONENT, StrictModel


class ConsultationEvidenceContext(StrictModel):
    evidenceId: str
    component: PRQC_COMPONENT
    score: int
    summary: str


class ConsultationHistoryMessage(StrictModel):
    role: Literal["USER", "ASSISTANT"]
    content: str


class ConsultationAnswerRequest(StrictModel):
    reportId: str
    overallScore: int
    scoreChange: int | None = None
    prqc: dict[str, int]
    evidences: list[ConsultationEvidenceContext]
    recentMessages: list[ConsultationHistoryMessage]
    userMessage: str


class ConsultationEvidenceReference(StrictModel):
    evidenceId: str
    label: str


class ConsultationResourceQuery(StrictModel):
    category: Literal["MENTAL_HEALTH_COUNSELING", "RELATIONSHIP_COUNSELING", "CRISIS_SUPPORT"]
    region: str = "KR"


class ConsultationSafetyNotice(StrictModel):
    type: Literal["CRISIS_SUPPORT", "SUPPORT_RECOMMENDATION"]
    title: str
    message: str
    resourceQuery: ConsultationResourceQuery


class ConsultationAnswerResponse(StrictModel):
    content: str
    evidenceRefs: list[ConsultationEvidenceReference]
    safetyNotice: ConsultationSafetyNotice | None