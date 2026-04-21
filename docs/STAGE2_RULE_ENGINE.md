# Stage-2 Rule Engine

## 목적

이 문서는 `PROJECT`에서 3단계 LLM 호출 이전에 구현해야 하는 2단계 규칙 엔진 구조를 정리한다.

현재 목표는 아래와 같다.

- 규칙으로 처리 가능한 입력은 최대한 2단계에서 끝낸다.
- 자연어 지원을 하더라도 먼저 규칙 기반으로 회수한다.
- 3단계 LLM은 나중에 붙이되, 지금은 그 직전 인터페이스만 준비한다.

## 현재 공통 계약

현재 repo에는 `src/PROJECT/rule_engine/contracts.py` 기준으로 아래 계약이 정의되어 있다.

- `NormalizedInput`
- `IntentDecision`
- `ResolutionCandidate`
- `ValidationResult`
- `RecoveryContextDraft`
- `RuleSource`
- `ValidationClassification`

이 계약의 목적은 아래와 같다.

- 규칙 엔진 각 레이어의 입출력을 고정한다.
- `messages.py` 같은 핸들러에 규칙이 직접 퍼지는 것을 막는다.
- 이후 `yield`, `fertilizer`, `input.resolve.start`를 같은 형태로 올릴 수 있게 한다.

## 권장 4층 구조

2단계 규칙 엔진은 아래 4층으로 나눈다.

1. `Normalization`
   입력을 비교 가능한 문자열로 만든다.
2. `Intent / Step Routing`
   현재 입력이 어떤 canonical intent 또는 현재 step 응답인지 판정한다.
3. `Slot / Alias Resolution`
   날짜, 숫자, 단위, 지역, 제품명 같은 값을 추출하고 canonical 후보로 좁힌다.
4. `Validation / Repair / Handoff`
   허용 값인지 검증하고, 재질문 또는 운영 이관 여부를 결정한다.

## 현재 구현 상태

현재 repo는 아래 수준까지 와 있다.

- 프로필 흐름 기준 자연어 수정 intent 일부 지원
- 프로필 조회/수정 세션 유지
- 프로필 관련 일부 normalization/repair 로직 존재
- 공통 규칙 엔진 계약 추가 완료
- 공통 cheap gate 추가 완료
- recovery context assembler 추가 완료

아직 없는 것:

- `fertilizer` flow 이관
- `yield`, `fertilizer`, `input.resolve` 공통 step schema
- cross-domain fixture 정리

## 구현 순서

1. 공통 계약 정의
2. shared normalization layer 추가
3. global intent routing rules 추가
4. current-step local routing rules 추가
5. alias / slot extraction layer 추가
6. validation / repair decision layer 추가
7. cheap gate 추가
8. recovery context assembler 추가
9. fertilizer flow 이관
10. yield / input-resolve schema 추가
11. contract test와 fixture 정리

## 구현 원칙

- 새 규칙은 먼저 공통 레이어에 추가한다.
- 핸들러 안에서 문자열 비교를 직접 늘리지 않는다.
- alias와 validator를 한 함수에서 같이 처리하지 않는다.
- ambiguity는 일단 `reask` 또는 `manual`로 보내고, 나중에 3단계 LLM으로 회수한다.

## 커밋 단위 기준

현재 기준으로 1번은 이미 시작되었다.

- `feat: add stage-2 rule engine contracts`

다음 커밋은 아래가 된다.

- `feat: add shared normalization layer for rule-first processing`
