# Rule-First LLM Handoff

## 목적

이 문서는 `PROJECT`에서 3단계 LLM을 붙이기 전에 어떤 규칙 기반 전처리와 상태 조립이 먼저 있어야 하는지 정리한다.

핵심 원칙은 아래와 같다.

- 규칙으로 끝낼 수 있는 입력은 2단계에서 끝낸다.
- 3단계 LLM은 기본 경로가 아니라 예외적 회수 경로다.
- 3단계는 자유 대화 엔진이 아니라 `현재 step recovery classifier`로 쓴다.

## 3단계로 넘기기 전 최소 상태

향후 3단계로 넘길 때는 아래 필드만 준비한다.

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

이 구조는 현재 `RecoveryContextDraft`의 설계 기준이다.

## Cheap Gate

LLM 호출 전에 아래 입력은 규칙으로 먼저 닫는다.

- 명시적 help/support 요청
- 반복 실패 한도 초과
- 현재 step과 무관한 입력
- 사전에 있는 숫자/날짜/단위/동의어 패턴
- 욕설/민원/운영 이관 키워드

즉 흐름은 아래가 된다.

1. step parser
2. cheap gate
3. 규칙 기반 repair
4. 그래도 남는 경우에만 3단계 LLM

## 도메인 예시

### fertilizer

- `복합비료 20kg 한 포 썼어요`
  규칙으로 수량/단위/제품 후보를 잡을 수 있으면 2단계 종료
- `지난번에 쓰던 요소 비슷한 거예요`
  규칙으로 못 좁히면 나중에 3단계 recovery 대상

### yield

- `320kg`
  숫자 패턴으로 즉시 해결
- `지난번보다 적고 세 포대쯤 돼요`
  규칙으로 애매하면 3단계 후보

### input.resolve.start

- 후보 번호 선택, `없음`, `다시`
  전부 규칙 기반으로 닫아야 한다
- OCR 결과와 typed text가 반복 충돌
  cheap gate 이후 운영 이관 또는 나중에 제한적 3단계 보조

## 현재 구현 범위

현재 repo는 아직 3단계 LLM 호출을 구현하지 않는다.

지금 단계의 목표는 아래 둘이다.

- 2단계에서 가능한 한 넓게 규칙 기반으로 처리
- 3단계 직전 인터페이스를 미리 고정

즉 지금은 “LLM을 붙이는 작업”이 아니라 “LLM 없이도 최대한 버티는 규칙 엔진을 만드는 작업”이다.
