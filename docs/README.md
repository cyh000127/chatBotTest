# Docs

이 폴더는 `PROJECT`의 규칙 기반 처리 구조와 향후 3단계 LLM 연동 전제 조건을 정리하는 문서를 모아두는 곳이다.

## 문서 목록

- [`STAGE2_RULE_ENGINE.md`](./STAGE2_RULE_ENGINE.md)
  2단계 규칙 엔진의 목적, 공통 계약, 현재 구현 상태, 구현 순서를 정리한다.
- [`RULE_FIRST_LLM_HANDOFF.md`](./RULE_FIRST_LLM_HANDOFF.md)
  규칙 기반 처리 우선 원칙과 3단계 LLM 호출 직전까지 필요한 구조를 정리한다.
- [`GEMINI_RECOVERY_SETUP.md`](./GEMINI_RECOVERY_SETUP.md)
  Gemini API 키 설정, request builder, JSON parser, classifier 주입 위치를 정리한다.

## 현재 기준

- Gemini recovery classifier 인프라는 구현되어 있다.
- 실제 메시지 핸들러 자동 호출은 아직 연결하지 않는다.
- 먼저 2단계 규칙 엔진을 공통 파이프라인으로 만든다.
- `normalization -> intent routing -> slot/alias resolution -> validation/repair` 순서로 확장한다.
