# Structured Interaction Policy

## 목적

이 문서는 `PROJECT`에서 아래 3개 운영 원칙을 실제 구현으로 옮기기 전에, 기획과 코드 양쪽에서 흔들리지 않도록 기준을 고정하기 위한 문서다.

1. 알 수 없는 요청으로 대화를 종료하지 않고, 관련 항목 버튼으로 유도한다.
2. 자연어만으로 값을 직접 수정하지 않고, 수정 의도 확인과 명시적 재입력 단계를 거친다.
3. LLM은 제한된 범위의 구조화 판정기/추출기로만 쓰고, LLM 결과는 다시 확인 단계를 거친다.

이 문서는 구현 요청이 들어왔을 때 바로 작업 순서와 완료 기준으로 사용할 수 있어야 한다.

## 원칙 1. Unknown 요청은 버튼 유도로 닫는다

### 제품 원칙

- `알 수 없는 요청입니다`로 대화를 끝내지 않는다.
- 현재 상태와 가장 가까운 관련 항목을 2~5개 버튼으로 제시한다.
- 메인 메뉴 밖에서는 대분류 전체를 매번 다 보여주지 않는다.
- 현재 flow 안에서는 해당 flow 관련 intent만 우선 노출한다.

### 권장 버튼 계층

버튼은 아래 3층을 기준으로 설계한다.

1. 대분류
   - 예: `프로필`, `비료 입력`, `수확 입력`, `도움말`
2. 대분류 내부 intent
   - 예: `비료 사용 여부`, `비료 유형`, `제품명`, `사용량`, `사용일`
3. 해당 intent 처리 방식
   - 예: `직접 입력`, `후보 보기`, `뒤로가기`, `취소`

다만 현재 상태에 따라 2층 또는 3층부터 시작할 수 있어야 한다.

예:

- 메인 메뉴에서 모호한 입력
  - `프로필`, `비료 입력`, `수확 입력`, `도움말`
- 비료 confirm 단계에서 모호한 입력
  - `제품명 수정`, `사용량 수정`, `사용일 수정`, `취소`

### 구현에 필요한 것

- 도메인별 대분류 목록
- 도메인별 세부 intent 목록
- 상태별로 어떤 버튼 그룹을 우선 노출할지 매핑 테이블
- 버튼 선택 시 다음 상태 또는 다음 질문으로 넘기는 라우터
- fallback 문구와 버튼 그룹을 함께 반환하는 공통 helper

### 권장 코드 분리

- `dispatch/guided_fallback.py`
  - 상태별 버튼 후보 결정
- `conversations/*/keyboards.py`
  - intent 버튼 정의
- `i18n/catalogs/*`
  - fallback 안내 문구와 버튼 라벨

### 완료 기준

- 어떤 fallback에서도 대화가 `알 수 없는 요청` 단일 문장으로 끝나지 않는다.
- 최소 한 개 이상의 관련 버튼이 항상 같이 노출된다.
- 현재 flow 안 fallback은 현재 flow 관련 버튼을 우선 노출한다.

## 원칙 2. 자연어는 직접 수정 명령이 아니라 수정 의도 신호로만 쓴다

### 제품 원칙

- 자연어 입력만으로 값을 즉시 덮어쓰지 않는다.
- 자연어는 아래 두 가지까지만 허용한다.
  - 수정 의도 감지
  - 후보값 추출
- 실제 값 반영은 반드시 아래 단계를 거친다.
  - 수정 의도 확인
  - 수정 대상 확인
  - 새 값 명시적 입력 또는 후보값 확인
  - 최종 확인

### 권장 상호작용

예시 1:

- 사용자: `비료 이름을 수정하고 싶어`
- 시스템: `비료 이름을 수정하시겠어요?`
- 버튼: `예`, `아니오`
- `예` 선택 시: `수정할 비료 이름을 입력해주세요.`

예시 2:

- 사용자: `비료 이름을 한아름 복합비료로 바꾸고 싶어`
- 시스템: `비료 이름을 수정하시겠어요? 새 값은 "한아름 복합비료"로 이해했어요.`
- 버튼: `맞아요`, `다시 입력`, `취소`
- `맞아요` 선택 시에도 바로 저장하지 않고 confirm으로 이동

### 구현에 필요한 것

- 수정 의도 전용 canonical intent 목록
- 수정 대상 필드 목록
- 수정 의도 확인용 yes/no 질문 템플릿
- 후보값이 있는 경우와 없는 경우의 분기 표
- 최종 저장 전 confirm 단계 강제 규칙

### 필수 상태/세션 정보

- `pending_edit_domain`
- `pending_edit_target`
- `pending_candidate_value`
- `pending_confirmation_source`
  - `rule`
  - `llm`
  - `button`

### 권장 코드 분리

- `dispatch/repair_router.py`
  - 수정 의도와 대상 필드 결정
- `dispatch/edit_confirmation.py`
  - 수정 의도 확인과 후보값 확인 단계 관리
- `conversations/*/service.py`
  - 필드별 재입력 질문과 confirm 요약 생성

### 완료 기준

- 자연어 수정 요청이 들어와도 값이 즉시 확정되지 않는다.
- 반드시 `수정 의도 확인 -> 값 입력/확인 -> 최종 confirm`을 거친다.
- direct update는 제거하거나 confirm 전 후보 상태로만 유지한다.

## 원칙 3. LLM은 제한된 enum 기반 판정기/추출기로만 쓴다

### 제품 원칙

- LLM은 자유 응답 생성기가 아니다.
- 현재 상태와 허용된 action 범위 안에서만 분류/추출한다.
- LLM이 만든 값은 반드시 다시 확인한다.
- LLM이 값을 만들지 못하면 `null`을 반환하게 한다.

### 권장 역할

LLM은 아래 중 하나만 반환해야 한다.

- 관련된 수정 intent 분류
- 현재 step 관련성 판정
- 후보값 추출
- clarification question 초안
- human handoff 필요 여부

반대로 LLM이 하면 안 되는 것은 아래다.

- 즉시 저장 승인
- canonical 최종 확정
- 운영 우선순위 결정
- 여러 단계 상태 전이를 단독 결정

### 권장 출력 예시

```json
{
  "action": "fertilizer.edit.product_name",
  "candidate_value": "한아름 복합비료",
  "needs_confirmation": true,
  "clarification_question": null,
  "needs_human": false,
  "confidence": 0.91
}
```

또는

```json
{
  "action": "fertilizer.edit.product_name",
  "candidate_value": null,
  "needs_confirmation": true,
  "clarification_question": "수정할 비료 이름을 입력해주세요.",
  "needs_human": false,
  "confidence": 0.84
}
```

### 구현에 필요한 것

- 도메인별 허용 action enum
- action별 허용 target field enum
- `candidate_value` 허용 타입 정의
- `needs_confirmation`와 `needs_human` 해석 규칙
- LLM 결과를 다시 validator와 state machine에 태우는 후처리기

### 프롬프트 설계 원칙

- 현재 상태
- 허용 action 목록
- 허용 field 목록
- 금지 행동
- JSON schema

위 다섯 개를 반드시 포함한다.

프롬프트가 다소 길어져도, 자유 응답을 허용하는 것보다 훨씬 안전하다.

### LLM 결과 후처리 원칙

- 값이 있으면 `이 값으로 이해했어요. 맞나요?`
- 값이 없으면 `수정할 값을 입력해주세요.`
- `needs_human=true`면 운영 경로 또는 제한된 fallback 버튼으로 이동
- `needs_confirmation=true`면 반드시 버튼 확인 단계로 이동

### 완료 기준

- LLM 출력은 enum + JSON schema 밖으로 나가지 않는다.
- LLM이 만든 값은 저장 전에 반드시 확인 단계를 거친다.
- LLM 결과는 rule validator를 다시 통과해야 한다.

## 구현 준비 체크리스트

아래 항목이 준비되어야 구현이 흔들리지 않는다.

### 1. 도메인별 taxonomy

- 대분류 목록
- 대분류 내부 intent 목록
- 수정 가능한 field 목록
- 각 field의 입력 방식

### 2. 상태별 fallback map

- 현재 상태
- 우선 노출 버튼 그룹
- fallback 문구
- 다음 분기

### 3. edit flow decision table

- 수정 의도만 있음
- 수정 의도 + field 있음
- 수정 의도 + field + candidate value 있음
- 현재 값 조회 요청
- 취소 요청

### 4. LLM action schema

- 허용 action enum
- 허용 field enum
- `candidate_value` 타입
- `needs_confirmation`
- `needs_human`

### 5. 검증 및 로깅

- 어떤 fallback이 버튼 유도로 회수됐는지
- 어떤 자연어 수정 요청이 확인 단계로 갔는지
- 어떤 LLM 결과가 confirm에서 거절됐는지

## 권장 구현 순서

1. unknown fallback 버튼 유도 구조 추가
2. direct update 제거 또는 후보 상태로 축소
3. 수정 의도 확인 단계 추가
4. 수정 대상별 재입력 플로우 정리
5. LLM action enum/schema 고정
6. LLM 결과 후처리와 confirm 재질문 연결
7. 로그/메트릭 추가

## 이번 정책의 최종 요약

- fallback은 종료 문장이 아니라 guided choice여야 한다.
- 자연어 수정은 직접 반영이 아니라 수정 의도 신호여야 한다.
- LLM은 자유 대화형이 아니라 enum 제한 recovery classifier여야 한다.
- 값 변경이나 새 값 추출이 개입되면 반드시 다시 확인해야 한다.
