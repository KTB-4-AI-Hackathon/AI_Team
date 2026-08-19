import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from ai_team.client import score_all_components
from ai_team.main import classify_speaker
from ai_team.sample_data import SAMPLE_ANALYSIS_REQUEST  # TODO: 실제 샘플 데이터 위치에 맞게 수정

# 비교할 모델 목록
CANDIDATE_MODEL_NAMES = [
    'claude-sonnet-4-6',
    'claude-haiku-4-5-20251001',
]


def run_single_model(model_name: str) -> tuple[str, float, Exception | None]:
    classified_chats = classify_speaker(
        SAMPLE_ANALYSIS_REQUEST.chats,
        SAMPLE_ANALYSIS_REQUEST.user.nickname,
    )
    start = time.perf_counter()
    error: Exception | None = None
    try:
        score_all_components(
            chats=classified_chats,
            relationship_type=SAMPLE_ANALYSIS_REQUEST.relationship_type,
            model_name=model_name,
        )
    except Exception as e:
        error = e
    elapsed = time.perf_counter() - start
    return model_name, elapsed, error


def main() -> None:
    with ThreadPoolExecutor(max_workers=len(CANDIDATE_MODEL_NAMES)) as executor:
        futures = [executor.submit(run_single_model, name) for name in CANDIDATE_MODEL_NAMES]
        for future in as_completed(futures):
            model_name, elapsed, error = future.result()
            status = f'실패: {error!r}' if error else '성공'
            print(f'{model_name}: {elapsed:.2f}초 ({status})')


if __name__ == '__main__':
    main()