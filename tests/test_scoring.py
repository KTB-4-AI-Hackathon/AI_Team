import json
from datetime import datetime

from app.pipeline.scoring import build_prqc_prompt, parse_prqc_response, score_relationship
from app.schemas import AnalysisContext, Message

_TS = datetime(2024, 1, 1, 10, 23)


def test_prompt_includes_conversation_and_all_six_components():
    messages = [
        Message(speaker="나", timestamp=_TS, text="안녕"),
        Message(speaker="상대방", timestamp=_TS, text="어 오랜만이야"),
    ]

    prompt = build_prqc_prompt(messages, 2, 7)

    assert prompt[0]["role"] == "system"
    assert prompt[1]["role"] == "user"
    for component in ["Satisfaction", "Commitment", "Intimacy", "Trust", "Passion", "Love"]:
        assert component in prompt[0]["content"]
    assert "나: 안녕" in prompt[1]["content"]
    assert "상대방: 어 오랜만이야" in prompt[1]["content"]


def test_prompt_includes_pronoun_guidance_and_a_worked_example():
    messages = [Message(speaker="나", timestamp=_TS, text="안녕")]

    prompt = build_prqc_prompt(messages, 2, 7)
    system_message = prompt[0]["content"]

    assert "나'와 '상대방'을 혼동하지" in system_message
    assert "[예시]" in system_message


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


class _FakeLLMClient:
    def __init__(self, response_text: str):
        self._response_text = response_text

    def invoke(self, langchain_messages):
        class _Response:
            content = self._response_text

        return _Response()

def _context_with_check_in(relationship_feeling_score: int, conversation_comfort_score: int) -> AnalysisContext:
    return AnalysisContext.model_validate(
        {
            "user": {"userId": "0198c8a7-3000-7000-8000-000000000002", "displayName": "우", "timezone": "Asia/Seoul"},
            "relationship": {
                "relationshipId": "0198c8a7-3000-7000-8000-000000000003",
                "name": "민지",
                "relationshipType": "FRIEND",
                "status": "ANALYZING",
            },
            "current": {
                "conversationFileId": "0198c8a7-3000-7000-8000-000000000004",
                "checkIn": {
                    "checkInId": "0198c8a7-3000-7000-8000-000000000005",
                    "weekStart": "2026-08-17",
                    "inputAt": "2026-08-17T01:00:00Z",
                    "answers": [
                        {"questionCode": "RELATIONSHIP_FEELING", "score": relationship_feeling_score},
                        {"questionCode": "CONVERSATION_COMFORT", "score": conversation_comfort_score},
                    ],
                },
            },
            "history": [],
        }
    )

def test_score_relationship_orchestrates_prompt_build_and_response_parse():
    messages = [
        Message(speaker="나", timestamp=_TS, text="안녕"),
        Message(speaker="상대방", timestamp=_TS, text="어 오랜만이야"),
    ]
    fake_client = _FakeLLMClient(
        json.dumps(
            {
                "Satisfaction": 6,
                "Commitment": 3,
                "Intimacy": 6,
                "Trust": 6,
                "Passion": 6,
                "Love": 6,
                "evidence": {"Commitment": "선톡이 한쪽으로 쏠림"},
            }
        )
    )

    result = score_relationship(messages, fake_client, _context_with_check_in(2, 7))

    assert result.scores["Satisfaction"] == 6
    assert result.risk_components == ["Commitment"]
    assert result.evidence["Commitment"] == "선톡이 한쪽으로 쏠림"


def test_score_relationship_accepts_validated_analysis_context_without_changing_prompt_behavior():
    context = AnalysisContext.model_validate(
        {
            "user": {"userId": "0198c8a7-3000-7000-8000-000000000002", "displayName": "우", "timezone": "Asia/Seoul"},
            "relationship": {
                "relationshipId": "0198c8a7-3000-7000-8000-000000000003",
                "name": "민지",
                "relationshipType": "FRIEND",
                "status": "ANALYZING",
            },
            "current": {
                "conversationFileId": "0198c8a7-3000-7000-8000-000000000004",
                "checkIn": {
                    "checkInId": "0198c8a7-3000-7000-8000-000000000005",
                    "weekStart": "2026-08-17",
                    "inputAt": "2026-08-17T01:00:00Z",
                    "answers": [
                        {"questionCode": "RELATIONSHIP_FEELING", "score": 6},
                        {"questionCode": "CONVERSATION_COMFORT", "score": 6},
                    ],
                },
            },
            "history": [],
        }
    )
    fake_client = _FakeLLMClient(
        json.dumps(
            {
                "Satisfaction": 6,
                "Commitment": 6,
                "Intimacy": 6,
                "Trust": 6,
                "Passion": 6,
                "Love": 6,
                "evidence": {"Trust": "약속을 지켰어요."},
            }
        )
    )

    result = score_relationship([Message(speaker="나", timestamp=_TS, text="안녕")], fake_client, context)

    assert result.scores["Trust"] == 6
