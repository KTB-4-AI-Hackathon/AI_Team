from datetime import datetime, timezone

from app.pipeline.response_adapter import to_analysis_response
from app.schemas import ScoreResult

_COMPLETED_AT = datetime(2026, 8, 19, 6, 22, 24, tzinfo=timezone.utc)


def test_converts_score_result_to_lowercase_0_to_100_response():
    score_result = ScoreResult(
        scores={
            "Satisfaction": 7,
            "Commitment": 1,
            "Intimacy": 4,
            "Trust": 6,
            "Passion": 6,
            "Love": 6,
        },
        risk_components=["Commitment"],
        evidence={
            "Satisfaction": "긍정 표현이 꾸준함",
            "Commitment": "선톡이 한쪽으로 쏠림",
            "Intimacy": "표면적 대화만 지속됨",
            "Trust": "즉답 비율이 높음",
            "Passion": "반응 속도가 빠름",
            "Love": "애정 표현이 꾸준함",
        },
    )

    response = to_analysis_response(
        score_result,
        analysis_id="a1",
        model_version="prqc-2026-08-19.1",
        prompt_version="relationship-evidence-1.0.0",
        processed_message_count=42,
        completed_at=_COMPLETED_AT,
    )

    assert response.analysisId == "a1"
    assert response.modelVersion == "prqc-2026-08-19.1"
    assert response.promptVersion == "relationship-evidence-1.0.0"
    assert response.processedMessageCount == 42
    assert response.completedAt == _COMPLETED_AT
    assert response.components["satisfaction"] == 100
    assert response.components["commitment"] == 0
    assert response.components["intimacy"] == 50
    assert len(response.evidences) == 6
    assert response.evidences[0].component == "satisfaction"
    assert response.warnings == []


def test_adds_warning_for_component_missing_evidence():
    score_result = ScoreResult(
        scores={
            "Satisfaction": 7,
            "Commitment": 1,
            "Intimacy": 4,
            "Trust": 6,
            "Passion": 6,
            "Love": 6,
        },
        risk_components=["Commitment"],
        evidence={"Commitment": "선톡이 한쪽으로 쏠림"},
    )

    response = to_analysis_response(
        score_result,
        analysis_id="a1",
        model_version="prqc-2026-08-19.1",
        prompt_version="relationship-evidence-1.0.0",
        processed_message_count=42,
        completed_at=_COMPLETED_AT,
    )

    assert len(response.evidences) == 1
    assert response.warnings[0].code == "NO_STRUCTURED_EVIDENCE"
    assert "satisfaction" in response.warnings[0].message
