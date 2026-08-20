"""상담챗봇 엔드포인트를 실행 중인 서버에 직접 요청해서 눈으로 확인하는 스크립트.

사용법:
  1) 터미널 1: uvicorn app.main:app --reload --port 8000
  2) 터미널 2: python scripts/manual_test_consultation.py
"""

import json
import os

import httpx
from dotenv import load_dotenv

load_dotenv()

SERVER_URL = "http://localhost:8000/internal/v1/consultation-answers"

REQUEST_BODY = {
    "reportId": "manual-consult-1",
    "overallScore": 45,
    "prqc": {
        "satisfaction": 33,
        "commitment": 17,
        "intimacy": 33,
        "trust": 50,
        "passion": 17,
        "love": 33,
    },
    "evidences": [
        {
            "evidenceId": "e1",
            "component": "commitment",
            "score": 17,
            "summary": "상대방이 먼저 연락하는 경우가 거의 없음",
        },
        {
            "evidenceId": "e2",
            "component": "passion",
            "score": 17,
            "summary": "대화 반응 속도가 지속적으로 느림",
        },
    ],
    "recentMessages": [],
    "userMessage": "이 친구랑 계속 연락해야 할지 모르겠어요. 항상 제가 먼저 연락해요.",
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