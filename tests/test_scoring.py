import json
from datetime import datetime

from app.pipeline.scoring import build_prqc_prompt, parse_prqc_response
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


def test_parses_clean_json_response_into_score_result():
    raw_output = json.dumps(
        {
            "Satisfaction": 6,
            "Commitment": 5,
            "Intimacy": 6,
            "Trust": 5,
            "Passion": 4,
            "Love": 6,
            "evidence": {"Satisfaction": "긍정 표현이 꾸준함"},
        }
    )

    result = parse_prqc_response(raw_output)

    assert result.scores["Satisfaction"] == 6
    assert result.evidence["Satisfaction"] == "긍정 표현이 꾸준함"


def test_flags_scores_below_four_as_risk_components():
    raw_output = json.dumps(
        {
            "Satisfaction": 6,
            "Commitment": 3,
            "Intimacy": 6,
            "Trust": 2,
            "Passion": 4,
            "Love": 6,
            "evidence": {},
        }
    )

    result = parse_prqc_response(raw_output)

    assert set(result.risk_components) == {"Commitment", "Trust"}


def test_strips_markdown_code_fence_before_parsing():
    raw_output = "```json\n" + json.dumps(
        {
            "Satisfaction": 6,
            "Commitment": 6,
            "Intimacy": 6,
            "Trust": 6,
            "Passion": 6,
            "Love": 6,
            "evidence": {},
        }
    ) + "\n```"

    result = parse_prqc_response(raw_output)

    assert result.scores["Satisfaction"] == 6
