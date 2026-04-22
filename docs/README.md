# Docs

이 폴더는 `PROJECT`의 운영 정책, 규칙 기반 처리 구조, 그리고 제한적 LLM 연동 전제 조건을 정리하는 문서를 모아두는 곳이다.

## 문서 목록

- [`CHATBOT_OPERATION_POLICY_V2.md`](./CHATBOT_OPERATION_POLICY_V2.md)
  챗봇 운영의 기준 문서다. 상위 정책 정렬 메모, pending candidate, telemetry, handoff vocabulary, LLM 호출 경계를 함께 정리한다.
- [`STAGE2_RULE_ENGINE.md`](./STAGE2_RULE_ENGINE.md)
  2단계 규칙 엔진의 목적, 공통 계약, 현재 구현 상태, 구현 순서를 정리한다.
- [`RULE_FIRST_LLM_HANDOFF.md`](./RULE_FIRST_LLM_HANDOFF.md)
  규칙 기반 처리 우선 원칙과 3단계 LLM 호출 직전까지 필요한 구조를 정리한다. 운영 판단의 최종 기준은 v2 정책 문서다.
- [`GEMINI_RECOVERY_SETUP.md`](./GEMINI_RECOVERY_SETUP.md)
  Gemini API 키 설정, request builder, JSON parser, classifier 주입 위치를 정리한다. 현재 repo의 `.env` `AI_MODE`는 상위 정책을 흉내 내는 source of truth가 아니라 runtime-local helper gate로 설명한다.
- [`STRUCTURED_INTERACTION_POLICY.md`](./STRUCTURED_INTERACTION_POLICY.md)
  unknown fallback 버튼 유도, 자연어 수정 확인 단계, enum 제한 LLM 정책의 배경과 상호작용 원칙을 정리한다.

## 현재 기준

- 운영 정책의 최상위 기준은 [`CHATBOT_OPERATION_POLICY_V2.md`](./CHATBOT_OPERATION_POLICY_V2.md)다.
- Gemini recovery classifier 인프라는 구현되어 있다.
- 실제 메시지 핸들러의 edit-intent 보조 호출 범위는 v2 정책 기준으로 제한 연결되어 있다.
- 현재 repo는 상위 policy record, fallback mode, release gate가 직접 연결되어 있지 않아 `.env` `AI_MODE`를 local helper gate로 사용한다.
- handoff vocabulary는 `support.escalate`, `manual_resolution_required`, 관리자 follow-up queue 기준으로 정렬하는 방향을 따른다.
- 먼저 2단계 규칙 엔진을 공통 파이프라인으로 만든다.
- `normalization -> intent routing -> slot/alias resolution -> validation/repair` 순서로 확장한다.
- unknown 입력 경계, pending candidate, handoff vocabulary는 정책 코드와 테스트에 반영되어 있다.

## 검증 기준

- 전체 검증 명령: `python -m pytest`
- 정책 관련 핵심 검증 범위:
  - `tests/unit/test_ai_policy.py`
  - `tests/unit/test_repair_candidate_flow.py`
  - `tests/unit/test_rule_engine_recovery_context.py`
  - `tests/contract/test_rule_engine_cross_domain_fixtures.py`
