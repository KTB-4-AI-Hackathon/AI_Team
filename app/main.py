import logging
import uuid

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.dependencies import get_llm_client  # noqa: F401  (테스트의 dependency override용 재노출)
from app.pipeline.errors import ApiError
from app.routers import analysis, consultation
from app.schemas import ErrorDetail, ErrorResponse

load_dotenv()

logger = logging.getLogger("ai_server")

app = FastAPI()

app.include_router(analysis.router)
app.include_router(consultation.router)


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