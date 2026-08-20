import os

from fastapi import Request

from app.pipeline.errors import ApiError
from app.pipeline.llm_client import create_gemini_client


def get_llm_client():
    return create_gemini_client()


def require_service_token(request: Request) -> None:
    expected_token = os.environ.get("AI_INTERNAL_SERVICE_TOKEN")
    if not expected_token or request.headers.get("authorization") != f"Bearer {expected_token}":
        raise ApiError(401, "AUTH_REQUIRED", "invalid service token", False)