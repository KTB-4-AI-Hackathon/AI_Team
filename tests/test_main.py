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
        headers={"Authorization": "Bearer test-token"},
        data={"analysisId": "a1", "relationshipType": "FRIEND", "sha256": sha256},
        files={"file": ("conversation.ndjson.gz", payload, "application/gzip")},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["analysisId"] == "a1"
    assert body["components"]["satisfaction"] == 83


def test_rejects_request_without_valid_bearer_token(monkeypatch):
    monkeypatch.setenv("AI_INTERNAL_SERVICE_TOKEN", "test-token")
    app.dependency_overrides[get_llm_client] = lambda: _FakeLLMClient()
    client = TestClient(app)

    payload = _gzip_ndjson_fixture()
    sha256 = hashlib.sha256(payload).hexdigest()

    response = client.post(
        "/internal/v1/prqc-analyses",
        headers={"Authorization": "Bearer wrong-token"},
        data={"analysisId": "a1", "relationshipType": "FRIEND", "sha256": sha256},
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
        headers={"Authorization": "Bearer test-token"},
        data={"analysisId": "a1", "relationshipType": "FRIEND", "sha256": "0" * 64},
        files={"file": ("conversation.ndjson.gz", payload, "application/gzip")},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "FILE_INTEGRITY_MISMATCH"
