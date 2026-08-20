from app.pipeline.analysis.ingest import verify_sha256


def test_returns_true_when_hash_matches():
    data = b"hello world"
    correct_hash = "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"

    assert verify_sha256(data, correct_hash) is True


def test_returns_false_when_hash_does_not_match():
    data = b"hello world"

    assert verify_sha256(data, "0000000000000000000000000000000000000000000000000000000000000") is False
