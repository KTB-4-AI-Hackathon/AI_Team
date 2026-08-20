import gzip
import json
import logging
import os
import uuid
from datetime import datetime, timezone

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, Form, Request, UploadFile
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.pipeline.consultation import (
    build_evidence_refs,
    build_safety_notice,
    classify_safety_signal,
    consult,
    risk_components_below_cutoff,
)
from app.pipeline.ingest import decompress_gzip, parse_ndjson, verify_sha256
from app.pipeline.llm_client import create_gemini_client
from app.pipeline.response_adapter import to_analysis_response
from app.pipeline.scoring import score_relationship
from app.pipeline.errors import ApiError
from app.schemas import (
    AnalysisContext,
    AnalysisResponse,
    ConsultationAnswerRequest,
    ConsultationAnswerResponse,
    ErrorDetail,
    ErrorResponse,
)

load_dotenv()

logger = logging.getLogger("ai_server")

app = FastAPI()

MODEL_VERSION = "prqc-2026-08-19.1"
PROMPT_VERSION = "relationship-evidence-1.0.0"
MIN_MESSAGE_COUNT = 2
REQUIRED_HEADERS = ("x-request-id", "idempotency-key")


def get_llm_client():
    return create_gemini_client()


def require_service_token(request: Request) -> None:
    expected_token = os.environ.get("AI_INTERNAL_SERVICE_TOKEN")
    if not expected_token or request.headers.get("authorization") != f"Bearer {expected_token}":
        raise ApiError(401, "AUTH_REQUIRED", "invalid service token", False)


@app.exception_handler(ApiError)
async def api_error_handler(request: Request, exc: ApiError) -> JSONResponse:
    request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
    body = ErrorResponse(
        error=ErrorDetail(code=exc.code, message=exc.message, retryable=exc.retryable, requestId=request_id)
    )
    return JSONResponse(status_code=exc.status_code, content=body.model_dump())


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/internal/v1/prqc-analyses", response_model=AnalysisResponse)
def analyze(
    request: Request,
    analysisId: str = Form(...),
    relationshipType: str = Form(...),
    format: str = Form(...),
    formatVersion: str = Form(...),
    sha256: str = Form(...),
    context: str = Form(...),
    file: UploadFile = File(...),
    _auth: None = Depends(require_service_token),
    llm_client=Depends(get_llm_client)
):
    missing_headers = [h for h in REQUIRED_HEADERS if not request.headers.get(h)]
    if missing_headers:
        raise ApiError(400, "INVALID_REQUEST", f"필수 헤더 누락: {', '.join(missing_headers)}", False)

    try:
        analysis_context = AnalysisContext.model_validate(json.loads(context))
    except (json.JSONDecodeError, ValidationError):
        raise ApiError(400, "INVALID_REQUEST", "분석 context 형식이 올바르지 않습니다.", False)

    data = file.file.read()

    if not verify_sha256(data, sha256):
        raise ApiError(400, "INVALID_REQUEST", "파일 무결성 검증에 실패했습니다.", False)

    try:
        messages = parse_ndjson(decompress_gzip(data))
    except (gzip.BadGzipFile, UnicodeDecodeError, json.JSONDecodeError, ValidationError):
        raise ApiError(422, "INVALID_CONVERSATION_DATA", "정규화 데이터 파싱에 실패했습니다.", False)

    if len(messages) < MIN_MESSAGE_COUNT:
        raise ApiError(422, "INSUFFICIENT_MESSAGES", "분석하기에 대화가 너무 적습니다.", False)

    try:
        score_result = score_relationship(messages, llm_client, analysis_context)
    except ValueError as e:
        raise ApiError(422, "INVALID_CONVERSATION_DATA", str(e), False)
    except Exception:
        logger.exception("scoring failed for analysisId=%s", analysisId)
        raise ApiError(503, "AI_PROVIDER_UNAVAILABLE", "일시적으로 분석 모델을 호출할 수 없습니다.", True)

    return to_analysis_response(
        score_result,
        analysis_id=analysisId,
        model_version=MODEL_VERSION,
        prompt_version=PROMPT_VERSION,
        processed_message_count=len(messages),
        completed_at=datetime.now(timezone.utc),
    )


@app.post("/internal/v1/consultation-answers", response_model=ConsultationAnswerResponse)
def consultation_answers(
    request: Request,
    body: ConsultationAnswerRequest,
    _auth: None = Depends(require_service_token),
    llm_client=Depends(get_llm_client),
):
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
