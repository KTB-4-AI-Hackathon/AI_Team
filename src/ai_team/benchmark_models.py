import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

from ai_team.client_anthropic import score_all_components_anthropic
from ai_team.client_gemini import score_all_components_gemini
from ai_team.main import classify_speaker
from ai_team.sample_data import SAMPLE_ANALYSIS_REQUEST  # TODO: 실제 샘플 데이터 위치에 맞게 수정


@dataclass
class ModelCandidate:
    provider: str  # 'anthropic' | 'gemini'
    model_name: str


# 비교할 모델 목록
CANDIDATE_MODELS = [
    # ModelCandidate(provider='anthropic', model_name='claude-sonnet-4-6'),
    ModelCandidate(provider='anthropic', model_name='claude-haiku-4-5-20251001'),
    # ModelCandidate(provider='gemini', model_name='gemini-3.1-pro-preview'),
    ModelCandidate(provider='gemini', model_name='gemini-3.5-flash-lite'),
]


def run_single_model(candidate: ModelCandidate) -> tuple[ModelCandidate, float, Exception | None]:
    classified_chats = classify_speaker(
        SAMPLE_ANALYSIS_REQUEST.chats,
        SAMPLE_ANALYSIS_REQUEST.user.nickname,
    )
    start = time.perf_counter()
    error: Exception | None = None
    try:
        if candidate.provider == 'anthropic':
            score_all_components_anthropic(
                chats=classified_chats,
                relationship_type=SAMPLE_ANALYSIS_REQUEST.relationship_type,
                model_name=candidate.model_name,
            )
        elif candidate.provider == 'gemini':
            score_all_components_gemini(
                chats=classified_chats,
                relationship_type=SAMPLE_ANALYSIS_REQUEST.relationship_type,
                model_name=candidate.model_name,
            )
        else:
            raise ValueError(f'알 수 없는 provider: {candidate.provider}')
    except Exception as e:
        error = e
    elapsed = time.perf_counter() - start
    return candidate, elapsed, error


def main() -> None:
    with ThreadPoolExecutor(max_workers=len(CANDIDATE_MODELS)) as executor:
        futures = [executor.submit(run_single_model, candidate) for candidate in CANDIDATE_MODELS]
        for future in as_completed(futures):
            candidate, elapsed, error = future.result()
            status = f'실패: {error!r}' if error else '성공'
            print(f'[{candidate.provider}] {candidate.model_name}: {elapsed:.2f}초 ({status})')


if __name__ == '__main__':
    main()