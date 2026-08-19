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
    {"sender": "OTHER", "sentAt": "2026-08-10T10:20:00+09:00", "text": "요즘 왜 이렇게 연락이 뜸해?"},
    {"sender": "SELF", "sentAt": "2026-08-10T14:40:00+09:00", "text": "어 미안 요즘 좀 바빴어"},
    {"sender": "OTHER", "sentAt": "2026-08-10T14:41:00+09:00", "text": "맨날 바쁘다고만 하고... 나랑 만나는 거 귀찮은 거 아니야?"},
    {"sender": "SELF", "sentAt": "2026-08-10T15:10:00+09:00", "text": "그런거 아니야 진짜 일이 많아서 그래"},
    {"sender": "OTHER", "sentAt": "2026-08-11T09:00:00+09:00", "text": "됐어 신경쓰지마"},
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
