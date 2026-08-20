"""상담챗봇 엔드포인트를 실행 중인 서버에 직접 요청해서 눈으로 확인하는 스크립트.

사용법:
  1) 터미널 1: uvicorn app.main:app --reload --port 8000
  2) 터미널 2: python scripts/manual_test_consultation.py

USER_MESSAGE만 바꿔서 재실행하면 바로 다른 질문으로 테스트할 수 있습니다.
HISTORY는 실제로 문제가 됐던 대화 흐름(문구 추천 요청 직전까지)을 넣어뒀어요.
"""

import json
import os

import httpx
from dotenv import load_dotenv

load_dotenv()

SERVER_URL = "http://localhost:8000/internal/v1/consultation-answers"

# 여기만 바꿔서 다시 실행해보세요.
USER_MESSAGE = "너가 결정해서 얘기해줘"

HISTORY = [
    {"role": "USER", "content": "대답을 너무 성의 없게해"},
    {"role": "ASSISTANT", "content": "(공감 + 관찰된 패턴 + 선택 위임)"},
    {"role": "USER", "content": "요즘 대화가 눈에 띄게 줄어든 것 같아"},
    {"role": "ASSISTANT", "content": "(공감 + 관찰된 패턴 + 선택 위임)"},
    {"role": "USER", "content": "이 관계 계속 유지해도 될까?"},
    {"role": "ASSISTANT", "content": "(공감 + 관찰된 패턴 + 선택 위임)"},
    {"role": "USER", "content": "요즘 좀 나아진 것 같아"},
    {"role": "ASSISTANT", "content": "(긍정 반응 + 선택 위임)"},
    {"role": "USER", "content": "그럼 오랜만에 연락하는 동생한테 뭐라고 연락을 보내는게 좋을까?"},
    {
        "role": "ASSISTANT",
        "content": (
            "오랫동안 연락이 뜸했던 동생에게 보낼 메시지라면, 부담스럽지 않으면서도 "
            "따뜻한 안부를 묻는 내용이 좋아요. 이렇게 보내보세요.\n\n"
            "\"OO야, 잘 지내고 있지? 문득 네 생각이 나서 연락해 봤어. 바쁘겠지만 시간 날 때 "
            "가볍게 안부 전해줘!\""
        ),
    },
]

REQUEST_BODY = {
    "reportId": "manual-consult-1",
    "overallScore": 42,
    "prqc": {
        "satisfaction": 45,
        "commitment": 40,
        "intimacy": 35,
        "trust": 50,
        "passion": 40,
        "love": 45,
    },
    "evidences": [
        {
            "evidenceId": "e1",
            "component": "passion",
            "score": 40,
            "summary": "최근 2주간 답장이 평균 24시간 이상 걸림",
        },
        {
            "evidenceId": "e2",
            "component": "commitment",
            "score": 40,
            "summary": "지난 3번의 약속 중 2번이 취소됨",
        },
    ],
    "recentMessages": HISTORY,
    "userMessage": USER_MESSAGE,
}


def main() -> None:
    token = os.environ["AI_INTERNAL_SERVICE_TOKEN"]

    response = httpx.post(
        SERVER_URL,
        headers={
            "Authorization": f"Bearer {token}",
            "X-Request-Id": "manual-consult-1",
        },
        json=REQUEST_BODY,
        timeout=60,
    )

    print(f"상태 코드: {response.status_code}\n")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()