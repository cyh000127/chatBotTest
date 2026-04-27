# Chatbot Operation Policy v2

## 1. 목적

이 문서는 챗봇 상호작용 규칙을 `문서 -> 정책 코드 -> 런타임 강제` 순서로 고정하기 위한 운영 정책 문서다.

핵심 목표는 아래와 같다.

- 메인 경로를 끝까지 룰베이스로 유지한다.
- 모델 사용을 예외적 보조 판정기로 제한한다.
- 후보값과 확정값을 분리해 오작동을 막는다.
- 버튼, 재질문, restart, handoff를 포함한 guided recovery를 기본으로 둔다.
- telemetry, handoff, recovery vocabulary를 코드와 동일한 이름으로 고정한다.

## 2. 핵심 원칙

- 메인 경로는 끝까지 rule-first다.
- unknown 입력은 단일 종료 문장으로 닫지 않는다.
- 자연어 수정은 직접 반영하지 않고 수정 의도 신호로만 사용한다.
- 모델 결과는 항상 validator와 state machine을 다시 거친다.
- bot과 모델은 authoritative write owner가 아니다.
- candidate value는 pending candidate로만 저장한다.

## 3. Vocabulary

### 3.1 AI 정책 정렬

모델 사용 여부의 source of truth는 런타임 local enum이 아니라 상위 정책 레코드와 release gate다.

- feature enablement policy
- fallback mode
- release gate status
- recorded cost ceiling
- budget ceiling

강제 규칙:

- 상위 정책이 비활성화하면 해당 모델 호출은 금지한다.
- 품질, 비용, 가용성 gate를 통과하지 못하면 기본 모드는 `rules-only validation + admin review`다.
- local guard는 상위 정책보다 넓은 권한을 줄 수 없다.

### 3.2 권장 Telemetry 이벤트

- `rule_matched`
- `cheap_gate_blocked`
- `fallback_shown`
- `recovery_classified`
- `recovery_action_selected`
- `llm_invoked`
- `llm_skipped_by_policy`
- `llm_rejected_low_confidence`
- `handoff_requested`
- `pending_candidate_created`
- `pending_candidate_confirmed`
- `pending_candidate_discarded`

### 3.3 Handoff vocabulary

- `support.escalate`
- `manual_resolution_required`
- `admin_follow_up_queue`
- `bot_mediated_admin_reply`

### 3.4 Recovery vocabulary

- `empty_input`
- `missing_required_value`
- `input_format_mismatch`
- `target_ambiguity`
- `step_scope_mismatch`
- `generic_recoverable`
- `repeated_failure`
- `support_escalation`
- `admin_followup`
- `manual_resolution`

### 3.5 Recovery policy level

- `soft`
- `guided`
- `escalation_ready`

## 4. 입력 처리 규칙

| 상황 | 1차 처리 | 모델 사용 | 결과 처리 |
|---|---|---|---|
| 버튼/슬래시 명령 | 룰 100% | 금지 | 즉시 처리 |
| 현재 step에서 기대 형식과 맞는 입력 | parser/validator | 금지 | 성공 시 다음 step |
| 현재 step에서 핵심 값은 보이지만 문장이 복합적임 | heuristic parser + slot 추출 | 기본 금지 | 현재 step 값만 반영하거나 재질문 |
| 현재 step에서 형식이 틀린 입력 | cheap gate + reask | 금지 | 예시와 버튼 제공 |
| help성 질문 | help/menu rule | 금지 | 도움말 또는 관련 버튼 제공 |
| 수정 의도처럼 보이지만 룰이 애매한 입력 | repair rule | 허용 | 수정 대상 확인 단계로 이동 |
| confirm 단계의 애매한 수정 요청 | repair rule -> 실패 시 모델 | 허용 | field 후보만 고르고 다시 확인 |
| 완전한 잡담/도메인 불명 입력 | guided fallback | 금지 | 관련 항목 버튼 제시 |
| 공격적/민감/운영 이관 필요 입력 | safety gate | 금지 | 지원 이관 또는 운영 안내 |
| 반복 실패 누적 | recovery/handoff | 제한적 또는 금지 | 버튼 유도 강화 또는 지원 이관 |
| 증빙 파일 형식 불일치 또는 staged artifact read failure | parser/validator | 금지 | 재제출 안내 또는 운영 검토 |

## 5. Unknown / Fallback 규칙

- `알 수 없는 요청입니다` 단일 문장으로 종료하지 않는다.
- fallback은 항상 다음 행동을 제시해야 한다.
- 메인 메뉴 밖에서는 현재 flow와 가장 가까운 관련 버튼을 먼저 노출한다.
- 메인 메뉴에서는 대분류 버튼을 우선 노출한다.
- fallback 문구는 상태별로 다르게 유지한다.
- fallback은 가능하면 현재 step 질문을 짧게 다시 보여준다.
- recovery 버튼은 상태별 fast path를 공용 메뉴보다 우선한다.

## 6. 자연어 수정 규칙

- 자연어는 직접 수정 명령이 아니라 수정 의도 신호로만 사용한다.
- 자연어만으로 값을 즉시 저장하거나 덮어쓰지 않는다.
- 실제 값 반영은 아래 단계를 반드시 거친다.

1. 수정 의도 확인
2. 수정 대상 확인
3. 새 값 명시적 입력 또는 후보값 확인
4. 최종 confirm

예시:

- `이 항목 수정할래`
  수정 의도 확인 단계로 이동
- `이 값을 다른 값으로 바꾸고 싶어`
  새 값은 후보로만 보관하고 confirm 없이 overwrite 하지 않는다

## 7. Candidate 저장 규칙

세션 상태는 아래 세 층으로 분리한다.

- `draft_*`
- `pending_candidate_*`
- `confirmed_*`

강제 규칙:

- `candidate_value`는 `pending_candidate`에만 저장한다.
- `confirmed value`로 승격되기 전에는 `draft overwrite`를 금지한다.
- 명시적 confirm 전에는 pending candidate를 authoritative value처럼 다루지 않는다.
- pending candidate가 폐기되면 clear하고 telemetry를 남긴다.
- multi-slot candidate도 동일하게 pending candidate로만 유지한다.

## 8. Recovery 정책 레벨 규칙

- `soft`: 현재 질문 재안내 중심
- `guided`: 현재 step fast-path 버튼 우선
- `escalation_ready`: safe exit, restart, help, handoff 근접 경로 우선

권장 기준:

- 첫 실패의 단순 형식 오류: `soft`
- 2회차 실패 또는 step 재안내 필요: `guided`
- repeated failure, support/admin/manual resolution 성격: `escalation_ready`

## 9. Recovery context 규칙

fallback과 repair는 최소한 아래 context를 공유해야 한다.

- `current_question`
- `expected_input_type`
- `allowed_value_shape`
- `recent_messages_summary`
- `ux_recovery_reason`
- `recovery_policy_level`
- `recovery_task_hint`
- `recovery_resume_action`
- `recovery_focus_target`

## 10. 모델 호출 허용 조건

모델은 아래 조건을 모두 만족할 때만 호출한다.

1. 현재 세션에 `current_step`이 있다.
2. 현재 step이 structured input 또는 confirm/edit 문맥이다.
3. step parser, cheap gate, repair rule로 확정하지 못했다.
4. 사용자의 입력이 자유문장이다.
5. 상위 정책과 fallback mode가 해당 호출 유형을 허용한다.
6. 현재 step에서 호출 횟수 한도를 넘지 않았다.
7. 동일 `normalized_text + current_step` 조합으로 이미 호출한 적이 없다.

## 11. 모델 호출 금지 조건

- 버튼/슬래시 명령
- reply button
- parser/validator로 이미 확정 가능한 입력
- cheap gate에서 막힌 입력
- help/menu/support intent
- safety gate 대상 입력
- recovery 한도 초과 입력
- feature policy disabled
- runtime fallback mode가 `rules-only validation + admin review`로 고정된 경우
- 동일 `normalized_text + current_step` 재호출

## 12. Step별 모델 호출 한도

- `MAX_LLM_CALLS_PER_STRUCTURED_STEP = 1`
- `MAX_LLM_CALLS_PER_CONFIRM_STEP = 1`
- `MAX_RECOVERY_ATTEMPTS_BEFORE_HANDOFF = 3`

## 13. 모델 역할 제한

모델은 아래 역할만 허용한다.

- 수정 의도 분류
- 현재 step 관련성 판정
- target field 후보 추출
- candidate value 추출
- clarification question 1개 생성
- human handoff 필요 여부 표시

모델이 하면 안 되는 것:

- 즉시 저장 승인
- intent catalog 대체
- 최종 confirm 생략
- 여러 단계 상태 전이 단독 결정
- 운영 우선순위 결정
- 승인, 거절, 검토 결과 확정

## 14. 출력 형식

모델 출력은 항상 JSON-only 구조로 제한한다.

```json
{
  "action": "field.edit.item_name",
  "candidate_value": "standardized value",
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

## 15. Confirm 단계 규칙

- confirm 단계는 가장 강한 안전 단계다.
- confirm 단계의 애매한 수정 요청은 rule repair를 먼저 시도한다.
- rule repair 실패 시에만 모델을 허용한다.
- 모델이 field 후보를 뽑더라도 바로 저장하지 않는다.
- confirm 단계에서는 항상 수정 대상 재확인 또는 수정 단계 진입으로 처리한다.

## 16. Handoff 조건

아래는 모델보다 handoff가 우선이다.

- explicit help 요청
- complaint
- 상담원 요청
- 공격적/민감 입력
- repeated failure
- canonical ambiguity 반복
- OCR/typed input 충돌 반복
- correction/withdrawal 같은 운영성 요청

이 경우 아래 vocabulary 또는 aggregate 중 하나로 연결한다.

- `support.escalate`
- `manual_resolution_required`
- `admin_follow_up_queue`

지원 이관의 사용자 대화 표면은 기존 챗봇 대화창이다.

강제 규칙:

- 새 채팅방을 생성하지 않는다.
- 실시간 상담 연결을 보장하지 않는다.
- `support.escalate`는 운영자 후속 처리를 요청하는 이관 신호다.
- 운영자 답변은 봇을 통해 기존 챗봇 대화창으로 중계한다.
- 이관 상태에서 사용자의 추가 메시지는 이관 항목의 대화 이력으로 누적한다.
- 명시적 restart는 이관 상태에서도 우선 처리한다.

## 17. 증빙 파일 품질 규칙

- 증빙 업로드는 자유 형식 파일 수집이 아니다.
- 원본 JPEG document를 우선 허용 형식으로 본다.
- staged artifact가 존재하면 실제 파일 메타데이터 파서를 우선 사용한다.
- staged artifact가 없을 때만 payload fallback을 보조적으로 사용한다.
- 비JPEG 형식, 파손 파일, staged artifact read failure는 `메타데이터 없음`과 다른 실패 사유로 남겨야 한다.
- 파일 품질 실패는 즉시 재제출 안내 대상으로 보되, 반복되면 운영 검토로 승격할 수 있다.
- 관리자 상세에서는 최소한 staged artifact uri, checksum, parser status, signal detail을 확인할 수 있어야 한다.

## 18. 정책 코드 분리 원칙

정책 판단 로직은 메시지 핸들러 안에 분산하지 않는다.

최소 포함 요소:

- `ai_policy` adapter
- step별 호출 한도 상수
- `can_invoke_llm(...)`
- `should_handoff(...)`
- `same_input_cache_key(...)`

## 19. 런타임 강제 순서

1. command/button
2. step parser
3. cheap gate
4. rule repair
5. `can_invoke_llm(...)`
6. 모델 결과 schema validate
7. validator + state machine 재검증
8. confirm 또는 fallback 또는 handoff

## 20. 구현 순서

1. vocabulary와 정책을 문서에 먼저 고정한다.
2. 정책 판단 로직을 중앙화한다.
3. pending candidate 세션 분리를 추가한다.
4. step별 호출 한도와 재호출 방지를 추가한다.
5. telemetry 최소 이벤트 세트를 붙인다.
6. 모든 모델 호출을 정책 함수 뒤로 이동시킨다.

## 21. 최종 요약

- 메인 경로는 룰베이스로 유지한다.
- unknown 입력은 guided fallback으로 회수한다.
- 자연어 수정은 direct update가 아니라 수정 의도 신호로만 다룬다.
- 모델은 제한된 구조화 판정기로만 사용한다.
- candidate value는 pending candidate로만 저장한다.
- confirm 전에는 draft overwrite를 금지한다.
- 모든 모델 호출은 정책 함수 뒤에서만 허용한다.
- recovery는 `soft/guided/escalation_ready` 레벨로 운영한다.
- telemetry를 통해 rule, fallback, model, handoff 이유를 추적 가능해야 한다.
