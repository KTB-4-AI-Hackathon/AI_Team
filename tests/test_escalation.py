from app.pipeline.consultation import should_recommend_professional_help


def test_recommends_when_half_or_more_components_are_at_risk():
    assert should_recommend_professional_help(["Commitment", "Trust", "Passion"]) is True


def test_does_not_recommend_for_a_single_risk_component():
    assert should_recommend_professional_help(["Passion"]) is False
