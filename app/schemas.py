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


class AnalysisResponse(BaseModel):
    analysisId: str
    modelVersion: str
    components: dict[str, int]
    evidences: list[Evidence]
