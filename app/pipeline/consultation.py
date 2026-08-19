from app.pipeline.llm_client import invoke_llm, stream_llm
from app.schemas import ScoreResult

_CRISIS_KEYWORDS = [
    "죽고 싶",
    "자살",
    "자해",
    "살고 싶지",
]


def detect_crisis_signal(text: str) -> bool:
    return any(keyword in text for keyword in _CRISIS_KEYWORDS)


_TOTAL_PRQC_COMPONENTS = 6
_ESCALATION_RATIO = 0.5


def should_recommend_professional_help(risk_components: list[str]) -> bool:
    return len(risk_components) / _TOTAL_PRQC_COMPONENTS >= _ESCALATION_RATIO


def build_crisis_response() -> str:
    return (
        "지금 많이 힘드신 것 같아요. 저는 이런 순간에 충분한 도움을 드리기 어려운 AI라, "
        "혼자 견디지 마시고 전문가와 이야기 나눠보셨으면 해요."
    )


def classify_safety_signal(user_message: str, risk_components: list[str]) -> str | None:
    if detect_crisis_signal(user_message):
        return "CRISIS_SUPPORT"
    if should_recommend_professional_help(risk_components):
        return "SUPPORT_RECOMMENDATION"
    return None


_SYSTEM_PROMPT_TEMPLATE = """당신은 관계 고민을 들어주는 상담 도우미입니다. 반드시 아래 4단계 응답 구조를 따르세요.

1. 한계 인정: 확정적으로 진단하지 마세요 ("가스라이팅이 맞다" 같은 단정 금지). "제가 확정할 수 있는 부분은 아니에요" 같은 표현으로 먼저 선을 그으세요.
2. 관찰된 사실 진술: 아래 분석 데이터에 근거해, 판단이 아닌 관찰된 패턴만 언급하세요.
3. 선택은 사용자에게 위임: 결정을 대신 내려주지 말고, 사용자가 스스로 판단할 수 있도록 질문하거나 정보를 제공하세요.
4. 전문 상담 연계: 아래 "전문 상담 권유 필요" 표시가 있으면, 자연스럽게 전문 상담 리소스 이용을 권유하세요.

[관계 유형]: {relationship_type}
[위험 신호 구성요소와 근거]:
{risk_evidence}
[전문 상담 권유 필요]: {needs_escalation}
"""


def build_consultation_prompt(
    history: list[dict[str, str]],
    user_message: str,
    score_result: ScoreResult,
    relationship_type: str,
) -> list[dict[str, str]]:
    risk_evidence = "\n".join(
        f"- {component}: {score_result.evidence.get(component, '근거 없음')}"
        for component in score_result.risk_components
    ) or "없음"

    system_message = _SYSTEM_PROMPT_TEMPLATE.format(
        relationship_type=relationship_type,
        risk_evidence=risk_evidence,
        needs_escalation=should_recommend_professional_help(score_result.risk_components),
    )

    return (
        [{"role": "system", "content": system_message}]
        + list(history)
        + [{"role": "user", "content": user_message}]
    )


def consult(
    history: list[dict[str, str]],
    user_message: str,
    score_result: ScoreResult,
    relationship_type: str,
    llm_client,
) -> str:
    if detect_crisis_signal(user_message):
        return build_crisis_response()

    prompt = build_consultation_prompt(
        history=history,
        user_message=user_message,
        score_result=score_result,
        relationship_type=relationship_type,
    )
    return invoke_llm(llm_client, prompt)


def stream_consult(
    history: list[dict[str, str]],
    user_message: str,
    score_result: ScoreResult,
    relationship_type: str,
    llm_client,
):
    if detect_crisis_signal(user_message):
        yield build_crisis_response()
        return

    prompt = build_consultation_prompt(
        history=history,
        user_message=user_message,
        score_result=score_result,
        relationship_type=relationship_type,
    )
    yield from stream_llm(llm_client, prompt)
