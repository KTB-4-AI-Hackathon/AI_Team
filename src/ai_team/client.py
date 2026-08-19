import functools
import logging

from ai_team.schema import AnalysisResponse, Chat, PrqcComponentScore, RelationshipType

logger = logging.getLogger('ai_team.client')


def log_errors(func):
    """에러 발생 시 함수 이름과 인풋 값을 로그로 남기고 그대로 재발생시키는 데코레이터."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as error:
            logger.error(
                '함수 실행 실패: %s, args=%r, kwargs=%r, error=%r',
                func.__name__,
                args,
                kwargs,
                error,
            )
            raise

    return wrapper


@log_errors
def load_anthropic_api_key() -> str:
    # TODO: 환경변수(ANTHROPIC_API_KEY)에서 로드
    raise NotImplementedError


@log_errors
def load_model_name() -> str:
    # TODO: 환경변수 우선, 없으면 기본값 'claude-sonnet-4-6' 반환
    raise NotImplementedError


@log_errors
def get_client():
    # TODO: anthropic.Anthropic(api_key=load_anthropic_api_key()) 반환
    raise NotImplementedError


@log_errors
def build_prompt(component_name: str, chats: list[Chat], relationship_type: RelationshipType) -> str:
    # TODO: COMPONENT_DEFINITIONS[component_name] + few-shot 예시
    #       + relationship_type 안내 + chats 텍스트 직렬화를 조합해 프롬프트 문자열 생성
    raise NotImplementedError


@log_errors
def score_component(
    component_name: str,
    chats: list[Chat],
    relationship_type: RelationshipType,
) -> PrqcComponentScore:
    # TODO: build_prompt로 프롬프트 생성
    # TODO: PrqcComponentScore.model_json_schema()를 tool 정의로 사용해 Anthropic API 호출
    # TODO: tool_choice로 해당 tool 강제, 응답 tool_use 블록의 input을 PrqcComponentScore로 파싱
    # TODO: 파싱 실패 시 최대 3회 재시도
    raise NotImplementedError


@log_errors
def score_all_components(
    chats: list[Chat],
    relationship_type: RelationshipType,
) -> AnalysisResponse:
    # TODO: 6개 구성요소(satisfaction, commitment, intimacy, trust, passion, love)에 대해
    #       score_component를 순차 호출하고 AnalysisResponse로 조립해 반환
    raise NotImplementedError