# Stage 2 Rule Engine

## 1. 목적

이 문서는 메신저 기반 구조화 입력 서비스에서 사용하는 2단계 규칙 엔진의 목적, 공통 계약, 확장 순서를 설명한다.

이 규칙 엔진은 자유 대화 처리기가 아니라 다음 목적을 가진다.

- 현재 step에 맞는 입력인지 빠르게 판정한다.
- 값 후보를 규칙적으로 추출한다.
- 모델 호출 전에 cheap gate와 repair rule을 먼저 적용한다.
- fallback과 handoff를 상태 기반으로 일관되게 생성한다.

## 2. 기본 원칙

- 규칙으로 끝낼 수 있는 입력은 규칙에서 끝낸다.
- 모델은 규칙 실패 이후의 제한적 보조 경로다.
- 상태 없는 전역 의도와 상태 의존 로컬 의도를 분리한다.
- step schema를 먼저 정의하고 rule을 그 위에 올린다.
- recovery와 handoff vocabulary는 규칙 엔진과 정책 문서가 동일한 이름을 사용한다.

## 3. 단계 구조

권장 파이프라인은 아래와 같다.

1. normalization
2. global intent routing
3. step-local intent routing
4. slot / alias resolution
5. validation
6. repair classification
7. cheap gate
8. fallback 또는 handoff 또는 confirm

## 4. 단계별 책임

### 4.1 Normalization

- 공백 정리
- casing 정리
- locale별 표기 변형 흡수
- filler word 축소
- 비교 가능한 문자열 생성

### 4.2 Intent Routing

- `/start`, `/myfields`, `/yield`, `/fertilizer`, `input.resolve.start` 같은 global intent 판정
- 현재 step 문맥에서의 local action 판정
- help, cancel, restart, back, confirm, edit 같은 공통 intent 판정

### 4.3 Slot / Alias Resolution

- amount, date, item, candidate label 추출
- locale alias 사전 적용
- short text와 canonical candidate의 1차 정렬

### 4.4 Validation / Repair

- 현재 step 적합성 검증
- hard constraint 검증
- ambiguity 여부 판정
- 재질문, clarification, handoff 필요 여부 결정

## 5. 공통 Step Schema

step schema는 최소한 아래 필드를 가져야 한다.

- `state`
- `domain`
- `canonical_intent`
- `expected_input_type`
- `allowed_value_shape`
- `hard_constraints`
- `confirmation_policy`

이 schema는 다음 목적에 재사용된다.

- parser 입력 제약
- cheap gate 판단
- recovery context 구성
- 모델 입력 압축
- contract 테스트

## 6. 우선 도메인

규칙 엔진의 우선 도메인은 아래와 같다.

- start / locale selection
- fertilizer input
- yield input
- input resolve
- myfields entry
- confirm / edit / restart / support escalation

## 7. 구현 제외 항목

규칙 엔진의 핵심 범위에 포함하지 않는 항목:

- 날씨 조회
- 오늘 날짜 조회
- 범용 잡담 응답
- 비구조화 자유 대화 세션 유지

## 8. Cheap Gate 원칙

cheap gate는 아래 상황을 먼저 차단하거나 분류한다.

- 현재 step과 무관한 입력
- 명시적 help 요청
- 반복 실패 한도 초과
- 민감/공격/운영 이관 필요 입력
- parser로 이미 거절 가능한 형식 오류

cheap gate의 목적은 비용 절감과 안전성 강화다.

## 9. Recovery 연계

규칙 엔진은 recovery context를 함께 만든다.

최소 포함 요소:

- `current_question`
- `expected_input_type`
- `allowed_value_shape`
- `recent_messages_summary`
- `ux_recovery_reason`
- `recovery_policy_level`
- `recovery_task_hint`
- `recovery_resume_action`
- `recovery_focus_target`

## 10. 확장 순서

1. normalization 정리
2. global intent registry 정리
3. step-local intent rule 정리
4. step schema 고정
5. slot extractor 고정
6. validation / repair 분리
7. cheap gate 연동
8. fallback / handoff 정렬
9. contract test 추가

## 11. 최종 요약

- 규칙 엔진은 메인 경로의 기본 처리기다.
- 입력 판단은 step schema를 기준으로 이뤄진다.
- repair와 cheap gate는 모델 호출보다 먼저 실행된다.
- recovery context는 규칙 엔진 단계에서 먼저 조립한다.
- 제품 범위에 없는 데모성 기능은 규칙 엔진 확장 대상에 넣지 않는다.
