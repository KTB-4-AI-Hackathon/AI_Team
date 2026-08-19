from app.pipeline.llm_client import invoke_llm, stream_llm
from app.schemas import RelationshipContext

# 자살/자해 관련 표현을 걸러내는 키워드 목록 (AI LLM에 넘기기 전에 먼저 감지)
_CRISIS_KEYWORDS = [
    "죽고 싶",
    "자살",
    "자해",
    "살고 싶지",
]


def detect_crisis_signal(text: str) -> bool:
    # 사용자 메시지에 위기 키워드가 하나라도 포함되어 있으면 True
    return any(keyword in text for keyword in _CRISIS_KEYWORDS)


# PRQC는 6개 구성요소(satisfaction, commitment, intimacy, trust, passion, love)로 구성됨
_TOTAL_PRQC_COMPONENTS = 6
# 6개 중 절반(3개) 이상이 위험 수준이면 전문 상담을 권유할 만큼 심각하다고 판단
_ESCALATION_RATIO = 0.5


def should_recommend_professional_help(risk_components: list[str]) -> bool:
    # 위험 판정된 구성요소 비율이 기준(50%) 이상이면 전문 상담 권유가 필요하다고 판단
    return len(risk_components) / _TOTAL_PRQC_COMPONENTS >= _ESCALATION_RATIO


def build_crisis_response() -> str:
    # 위기 감지 시 LLM 호출 없이 즉시 반환하는 고정 공감 문구.

    # 1393 같은 구체적인 안내 문구는 여기서 만들지 않고 백엔드가 안전 정책에 맞춰 완성할 것임
    # (안내 문구의 최종 결정권은 백엔드가 갖는다)
    
    return (
        "지금 많이 힘드신 것 같아요. 저는 이런 순간에 충분한 도움을 드리기 어려운 AI라, "
        "혼자 견디지 마시고 전문가와 이야기 나눠보셨으면 해요."
    )


def classify_safety_signal(user_message: str, risk_components: list[str]) -> str | None:
    """이번 메시지가 어떤 안전 신호에 해당하는지 분류만 해서 돌려준다.

    - "CRISIS_SUPPORT": 위기 표현 감지 (최우선 판정, 아래 권유 판정보다 우선)
    - "SUPPORT_RECOMMENDATION": 위기는 아니지만 위험 신호가 누적된 상태
    - None: 둘 다 아님 (평범한 상담)

    실제 사용자에게 보여줄 문구는 여기서 안만들고 백엔드가 이 분류값을
    받아서 safetyNotice(제목/메시지/리소스 안내)를 정책에 맞게 완성
    """
    if detect_crisis_signal(user_message):
        return "CRISIS_SUPPORT"
    if should_recommend_professional_help(risk_components):
        return "SUPPORT_RECOMMENDATION"
    return None


# LLM에게 보내는 시스템 프롬프트
# 4단계 응답 구조(한계 인정 → 관찰된 사실 → 선택 위임 → 전문상담 연계)를 강제

_SYSTEM_PROMPT_TEMPLATE = """당신은 관계 고민을 들어주는 상담 도우미입니다. 반드시 아래 4단계 응답 구조를 따르되,
이 단계 구분은 답변을 구성하는 내부 가이드라인일 뿐입니다. "1. 한계 인정" 같은 번호나
라벨을 답변에 그대로 쓰지 마세요. 자연스럽게 이어지는 대화체 문장으로만 답하세요.

1. 한계 인정: 확정적으로 진단하지 마세요 ("가스라이팅이 맞다" 같은 단정 금지). "제가 확정할 수 있는 부분은 아니에요" 같은 표현으로 먼저 선을 그으세요.
2. 관찰된 사실 진술: 아래 분석 데이터에 근거해, 판단이 아닌 관찰된 패턴만 언급하세요.
3. 선택은 사용자에게 위임: 결정을 대신 내려주지 말고, 사용자가 스스로 판단할 수 있도록 질문하거나 정보를 제공하세요.
4. 전문 상담 연계: 아래 "전문 상담 권유 필요" 표시가 있으면, 자연스럽게 전문 상담 리소스 이용을 권유하세요.

[관계 유형]: {relationship_type}
[종합 관계온도(0~100, 참고용)]: {overall_score}
[위험 신호 구성요소와 근거]:
{risk_evidence}
[전문 상담 권유 필요]: {needs_escalation}
"""

# 백엔드가 넘겨주는 컴포넌트 점수는 0~100 스케일이라, "위험"의 기준선도
# 그 스케일에 맞춰 50점으로 잡았다. (관계 수치화 쪽 내부 1~7점 스케일의
# DAS-4 절단점 4점을 0~100으로 환산하면 정확히 50점이 되어 서로 맞아떨어짐)
_RISK_CUTOFF_100 = 50


def risk_components_below_cutoff(components: dict[str, int]) -> list[str]:
    # 0~100점 컴포넌트 중 50점 미만인 것들의 이름 리스트를 반환
    return [component for component, score in components.items() if score < _RISK_CUTOFF_100]


def build_consultation_prompt(
    history: list[dict[str, str]],
    user_message: str,
    relationship_context: RelationshipContext,
) -> list[dict[str, str]]:
    """LLM에게 보낼 메시지 리스트를 만든다

    구조: [시스템 프롬프트] + [이전 대화 이력] + [이번 사용자 메시지]
    시스템 프롬프트 안에 위험 구성요소와 그 근거를 텍스트로 박아 넣어서,
    LLM이 근거 없이 답하지 않고 실제 분석 데이터를 참고하도록 만든다.
    """
    risk_components = risk_components_below_cutoff(relationship_context.components)
    evidence_by_component = {e.component: e.summary for e in relationship_context.evidences}
    risk_evidence = "\n".join(
        f"- {component}: {evidence_by_component.get(component, '근거 없음')}"
        for component in risk_components
    ) or "없음"

    system_message = _SYSTEM_PROMPT_TEMPLATE.format(
        relationship_type=relationship_context.relationshipType,
        overall_score=relationship_context.overallScore,
        risk_evidence=risk_evidence,
        needs_escalation=should_recommend_professional_help(risk_components),
    )

    return (
        [{"role": "system", "content": system_message}]
        + list(history)
        + [{"role": "user", "content": user_message}]
    )


def consult(
    history: list[dict[str, str]],
    user_message: str,
    relationship_context: RelationshipContext,
    llm_client,
) -> str:
    
    # 상담 답변을 한 번에 완성해서 반환 (엔드포인트가 쓰는 함수)
    # 위기 신호가 감지되면 LLM을 아예 호출하지 않고 고정 문구를 바로 반환
    
    if detect_crisis_signal(user_message):
        return build_crisis_response()

    prompt = build_consultation_prompt(
        history=history,
        user_message=user_message,
        relationship_context=relationship_context,
    )
    return invoke_llm(llm_client, prompt)


def stream_consult(
    history: list[dict[str, str]],
    user_message: str,
    relationship_context: RelationshipContext,
    llm_client,
):
    """consult()의 스트리밍 버전 — 답변을 토큰 단위로 하나씩 yield한다.

    지금은 백엔드가 "완성된 답변을 한 번에 달라"고 요청해서 엔드포인트에서
    쓰이진 않지만, 나중에 실시간 스트리밍이 필요해질 경우를 대비해 남겨둠.
    """
    if detect_crisis_signal(user_message):
        yield build_crisis_response()
        return

    prompt = build_consultation_prompt(
        history=history,
        user_message=user_message,
        relationship_context=relationship_context,
    )
    yield from stream_llm(llm_client, prompt)
