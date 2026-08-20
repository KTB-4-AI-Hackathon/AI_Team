# PRQC 위험 판정 기준선. 0~100 스케일이 Backend와 주고받는 정식 척도이므로 이 값을 기준으로 삼는다.
# DAS-4 절단점(11/21)을 7점 척도로 환산한 값(약 4점)과 정확히 대응한다.
RISK_CUTOFF_100 = 50

def to_hundred_scale(score_7: int) -> int:
    """내부 1~7 척도 점수를 Backend와 주고받는 0~100 척도로 변환한다."""
    return round((score_7 - 1) / 6 * 100)

def to_seven_scale_cutoff() -> float:
    """0~100 기준 절단점을 1~7 척도로 환산한다. (response_adapter._to_hundred_scale의 역변환)"""
    return RISK_CUTOFF_100 / 100 * 6 + 1