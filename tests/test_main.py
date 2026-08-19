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
    }
    base.update(overrides)
    return base


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
    assert response.json()["error"]["code"] == "AUTH_REQUIRED"


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


def test_returns_422_when_ndjson_is_malformed(monkeypatch):
    monkeypatch.setenv("AI_INTERNAL_SERVICE_TOKEN", "test-token")
    app.dependency_overrides[get_llm_client] = lambda: _FakeLLMClient()
    client = TestClient(app)

    broken_payload = gzip.compress(b"{not valid json at all")
    sha256 = hashlib.sha256(broken_payload).hexdigest()

    response = client.post(
        "/internal/v1/prqc-analyses",
        headers=_headers(),
        data=_form_data(sha256),
        files={"file": ("conversation.ndjson.gz", broken_payload, "application/gzip")},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_CONVERSATION_DATA"


def test_returns_422_when_gzip_is_corrupted(monkeypatch):
    monkeypatch.setenv("AI_INTERNAL_SERVICE_TOKEN", "test-token")
    app.dependency_overrides[get_llm_client] = lambda: _FakeLLMClient()
    client = TestClient(app)

    not_gzip = b"this is not gzip data"
    sha256 = hashlib.sha256(not_gzip).hexdigest()

    response = client.post(
        "/internal/v1/prqc-analyses",
        headers=_headers(),
        data=_form_data(sha256),
        files={"file": ("conversation.ndjson.gz", not_gzip, "application/gzip")},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_CONVERSATION_DATA"
