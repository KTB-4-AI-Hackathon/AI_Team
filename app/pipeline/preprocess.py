import re
from datetime import datetime

from app.schemas import Message

_MESSAGE_LINE = re.compile(
    r"^(?P<year>\d{4})년 (?P<month>\d{1,2})월 (?P<day>\d{1,2})일 "
    r"(?P<ampm>오전|오후) (?P<hour>\d{1,2}):(?P<minute>\d{2}), "
    r"(?P<speaker>.+?) : (?P<text>.*)$"
)


def anonymize_messages(messages: list[Message], my_name: str) -> list[Message]:
    return [
        m.model_copy(update={"speaker": "나" if m.speaker == my_name else "상대방"})
        for m in messages
    ]


def parse_messages(raw: str) -> list[Message]:
    messages = []
    for line in raw.splitlines():
        match = _MESSAGE_LINE.match(line.strip())
        if not match:
            continue
        messages.append(_to_message(match))
    return messages


def _to_message(match: re.Match) -> Message:
    hour = int(match["hour"])
    if match["ampm"] == "오전":
        hour = 0 if hour == 12 else hour
    else:
        hour = 12 if hour == 12 else hour + 12

    timestamp = datetime(
        int(match["year"]),
        int(match["month"]),
        int(match["day"]),
        hour,
        int(match["minute"]),
    )
    return Message(speaker=match["speaker"], timestamp=timestamp, text=match["text"])
