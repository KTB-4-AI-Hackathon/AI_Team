from app.pipeline.preprocess import parse_messages


def test_parses_single_message_line():
    raw = "2024년 1월 1일 오전 10:23, 민수 : 안녕"

    messages = parse_messages(raw)

    assert len(messages) == 1
    assert messages[0].speaker == "민수"
    assert messages[0].text == "안녕"
    assert messages[0].timestamp.hour == 10
    assert messages[0].timestamp.minute == 23


def test_ignores_date_separators_and_system_messages():
    raw = "\n".join(
        [
            "--------------- 2024년 1월 1일 월요일 ---------------",
            "민수님이 들어왔습니다.",
            "2024년 1월 1일 오전 10:23, 민수 : 안녕",
            "2024년 1월 1일 오후 12:01, 나 : 점심 먹었어?",
            "민수님이 나갔습니다.",
        ]
    )

    messages = parse_messages(raw)

    assert len(messages) == 2
    assert [m.speaker for m in messages] == ["민수", "나"]
    assert messages[1].timestamp.hour == 12
