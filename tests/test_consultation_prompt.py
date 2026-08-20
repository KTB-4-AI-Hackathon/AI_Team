from app.pipeline.consultation.consultation import build_consultation_prompt
from app.schemas import ConsultationEvidenceContext

_PRQC = {
    "satisfaction": 83,
    "commitment": 17,
    "intimacy": 83,
    "trust": 83,
    "passion": 83,
    "love": 83,
}


def test_prompt_includes_reliability_structure_and_risk_evidence():
    evidences = [
        ConsultationEvidenceContext(
            evidenceId="e1", component="commitment", score=17, summary="선톡이 한쪽으로 쏠림"
        ),
    ]
    history = [
        {"role": "USER", "content": "이 사람이랑 계속 만나도 될까요?"},
        {"role": "ASSISTANT", "content": "어떤 점이 가장 걸리시나요?"},
    ]
    conversation = [
        {"sender": "OTHER", "sentAt": "2026-08-20T10:00:00Z", "text": "오늘은 늦을 것 같아"},
    ]

    prompt = build_consultation_prompt(
        recent_messages=history,
        conversation_messages=conversation,
        user_message="답장이 너무 늦어서 서운해요",
        overall_score=58,
        prqc=_PRQC,
        evidences=evidences,
    )

    system_message = prompt[0]["content"]
    assert "한계" in system_message
    assert "선택은" in system_message
    assert "선톡이 한쪽으로 쏠림" in system_message
    assert "commitment" in system_message
    assert "오늘은 늦을 것 같아" in system_message

    assert prompt[1] == {"role": "user", "content": "이 사람이랑 계속 만나도 될까요?"}
    assert prompt[2] == {"role": "assistant", "content": "어떤 점이 가장 걸리시나요?"}
    assert prompt[-1] == {"role": "user", "content": "답장이 너무 늦어서 서운해요"}


def test_only_below_cutoff_components_are_treated_as_risk_evidence():
    prompt = build_consultation_prompt(
        recent_messages=[],
        conversation_messages=[],
        user_message="요즘 잘 지내요",
        overall_score=90,
        prqc={
            "satisfaction": 90,
            "commitment": 90,
            "intimacy": 90,
            "trust": 90,
            "passion": 90,
            "love": 90,
        },
        evidences=[],
    )

    assert "전문 상담 권유 필요]: False" in prompt[0]["content"]
