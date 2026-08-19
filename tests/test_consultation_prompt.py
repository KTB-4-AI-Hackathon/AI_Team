from datetime import datetime, timezone

from app.pipeline.consultation import build_consultation_prompt
from app.schemas import Evidence, RelationshipContext

_CONTEXT = RelationshipContext(
    relationshipType="FRIEND",
    analyzedAt=datetime(2026, 8, 19, tzinfo=timezone.utc),
    overallScore=58,
    components={
        "satisfaction": 83,
        "commitment": 33,
        "intimacy": 83,
        "trust": 83,
        "passion": 83,
        "love": 83,
    },
    evidences=[
        Evidence(component="commitment", score=33, summary="선톡이 한쪽으로 쏠림"),
    ],
)


def test_prompt_includes_reliability_structure_and_risk_evidence():
    history = [
        {"role": "user", "content": "이 사람이랑 계속 만나도 될까요?"},
        {"role": "assistant", "content": "어떤 점이 가장 걸리시나요?"},
    ]

    prompt = build_consultation_prompt(
        history=history,
        user_message="답장이 너무 늦어서 서운해요",
        relationship_context=_CONTEXT,
    )

    system_message = prompt[0]["content"]
    assert "한계" in system_message
    assert "선택은" in system_message
    assert "선톡이 한쪽으로 쏠림" in system_message
    assert "commitment" in system_message

    assert prompt[1] == {"role": "user", "content": "이 사람이랑 계속 만나도 될까요?"}
    assert prompt[2] == {"role": "assistant", "content": "어떤 점이 가장 걸리시나요?"}
    assert prompt[-1] == {"role": "user", "content": "답장이 너무 늦어서 서운해요"}


def test_only_below_cutoff_components_are_treated_as_risk_evidence():
    context = RelationshipContext(
        relationshipType="FRIEND",
        analyzedAt=datetime(2026, 8, 19, tzinfo=timezone.utc),
        overallScore=90,
        components={
            "satisfaction": 90,
            "commitment": 90,
            "intimacy": 90,
            "trust": 90,
            "passion": 90,
            "love": 90,
        },
        evidences=[],
    )

    prompt = build_consultation_prompt(
        history=[], user_message="요즘 잘 지내요", relationship_context=context
    )

    assert "전문 상담 권유 필요]: False" in prompt[0]["content"]
