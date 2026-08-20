from app.pipeline.consultation import build_evidence_refs, build_safety_notice
from app.schemas import ConsultationEvidenceContext


def test_returns_none_when_no_safety_type():
    assert build_safety_notice(None) is None


def test_builds_crisis_support_notice():
    notice = build_safety_notice("CRISIS_SUPPORT")

    assert notice.type == "CRISIS_SUPPORT"
    assert notice.title
    assert notice.message
    assert notice.resourceQuery.category == "CRISIS_SUPPORT"
    assert notice.resourceQuery.region == "KR"


def test_builds_support_recommendation_notice():
    notice = build_safety_notice("SUPPORT_RECOMMENDATION")

    assert notice.type == "SUPPORT_RECOMMENDATION"
    assert notice.resourceQuery.category == "RELATIONSHIP_COUNSELING"


def test_evidence_refs_only_include_risk_components():
    evidences = [
        ConsultationEvidenceContext(
            evidenceId="e1", component="commitment", score=17, summary="선톡이 한쪽으로 쏠림"
        ),
        ConsultationEvidenceContext(
            evidenceId="e2", component="passion", score=83, summary="반응이 빠름"
        ),
    ]

    refs = build_evidence_refs(evidences, risk_components=["commitment"])

    assert len(refs) == 1
    assert refs[0].evidenceId == "e1"
    assert refs[0].label == "선톡이 한쪽으로 쏠림"
