# Model Recovery Setup

## 1. 목적

이 문서는 구조화 입력 recovery를 위한 외부 모델 classifier를 런타임에 연결할 때 필요한 구성 원칙을 설명한다.

이 문서는 특정 회사나 제품명을 source of truth로 두지 않는다. 중요한 것은 공급자 이름이 아니라 아래 제약을 만족하는가이다.

- JSON-only 출력
- enum 제한 action
- current-step recovery classifier 역할
- policy gate 뒤에서만 호출

## 2. 런타임 전제

모델 연결은 아래 조건을 만족해야 한다.

- API key 또는 동등한 자격 증명이 안전하게 주입된다.
- timeout과 retry 정책이 명시된다.
- response parser가 JSON schema를 강제한다.
- low confidence 결과를 버릴 수 있다.
- 비활성 모드에서 rules-only fallback이 즉시 가능하다.

## 3. 권장 구성 요소

- request builder
- JSON parser
- schema validator
- confidence gate
- policy adapter
- classifier provider wrapper

## 4. request 입력 구조

모델 입력은 대화 전체가 아니라 최소 상태만 사용한다.

- `canonical_intent`
- `current_step`
- `current_question`
- `expected_input_type`
- `allowed_value_shape`
- `latest_user_message`
- `recent_messages_summary`
- `locale`
- `recovery_attempt_count`
- `hard_constraints`

## 5. response 출력 구조

권장 출력 필드:

- `classification`
- `relevance_to_current_step`
- `normalized_candidate`
- `candidate_confidence`
- `needs_clarification`
- `clarification_question`
- `needs_human`
- `human_handoff_reason`
- `safety_flags`

## 6. 주입 위치 원칙

- 핸들러는 provider SDK 세부사항을 직접 알지 않는다.
- 핸들러는 classifier interface만 의존한다.
- provider wrapper는 runtime configuration과 parser를 내부에서 처리한다.
- policy adapter가 비활성화하면 provider를 호출하지 않는다.

## 7. fallback 원칙

아래 경우는 rules-only fallback으로 내려간다.

- 자격 증명 미설정
- timeout
- network 오류
- invalid JSON
- schema validation 실패
- low confidence
- policy disabled

## 8. 운영 메모

- 모델 연결은 선택 기능이다.
- 모델이 꺼져 있어도 structured input, fallback, handoff는 계속 동작해야 한다.
- launch readiness 판단은 품질, 비용, 가용성 gate 기준으로 한다.

## 9. 최종 요약

- 공급자 이름보다 classifier 역할과 출력 제약이 중요하다.
- 모델 호출은 policy gate 뒤에서만 허용한다.
- 실패 시 rules-only fallback을 유지한다.
- farmer-facing main path는 모델 없이도 작동해야 한다.
