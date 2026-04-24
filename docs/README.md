# Documentation Index

이 문서 묶음은 메신저 기반 구조화 입력 서비스의 상호작용 정책, 규칙 엔진 구조, 제한적 모델 보조 기준을 설명한다.

기본 해석 원칙:

- `reference-docs`가 우선 참고 기준이다.
- `reference-docs`에 명시되지 않은 추가 명세와 상세 기능을 정하는 것이 현재 문서 묶음의 목적이다.
- 현재 문서 묶음은 상위 참고 문서를 런타임 정책과 구현 기준으로 구체화한다.

문서 전체는 아래 원칙을 따른다.

- 특정 회사명, 제품명, 내부 코드명은 사용하지 않는다.
- 특정 구현 구조나 상대경로를 전제로 설명하지 않는다.
- 운영 정책과 런타임 제약을 먼저 설명하고, 구현은 그 제약을 따르는 하위 항목으로 정리한다.
- 문서는 독립적으로 읽혀야 하며 외부 문맥이 없어도 개요를 이해할 수 있어야 한다.

문서 구성은 다음과 같다.

- `CHATBOT_OPERATION_POLICY_V2.md`
  상호작용 정책, 복구 정책, handoff 기준, telemetry vocabulary를 정의한다.
- `STAGE2_RULE_ENGINE.md`
  규칙 엔진의 단계 구조, 공통 계약, 확장 순서를 정의한다.
- `RULE_FIRST_LLM_HANDOFF.md`
  규칙 우선 처리 이후에만 허용되는 모델 보조 판정 흐름을 정의한다.
- `MODEL_RECOVERY_SETUP.md`
  모델 기반 recovery classifier를 주입할 때 필요한 런타임 구성 조건을 설명한다.
- `STRUCTURED_INTERACTION_POLICY.md`
  구조화 입력, 수정 요청, fallback, confirm, handoff UX 원칙을 설명한다.
- `FEATURE_SCOPE_BASELINE.md`
  구현 대상 기능과 비대상 기능을 구분하는 제품 범위 기준을 정리한다.
- `SUPPORT_HANDOFF_CHATBOT_RELAY.md`
  지원 이관이 기존 챗봇 대화창 안에서 운영자 후속 답변을 중계하는 방식임을 정의한다.
- `SQLITE_RUNTIME_SETUP.md`
  SQLite 영속 저장소가 추가되는 환경의 기본 설정, 실행 전제, 데이터 보존 기준을 정의한다.
- `SQLITE_SCHEMA_PLAN.md`
  SQLite migration으로 구현할 테이블, 상태 코드, 인덱스, 레퍼런스 정렬 기준을 정의한다.
- `SQLITE_IMPLEMENTATION_RUNBOOK.md`
  SQLite 적용 후 실행 흐름, Admin API 검증 절차, 구현 완료 상태, 운영 검증 기준을 정의한다.
- `REFERENCE_ALIGNMENT_REVIEW.md`
  SQLite/Admin/온보딩 계획이 상위 참고 기준을 해치지 않는지 검증하고 조건부 승인 기준을 정의한다.

현재 기준 핵심 요약:

- 메인 경로는 rule-first structured interaction이다.
- 자유 대화형 응답 엔진이 아니라 단계형 입력 수집과 검증 중심 구조를 따른다.
- 모델 호출은 예외적 보조 판정기로만 허용한다.
- unknown 입력은 종료하지 않고 guided recovery로 회수한다.
- 자연어 수정은 직접 반영하지 않고 수정 의도와 후보 추출 신호로만 다룬다.
- 후보값은 pending candidate로만 저장하고, 명시적 확인 전에는 확정값으로 승격하지 않는다.
- 상위 참고 문서에 없는 세부 상호작용 규칙은 현재 `docs`에서 결정한다.

현재 구현 기준의 우선 기능 범위:

- 시작 진입과 언어 선택
- 비료 입력
- 수확량 입력
- 자기 조회 진입점
- input resolve 진입점
- restart, fallback, support escalation 안내
- 기존 챗봇 대화창 안에서 이루어지는 운영자 후속 답변 중계

샘플로 남아 있는 프로필 입력 흐름은 제품 온보딩 계약이 아니라 구조화 입력 UX 검증용 흐름이다.
제품 온보딩은 상위 참고 기준의 이름, 전화번호, 선호 언어, 지원 국가 코드 기반 전화번호 정규화 규칙을 따라야 한다.

현재 구현 기준의 제외 대상:

- 오늘 날짜 조회
- 오늘 날씨 조회
- 데모성 도시 선택 플로우
- 로컬 샘플용 인증 흐름
- 로컬 샘플용 프로필 입력 흐름을 제품 온보딩으로 사용하는 것
