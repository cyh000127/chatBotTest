# Gemini Recovery Setup

## 목적

이 문서는 `PROJECT`에서 Gemini를 3단계 recovery classifier로 붙이기 위한 설정과 현재 구현 범위를 정리한다.

현재 구현은 아래 범위까지 포함한다.

- `.env`에 Gemini API 키를 넣을 수 있는 설정 슬롯 추가
- `.env`에 `ENABLE_LLM_EDIT_INTENT` 정책 게이트 추가
- `Settings`에 Gemini 설정 모델 추가
- `RecoveryContextDraft`를 Gemini `generateContent` 요청으로 바꾸는 request builder 추가
- Gemini JSON 응답을 `LlmRecoveryResult`로 파싱하는 parser 추가
- 텔레그램 앱 부트스트랩 시 정책 게이트를 통과한 Gemini classifier만 `bot_data`에 주입

현재는 아직 메시지 핸들러에서 자동 호출하지 않는다.

중요한 점은 아래와 같다.

- `GEMINI_API_KEY`가 없으면 `Settings.gemini`는 `None`이다.
- 즉 키가 없을 때는 Gemini 설정 객체 자체를 만들지 않는다.
- `ENABLE_LLM_EDIT_INTENT=true`가 아니면 edit-intent 보조 분류기는 주입하지 않는다.
- 민감값은 코드 기본값으로 보관하지 않는다.

## 환경 변수

`.env.example` 기준으로 아래 값을 사용할 수 있다.

```dotenv
BOT_TOKEN=your_bot_token_here
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
GEMINI_API_BASE=https://generativelanguage.googleapis.com/v1beta
GEMINI_TIMEOUT_SECONDS=15
ENABLE_LLM_EDIT_INTENT=false
```

## 구현 위치

- `src/PROJECT/settings.py`
  Gemini 설정 로드
- `src/PROJECT/llm/contracts.py`
  LLM recovery 결과 계약
- `src/PROJECT/llm/gemini_recovery.py`
  Gemini request builder, response parser, classifier
- `src/PROJECT/channels/telegram/app.py`
  앱 시작 시 classifier 주입

## 호출 형태

현재 구현은 Google Gemini 공식 REST `generateContent` 형식을 따른다.

- 인증 헤더: `x-goog-api-key`
- 엔드포인트: `/models/{model}:generateContent`
- 출력 모드: `application/json`
- 출력 스키마: `responseJsonSchema`

즉 Gemini는 자유 대화 응답기가 아니라, JSON-only recovery classifier로 다루는 구조다.

## 다음 연결 포인트

핸들러에 실제 연결할 때는 아래 순서가 권장된다.

1. step parser 실패
2. cheap gate 통과
3. recovery context 조립
4. `bot_data["gemini_recovery_classifier"]` 존재 여부 확인
5. Gemini 호출
6. JSON 결과를 validator와 state machine으로 다시 검증
