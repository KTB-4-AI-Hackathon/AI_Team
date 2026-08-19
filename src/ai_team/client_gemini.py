import logging
import os

from google import genai
from google.genai import types

from ai_team.client import MAX_RETRY_COUNT, build_prompt, log_errors
from ai_team.schema import AnalysisResponse, Chat, RelationshipType

logger = logging.getLogger('ai_team.client_gemini')


@log_errors
def load_google_api_key() -> str:
    api_key = os.environ.get('GOOGLE_API_KEY')
    if not api_key:
        raise ValueError('환경변수 GOOGLE_API_KEY가 설정되어 있지 않습니다.')
    return api_key


@log_errors
def load_gemini_model_name() -> str:
    return os.environ.get('AI_TEAM_GEMINI_MODEL_NAME', 'gemini-3.1-pro')


@log_errors
def get_gemini_client() -> genai.Client:
    return genai.Client(api_key=load_google_api_key())


@log_errors
def score_all_components_gemini(
    chats: list[tuple[Chat, str]],
    relationship_type: RelationshipType,
    model_name: str | None = None,
) -> AnalysisResponse:
    """Gemini API를 한 번만 호출해 6개 구성요소를 동시에 채점한다."""

    client = get_gemini_client()
    model_name = model_name or load_gemini_model_name()
    prompt = build_prompt(chats, relationship_type)

    last_error: Exception | None = None
    for attempt in range(1, MAX_RETRY_COUNT + 1):
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type='application/json',
                    response_schema=AnalysisResponse,
                ),
            )
            return AnalysisResponse.model_validate(response.parsed)

        except Exception as error:
            last_error = error
            logger.warning(
                'score_all_components_gemini 재시도 (%d/%d): error=%r',
                attempt,
                MAX_RETRY_COUNT,
                error,
            )

    raise RuntimeError(
        f'score_all_components_gemini 최대 재시도({MAX_RETRY_COUNT}회) 초과'
    ) from last_error