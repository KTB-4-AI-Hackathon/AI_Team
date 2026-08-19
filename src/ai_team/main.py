from fastapi import FastAPI, HTTPException

from ai_team.client_anthropic import score_all_components_anthropic
from ai_team.schema import AnalysisRequest, AnalysisResponse, Chat

app = FastAPI()


def classify_speaker(chats: list[Chat], user_nickname: str) -> list[tuple[Chat, str]]:
    """chat.name과 user.nickname을 비교해 본인/상대방 발화를 구분한다."""
    classified: list[tuple[Chat, str]] = []
    for chat in chats:
        speaker = 'user' if chat.name == user_nickname else 'person'
        classified.append((chat, speaker))
    return classified


@app.post('/api/analysis/prqc', response_model=AnalysisResponse)
def analyze_prqc(request: AnalysisRequest) -> AnalysisResponse:
    if not request.chats:
        raise HTTPException(status_code=400, detail='chats가 비어 있습니다.')

    try:
        classified_chats = classify_speaker(request.chats, request.user.nickname)
    except Exception:
        raise HTTPException(status_code=400, detail='발화자 구분에 실패했습니다.')

    try:
        result = score_all_components_anthropic(
            chats=classified_chats,
            relationship_type=request.relationship_type,
        )
    except Exception:
        raise HTTPException(status_code=502, detail='채점 처리에 실패했습니다.')

    return result