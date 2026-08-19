from app.pipeline.preprocess import anonymize_messages
from app.schemas import Message

_TS = __import__("datetime").datetime(2024, 1, 1, 10, 23)


def test_replaces_my_name_with_na_and_others_with_sangdaebang():
    messages = [
        Message(speaker="민수", timestamp=_TS, text="안녕"),
        Message(speaker="지영", timestamp=_TS, text="어 안녕"),
    ]

    anonymized = anonymize_messages(messages, my_name="지영")

    assert anonymized[0].speaker == "상대방"
    assert anonymized[1].speaker == "나"
