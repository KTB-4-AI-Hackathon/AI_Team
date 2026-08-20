import gzip

from app.pipeline.analysis.ingest import decompress_gzip


def test_decompresses_gzip_bytes_to_text():
    original = '{"sender":"SELF","sentAt":"2026-08-17T12:04:00+09:00","text":"안녕"}'
    compressed = gzip.compress(original.encode("utf-8"))

    result = decompress_gzip(compressed)

    assert result == original
