from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class RelationshipType(str, Enum):
    ROMANTIC = 'ROMANTIC'
    FRIEND = 'FRIEND'
    FAMILY = 'FAMILY'
    COLLEAGUE = 'COLLEAGUE'
    OTHER = 'OTHER'


class User(BaseModel):
    id: int
    name: str
    nickname: str


class Chat(BaseModel):
    date: datetime
    name: str
    message: str


class AnalysisRequest(BaseModel):
    user: User
    relationship_type: RelationshipType
    chats: list[Chat]


class PrqcComponentScore(BaseModel):
    score: int = Field(ge=1, le=7, description='PRQC 구성요소 1개에 대한 7점 척도 점수')
    evidence: list[str] = Field(description='점수 판단 근거 (대화 원문이 아닌 요약된 근거 문장)')


class PrqcScores(BaseModel):
    satisfaction: PrqcComponentScore
    commitment: PrqcComponentScore
    intimacy: PrqcComponentScore
    trust: PrqcComponentScore
    passion: PrqcComponentScore
    love: PrqcComponentScore


class AnalysisResponse(BaseModel):
    prqc_scores: PrqcScores
    completed_at: datetime


# DAS-4 절단점(11/21)을 7점 척도로 환산한 위험 기준선. 관계 유형과 무관하게 고정된 상수.
PRQC_CUTOFF_REFERENCE: float = 4.0