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
- 뒤로가기, 취소, 처음부터
- 상태별 fallback, 알 수 없는 입력 처리

## 구조

- `channels/telegram/*`: 텔레그램 라이브러리 의존 코드
- `canonical_intents/*`: 외부 입력을 내부 intent로 정규화
- `dispatch/*`: 세션 상태 기반 라우팅
- `conversations/sample_menu/*`: 메뉴 플로우 상태, 키보드, 메시지 조합
- `i18n/catalogs/ko.py`: 사용자 노출 문구
