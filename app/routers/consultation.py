import logging

from fastapi import APIRouter, Depends, Request

from app.dependencies import get_llm_client, require_service_token
from app.pipeline.consultation import (
    build_evidence_refs,
    build_safety_notice,
    classify_safety_signal,
    consult,
    risk_components_below_cutoff,
)
from app.pipeline.errors import ApiError
from app.schemas import ConsultationAnswerRequest, ConsultationAnswerResponse

logger = logging.getLogger("ai_server")

router = APIRouter()


@router.post("/internal/v1/consultation-answers", response_model=ConsultationAnswerResponse)
def consultation_answers(
    request: Request,
    body: ConsultationAnswerRequest,
    _auth: None = Depends(require_service_token),
    llm_client=Depends(get_llm_client),
) -> ConsultationAnswerResponse:
    # 분석 엔드포인트와 달리 이 엔드포인트는 Idempotency-Key를 요구하지 않는다
    # (명세서 create_consultation_answer 시그니처 기준).
    if not request.headers.get("x-request-id"):
        raise ApiError(400, "INVALID_REQUEST", "필수 헤더 누락: x-request-id", False)

    recent_messages = [m.model_dump() for m in body.recentMessages]
    risk_components = risk_components_below_cutoff(body.prqc)
    safety_type = classify_safety_signal(body.userMessage, risk_components)

    try:
        content = consult(
            recent_messages=recent_messages,
            user_message=body.userMessage,
            overall_score=body.overallScore,
            prqc=body.prqc,
            evidences=body.evidences,
            llm_client=llm_client,
        )
    except Exception:
        logger.exception("consultation failed for reportId=%s", body.reportId)
        raise ApiError(503, "AI_PROVIDER_UNAVAILABLE", "일시적으로 상담 모델을 호출할 수 없습니다.", True)

    return ConsultationAnswerResponse(
        content=content,
        evidenceRefs=build_evidence_refs(body.evidences, risk_components),
        safetyNotice=build_safety_notice(safety_type),
    )