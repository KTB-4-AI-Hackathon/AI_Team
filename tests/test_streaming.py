from app.pipeline.llm_client import stream_llm


class _FakeStreamingClient:
    def stream(self, langchain_messages):
        class _Chunk:
            def __init__(self, content):
                self.content = content

        for text in ["안녕", "하세요", ", 반가워요"]:
            yield _Chunk(text)


def test_yields_text_chunks_as_they_stream_in():
    client = _FakeStreamingClient()
    prompt = [{"role": "user", "content": "안녕"}]

    chunks = list(stream_llm(client, prompt))

    assert chunks == ["안녕", "하세요", ", 반가워요"]


def test_stream_consult_yields_single_crisis_chunk_when_signal_detected():
    from app.pipeline.consultation import stream_consult
    from app.schemas import ScoreResult

    score_result = ScoreResult(
        scores={"Satisfaction": 6, "Commitment": 6, "Intimacy": 6, "Trust": 6, "Passion": 6, "Love": 6},
        risk_components=[],
        evidence={},
    )

    chunks = list(
        stream_consult(
            history=[],
            user_message="죽고 싶다는 생각이 들어",
            score_result=score_result,
            relationship_type="FRIEND",
            llm_client=_FakeStreamingClient(),
        )
    )

    assert len(chunks) == 1
    assert chunks[0] not in ("안녕", "하세요", ", 반가워요")
    assert "1393" not in chunks[0]


def test_stream_consult_yields_llm_chunks_for_ordinary_message():
    from app.pipeline.consultation import stream_consult
    from app.schemas import ScoreResult

    score_result = ScoreResult(
        scores={"Satisfaction": 6, "Commitment": 6, "Intimacy": 6, "Trust": 6, "Passion": 6, "Love": 6},
        risk_components=[],
        evidence={},
    )

    chunks = list(
        stream_consult(
            history=[],
            user_message="요즘 연락이 좀 뜸해요",
            score_result=score_result,
            relationship_type="FRIEND",
            llm_client=_FakeStreamingClient(),
        )
    )

    assert chunks == ["안녕", "하세요", ", 반가워요"]
