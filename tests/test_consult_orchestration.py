from datetime import datetime, timezone

from app.pipeline.consultation import consult
from app.schemas import Evidence, RelationshipContext


class _FakeLLMClient:
    def __init__(self, response_text: str):
        self._response_text = response_text

    def invoke(self, langchain_messages):
        class _Response:
            content = self._response_text

        return _Response()


def _relationship_context() -> RelationshipContext:
    return RelationshipContext(
        relationshipType="FRIEND",
        analyzedAt=datetime(2026, 8, 19, tzinfo=timezone.utc),
        overallScore=58,
        components={
            "satisfaction": 83,
            "commitment": 17,
            "intimacy": 83,
            "trust": 83,
            "passion": 83,
            "love": 83,
        },
        evidences=[
            Evidence(component="commitment", score=17, summary="선톡이 한쪽으로 쏠림"),
        ],
    )


def test_bypasses_llm_and_returns_crisis_response_when_signal_detected():
    fake_client = _FakeLLMClient("이 응답은 쓰이면 안 됨")

    reply = consult(
        history=[],
        user_message="요즘 너무 힘들어서 죽고 싶다는 생각이 들어",
        relationship_context=_relationship_context(),
        llm_client=fake_client,
    )

    assert reply != "이 응답은 쓰이면 안 됨"
    assert "1393" not in reply


def test_calls_llm_for_ordinary_message():
    fake_client = _FakeLLMClient("답장이 늦는 게 신경 쓰이시는군요. 어떤 부분이 가장 서운하셨어요?")

    reply = consult(
        history=[],
        user_message="답장이 너무 늦어서 서운해요",
        relationship_context=_relationship_context(),
        llm_client=fake_client,
    )

    assert reply == "답장이 늦는 게 신경 쓰이시는군요. 어떤 부분이 가장 서운하셨어요?"
