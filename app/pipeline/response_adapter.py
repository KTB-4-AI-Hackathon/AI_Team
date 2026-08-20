from datetime import datetime

from app.schemas import AnalysisResponse, AnalysisWarning, Evidence, ScoreResult


def _to_hundred_scale(score_7: int) -> int:
    return round((score_7 - 1) / 6 * 100)


def to_analysis_response(
    score_result: ScoreResult,
    analysis_id: str,
    model_version: str,
    prompt_version: str,
    processed_message_count: int,
    completed_at: datetime,
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
    warnings = [
        AnalysisWarning(
            code="NO_STRUCTURED_EVIDENCE",
            message=f"{component.lower()}: 근거 문장이 생성되지 않았습니다.",
        )
        for component in score_result.scores
        if component not in score_result.evidence
    ]
    return AnalysisResponse(
        analysisId=analysis_id,
        modelVersion=model_version,
        promptVersion=prompt_version,
        processedMessageCount=processed_message_count,
        components=components,
        evidences=evidences,
        warnings=warnings,
        completedAt=completed_at,
    )
