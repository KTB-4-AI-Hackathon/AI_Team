from app.schemas import Message

PRQC_COMPONENTS = [
    "Satisfaction",
    "Commitment",
    "Intimacy",
    "Trust",
    "Passion",
    "Love",
]

_SYSTEM_PROMPT = """당신은 대화 로그를 관찰해 관계 품질을 평가하는 분석가입니다.
학술적으로 정립된 관계 품질의 6가지 축(PRQC)을 참고해, 아래 대화에서 관찰 가능한
신호만 근거로 각 구성요소를 1~7점으로 채점하세요. 임상적 진단이 아닌 자기성찰용
참고 지표이니 과도하게 단정적인 판단은 피하세요.

평가할 구성요소: {components}

JSON으로만 응답하세요. 다른 텍스트를 포함하지 마세요. 형식:
{{"Satisfaction": <1-7>, "Commitment": <1-7>, "Intimacy": <1-7>,
  "Trust": <1-7>, "Passion": <1-7>, "Love": <1-7>,
  "evidence": {{"<구성요소>": "<판정 근거 한 문장>", ...}}}}""".format(
    components=", ".join(PRQC_COMPONENTS)
)


def build_prqc_prompt(messages: list[Message]) -> list[dict[str, str]]:
    conversation = "\n".join(f"{m.speaker}: {m.text}" for m in messages)
    return [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": conversation},
    ]
