# Runtime Guide

## 1. 목적

이 문서는 메신저 기반 구조화 입력 서비스의 farmer-facing runtime, rule-first interaction, 제한적 모델 보조 규칙을 요약한다.

핵심 동작 원칙과 우선 구현 범위를 빠르게 이해하기 위한 기준으로 사용한다.

문서 기준 우선순위는 아래와 같다.

- `reference-docs`가 기본 명세 기준이다.
- `reference-docs`에 없는 추가 명세와 상세 기능은 이 프로젝트에서 정의한다.
- 이 프로젝트의 `docs`는 위 기준을 해석하고 구현 가능한 런타임 규칙으로 정리하는 역할을 가진다.

## 2. 제품 성격

- 메신저 네이티브 구조화 입력 서비스
- 단계형 입력 수집과 검증 중심
- 운영 검토 및 예외 처리와 연결되는 farmer-facing surface
- rule-first, limited-model-assist 구조

## 3. 우선 구현 범위

- 시작 진입
- 언어 선택
- 비료 입력
- 수확량 입력
- 자기 조회 진입점
- input resolve 진입점
- restart / fallback / support escalation 안내

## 4. 제외 범위

- 오늘 날짜 조회
- 오늘 날씨 조회
- 도시 선택형 데모 메뉴
- 로컬 샘플용 인증 흐름
- 범용 잡담 챗봇 기능

## 5. 상호작용 원칙

- 메인 경로는 룰베이스다.
- 모델은 current-step recovery classifier로만 사용한다.
- natural language edit는 direct update가 아니라 수정 의도 신호다.
- candidate value는 pending candidate로만 저장한다.
- confirm 전에는 authoritative value로 승격하지 않는다.
- unknown 입력은 guided fallback으로 회수한다.

## 6. 문서 작성 규칙

문서 작성 시 아래 규칙을 따른다.

- 특정 회사명 사용 금지
- 특정 제품명, 프로젝트명, 내부 코드명 사용 금지
- 상대경로 안내 금지
- 외부 구현 문맥을 전제한 설명 금지
- 독립 문서처럼 읽히는 서술 유지

## 7. 문서 묶음

현재 기본 문서는 다음과 같다.

- Documentation Index
- Feature Scope Baseline
- Chatbot Operation Policy v2
- Stage 2 Rule Engine
- Rule-First LLM Handoff
- Model Recovery Setup
- Structured Interaction Policy

추가 기준:

- `reference-docs`는 상위 참고 문서 묶음으로 우선 해석한다.
- 현재 문서 묶음은 `reference-docs`에 없는 상세 상호작용 규칙, 구현 범위, recovery 정책을 구체화한다.

## 8. 구현 방향

- 명세 있는 기능만 구현한다.
- 데모성 기능은 삭제하거나 비활성화한다.
- 정책 문서와 vocabulary를 코드보다 먼저 고정한다.
- 테스트는 happy path, fallback, handoff, policy gate를 함께 검증한다.
