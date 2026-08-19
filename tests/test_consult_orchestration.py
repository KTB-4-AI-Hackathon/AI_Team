import json

from app.pipeline.consultation import consult
from app.schemas import ScoreResult


class _FakeLLMClient:
    def __init__(self, response_text: str):
        self._response_text = response_text

    def invoke(self, langchain_messages):
        class _Response:
            content = self._response_text

        return _Response()


def _score_result() -> ScoreResult:
    return ScoreResult(
        scores={
            "Satisfaction": 6,
            "Commitment": 2,
            "Intimacy": 6,
            "Trust": 6,
            "Passion": 6,
            "Love": 6,
        },
        risk_components=["Commitment"],
        evidence={"Commitment": "선톡이 한쪽으로 쏠림"},
    )


def test_bypasses_llm_and_returns_crisis_response_when_signal_detected():
    fake_client = _FakeLLMClient("이 응답은 쓰이면 안 됨")

    reply = consult(
        history=[],
        user_message="요즘 너무 힘들어서 죽고 싶다는 생각이 들어",
        score_result=_score_result(),
        relationship_type="FRIEND",
        llm_client=fake_client,
    )

    assert reply != "이 응답은 쓰이면 안 됨"
    assert "1393" not in reply


def test_calls_llm_for_ordinary_message():
    fake_client = _FakeLLMClient("답장이 늦는 게 신경 쓰이시는군요. 어떤 부분이 가장 서운하셨어요?")

    reply = consult(
        history=[],
        user_message="답장이 너무 늦어서 서운해요",
        score_result=_score_result(),
        relationship_type="FRIEND",
        llm_client=fake_client,
    )

    assert reply == "답장이 늦는 게 신경 쓰이시는군요. 어떤 부분이 가장 서운하셨어요?"
