# Rule-First LLM Handoff

## 1. 목적

이 문서는 규칙 우선 처리 원칙 아래에서 모델 호출이 허용되는 조건과 handoff 구조를 설명한다.

핵심 원칙은 아래와 같다.

- 메인 경로는 규칙 기반 처리다.
- 모델은 현재 step recovery 판단을 돕는 제한적 보조기다.
- handoff는 모델 실패의 대체재가 아니라 별도의 운영 경로다.

## 2. 기본 흐름

권장 런타임 순서는 다음과 같다.

1. command/button
2. step parser
3. cheap gate
4. rule repair
5. model policy check
6. model invocation
7. schema validation
8. validator + state machine 재검증
9. confirm, fallback, handoff 중 하나 선택

## 3. 모델로 넘기기 전 필요한 조건

모델 호출 전에는 아래 정보가 정리되어 있어야 한다.

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

이 정보가 정리되지 않으면 모델 호출을 지연하거나 금지한다.

## 4. 모델의 책임

모델은 아래 역할만 수행한다.

- 현재 step 관련성 판정
- 회수 가능한 입력인지 판단
- 구조화된 후보 생성
- clarification question 1개 생성
- human handoff 필요 여부 표시

모델이 수행하지 않는 역할:

- 최종 저장
- 승인/반려 결정
- intent catalog 대체
- 장문 상담 응대
- 운영 우선순위 판단

## 5. 허용 도메인

현재 제품 범위에서 모델 보조를 고려할 수 있는 도메인은 다음과 같다.

- fertilizer confirm/edit ambiguity
- yield confirm/edit ambiguity
- input resolve ambiguity
- repeated structured-input recovery

## 6. 금지 도메인

아래는 모델 호출 금지 대상이다.

- 버튼/슬래시 명령
- help/menu/support intent
- safety gate 대상 입력
- parser/validator로 확정 가능한 입력
- cheap gate에서 차단된 입력
- 데모성 기능

## 7. 출력 제약

모델 출력은 JSON-only 구조여야 하며, enum 제한을 벗어나면 안 된다.

예시:

```json
{
  "classification": "needs_clarification",
  "relevance_to_current_step": "high",
  "normalized_candidate": {
    "value": "20kg"
  },
  "candidate_confidence": 0.72,
  "needs_clarification": true,
  "clarification_question": "정확한 수치를 다시 입력해 주세요.",
  "needs_human": false,
  "human_handoff_reason": null,
  "safety_flags": []
}
```

## 8. Pending Candidate 규칙

- 모델이 만든 값은 pending candidate로만 저장한다.
- confirm 전에는 authoritative value처럼 다루지 않는다.
- discard, confirm, handoff 전환 시 telemetry를 남긴다.

## 9. Handoff 기준

아래 경우는 모델보다 handoff가 우선이다.

- explicit help 요청
- 상담원 연결 요청
- complaint
- repeated failure
- OCR/typed input 충돌 반복
- correction/withdrawal 같은 운영성 요청

권장 route hint:

- `support.escalate`
- `manual_resolution_required`
- `admin_follow_up_queue`

## 10. 실패 처리

모델 호출 실패 시:

- 조용히 실패하지 않는다.
- `llm_failed` 또는 `llm_skipped_by_policy`를 남긴다.
- `rules-only validation + admin review` fallback을 유지한다.
- farmer-facing UX는 restart, reask, handoff 중 하나로 이어져야 한다.

## 11. 최종 요약

- 규칙 우선 원칙이 메인 경로다.
- 모델은 recovery classifier로만 사용한다.
- 모델 출력은 항상 구조화 결과로 제한한다.
- confirm 없이 저장하지 않는다.
- handoff는 명시적 정책 경로로 유지한다.
