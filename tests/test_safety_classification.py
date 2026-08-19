from app.pipeline.consultation import classify_safety_signal


def test_classifies_crisis_support_when_crisis_keyword_present():
    signal = classify_safety_signal(
        user_message="죽고 싶다는 생각이 들어", risk_components=[]
    )

    assert signal == "CRISIS_SUPPORT"


def test_crisis_takes_priority_even_with_no_accumulated_risk():
    signal = classify_safety_signal(
        user_message="자해하고 싶은 충동이 들어", risk_components=["Passion"]
    )

    assert signal == "CRISIS_SUPPORT"


def test_classifies_support_recommendation_when_risk_accumulates_without_crisis():
    signal = classify_safety_signal(
        user_message="요즘 연락이 뜸해요",
        risk_components=["Commitment", "Trust", "Passion"],
    )

    assert signal == "SUPPORT_RECOMMENDATION"


def test_classifies_none_for_ordinary_low_risk_message():
    signal = classify_safety_signal(
        user_message="요즘 연락이 뜸해요", risk_components=["Passion"]
    )

    assert signal is None
