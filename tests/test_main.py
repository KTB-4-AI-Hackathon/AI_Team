import gzip
import hashlib
import json

from fastapi.testclient import TestClient

from app.main import app, get_llm_client


def _gzip_ndjson_fixture() -> bytes:
    lines = [
        json.dumps(
            {"sender": "OTHER", "sentAt": "2026-08-17T10:20:00+09:00", "text": "안녕"}
        ),
        json.dumps(
            {"sender": "SELF", "sentAt": "2026-08-17T10:21:00+09:00", "text": "어 안녕"}
        ),
    ]
    return gzip.compress("\n".join(lines).encode("utf-8"))


def _headers(**overrides) -> dict[str, str]:
    base = {
        "Authorization": "Bearer test-token",
        "X-Request-Id": "req_1",
        "Idempotency-Key": "a1",
    }
    base.update(overrides)
    return base


def _form_data(sha256: str, **overrides) -> dict[str, str]:
    base = {
        "analysisId": "a1",
        "relationshipType": "FRIEND",
        "format": "NORMALIZED_NDJSON_GZIP",
        "formatVersion": "conversation-ndjson-1.0.0",
        "sha256": sha256,
        "context": json.dumps(_analysis_context()),
    }
    base.update(overrides)
    return base


def _analysis_context() -> dict:
    return {
        "user": {
            "userId": "0198c8a7-3000-7000-8000-000000000002",
            "displayName": "우",
            "timezone": "Asia/Seoul",
        },
        "relationship": {
            "relationshipId": "0198c8a7-3000-7000-8000-000000000003",
            "name": "민지",
            "relationshipType": "FRIEND",
            "status": "ANALYZING",
        },
        "current": {
            "conversationFileId": "0198c8a7-3000-7000-8000-000000000004",
            "checkIn": {
                "checkInId": "0198c8a7-3000-7000-8000-000000000005",
                "weekStart": "2026-08-17",
                "inputAt": "2026-08-17T01:00:00Z",
                "answers": [{"questionCode": "RELATIONSHIP_FEELING", "score": 6}],
            },
        },
        "history": [
            {
                "inputAt": "2026-08-10T01:00:00Z",
                "conversation": {
                    "conversationFileId": "0198c8a7-3000-7000-8000-000000000006",
                    "messages": [
                        {"sender": "SELF", "sentAt": "2026-08-09T12:00:00Z", "text": "지난 대화"}
                    ],
                },
                "checkIn": {
                    "checkInId": "0198c8a7-3000-7000-8000-000000000007",
                    "weekStart": "2026-08-10",
                    "inputAt": "2026-08-10T01:00:00Z",
                    "answers": [{"questionCode": "RELATIONSHIP_FEELING", "score": 4}],
                },
                "analysis": {
                    "reportId": "0198c8a7-3000-7000-8000-000000000008",
                    "analyzedAt": "2026-08-10T01:02:00Z",
                    "overallScore": 58,
                    "scoreChange": -7,
                    "prqc": {
                        "satisfaction": 55,
                        "commitment": 56,
                        "intimacy": 57,
                        "trust": 58,
                        "passion": 59,
                        "love": 60,
                    },
                    "evidences": [
                        {"component": "trust", "score": 58, "summary": "응답 간격이 길어졌어요.", "metric": None}
                    ],
                },
            }
        ],
    }


class _FakeLLMClient:
    def invoke(self, langchain_messages):
        class _Response:
            content = json.dumps(
                {
                    "Satisfaction": 6,
                    "Commitment": 6,
                    "Intimacy": 6,
                    "Trust": 6,
                    "Passion": 6,
                    "Love": 6,
                    "evidence": {},
                }
            )

        return _Response()


def test_returns_analysis_response_for_authenticated_valid_request(monkeypatch):
    monkeypatch.setenv("AI_INTERNAL_SERVICE_TOKEN", "test-token")
    app.dependency_overrides[get_llm_client] = lambda: _FakeLLMClient()
    client = TestClient(app)

    payload = _gzip_ndjson_fixture()
    sha256 = hashlib.sha256(payload).hexdigest()

    response = client.post(
        "/internal/v1/prqc-analyses",
        headers=_headers(),
        data=_form_data(sha256),
        files={"file": ("conversation.ndjson.gz", payload, "application/gzip")},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["analysisId"] == "a1"
    assert body["components"]["satisfaction"] == 83
    assert body["promptVersion"] == "relationship-evidence-1.0.0"
    assert body["processedMessageCount"] == 2
    assert "completedAt" in body


def test_rejects_request_without_valid_bearer_token(monkeypatch):
    monkeypatch.setenv("AI_INTERNAL_SERVICE_TOKEN", "test-token")
    app.dependency_overrides[get_llm_client] = lambda: _FakeLLMClient()
    client = TestClient(app)

    payload = _gzip_ndjson_fixture()
    sha256 = hashlib.sha256(payload).hexdigest()

    response = client.post(
        "/internal/v1/prqc-analyses",
        headers=_headers(Authorization="Bearer wrong-token"),
        data=_form_data(sha256),
        files={"file": ("conversation.ndjson.gz", payload, "application/gzip")},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 401


def test_returns_400_when_sha256_does_not_match(monkeypatch):
    monkeypatch.setenv("AI_INTERNAL_SERVICE_TOKEN", "test-token")
    app.dependency_overrides[get_llm_client] = lambda: _FakeLLMClient()
    client = TestClient(app)

    payload = _gzip_ndjson_fixture()

    response = client.post(
        "/internal/v1/prqc-analyses",
        headers=_headers(),
        data=_form_data("0" * 64),
        files={"file": ("conversation.ndjson.gz", payload, "application/gzip")},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_REQUEST"
    assert "details" in response.json()["error"]


def test_rejects_invalid_analysis_context(monkeypatch):
    monkeypatch.setenv("AI_INTERNAL_SERVICE_TOKEN", "test-token")
    app.dependency_overrides[get_llm_client] = lambda: _FakeLLMClient()
    client = TestClient(app)

    payload = _gzip_ndjson_fixture()
    sha256 = hashlib.sha256(payload).hexdigest()

    response = client.post(
        "/internal/v1/prqc-analyses",
        headers=_headers(),
        data=_form_data(sha256, context="{not-json"),
        files={"file": ("conversation.ndjson.gz", payload, "application/gzip")},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_REQUEST"


def test_returns_400_when_idempotency_key_header_missing(monkeypatch):
    monkeypatch.setenv("AI_INTERNAL_SERVICE_TOKEN", "test-token")
    app.dependency_overrides[get_llm_client] = lambda: _FakeLLMClient()
    client = TestClient(app)

    payload = _gzip_ndjson_fixture()
    sha256 = hashlib.sha256(payload).hexdigest()
    headers = _headers()
    del headers["Idempotency-Key"]

    response = client.post(
        "/internal/v1/prqc-analyses",
        headers=headers,
        data=_form_data(sha256),
        files={"file": ("conversation.ndjson.gz", payload, "application/gzip")},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_REQUEST"
