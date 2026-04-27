# Runtime Overview

이 저장소는 메신저 기반 구조화 입력 런타임을 검증하기 위한 구현체다.

핵심 목적은 사용자의 자유 대화를 처리하는 범용 챗봇이 아니라, 정해진 단계에서 필요한 값을 수집하고 검증한 뒤 확인 절차를 거쳐 다음 행동으로 연결하는 것이다.

## 기준 문서

해석 우선순위는 다음 순서를 따른다.

1. 상위 참고 문서 묶음
2. 현재 저장소의 문서 묶음
3. 코드와 테스트

현재 저장소의 문서 묶음은 상위 참고 문서에 없는 세부 런타임 규칙을 구현 가능한 형태로 정리한다.

대표 문서는 다음과 같다.

- `Documentation Index`: 문서 묶음의 해석 원칙과 현재 기준 요약
- `Feature Scope Baseline`: 구현 대상과 제외 대상을 구분하는 범위 기준
- `Chatbot Operation Policy v2`: rule-first 상호작용, recovery, handoff, telemetry 기준
- `Stage 2 Rule Engine`: 규칙 엔진 단계와 공통 계약
- `Rule-First LLM Handoff`: 제한적 모델 보조와 handoff 경계
- `Model Recovery Setup`: recovery classifier 구성과 런타임 gate 기준
- `Structured Interaction Policy`: confirm, edit, fallback UX 원칙
- `Field Binding Implementation Baseline`: 농지 바인딩과 `/myfields` 실체화 기준
- `Support Handoff Chatbot Relay`: 기존 챗봇 대화창 안에서 운영자 후속 답변을 중계하는 기준
- `SQLite Backup And Recovery Runbook`: 로컬 SQLite 백업, 복구, 검증 절차
- `Target Runtime Integration Guide`: 다른 런타임으로 옮길 때 재사용 범위와 금지 범위를 정리한 이식 기준

## 현재 구현 범위

현재 우선 구현 범위는 farmer-facing 핵심 루프에 맞춰져 있다.

- 시작 진입, 도움말, 메뉴, 취소, 재시작
- 언어 선택
- 비료 입력
- 수확량 입력
- 자기 조회와 농지 바인딩
- input resolve 진입점 안내
- 상태별 fallback과 guided recovery
- pending candidate 분리와 confirm 전 저장 금지
- 제한적 recovery classifier와 정책 gate
- `support.escalate`, `manual_resolution_required`, admin follow-up queue 정렬
- 지원 이관 상태의 사용자 추가 메시지 수집
- 운영자 후속 답변의 챗봇 대화창 중계
- admin follow-up outbox와 delivery loop
- 로컬 관리자 follow-up API와 편의용 웹 화면

## 운영 원칙

- 메인 경로는 rule-first로 유지한다.
- 모델은 current-step recovery classifier 또는 edit intent 보조기로만 사용한다.
- 자연어 수정 요청은 직접 업데이트가 아니라 수정 의도 신호로만 다룬다.
- 모델이나 규칙에서 추출한 후보값은 pending candidate로만 저장한다.
- 명시적 confirm 전에는 authoritative value로 승격하지 않는다.
- unknown 입력은 종료하지 않고 guided fallback으로 회수한다.
- 반복 실패, 명시적 도움 요청, 운영성 요청은 handoff 경로로 보낸다.
- handoff는 새 채팅방 생성이나 실시간 상담 연결이 아니라 기존 챗봇 대화창 안에서 운영자 후속 답변을 중계하기 위한 이관 신호다.

## 편의 기능의 해석

아래 기능은 명세의 제품 계약을 확장하기 위한 것이 아니라, 현재 프로젝트에서 개발과 검증을 쉽게 하기 위해 부득이하게 둔 로컬 보조 기능이다.

- 로컬 관리자 follow-up 웹 화면은 정식 운영 콘솔이 아니라 요청 확인, 대화 내용 확인, 응답 전송을 빠르게 검증하기 위한 편의 화면이다.
- 웹 응답 화면은 PowerShell JSON 요청에서 한글 본문이 깨질 수 있는 문제를 피하기 위해 UTF-8 HTML form 경로를 제공한다.
- 프로필 입력 흐름은 제품 온보딩 계약이 아니라 구조화 입력, 수정, confirm, recovery UX를 검증하기 위한 샘플 흐름이다.
- 샘플 프로필 코드는 저장소에 남아 있을 수 있지만 메인 메뉴, slash command surface, 전역 자연어 repair routing에서는 노출하지 않는다.
- runtime-local AI gate는 상위 정책 시스템이 아직 연결되지 않은 상태에서 모델 호출 가능 여부를 로컬에서 제한하기 위한 보조 장치다.
- 인메모리 follow-up queue와 outbox는 프로세스 로컬 검증용이며, 영속 저장소나 정식 운영 큐를 대체하지 않는다.

따라서 위 항목은 문서와 테스트에서 명확히 편의 기능으로 격리해야 하며, 상위 참고 문서의 제품 범위와 충돌하는 근거로 사용하지 않는다.

## 제외 범위

아래 항목은 제품 범위에 없거나 데모성 기능이므로 새 구현 대상으로 삼지 않는다.

- 오늘 날짜 조회
- 오늘 날씨 조회
- 도시 선택형 날씨 메뉴
- 단순 데모 메뉴
- 로컬 샘플용 임시 인증 흐름 자체
- 로컬 샘플용 프로필 입력 흐름을 제품 온보딩으로 사용하는 것
- 운영 시스템과 무관한 범용 잡담 응답
- 별도 상담방 생성
- 실시간 상담 보장

## 로컬 실행

저장소 루트에서 가상환경을 활성화한 뒤 의존성을 설치하고 런타임을 실행한다.

```powershell
.\.venv\Scripts\Activate.ps1
pip install -e .[dev]
python -m PROJECT.main
```

관리자 follow-up API가 켜져 있으면 같은 프로세스에서 로컬 API 서버가 함께 시작된다.

환경 변수 예시는 다음과 같다.

```powershell
$env:ADMIN_API_ENABLED = "true"
$env:ADMIN_API_HOST = "127.0.0.1"
$env:ADMIN_API_PORT = "8000"
$env:ADMIN_API_ACCESS_TOKEN = "replace_with_local_admin_token"
$env:ADMIN_API_PREVIOUS_ACCESS_TOKEN = "replace_with_previous_local_admin_token"
$env:ADMIN_API_PREVIOUS_ACCESS_TOKEN_EXPIRES_AT = "2026-12-31T23:59:59+00:00"
$env:ADMIN_API_ACCESS_ROLE = "operator"
python -m PROJECT.main
```

비-SQLite 로컬 런타임에서는 `/start`가 세션 시작 게이트 역할만 한다. `/start sample-user` 같은 레거시 로컬 로그인 인자는 더 이상 인증 흐름으로 해석하지 않는다.

## 로컬 관리자 화면

관리자 follow-up API가 실행 중일 때 아래 화면을 사용할 수 있다.

- 대시보드: `http://127.0.0.1:8000/admin`
- 요청 목록: `http://127.0.0.1:8000/admin/pages/follow-ups`
- 농지 바인딩 예외: `http://127.0.0.1:8000/admin/pages/field-binding-exceptions`
- 사용자 대화 내용: `http://127.0.0.1:8000/admin/pages/follow-ups/{follow_up_id}`
- 사용자 응답 작성: `http://127.0.0.1:8000/admin/pages/follow-ups/{follow_up_id}/reply`
- 감사 로그: `http://127.0.0.1:8000/admin/pages/audit-events`
- 보안 상태: `http://127.0.0.1:8000/admin/pages/security`

대시보드는 지원 이관, 초대 코드, 온보딩 승인, outbox, 감사 로그, 보안 상태 화면으로 이동하는 로컬 운영 홈이다.
이 화면에서 응답을 보내면 admin reply가 follow-up 항목에 기록되고 outbox에 메시지가 생성된다. 상세 화면에서는 답변 없이 요청을 종료할 수 있으며, 종료 안내도 outbox를 통해 봇 delivery loop가 전송한다.

`ADMIN_API_ACCESS_TOKEN`이 설정되어 있으면 관리자 화면은 `/admin/login`에서 access token을 입력한 뒤 접근할 수 있다. 이 값은 실제 환경 파일에만 두고 코드나 문서 예시에 실제 토큰을 남기지 않는다.
관리자 화면의 `로그아웃` 버튼은 브라우저 로그인 쿠키를 삭제하고 다시 `/admin/login`으로 이동한다.

토큰 교체 중에는 `ADMIN_API_PREVIOUS_ACCESS_TOKEN`과 `ADMIN_API_PREVIOUS_ACCESS_TOKEN_EXPIRES_AT`을 함께 설정해 이전 토큰을 짧은 기간만 임시 허용할 수 있다. 만료 시각이 지났거나 잘못된 형식이면 이전 토큰은 자동으로 거부된다.

`ADMIN_API_ACCESS_ROLE`은 로컬 관리자 권한을 제한한다. `viewer`는 조회만 가능하고, `operator`는 초대 코드 생성, 온보딩 승인/반려, follow-up 응답 같은 쓰기 작업을 수행할 수 있다.

보안 상태 화면과 `GET /admin/security-status`는 토큰 값을 표시하지 않고 로컬 access token gate, 이전 토큰 활성 여부, 운영 IDP 미연결 상태, 남은 production hardening 항목만 노출한다.
감사 로그는 로그인 성공/실패, 미인증 관리자 route 접근, 권한 부족으로 차단된 쓰기 요청, 관리자 쓰기 작업을 기록하되 access token과 사용자 입력 본문은 남기지 않는다.

## JSON API

로컬 검증용 JSON API는 다음 경로를 제공한다.

- `GET /admin/follow-ups`
- `GET /admin/follow-ups/{follow_up_id}`
- `POST /admin/follow-ups/{follow_up_id}/reply`
- `POST /admin/follow-ups/{follow_up_id}/close`
- `GET /admin/field-binding-exceptions`
- `POST /admin/field-binding-exceptions/{exception_id}/resolve`
- `GET /admin/invitations`
- `POST /admin/invitations`
- `POST /admin/invitations/{invitation_id}/revoke`
- `GET /admin/outbox`
- `POST /admin/outbox/{outbox_id}/requeue`
- `GET /admin/audit-events`
- `GET /admin/security-status`

초대 코드는 `expires_at`에 ISO-8601 만료 시각을 넣어 생성할 수 있다. 만료된 초대 코드는 `/start <invite_code>` 온보딩을 시작하지 않는다.

`GET /admin/outbox?status=manual_review`로 재시도 한도를 초과해 운영자 확인이 필요한 발송 실패만 조회할 수 있다. `POST /admin/outbox/{outbox_id}/requeue`는 해당 메시지를 직접 전송하지 않고 다시 `pending`으로 되돌려 봇 delivery loop가 재처리하게 한다.

PowerShell에서 JSON API로 한글 응답을 직접 보낼 때는 `charset=utf-8`을 명시해야 한다.

```powershell
Invoke-RestMethod -Method Post `
  -Uri "http://127.0.0.1:8000/admin/follow-ups/{follow_up_id}/reply" `
  -Headers @{ "X-Admin-Token" = $env:ADMIN_API_ACCESS_TOKEN } `
  -ContentType "application/json; charset=utf-8" `
  -Body '{"message":"입력 내용을 확인했습니다. 아래 메뉴에서 다시 선택해주세요."}'
```

더 안전하게 보내려면 UTF-8 byte array를 사용한다.

```powershell
$json = '{"message":"입력 내용을 확인했습니다. 아래 메뉴에서 다시 선택해주세요."}'
$body = [System.Text.Encoding]::UTF8.GetBytes($json)

Invoke-RestMethod -Method Post `
  -Uri "http://127.0.0.1:8000/admin/follow-ups/{follow_up_id}/reply" `
  -Headers @{ "X-Admin-Token" = $env:ADMIN_API_ACCESS_TOKEN } `
  -ContentType "application/json; charset=utf-8" `
  -Body $body
```

## 검증

전체 테스트는 단위 테스트와 계약 테스트를 함께 실행한다.

```powershell
.\.venv\Scripts\python.exe -m pytest
```

현재 검증 대상은 rule-first routing, fallback, pending candidate, 제한적 모델 gate, support handoff, admin follow-up API, 웹 응답 화면, outbox delivery를 포함한다.

## 코드 구조 요약

- `canonical_intents`: 외부 입력을 내부 intent로 정규화
- `rule_engine`: normalization, intent rule, step schema, validation, recovery context
- `dispatch`: 세션 상태 기반 라우팅과 handoff dispatch
- `conversations`: 단계형 입력 상태와 메시지 조합
- `admin`: follow-up queue와 outbox runtime
- `admin_api`: 로컬 follow-up JSON API와 편의용 HTML 화면
- `channels`: 메신저 채널 adapter
- `i18n`: 사용자 노출 문구 catalog
- `telemetry`: 운영 이벤트 이름과 로깅
- `tests`: 정책, 런타임, 계약, 편의 화면 검증
