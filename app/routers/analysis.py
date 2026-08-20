import gzip
import json
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from pydantic import ValidationError

from app.dependencies import get_llm_client, require_service_token
from app.pipeline.errors import ApiError
from app.pipeline.ingest import decompress_gzip, parse_ndjson, verify_sha256
from app.pipeline.response_adapter import to_analysis_response
from app.pipeline.scoring import score_relationship
from app.schemas import AnalysisContext, AnalysisResponse

logger = logging.getLogger("ai_server")

router = APIRouter()

MODEL_VERSION = "prqc-2026-08-19.1"
PROMPT_VERSION = "relationship-evidence-1.0.0"
MIN_MESSAGE_COUNT = 2
REQUIRED_HEADERS = ("x-request-id", "idempotency-key")


@router.post("/internal/v1/prqc-analyses", response_model=AnalysisResponse)
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
    llm_client=Depends(get_llm_client),
) -> AnalysisResponse:
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