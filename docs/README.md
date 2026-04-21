# Docs

이 폴더는 `PROJECT`의 운영 정책, 규칙 기반 처리 구조, 그리고 제한적 LLM 연동 전제 조건을 정리하는 문서를 모아두는 곳이다.

## 문서 목록

- [`CHATBOT_OPERATION_POLICY_V2.md`](./CHATBOT_OPERATION_POLICY_V2.md)
  챗봇 운영의 최상위 정책 문서다. `AI_MODE`, pending candidate, telemetry, handoff vocabulary, LLM 호출 경계를 런타임 강제 기준으로 정리한다.
- [`STAGE2_RULE_ENGINE.md`](./STAGE2_RULE_ENGINE.md)
  2단계 규칙 엔진의 목적, 공통 계약, 현재 구현 상태, 구현 순서를 정리한다.
- [`RULE_FIRST_LLM_HANDOFF.md`](./RULE_FIRST_LLM_HANDOFF.md)
  규칙 기반 처리 우선 원칙과 3단계 LLM 호출 직전까지 필요한 구조를 정리한다. 운영 판단의 최종 기준은 v2 정책 문서다.
- [`GEMINI_RECOVERY_SETUP.md`](./GEMINI_RECOVERY_SETUP.md)
  Gemini API 키 설정, request builder, JSON parser, classifier 주입 위치를 정리한다. 호출 허용 여부는 v2 정책의 `AI_MODE`와 호출 게이트를 따른다.
- [`STRUCTURED_INTERACTION_POLICY.md`](./STRUCTURED_INTERACTION_POLICY.md)
  unknown fallback 버튼 유도, 자연어 수정 확인 단계, enum 제한 LLM 정책의 배경과 상호작용 원칙을 정리한다.

## 현재 기준

- 운영 정책의 최상위 기준은 [`CHATBOT_OPERATION_POLICY_V2.md`](./CHATBOT_OPERATION_POLICY_V2.md)다.
- Gemini recovery classifier 인프라는 구현되어 있다.
- 실제 메시지 핸들러 자동 호출 범위는 v2 정책에 맞춰 점진적으로 연결한다.
- 먼저 2단계 규칙 엔진을 공통 파이프라인으로 만든다.
- `normalization -> intent routing -> slot/alias resolution -> validation/repair` 순서로 확장한다.
