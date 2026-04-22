# Gemini Recovery Setup

## 문서 역할

이 문서는 Gemini 연동의 설정 경로와 JSON request/response 구조를 설명하는 구현 문서다.

Gemini 호출 허용 여부, `AI_MODE`, pending candidate 처리, 호출 한도 같은 운영 정책의 최종 기준은 [`CHATBOT_OPERATION_POLICY_V2.md`](./CHATBOT_OPERATION_POLICY_V2.md)를 따른다.

## 목적

이 문서는 `PROJECT`에서 Gemini를 3단계 recovery classifier로 붙이기 위한 설정과 현재 구현 범위를 정리한다.

현재 구현은 아래 범위까지 포함한다.

- `.env`에 Gemini API 키를 넣을 수 있는 설정 슬롯 추가
- `.env`에 `AI_MODE` 정책 게이트 추가
- `Settings`에 Gemini 설정 모델 추가
- `AiMode` enum과 정책 모듈 추가
- `RecoveryContextDraft`를 Gemini `generateContent` 요청으로 바꾸는 request builder 추가
- Gemini JSON 응답을 `LlmRecoveryResult`로 파싱하는 parser 추가
- 텔레그램 앱 부트스트랩 시 정책 게이트를 통과한 Gemini classifier만 `bot_data`에 주입

현재는 아직 recovery classifier를 메시지 핸들러 전역 경로에 자동 호출하지 않는다.

중요한 점은 아래와 같다.

- `GEMINI_API_KEY`가 없으면 `Settings.gemini`는 `None`이다.
- 즉 키가 없을 때는 Gemini 설정 객체 자체를 만들지 않는다.
- `AI_MODE=repair_assist_only`일 때만 edit-intent 보조 분류기를 주입한다.
- `AI_MODE=recovery_assist_only`일 때만 recovery classifier를 주입한다.
- 기존 `ENABLE_LLM_EDIT_INTENT=true`는 `AI_MODE`가 비어 있을 때만 임시 호환 경로로 `repair_assist_only`로 승격된다.
- 민감값은 코드 기본값으로 보관하지 않는다.

## 환경 변수

`.env.example` 기준으로 아래 값을 사용할 수 있다.

```dotenv
BOT_TOKEN=your_bot_token_here
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
GEMINI_API_BASE=https://generativelanguage.googleapis.com/v1beta
GEMINI_TIMEOUT_SECONDS=15
AI_MODE=disabled
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
3. rule repair 실패
4. recovery context 조립
5. 정책 함수가 현재 `AI_MODE`, 호출 한도, 동일 입력 재호출 여부를 확인
6. `bot_data["gemini_recovery_classifier"]` 존재 여부 확인
7. Gemini 호출
8. JSON 결과를 validator와 state machine으로 다시 검증
