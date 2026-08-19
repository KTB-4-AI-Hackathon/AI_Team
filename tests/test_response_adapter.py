from app.pipeline.response_adapter import to_analysis_response
from app.schemas import ScoreResult


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
        evidence={"Commitment": "선톡이 한쪽으로 쏠림"},
    )

    response = to_analysis_response(
        score_result, analysis_id="a1", model_version="prqc-2026-08-19.1"
    )

    assert response.analysisId == "a1"
    assert response.modelVersion == "prqc-2026-08-19.1"
    assert response.components["satisfaction"] == 100
    assert response.components["commitment"] == 0
    assert response.components["intimacy"] == 50
    assert len(response.evidences) == 1
    assert response.evidences[0].component == "commitment"
    assert response.evidences[0].score == 0
    assert response.evidences[0].summary == "선톡이 한쪽으로 쏠림"
