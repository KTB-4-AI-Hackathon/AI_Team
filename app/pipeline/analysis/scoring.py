import json

from app.pipeline.llm_client import invoke_llm
from app.schemas import AnalysisContext, Message, ScoreResult
from app.pipeline.risk import to_seven_scale_cutoff

PRQC_COMPONENTS = [
    "Satisfaction",
    "Commitment",
    "Intimacy",
    "Trust",
    "Passion",
    "Love",
]

_SYSTEM_PROMPT_TEMPLATE = """당신은 대화 로그를 관찰해 관계 품질을 평가하는 분석가입니다.
학술적으로 정립된 관계 품질의 6가지 축(PRQC)을 참고해, 아래 대화에서 관찰 가능한
신호만 근거로 각 구성요소를 1~7점으로 채점하세요. 임상적 진단이 아닌 자기성찰용
참고 지표이니 과도하게 단정적인 판단은 피하세요.

평가할 구성요소: {components}

사용자는 이번 주 체크인에서 관계에 대한 전반적인 감정을 {relationship_feeling_score}점,
대화의 편안함을 {conversation_comfort_score}점(둘 다 1~7점)으로 스스로 평가했습니다.
이 자기보고 값은 채점의 근거로 쓰지 마세요. 6개 구성요소 점수는 반드시 대화 로그에서
관찰되는 신호만으로 산출해야 합니다. 자기보고 값은 아래 self_report_comparison
필드를 작성할 때만 참고하세요.

대화에서 "나"는 분석을 요청한 사용자 본인, "상대방"은 대화 상대입니다.
근거 문장을 쓸 때 '나'와 '상대방'을 혼동하지 마세요 — 누가 한 행동인지
대화 내용과 정확히 일치시키세요. "상대방이 상대방을 의심했다"처럼 같은
대상을 반복 지칭하는 실수를 하면 안 됩니다.

중요: JSON 문자열 값 안에서는 큰따옴표(")를 절대 사용하지 마세요.
"나"를 강조하고 싶어도 따옴표 없이 그냥 나라고 쓰세요. 큰따옴표를
쓰면 JSON 형식이 깨집니다.

[예시]
대화:
나: 오늘 저녁에 시간 괜찮아?
상대방: 미안, 오늘은 좀 피곤해서 안 될 것 같아
나: 요즘 계속 바쁘다고만 하네
상대방: 진짜 미안해, 다음 주에 꼭 보자

올바른 근거 예시 (Commitment):
"상대방이 만남을 미루면서도 다음 만남을 먼저 제안해 관계를 유지하려는
의지를 보였습니다." (행동의 주체가 실제 화자와 일치함)

같은 대화를 반복 채점해도 이 예시와 같은 기준으로 일관되게 점수를 매기세요.

JSON으로만 응답하세요. 다른 텍스트를 포함하지 마세요. 형식:
{{"Satisfaction": <1-7>, "Commitment": <1-7>, "Intimacy": <1-7>,
  "Trust": <1-7>, "Passion": <1-7>, "Love": <1-7>,
  "evidence": {{"<구성요소>": "<판정 근거 한 문장>", ...}},
  "self_report_comparison": "<사용자의 자기보고 점수와 대화에서 관찰된 패턴이
  일치하는지, 차이가 있다면 어떤 방향으로 차이가 나는지 한두 문장으로 서술>"}}"""


def build_system_prompt(relationship_feeling_score: int, conversation_comfort_score: int) -> str:
    return _SYSTEM_PROMPT_TEMPLATE.format(
        components=", ".join(PRQC_COMPONENTS),
        relationship_feeling_score=relationship_feeling_score,
        conversation_comfort_score=conversation_comfort_score,
    )


def build_prqc_prompt(
    messages: list[Message],
    relationship_feeling_score: int,
    conversation_comfort_score: int,
) -> list[dict[str, str]]:
    conversation = "\n".join(f"{m.speaker}: {m.text}" for m in messages)
    system_prompt = build_system_prompt(relationship_feeling_score, conversation_comfort_score)
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": conversation},
    ]


_RISK_CUTOFF = to_seven_scale_cutoff()


def parse_prqc_response(raw_output: str) -> ScoreResult:
    data = json.loads(_strip_code_fence(raw_output))
    scores = {c: data[c] for c in PRQC_COMPONENTS}
    risk_components = [c for c, s in scores.items() if s < _RISK_CUTOFF]
    evidence = data.get("evidence", {})
    self_report_comparison = data.get("self_report_comparison", "")
    return ScoreResult(
        scores=scores,
        risk_components=risk_components,
        evidence=evidence,
        self_report_comparison=self_report_comparison,
    )


def _strip_code_fence(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.removeprefix("```json").removeprefix("```")
        text = text.removesuffix("```")
    return text.strip()


def score_relationship(
    messages: list[Message], llm_client, analysis_context: AnalysisContext
) -> ScoreResult:
    check_in_answers = analysis_context.current.checkIn.answers

    relationship_feeling_answer = next((answer for answer in check_in_answers if answer.questionCode == 'RELATIONSHIP_FEELING'), None)
    if relationship_feeling_answer is None:
        raise ValueError("RELATIONSHIP_FEELING 응답이 존재하지 않음")
    relationship_feeling_score = relationship_feeling_answer.score

    conversation_comfort_answer = next((answer for answer in check_in_answers if answer.questionCode == 'CONVERSATION_COMFORT'), None)
    if conversation_comfort_answer is None:
        raise ValueError("CONVERSATION_COMFORT 응답이 존재하지 않음")
    conversation_comfort_score = conversation_comfort_answer.score

    prompt = build_prqc_prompt(messages, relationship_feeling_score, conversation_comfort_score)
    raw_output = invoke_llm(llm_client, prompt)
    return parse_prqc_response(raw_output)