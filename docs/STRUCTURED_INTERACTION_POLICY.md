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
- 사용자는 항상 현재 단계와 다음 행동을 이해할 수 있어야 한다.

## 3. 진행 상태 원칙

- 구조화 플로우는 가능하면 현재 작업과 현재 단계 표시를 제공한다.
- confirm 직전에는 현재 draft를 짧게 요약한다.
- retry 시점에도 현재 step를 다시 식별할 수 있어야 한다.
- 진행 상태는 긴 설명보다 우선한다.

## 4. 입력 단계 원칙

- 입력 단계는 required value를 명확히 묻는다.
- 허용 형식 예시를 짧게 제공한다.
- 검증 실패 시 같은 step를 재안내한다.
- 필요한 경우 fast-path 버튼을 우선 제공한다.
- 버튼 전용 단계인지 텍스트 입력 허용 단계인지 분명히 알려준다.

## 5. 수정 단계 원칙

- 수정 의도는 signal로만 사용한다.
- 수정 대상이 확정되지 않으면 먼저 target selection으로 이동한다.
- 새 값이 잡혀도 pending candidate preview를 먼저 보여준다.
- confirm 없이 overwrite 하지 않는다.

## 6. Confirm 단계 원칙

- confirm 단계는 가장 강한 안전 단계다.
- `맞아요`, `수정`, `취소`, `처음부터` 같은 명시 응답을 우선 처리한다.
- 자유문장 수정 요청은 일반 unknown으로 닫지 않는다.
- 먼저 contextual repair를 시도하고, 실패 시 제한적으로 모델 보조를 고려한다.
- confirm 단계에서는 전체 요약과 수정 가능한 항목을 함께 보여주는 것이 좋다.

## 7. Recovery UX 원칙

fallback은 아래 요소를 포함하는 것이 좋다.

- 짧은 headline
- 현재 step 요약
- 입력 모드
- 실패 이유
- 가능한 다음 행동
- fast-path 버튼
- 필요 시 restart 또는 handoff 안내

권장 recovery level:

- `soft`
- `guided`
- `escalation_ready`

## 8. Retry copy 원칙

- retry copy는 첫 진입 copy보다 짧아야 한다.
- 동일 step에서 같은 안내문을 길게 반복하지 않는다.
- retry copy는 최소한 `왜 실패했는지`, `지금 무엇을 보내야 하는지`를 알려줘야 한다.
- 형식 오류와 버튼 전용 단계 오류는 서로 다른 copy를 사용한다.
- 특정 필드 재입력 단계에서는 `현재 값 1개 + 새 값 입력` 패턴을 기본으로 한다.
- retry가 이미 선택된 target, method, lookup path를 가진 상태라면 그 문맥만 유지하고 전체 draft 재설명은 피한다.

## 9. Restart / Text Fallback 원칙

- 버튼 전달 실패 시 text keyword 또는 guided prompt로 같은 intent에 재진입할 수 있어야 한다.
- 중단된 draft가 복구 가능하면 `계속`, `다시 입력`, `취소` 같은 액션만 노출한다.
- recovery action은 validation rule을 바꾸지 않는다.
- resume 가능한 상태에서는 같은 요청을 이어서 진행하는지, 새로 시작하는지 사용자에게 분명히 알려준다.

## 10. 지원 이관 및 운영 검토 대기 원칙

- 지원 이관은 실시간 상담 연결처럼 보이게 안내하지 않는다.
- 같은 챗봇 대화창에서 후속 답변이 이어진다는 점을 유지한다.
- 대기 상태에서는 `추가 설명`, `도움말`, `처음으로` 같은 안전 액션을 함께 유지한다.

## 11. 자기 조회 및 입력 진입점 원칙

우선 진입점:

- `/start`
- `/myfields`
- `/yield`
- `/fertilizer`
- `input.resolve.start`

이 진입점은 모두 동일한 제품 범위 안에서 localized copy, fallback, restart 규칙을 공유해야 한다.

추가 규칙:

- `/myfields` 위치 실패는 generic 오류가 아니라 고유 번호 입력 repair step으로 전환한다.
- `/myfields` 고유 번호 재입력은 `등록 방법 + 직전 고유 번호`만 보여준다.
- `input resolve` 후보 없음 상태는 버튼 선택 단계로 유지하고, retry 선택 시 raw input repair prompt로 복귀한다.

## 12. 제외 항목

structured interaction 정책에서 다루지 않는 항목:

- 날씨 조회
- 오늘 날짜 조회
- 범용 정보 검색
- 자유 잡담 응답

## 13. 최종 요약

- structured interaction은 현재 step 중심으로 운영한다.
- 진행 상태, 입력 모드, 실패 이유가 사용자에게 보이는 guided UX를 지향한다.
- 수정은 signal, 후보, confirm 단계를 분리한다.
- fallback은 종료가 아니라 회수 경로다.
- restart와 text fallback은 정규 기능이다.
- 제품 범위 밖의 데모성 기능은 정책 대상에서 제외한다.
