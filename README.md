# PROJECT

텔레그램 입력을 canonical intent로 정규화하고, 세션 상태에 따라 메뉴 응답을 구성하는 샘플 봇입니다.

## 실행

```powershell
.\.venv\Scripts\Activate.ps1
pip install -e .[dev]
python -m PROJECT.main
```

## 현재 기능

- `/start`, `/help`, `/menu`, `/cancel`
- 오늘 날짜 확인
- 오늘 날씨 확인
- `/fertilizer` 비료 입력 정상 경로
- 뒤로가기, 취소, 처음부터
- 상태별 fallback, 알 수 없는 입력 처리
- Gemini recovery classifier 설정/파서 준비

## 운영 기준

- 메인 경로는 rule-first로 유지하고, LLM은 제한적 보조 판정기로만 사용한다.
- 자연어 수정은 직접 반영하지 않고 수정 의도 신호로만 다룬다.
- LLM 결과는 항상 validator와 state machine을 다시 거친다.
- 최상위 운영 정책은 [`docs/CHATBOT_OPERATION_POLICY_V2.md`](./docs/CHATBOT_OPERATION_POLICY_V2.md)를 기준으로 한다.

## 구조

- `channels/telegram/*`: 텔레그램 라이브러리 의존 코드
- `canonical_intents/*`: 외부 입력을 내부 intent로 정규화
- `dispatch/*`: 세션 상태 기반 라우팅
- `conversations/sample_menu/*`: 메뉴 플로우 상태, 키보드, 메시지 조합
- `i18n/catalogs/ko.py`: 사용자 노출 문구

## 문서

- [`docs/README.md`](./docs/README.md): 프로젝트 내부 문서 인덱스
- [`docs/CHATBOT_OPERATION_POLICY_V2.md`](./docs/CHATBOT_OPERATION_POLICY_V2.md): 챗봇 운영의 최상위 정책 문서
- [`docs/STAGE2_RULE_ENGINE.md`](./docs/STAGE2_RULE_ENGINE.md): 2단계 규칙 엔진 구조
- [`docs/RULE_FIRST_LLM_HANDOFF.md`](./docs/RULE_FIRST_LLM_HANDOFF.md): 3단계 LLM 호출 전제 조건
- [`docs/GEMINI_RECOVERY_SETUP.md`](./docs/GEMINI_RECOVERY_SETUP.md): Gemini 설정과 recovery parser 구조
- [`docs/STRUCTURED_INTERACTION_POLICY.md`](./docs/STRUCTURED_INTERACTION_POLICY.md): fallback, 수정 확인, 제한적 LLM 상호작용 정책
