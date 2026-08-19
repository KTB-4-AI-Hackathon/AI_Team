import json

from fastapi.testclient import TestClient

from app.main import app, get_llm_client


def _headers(**overrides) -> dict[str, str]:
    base = {
        "Authorization": "Bearer test-token",
        "X-Request-Id": "req_1",
        "Idempotency-Key": "c1",
        "Content-Type": "application/json",
    }
    base.update(overrides)
    return base


def _request_body(**overrides) -> dict:
    base = {
        "consultationId": "c1",
        "userMessage": "답장이 너무 늦어서 서운해요",
        "history": [],
        "relationshipContext": {
            "relationshipType": "FRIEND",
            "analyzedAt": "2026-08-19T00:00:00Z",
            "overallScore": 58,
            "components": {
                "satisfaction": 83,
                "commitment": 17,
                "intimacy": 83,
                "trust": 83,
                "passion": 83,
                "love": 83,
            },
            "evidences": [
                {"component": "commitment", "score": 17, "summary": "선톡이 한쪽으로 쏠림"}
            ],
        },
    }
    base.update(overrides)
    return base


class _FakeLLMClient:
    def invoke(self, langchain_messages):
        class _Response:
            content = "답장이 늦는 게 신경 쓰이셨군요. 어떤 부분이 가장 걸리셨어요?"

        return _Response()


def test_returns_reply_and_safety_type_for_authenticated_valid_request(monkeypatch):
    monkeypatch.setenv("AI_INTERNAL_SERVICE_TOKEN", "test-token")
    app.dependency_overrides[get_llm_client] = lambda: _FakeLLMClient()
    client = TestClient(app)

    response = client.post(
        "/internal/v1/consultations/messages",
        headers=_headers(),
        json=_request_body(),
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["consultationId"] == "c1"
    assert body["reply"] == "답장이 늦는 게 신경 쓰이셨군요. 어떤 부분이 가장 걸리셨어요?"
    assert body["safetyType"] is None


def test_returns_crisis_support_safety_type_when_crisis_signal_detected(monkeypatch):
    monkeypatch.setenv("AI_INTERNAL_SERVICE_TOKEN", "test-token")
    app.dependency_overrides[get_llm_client] = lambda: _FakeLLMClient()
    client = TestClient(app)

    response = client.post(
        "/internal/v1/consultations/messages",
        headers=_headers(),
        json=_request_body(userMessage="요즘 너무 힘들어서 죽고 싶다는 생각이 들어"),
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["safetyType"] == "CRISIS_SUPPORT"


def test_rejects_request_without_valid_bearer_token(monkeypatch):
    monkeypatch.setenv("AI_INTERNAL_SERVICE_TOKEN", "test-token")
    app.dependency_overrides[get_llm_client] = lambda: _FakeLLMClient()
    client = TestClient(app)

    response = client.post(
        "/internal/v1/consultations/messages",
        headers=_headers(Authorization="Bearer wrong-token"),
        json=_request_body(),
    )

    app.dependency_overrides.clear()

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTH_REQUIRED"
