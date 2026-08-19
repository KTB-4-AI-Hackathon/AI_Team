from datetime import datetime

from app.pipeline.scoring import build_prqc_prompt
from app.schemas import Message

_TS = datetime(2024, 1, 1, 10, 23)


def test_prompt_includes_conversation_and_all_six_components():
    messages = [
        Message(speaker="나", timestamp=_TS, text="안녕"),
        Message(speaker="상대방", timestamp=_TS, text="어 오랜만이야"),
    ]

    prompt = build_prqc_prompt(messages)

    assert prompt[0]["role"] == "system"
    assert prompt[1]["role"] == "user"
    for component in ["Satisfaction", "Commitment", "Intimacy", "Trust", "Passion", "Love"]:
        assert component in prompt[0]["content"]
    assert "나: 안녕" in prompt[1]["content"]
    assert "상대방: 어 오랜만이야" in prompt[1]["content"]
