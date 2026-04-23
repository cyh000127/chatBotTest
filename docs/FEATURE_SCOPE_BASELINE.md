# Feature Scope Baseline

## 1. 목적

이 문서는 메신저 기반 구조화 입력 서비스에서 구현 대상으로 인정되는 기능과 제외해야 하는 기능을 구분하기 위한 기준 문서다.

이 문서는 아래 전제를 가진다.

- `reference-docs`가 기본 기능 기준이다.
- `reference-docs`에 없는 추가 명세와 상세 기능 정의는 현재 프로젝트 문서가 담당한다.

핵심 목적은 다음과 같다.

- 데모성 기능과 실제 제품 범위를 구분한다.
- 구현 우선순위를 farmer-facing 핵심 루프에 맞춘다.
- 규칙 엔진, recovery, handoff, 다국어 메시지를 기능 범위와 함께 묶어 관리한다.

## 2. 제품 정의

이 서비스는 현장 참여자가 메신저에서 구조화된 데이터를 제출하고, 운영자는 별도 운영 표면에서 검토와 예외 처리를 수행하는 구조를 전제로 한다.

farmer-facing runtime의 핵심 범위는 다음과 같다.

- 메신저 시작 진입
- 언어 선택
- 단계형 입력 수집
- self-service 조회
- restart 및 guided recovery
- support escalation 또는 admin follow-up 연결
- 기존 챗봇 대화창 안에서 운영자 후속 답변을 중계하는 지원 이관

## 3. 구현 대상 기능

우선 구현 대상은 아래와 같다.

- `/start` 또는 동등 진입점
- 언어 선택과 재진입 도움
- `/fertilizer` 입력
- `/yield` 입력
- `/myfields` 진입점
- `input.resolve.start` 진입점
- structured confirm / edit / cancel / restart
- unknown fallback과 state-aware recovery
- `support.escalate`, `manual_resolution_required`, admin follow-up 안내
- 지원 이관 상태의 사용자 추가 메시지 수집
- 운영자 후속 답변의 챗봇 대화창 중계
- 다국어 farmer-facing 메시지 카탈로그

## 4. 제한적 보조 기능

아래 기능은 주 경로가 아니라 보조 기능으로만 허용한다.

- current-step recovery classifier
- edit intent 분류
- clarification question 1개 생성
- candidate value 추출
- human handoff 필요 여부 판정

강제 원칙:

- 주 경로는 끝까지 룰베이스다.
- 모델 출력은 항상 구조화 JSON이어야 한다.
- 모델이 만든 후보는 pending candidate로만 저장한다.
- confirm 없이 직접 저장하지 않는다.

## 5. 구현 제외 기능

아래 항목은 제품 범위에 없거나 데모성 기능이므로 제거 대상이다.

- 오늘 날짜 조회
- 오늘 날씨 조회
- 도시 선택형 날씨 메뉴
- 단순 데모 메뉴
- 로컬 샘플용 임시 인증 흐름
- 운영 시스템과 무관한 범용 잡담 응답
- 별도 상담방 생성
- 실시간 상담 보장

## 6. 구현 우선순위

1. 시작 진입, 언어 선택, restart, fallback
2. 비료 입력
3. 수확량 입력
4. 자기 조회 진입점
5. input resolve 진입점
6. 제한적 모델 보조와 handoff 정렬

## 7. 문서화 원칙

- 문서에는 특정 회사명, 제품명, 내부 프로젝트명, 경로 의존 설명을 넣지 않는다.
- 문서는 독립적으로 읽혀야 하며 외부 구현 맥락을 요구하지 않는다.
- 기능 설명은 제품 범위, 정책 제약, 런타임 동작 순서 중심으로 정리한다.
