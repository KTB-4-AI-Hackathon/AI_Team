import os
import uuid
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse

from app.pipeline.ingest import decompress_gzip, parse_ndjson, verify_sha256
from app.pipeline.llm_client import create_gemini_client
from app.pipeline.response_adapter import to_analysis_response
from app.pipeline.scoring import score_relationship
from app.schemas import AnalysisResponse, ErrorDetail, ErrorResponse

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
        raise HTTPException(status_code=401, detail="invalid service token")


def _error_response(
    request: Request, status_code: int, code: str, message: str, retryable: bool
) -> JSONResponse:
    request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
    body = ErrorResponse(
        error=ErrorDetail(code=code, message=message, retryable=retryable, requestId=request_id)
    )
    return JSONResponse(status_code=status_code, content=body.model_dump())


@app.post("/internal/v1/prqc-analyses", response_model=AnalysisResponse)
def analyze(
    request: Request,
    analysisId: str = Form(...),
    relationshipType: str = Form(...),
    format: str = Form(...),
    formatVersion: str = Form(...),
    sha256: str = Form(...),
    file: UploadFile = File(...),
    _auth: None = Depends(require_service_token),
    llm_client=Depends(get_llm_client),
):
    missing_headers = [h for h in REQUIRED_HEADERS if not request.headers.get(h)]
    if missing_headers:
        return _error_response(
            request, 400, "INVALID_REQUEST", f"필수 헤더 누락: {', '.join(missing_headers)}", False
        )

    data = file.file.read()

    if not verify_sha256(data, sha256):
        return _error_response(
            request, 400, "INVALID_REQUEST", "파일 무결성 검증에 실패했습니다.", False
        )

    messages = parse_ndjson(decompress_gzip(data))
    if len(messages) < MIN_MESSAGE_COUNT:
        return _error_response(
            request, 422, "INSUFFICIENT_MESSAGES", "분석하기에 대화가 너무 적습니다.", False
        )

    try:
        score_result = score_relationship(messages, llm_client)
    except Exception:
        return _error_response(
            request, 503, "AI_PROVIDER_UNAVAILABLE", "일시적으로 분석 모델을 호출할 수 없습니다.", True
        )

    return to_analysis_response(
        score_result,
        analysis_id=analysisId,
        model_version=MODEL_VERSION,
        prompt_version=PROMPT_VERSION,
        processed_message_count=len(messages),
        completed_at=datetime.now(timezone.utc),
    )
