import functools
import logging
import os

import anthropic
from dotenv import load_dotenv

from ai_team.schema import AnalysisResponse, Chat, RelationshipType

load_dotenv()

logger = logging.getLogger('ai_team.client')

MAX_RETRY_COUNT = 3

COMPONENT_NAMES = ['satisfaction', 'commitment', 'intimacy', 'trust', 'passion', 'love']


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
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        raise ValueError('환경변수 ANTHROPIC_API_KEY가 설정되어 있지 않습니다.')
    return api_key


@log_errors
def load_model_name() -> str:
    return os.environ.get('AI_TEAM_MODEL_NAME', 'claude-sonnet-4-6')


@log_errors
def get_client() -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=load_anthropic_api_key())


# PRQC 구성요소별 일반 정의. Fletcher, Simpson & Thomas(2000) 기준.
# TODO: 각 구성요소를 채팅 로그에서 관찰 가능한 신호로 재정의하는 매핑 작업 미완료
#       (예: Trust → 약속 이행 언급 빈도, Intimacy → 개인적 화제 공유 빈도).
#       이 매핑이 확정되기 전까지는 아래 정의가 일반론 수준에 머무른다.
COMPONENT_DEFINITIONS: dict[str, str] = {
    'satisfaction': '이 관계에 얼마나 만족하는지를 나타내는 구성요소.',
    'commitment': '이 관계에 얼마나 헌신하는지를 나타내는 구성요소.',
    'intimacy': '상대방과 얼마나 연결되어 있다고 느끼는지를 나타내는 구성요소.',
    'trust': '상대방을 얼마나 신뢰하는지를 나타내는 구성요소.',
    'passion': '관계가 얼마나 열정적인지를 나타내는 구성요소.',
    'love': '상대방에 대한 애정의 정도를 나타내는 구성요소.',
}

# 구성요소별 few-shot 예시 (위험/안전 대화 쌍).
# TODO: COMPONENT_DEFINITIONS의 매핑 작업이 끝난 뒤 구성요소별로 채울 것.
#       현재는 빈 리스트라 few-shot 없이 정의문만으로 채점을 시도하는 상태.
COMPONENT_FEW_SHOT_EXAMPLES: dict[str, list[dict]] = {
    'satisfaction': [],
    'commitment': [],
    'intimacy': [],
    'trust': [],
    'passion': [],
    'love': [],
}


@log_errors
def build_prompt(chats: list[Chat], relationship_type: RelationshipType) -> str:
    """6개 구성요소를 한 번의 호출로 모두 채점하기 위한 단일 프롬프트를 조립한다."""

    definitions_block = '\n'.join(
        f'- {name}: {definition}' for name, definition in COMPONENT_DEFINITIONS.items()
    )

    # TODO: 구성요소별 few_shot 예시가 채워지면 아래 블록을 구성요소별로 구체화할 것
    # few_shot_block = '\n'.join(
    #     f'- {name}: {examples}' for name, examples in COMPONENT_FEW_SHOT_EXAMPLES.items()
    # )

    chats_block = '\n'.join(f'[{chat.date}] {chat.name}: {chat.message}' for chat in chats)

    prompt = (
        f'당신은 두 사람의 대화 로그를 읽고 관계의 PRQC 6개 구성요소를 한 번에 채점하는 평가자입니다.\n'
        f'\n'
        f'구성요소 정의:\n{definitions_block}\n'
        f'\n'
        f'관계 유형: {relationship_type.value}\n'
        # f'\n'
        # f'참고 예시:\n{few_shot_block}\n'
        f'\n'
        f'대화 로그:\n{chats_block}\n'
        f'\n'
        f'위 대화를 근거로 satisfaction, commitment, intimacy, trust, passion, love '
        f'6개 구성요소 각각을 1~7점으로 채점하고, 구성요소별 판단 근거를 요약된 문장으로 제시하세요.'
    )
    return prompt


@log_errors
def score_all_components(
    chats: list[Chat],
    relationship_type: RelationshipType,
) -> AnalysisResponse:
    """API를 한 번만 호출해 6개 구성요소를 동시에 채점한다."""

    client = get_client()
    model_name = load_model_name()
    prompt = build_prompt(chats, relationship_type)

    tool_schema = AnalysisResponse.model_json_schema()
    tool_name = 'submit_prqc_analysis'

    last_error: Exception | None = None
    for attempt in range(1, MAX_RETRY_COUNT + 1):
        try:
            response = client.messages.create(
                model=model_name,
                max_tokens=2048,
                tools=[
                    {
                        'name': tool_name,
                        'description': 'PRQC 6개 구성요소 각각의 1~7점 점수와 판단 근거를 한 번에 제출한다.',
                        'input_schema': tool_schema,
                    }
                ],
                tool_choice={'type': 'tool', 'name': tool_name},
                messages=[{'role': 'user', 'content': prompt}],
            )

            tool_use_block = next(
                block for block in response.content if block.type == 'tool_use'
            )
            return AnalysisResponse.model_validate(tool_use_block.input)

        except Exception as error:
            last_error = error
            logger.warning(
                'score_all_components 재시도 (%d/%d): error=%r',
                attempt,
                MAX_RETRY_COUNT,
                error,
            )

    raise RuntimeError(
        f'score_all_components 최대 재시도({MAX_RETRY_COUNT}회) 초과'
    ) from last_error