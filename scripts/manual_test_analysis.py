"""로컬에서 띄운 AI 서버가 실제로 잘 동작하는지 눈으로 확인하는 수동 테스트 스크립트.

사용법:
  1) 터미널 1: uvicorn app.main:app --reload --port 8000
  2) 터미널 2: python scripts/manual_test_analysis.py
"""

import gzip
import hashlib
import json
import os

import httpx
from dotenv import load_dotenv

load_dotenv()

SERVER_URL = "http://localhost:8000/internal/v1/prqc-analyses"

# 원하는 대화로 바꿔서 테스트해봐도 됩니다.
SAMPLE_CONVERSATION = [
    {"sender": "OTHER", "sentAt": "2026-08-10T10:20:00+09:00", "text": "오늘 하루 어땠어? 아침에 비 와서 걱정했는데"},
    {"sender": "SELF", "sentAt": "2026-08-10T10:22:00+09:00", "text": "ㅋㅋㅋ 챙겨줘서 고마워! 우산 챙겨서 괜찮았어"},
    {"sender": "OTHER", "sentAt": "2026-08-10T10:23:00+09:00", "text": "다행이다 ㅎㅎ 이번 주말에 같이 그 영화 볼래? 계속 기대하고 있었잖아"},
    {"sender": "SELF", "sentAt": "2026-08-10T10:25:00+09:00", "text": "완전 좋지! 나도 진짜 기대하고 있었어 ㅎㅎ 끝나고 맛있는 것도 먹자"},
    {"sender": "OTHER", "sentAt": "2026-08-10T10:26:00+09:00", "text": "역시 잘 통한다니까 ㅋㅋ 요즘 힘든 일 있으면 언제든 얘기해도 돼"},
    {"sender": "SELF", "sentAt": "2026-08-10T10:28:00+09:00", "text": "고마워 진짜. 너랑 얘기하면 항상 마음이 편해져"},
]


def main() -> None:
    lines = [json.dumps(m, ensure_ascii=False) for m in SAMPLE_CONVERSATION]
    payload = gzip.compress("\n".join(lines).encode("utf-8"))
    sha256 = hashlib.sha256(payload).hexdigest()

    token = os.environ["AI_INTERNAL_SERVICE_TOKEN"]

    response = httpx.post(
        SERVER_URL,
        headers={
            "Authorization": f"Bearer {token}",
            "X-Request-Id": "manual-test-1",
            "Idempotency-Key": "manual-test-1",
        },
        data={
            "analysisId": "manual-test-1",
            "relationshipType": "FRIEND",
            "format": "NORMALIZED_NDJSON_GZIP",
            "formatVersion": "conversation-ndjson-1.0.0",
            "sha256": sha256,
        },
        files={"file": ("conversation.ndjson.gz", payload, "application/gzip")},
        timeout=60,
    )

    print(f"상태 코드: {response.status_code}\n")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
