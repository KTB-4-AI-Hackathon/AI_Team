from app.pipeline.analysis.ingest import parse_ndjson


def test_parses_ndjson_lines_mapping_self_and_other_to_korean_labels():
    raw = "\n".join(
        [
            '{"sender":"OTHER","sentAt":"2026-08-17T10:20:00+09:00","text":"오늘 저녁에 시간 괜찮아?"}',
            '{"sender":"SELF","sentAt":"2026-08-17T12:04:00+09:00","text":"조금 늦게 끝날 것 같아"}',
        ]
    )

    messages = parse_ndjson(raw)

    assert len(messages) == 2
    assert messages[0].speaker == "상대방"
    assert messages[0].text == "오늘 저녁에 시간 괜찮아?"
    assert messages[1].speaker == "나"
    assert messages[1].timestamp.hour == 12
