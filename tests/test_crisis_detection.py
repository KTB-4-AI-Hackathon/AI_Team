from app.pipeline.consultation import detect_crisis_signal


def test_detects_suicidal_expression():
    assert detect_crisis_signal("요즘 너무 힘들어서 죽고 싶다는 생각이 들어") is True


def test_does_not_flag_ordinary_relationship_complaint():
    assert detect_crisis_signal("걔 때문에 너무 짜증나고 스트레스 받아") is False


def test_crisis_response_includes_1393_hotline():
    from app.pipeline.consultation import build_crisis_response

    response = build_crisis_response()

    assert "1393" in response
