from app.pipeline.consultation.consultation import detect_crisis_signal


def test_detects_suicidal_expression():
    assert detect_crisis_signal("요즘 너무 힘들어서 죽고 싶다는 생각이 들어") is True


def test_does_not_flag_ordinary_relationship_complaint():
    assert detect_crisis_signal("걔 때문에 너무 짜증나고 스트레스 받아") is False


def test_crisis_response_does_not_include_hotline_text():
    # 백엔드가 safetyNotice로 공식 안내 문구(1393 등)를 통제하기로 합의했으므로,
    # AI 응답은 짧은 공감 문구만 담고 구체적 리소스 텍스트는 만들지 않는다.
    from app.pipeline.consultation.consultation import build_crisis_response

    response = build_crisis_response()

    assert "1393" not in response
    assert len(response) > 0
