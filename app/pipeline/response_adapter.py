from app.schemas import AnalysisResponse, Evidence, ScoreResult


def _to_hundred_scale(score_7: int) -> int:
    return round((score_7 - 1) / 6 * 100)


def to_analysis_response(
    score_result: ScoreResult, analysis_id: str, model_version: str
) -> AnalysisResponse:
    components = {
        key.lower(): _to_hundred_scale(value)
        for key, value in score_result.scores.items()
    }
    evidences = [
        Evidence(
            component=component.lower(),
            score=_to_hundred_scale(score_result.scores[component]),
            summary=summary,
        )
        for component, summary in score_result.evidence.items()
    ]
    return AnalysisResponse(
        analysisId=analysis_id,
        modelVersion=model_version,
        components=components,
        evidences=evidences,
    )
