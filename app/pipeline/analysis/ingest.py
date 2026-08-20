import gzip
import hashlib
import json
from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from app.schemas import Message

_SPEAKER_LABEL = {"SELF": "나", "OTHER": "상대방"}


class NormalizedLine(BaseModel):
    sender: Literal["SELF", "OTHER"]
    sentAt: datetime
    text: str


def verify_sha256(data: bytes, expected_hash: str) -> bool:
    return hashlib.sha256(data).hexdigest() == expected_hash


def decompress_gzip(data: bytes) -> str:
    return gzip.decompress(data).decode("utf-8")


def parse_ndjson(raw: str) -> list[Message]:
    messages = []
    for line in raw.splitlines():
        if not line.strip():
            continue
        normalized = NormalizedLine.model_validate(json.loads(line))
        messages.append(
            Message(
                speaker=_SPEAKER_LABEL[normalized.sender],
                timestamp=normalized.sentAt,
                text=normalized.text,
            )
        )
    return messages
