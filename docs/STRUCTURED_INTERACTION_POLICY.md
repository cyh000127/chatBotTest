# Structured Interaction Policy

## 1. 목적

이 문서는 메신저 기반 단계형 입력 서비스에서 structured interaction을 어떻게 유지할지 설명한다.

핵심 목표:

- 한 메시지에서 하나의 primary action을 요구한다.
- 버튼 실패나 자유문장 입력에도 같은 intent로 복구 가능해야 한다.
- 수정 요청과 확인 요청을 안전하게 처리한다.

## 2. 기본 원칙

- current step이 항상 최우선 문맥이다.
- 사용자는 현재 step에서 필요한 값만 입력하도록 유도한다.
- unknown 입력은 종료가 아니라 guided recovery로 연결한다.
- restart, cancel, back, help는 모든 구조화 플로우에서 일관되게 동작해야 한다.

## 3. 입력 단계 원칙

- 입력 단계는 required value를 명확히 묻는다.
- 허용 형식 예시를 짧게 제공한다.
- 검증 실패 시 같은 step를 재안내한다.
- 필요한 경우 fast-path 버튼을 우선 제공한다.

## 4. 수정 단계 원칙

- 수정 의도는 signal로만 사용한다.
- 수정 대상이 확정되지 않으면 먼저 target selection으로 이동한다.
- 새 값이 잡혀도 pending candidate preview를 먼저 보여준다.
- confirm 없이 overwrite 하지 않는다.

## 5. Confirm 단계 원칙

- confirm 단계는 가장 강한 안전 단계다.
- `맞아요`, `수정`, `취소`, `처음부터` 같은 명시 응답을 우선 처리한다.
- 자유문장 수정 요청은 일반 unknown으로 닫지 않는다.
- 먼저 contextual repair를 시도하고, 실패 시 제한적으로 모델 보조를 고려한다.

## 6. Recovery UX 원칙

fallback은 아래 요소를 포함하는 것이 좋다.

- 짧은 headline
- 현재 step 요약
- 가능한 다음 행동
- fast-path 버튼
- 필요 시 restart 또는 handoff 안내

권장 recovery level:

- `soft`
- `guided`
- `escalation_ready`

## 7. Restart / Text Fallback 원칙

- 버튼 전달 실패 시 text keyword 또는 guided prompt로 같은 intent에 재진입할 수 있어야 한다.
- 중단된 draft가 복구 가능하면 `계속`, `다시 입력`, `취소` 같은 액션만 노출한다.
- recovery action은 validation rule을 바꾸지 않는다.

## 8. 자기 조회 및 입력 진입점 원칙

우선 진입점:

- `/start`
- `/myfields`
- `/yield`
- `/fertilizer`
- `input.resolve.start`

이 진입점은 모두 동일한 제품 범위 안에서 localized copy, fallback, restart 규칙을 공유해야 한다.

## 9. 제외 항목

structured interaction 정책에서 다루지 않는 항목:

- 날씨 조회
- 오늘 날짜 조회
- 범용 정보 검색
- 자유 잡담 응답

## 10. 최종 요약

- structured interaction은 현재 step 중심으로 운영한다.
- 수정은 signal, 후보, confirm 단계를 분리한다.
- fallback은 종료가 아니라 회수 경로다.
- restart와 text fallback은 정규 기능이다.
- 제품 범위 밖의 데모성 기능은 정책 대상에서 제외한다.
