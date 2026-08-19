from fastapi import FastAPI, HTTPException

from ai_team.schema import AnalysisRequest, AnalysisResponse, Chat, PrqcComponentScore, RelationshipType

app = FastAPI()


def classify_speaker(chats: list[Chat], user_nickname: str) -> list[tuple[Chat, str]]:
    """chat.name과 user.nickname을 비교해 본인/상대방 발화를 구분한다."""
    classified: list[tuple[Chat, str]] = []
    for chat in chats:
        speaker = 'user' if chat.name == user_nickname else 'person'
        classified.append((chat, speaker))
    return classified


def score_all_components(chats: list[Chat], relationship_type: RelationshipType) -> AnalysisResponse:
    """
    TODO: client.py 완성되면 이 함수를 client.score_all_components로 교체.
    현재는 워킹 스켈레톤 확인을 위한 stub이며, 고정값을 반환한다.
    """
    dummy_score = PrqcComponentScore(score=4, evidence=['stub: 실제 채점 로직 미구현'])
    return AnalysisResponse(
        satisfaction=dummy_score,
        commitment=dummy_score,
        intimacy=dummy_score,
        trust=dummy_score,
        passion=dummy_score,
        love=dummy_score,
    )


@app.post('/api/analysis/prqc', response_model=AnalysisResponse)
def analyze_prqc(request: AnalysisRequest) -> AnalysisResponse:
    if not request.chats:
        raise HTTPException(status_code=400, detail='chats가 비어 있습니다.')

    try:
        classified_chats = classify_speaker(request.chats, request.user.nickname)
    except Exception:
        raise HTTPException(status_code=400, detail='발화자 구분에 실패했습니다.')

    try:
        result = score_all_components(
            chats=[chat for chat, _ in classified_chats],
            relationship_type=request.relationship_type,
        )
    except Exception:
        raise HTTPException(status_code=502, detail='채점 처리에 실패했습니다.')

    return result