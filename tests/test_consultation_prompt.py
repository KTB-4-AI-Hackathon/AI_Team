from app.pipeline.consultation import build_consultation_prompt
from app.schemas import ScoreResult


def test_prompt_includes_reliability_structure_and_risk_evidence():
    score_result = ScoreResult(
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
    history = [
        {"role": "user", "content": "이 사람이랑 계속 만나도 될까요?"},
        {"role": "assistant", "content": "어떤 점이 가장 걸리시나요?"},
    ]

    prompt = build_consultation_prompt(
        history=history,
        user_message="답장이 너무 늦어서 서운해요",
        score_result=score_result,
        relationship_type="FRIEND",
    )

    system_message = prompt[0]["content"]
    assert "한계" in system_message
    assert "선택은" in system_message
    assert "선톡이 한쪽으로 쏠림" in system_message

    assert prompt[1] == {"role": "user", "content": "이 사람이랑 계속 만나도 될까요?"}
    assert prompt[2] == {"role": "assistant", "content": "어떤 점이 가장 걸리시나요?"}
    assert prompt[-1] == {"role": "user", "content": "답장이 너무 늦어서 서운해요"}
