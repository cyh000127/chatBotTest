# CHATBOT_OPERATION_POLICY_V2

## 1. 목적

이 문서는 챗봇 운영 규칙을 `문서 -> 정책 코드 -> 런타임 강제` 순서로 고정하기 위한 v2 정책 문서다.

`llm rule.md`가 LLM 설계 원칙과 step recovery 구조를 설명하는 문서라면, 이 문서는 실제 코드와 런타임에서 바로 강제해야 하는 정책을 정의한다.

이 문서의 핵심 목표는 아래와 같다.

- 메인 경로를 끝까지 룰베이스로 유지한다.
- LLM을 예외적 보조 판정기로 제한한다.
- 후보값과 확정값을 분리해 오작동을 막는다.
- 버튼/재질문/사람 연결을 포함한 guided recovery를 기본으로 둔다.
- vocabulary, telemetry, handoff 규칙을 코드와 동일한 이름으로 고정한다.

## 2. 핵심 원칙

- 메인 경로는 끝까지 룰베이스다.
- unknown 입력은 종료하지 않고 버튼으로 회수한다.
- 자연어 수정은 직접 반영하지 않고 수정 의도 신호로만 쓴다.
- LLM 결과는 항상 validator와 state machine을 다시 거친다.
- bot과 LLM은 authoritative write owner가 아니다.
- candidate value는 pending candidate로만 저장한다.

## 3. Vocabulary 고정

### 3.1 AI_MODE

런타임 AI 정책 상태는 아래 enum으로 고정한다.

- `disabled`
- `repair_assist_only`
- `recovery_assist_only`
- `manual_review_fallback`

의미는 아래와 같다.

- `disabled`
  - 모든 LLM 호출 금지
- `repair_assist_only`
  - 수정 의도/수정 대상 판정 보조만 허용
- `recovery_assist_only`
  - 현재 structured step recovery 보조만 허용
- `manual_review_fallback`
  - 자동 LLM 호출 금지
  - rules-only + manual review 경로만 허용

### 3.2 Telemetry 이벤트

아래 이벤트 이름은 코드와 로그에서 그대로 사용한다.

- `rule_matched`
- `cheap_gate_blocked`
- `fallback_shown`
- `llm_invoked`
- `llm_skipped_by_policy`
- `llm_rejected_low_confidence`
- `handoff_requested`
- `pending_candidate_created`
- `pending_candidate_confirmed`
- `pending_candidate_discarded`

### 3.3 Handoff / 운영 경로 vocabulary

아래 vocabulary를 handoff 조건과 운영 연결에 사용한다.

- `support.escalate`
- `manual_review_required`
- `admin_followup_required`

## 4. 입력 처리 규칙

| 상황 | 1차 처리 | LLM 사용 | 결과 처리 |
|---|---|---|---|
| 버튼/슬래시 명령 | 룰 100% | 금지 | 즉시 처리 |
| 현재 step에서 기대 형식과 맞는 입력 | parser/validator | 금지 | 성공 시 다음 step |
| 현재 step에서 핵심 값은 보이지만 문장이 복합적임 | heuristic parser + slot 추출 | 기본 금지 | 현재 step 값만 반영, 남는 정보는 무시 또는 재질문 |
| 현재 step에서 형식이 틀린 입력 | cheap gate + reask | 금지 | 예시와 버튼 제공 |
| help성 질문 | help/menu rule | 금지 | 도움말 또는 관련 버튼 제공 |
| 수정 의도처럼 보이지만 룰이 애매한 입력 | repair rule | 허용 | 수정 대상 확인 단계로 이동 |
| confirm 단계의 애매한 수정 요청 | repair rule -> 실패 시 LLM | 허용 | field 후보만 고르고 다시 확인 |
| 완전한 잡담/도메인 불명 입력 | guided fallback | 금지 | 관련 항목 버튼 제시 |
| 공격적/민감/운영 이관 필요 입력 | safety gate | 금지 | 사람 연결 또는 운영 안내 |
| 반복 실패 누적 | recovery/handoff | 제한적 또는 금지 | 버튼 유도 강화 또는 사람 연결 |

## 5. Unknown / Fallback 규칙

- `알 수 없는 요청입니다` 단일 문장으로 종료하지 않는다.
- fallback은 항상 다음 행동을 제시해야 한다.
- 메인 메뉴 밖에서는 현재 flow와 가장 가까운 관련 버튼을 먼저 노출한다.
- 메인 메뉴에서는 대분류 버튼을 우선 노출한다.
- fallback 문구는 상태별로 다르게 유지한다.

권장 예시:

- 메인 메뉴
  - `이해하지 못했어요. 아래에서 원하는 작업을 선택해주세요.`
- 입력 단계
  - `이 단계에서는 사용량만 입력할 수 있어요. 예시를 보거나 아래 버튼을 선택해주세요.`
- 수정 단계
  - `이해하지 못했어요. 수정할 항목을 아래에서 선택해주세요.`

## 6. 자연어 수정 규칙

- 자연어는 직접 수정 명령이 아니라 수정 의도 신호로만 사용한다.
- 자연어만으로 값을 즉시 저장하거나 덮어쓰지 않는다.
- 실제 값 반영은 아래 단계를 반드시 거친다.
  1. 수정 의도 확인
  2. 수정 대상 확인
  3. 새 값 명시적 입력 또는 후보값 확인
  4. 최종 confirm

예:

- `제품명 수정할래`
  - 수정 의도 확인 단계로 이동
- `제품명은 한아름 복합비료로 바꾸고 싶어`
  - 새 값은 후보로만 보관
  - confirm 없이 draft overwrite 금지

## 7. Candidate value 저장 규칙

세션 상태는 아래 세 층으로 분리한다.

- `draft_*`
  - 사용자가 직접 입력하며 편집 중인 값
- `pending_candidate_*`
  - rule 또는 LLM이 제안한 후보값
- `confirmed_*`
  - 사용자가 최종 확인한 값

강제 규칙:

- `candidate_value`는 `pending_candidate`에만 저장한다.
- `confirmed value`로 승격되기 전에는 `draft overwrite`를 금지한다.
- 사용자가 `[맞아요]` 또는 동등한 confirm action을 실행하기 전에는 pending candidate를 authoritative value처럼 다루지 않는다.
- pending candidate가 폐기되면 반드시 clear하고 telemetry를 남긴다.

## 8. LLM 호출 허용 조건

LLM은 아래 조건을 모두 만족할 때만 호출한다.

1. 현재 세션에 `current_step`이 있다.
2. 현재 step이 structured input 또는 confirm/edit 문맥이다.
3. step parser, cheap gate, repair rule로 확정하지 못했다.
4. 사용자의 입력이 자유문장이다.
5. 현재 `AI_MODE`가 해당 호출 유형을 허용한다.
6. 현재 step에서 호출 횟수 한도를 넘지 않았다.
7. 동일 `normalized_text + current_step` 조합으로 이미 호출한 적이 없다.

## 9. LLM 호출 금지 조건

아래 경우는 LLM 호출을 금지한다.

- 버튼/슬래시 명령
- reply button
- parser/validator로 이미 확정 가능한 입력
- cheap gate에서 막힌 입력
- help/menu/support intent
- safety gate 대상 입력
- recovery 한도 초과 입력
- `AI_MODE=disabled`
- `AI_MODE=manual_review_fallback`
- 동일 `normalized_text + current_step` 재호출

## 10. Step별 LLM 호출 한도

아래 상수는 정책 코드에서 그대로 강제한다.

- `MAX_LLM_CALLS_PER_STRUCTURED_STEP = 1`
- `MAX_LLM_CALLS_PER_CONFIRM_STEP = 1`
- `MAX_RECOVERY_ATTEMPTS_BEFORE_HANDOFF = 3`

강제 규칙:

- confirm/edit step: 최대 1회
- structured input step: 최대 1회
- 동일 `normalized_text + current_step` 재호출 금지

## 11. LLM 역할 제한

LLM은 아래 역할만 허용한다.

- 수정 의도 분류
- 현재 step 관련성 판정
- target field 후보 추출
- candidate value 추출
- clarification question 1개 생성
- human handoff 필요 여부 표시

LLM이 하면 안 되는 것:

- 즉시 저장 승인
- canonical intent catalog 대체
- 최종 confirm 생략
- 여러 단계 상태 전이 단독 결정
- 운영 우선순위 결정
- 승인/거절/검토 결과 확정

## 12. LLM 출력 형식

LLM 출력은 항상 JSON-only 구조로 제한한다.

예:

```json
{
  "action": "fertilizer.edit.product",
  "candidate_value": "한아름 복합비료",
  "needs_confirmation": true,
  "clarification_question": null,
  "needs_human": false,
  "confidence": 0.91
}
```

강제 규칙:

- enum 밖으로 나가지 않는다.
- schema validate를 통과해야 한다.
- validator와 state machine을 다시 통과해야 한다.
- 값이 있더라도 pending candidate로만 저장한다.
- confirm 없이 확정값으로 승격할 수 없다.

## 13. Confirm 단계 규칙

- confirm 단계는 가장 강한 안전 단계다.
- confirm 단계의 애매한 수정 요청은 rule repair를 먼저 시도한다.
- rule repair 실패 시에만 LLM을 허용한다.
- LLM이 field 후보를 뽑더라도 바로 저장하지 않는다.
- confirm 단계에서는 항상 수정 대상 재확인 또는 수정 단계 진입으로 처리한다.

## 14. Handoff 조건

아래는 LLM보다 handoff가 우선이다.

- explicit help 요청
- 민원/complaint
- 상담원 요청
- 공격적/민감 입력
- repeated failure
- canonical ambiguity 반복
- OCR/typed input 충돌 반복
- correction/withdrawal 같은 운영성 요청

이 경우 아래 vocabulary 중 하나로 연결한다.

- `support.escalate`
- `manual_review_required`
- `admin_followup_required`

## 15. Telemetry 규칙

아래 이벤트는 최소 세트로 항상 기록한다.

- `rule_matched`
  - 룰이 입력을 성공적으로 처리했을 때
- `cheap_gate_blocked`
  - cheap gate가 입력을 차단했을 때
- `fallback_shown`
  - fallback 문구와 버튼을 사용자에게 보여줬을 때
- `llm_invoked`
  - 정책을 통과해 실제 LLM을 호출했을 때
- `llm_skipped_by_policy`
  - 정책상 금지되어 LLM 호출을 생략했을 때
- `llm_rejected_low_confidence`
  - low confidence로 LLM 결과를 버렸을 때
- `handoff_requested`
  - 운영 또는 사람 검토 경로로 넘겼을 때
- `pending_candidate_created`
  - pending candidate를 생성했을 때
- `pending_candidate_confirmed`
  - pending candidate가 confirm을 거쳐 확정됐을 때
- `pending_candidate_discarded`
  - pending candidate가 폐기됐을 때

## 16. 정책 코드 분리 원칙

정책 판단 로직은 메시지 핸들러 안에 분산하지 않는다.

권장 정책 파일:

- `src/PROJECT/policy/ai_policy.py`

최소 포함 요소:

- `AiMode` enum
- step별 호출 한도 상수
- `can_invoke_llm(...)`
- `should_handoff(...)`
- `same_input_cache_key(...)`

## 17. 런타임 강제 순서

모든 LLM 관련 런타임 흐름은 아래 순서를 고정한다.

1. command/button
2. step parser
3. cheap gate
4. rule repair
5. `can_invoke_llm(...)`
6. LLM 결과 schema validate
7. validator + state machine 재검증
8. confirm 또는 fallback 또는 handoff

이 순서가 깨지면 안 된다.

## 18. 구현 순서

권장 구현 순서는 아래와 같다.

1. 문서에 vocabulary와 정책을 먼저 고정한다.
2. `ai_policy.py`로 정책 판단 로직을 중앙화한다.
3. pending candidate 세션 분리를 추가한다.
4. step별 호출 한도와 재호출 방지를 추가한다.
5. telemetry 최소 이벤트 세트를 붙인다.
6. 모든 LLM 호출을 정책 함수 뒤로 이동시킨다.

권장 커밋 단위:

- `docs: add chatbot operation policy v2`
- `feat: add AI_MODE enum and llm invoke gate`
- `feat: separate pending candidate from draft state`
- `feat: add llm retry limit and same-input guard`
- `feat: add chatbot telemetry policy events`

## 19. 최종 요약

- 메인 경로는 룰베이스로 유지한다.
- unknown 입력은 guided fallback으로 회수한다.
- 자연어 수정은 direct update가 아니라 수정 의도 신호로만 다룬다.
- LLM은 제한된 구조화 판정기로만 쓴다.
- candidate value는 pending candidate로만 저장한다.
- confirm 전에는 draft overwrite를 금지한다.
- 모든 LLM 호출은 정책 함수 뒤에서만 허용한다.
- telemetry를 통해 왜 룰이 처리했는지, 왜 LLM이 호출되었는지, 왜 handoff됐는지 추적 가능해야 한다.
