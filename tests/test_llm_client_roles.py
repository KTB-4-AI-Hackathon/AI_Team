from app.pipeline.llm_client import invoke_llm


class _CapturingClient:
    def __init__(self):
        self.received_messages = None

    def invoke(self, langchain_messages):
        self.received_messages = langchain_messages

        class _Response:
            content = "ok"

        return _Response()


def test_maps_assistant_role_to_ai_message_type():
    client = _CapturingClient()
    prompt = [
        {"role": "system", "content": "지침"},
        {"role": "user", "content": "질문"},
        {"role": "assistant", "content": "이전 답변"},
        {"role": "user", "content": "다음 질문"},
    ]

    invoke_llm(client, prompt)

    roles = [m.type for m in client.received_messages]
    assert roles == ["system", "human", "ai", "human"]
