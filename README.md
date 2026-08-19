# AI Team — 관계온도 분석 서버

카카오톡 대화 로그를 받아 PRQC(관계 품질) 6개 요소를 점수화하고 위험 신호를 판정하는 AI 서버입니다. **백엔드(Spring)가 내부적으로 호출하는 서비스**이고, 프론트엔드는 이 서버를 직접 호출하지 않습니다.

## 이 서버가 하는 일

1. 백엔드가 카카오톡 원본을 파싱·익명화해서 만든 정규화 대화 파일(NDJSON, gzip)을 받습니다.
2. LLM(Gemini 또는 Claude)에게 대화를 보여주고, 심리학 PRQC 척도의 6개 요소(만족·헌신·친밀감·신뢰·열정·애정)를 1~7점으로 채점하게 합니다.
3. 점수가 낮은(위험) 요소를 판정하고, 판정 근거 문장을 함께 받습니다.
4. 백엔드가 요구하는 형태(0~100점, 소문자 키)로 변환해서 돌려줍니다.

## 전체 흐름에서 이 서버의 위치

```
프론트엔드
  └─ POST /relationships/{id}/analyses  (백엔드 API, 202 즉시 응답)
       ↓
백엔드 Worker
  ├─ 업로드된 카카오톡 파일 → 정규화 NDJSON(gzip)으로 변환
  ├─ 이 AI 서버를 동기 호출   ← 우리가 만드는 부분
  └─ 결과를 저장하고 Job 완료 처리
       ↓
프론트엔드
  └─ GET /analysis-jobs/{jobId} 폴링으로 결과 확인
```

분석에 20~30초 정도 걸릴 수 있지만, 진행률 API 같은 건 우리가 따로 만들지 않습니다. **한 번 호출에 최종 결과만** 돌려주면 되고, 프론트엔드에 보여줄 진행률 표시는 백엔드가 자체적으로 처리합니다.

## 파이프라인 내부 구조

```
raw NDJSON(gzip)
   │
   ▼
[app/pipeline/ingest.py]         gzip 해제 → sha256 무결성 검증 → NDJSON 파싱
   │   (sender: SELF/OTHER 를 나/상대방으로 변환)
   ▼
[app/schemas.py] Message 리스트   ← 여기서부터는 카카오 원본이든 정규화 데이터든 동일하게 처리됨
   │
   ▼
[app/pipeline/scoring.py]
   ├─ build_prqc_prompt()    대화를 LLM 프롬프트로 변환
   ├─ (LLM 호출)              app/pipeline/llm_client.py — Claude/Gemini 중 택1, 호출 인터페이스는 동일
   ├─ parse_prqc_response()   LLM이 뱉은 JSON 텍스트를 파싱 (마크다운 코드펜스 자동 제거)
   └─ score_relationship()    위 단계를 묶어 실행 + 위험 요소(4점 미만) 판정
   │
   ▼
[app/schemas.py] ScoreResult      내부 표준 포맷 (1~7점, Title-case 키)
   │
   ▼
[app/pipeline/response_adapter.py]   0~100점 · 소문자 키로 변환 (백엔드 계약에 맞춤)
   │
   ▼
[app/main.py] FastAPI 엔드포인트가 위 전체를 실행하고 최종 응답을 반환
```

**설계 포인트 — LLM 교체가 한 줄로 끝나도록 만들었습니다.** `build_prqc_prompt`/`parse_prqc_response`는 Claude든 Gemini든 상관없이 동일하게 동작하는 순수 함수라, 실제 API 호출부(`llm_client.py`)만 바꾸면 됩니다. 지금은 Claude API 키가 초기 테스트에서 거부되어 **Gemini를 기본값**으로 쓰고 있습니다.

## 로컬에서 실행하기

```bash
# 1. 가상환경 생성 및 의존성 설치
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. 환경변수 설정
cp .env.example .env
# .env를 열어서 GOOGLE_API_KEY, AI_INTERNAL_SERVICE_TOKEN 값을 채워주세요

# 3. 테스트 실행
python -m pytest -v

# 4. 서버 실행
uvicorn app.main:app --reload --port 8000
```

`AI_INTERNAL_SERVICE_TOKEN`은 백엔드와 AI 서버가 **같은 값**을 각자 `.env`에 넣어서 맞춰야 인증이 통과됩니다 (임의의 랜덤 문자열이면 됩니다 — 실제 비밀번호처럼 유출되면 안 되니 저장소에는 커밋하지 않습니다).

## API 명세

### `POST /internal/v1/prqc-analyses`

백엔드 Worker 전용 내부 API입니다. 프론트엔드는 이 엔드포인트를 직접 호출하지 않습니다.

**인증**: `Authorization: Bearer {AI_INTERNAL_SERVICE_TOKEN}` 헤더 필수.

**요청** (`multipart/form-data`):

| 필드 | 타입 | 설명 |
|---|---|---|
| `analysisId` | string | 백엔드가 발급한 분석 작업 ID |
| `relationshipType` | string | `FRIEND`, `FAMILY` 등 (현재는 전달만 받고 점수 계산에는 아직 반영 안 함) |
| `sha256` | string | 업로드 파일의 sha256 해시 (무결성 검증용) |
| `file` | binary | gzip 압축된 NDJSON 대화 파일 |

NDJSON 한 줄 형식 예시:
```json
{"sender":"SELF","sentAt":"2026-08-17T10:20:00+09:00","text":"오늘 저녁에 시간 괜찮아?"}
```

**응답 (200)**:
```json
{
  "analysisId": "a1",
  "modelVersion": "prqc-2026-08-19.1",
  "components": {
    "satisfaction": 83, "commitment": 50, "intimacy": 17,
    "trust": 50, "passion": 0, "love": 17
  },
  "evidences": [
    { "component": "passion", "score": 0, "summary": "..." }
  ]
}
```

`overall.score`(종합 관계온도)는 이 서버가 만들지 않습니다 — 6개 요소에 관계유형별 가중치를 적용한 최종 점수는 **백엔드**가 계산하기로 합의했습니다.

**에러 응답** (형식은 항상 동일):
```json
{
  "error": { "code": "...", "message": "...", "retryable": true, "requestId": "..." }
}
```

| 상태 | 코드 | 상황 |
|---|---|---|
| 401 | - | Bearer 토큰 불일치 |
| 400 | `FILE_INTEGRITY_MISMATCH` | sha256 검증 실패 |
| 422 | `INSUFFICIENT_MESSAGES` | 대화 메시지가 너무 적음 |
| 503 | `AI_PROVIDER_UNAVAILABLE` | LLM 호출 실패 (`retryable: true`) |

## 프로젝트 구조

```
app/
  main.py                 FastAPI 엔드포인트
  schemas.py               Pydantic 모델 (Message, ScoreResult, AnalysisResponse, ErrorResponse ...)
  pipeline/
    ingest.py                백엔드 정규화 NDJSON 수신 (gzip 해제, 무결성 검증, 파싱)
    preprocess.py             (로컬 테스트/데모 픽스처용) 카카오톡 원본 텍스트 직접 파싱
    scoring.py                 PRQC 프롬프트 생성 + 응답 파싱 + 오케스트레이션
    llm_client.py               Claude/Gemini 클라이언트 (교체 가능한 구조)
    response_adapter.py         내부 ScoreResult → 백엔드 응답 스펙 변환
tests/                    모듈별 테스트 (TDD로 작성, `pytest -v`로 실행)
```

## 참고 — 점수 스케일 관련

- 내부 계산은 PRQC 학술 척도 그대로 **1~7점 Likert 스케일**을 씁니다. API 응답에서만 `(점수-1)/6*100` 공식으로 0~100점으로 환산합니다.
- 위험 신호 판정 기준(4점 미만)은 DAS-4 임상 절단점을 7점 척도로 환산한 값이고, 0~100 환산 시 정확히 50점에 대응합니다.
