# Evidence Submission Baseline

## 1. 목적

이 문서는 farmer-facing runtime에서 증빙 제출과 기본 검증 흐름을 구현할 때 따라야 하는 최소 기준을 정리한다.

핵심 목표는 다음과 같다.

- 증빙 요청 문맥을 저장한다.
- 위치 확인 이후에만 원본 document 업로드를 받는다.
- EXIF, GPS, 촬영 시각 같은 기본 검증 신호를 저장한다.
- 자동 승인 불가 상황을 재제출 또는 운영 검토로 보낸다.

## 2. 범위

현재 단계에서 구현하는 범위는 아래와 같다.

- 증빙 요청 event 저장
- 증빙 제출 session 저장
- 위치 선행 수집 상태 저장
- document 업로드 메타데이터 저장
- EXIF, GPS, 촬영 시각 signal 저장
- validation state log 저장

현재 단계에서 구현하지 않는 범위는 아래와 같다.

- 외부 object storage 승격 파이프라인
- vision 모델 판독
- signed download URL
- 운영 export surface
- 대규모 media worker 분산 처리

## 3. 기본 원칙

- 증빙 제출은 자유 업로드가 아니라 요청 문맥 또는 명시적 제출 단계에서만 열린다.
- 위치 수락 전에는 업로드 완료 상태로 처리하지 않는다.
- 압축 이미지보다 document 업로드 경로를 우선 사용한다.
- 업로드 성공은 검증 성공과 같은 의미가 아니다.
- EXIF, GPS, 촬영 시각이 없으면 조용히 통과시키지 않는다.
- 자동 확정이 어려우면 재제출 또는 운영 검토로 내려간다.

## 4. 대화 흐름

### 4.1 증빙 요청 시작

1. 런타임이 증빙 요청 event를 연다.
2. 사용자는 요청 안내를 보고 증빙 제출을 시작한다.
3. 세션은 먼저 위치 공유 단계를 요구한다.

### 4.2 위치 선행 수집

1. 사용자가 위치를 보낸다.
2. 런타임은 위치 좌표, 정확도, 수신 시각을 session에 저장한다.
3. 위치 수락이 완료되면 document 업로드 단계로 이동한다.

### 4.3 document 업로드

1. 사용자는 원본 document로 파일을 올린다.
2. 런타임은 파일 식별자, 파일명, mime type, 업로드 시각을 저장한다.
3. 이후 EXIF, GPS, 촬영 시각 signal 계산 단계로 이동한다.

### 4.4 검증 결과 처리

1. 런타임은 저장된 signal을 바탕으로 validation state를 기록한다.
2. 자동 승인 가능하면 제출을 완료한다.
3. 신호가 부족하거나 충돌하면 재제출 안내 또는 운영 검토로 보낸다.

## 5. 저장 구조 기준

현재 단계의 SQLite 저장 구조는 아래 책임을 가져야 한다.

- `evidence_request_events`
  - 어떤 참여자, 어떤 농지 문맥에서 증빙이 필요한지 저장
- `evidence_submission_sessions`
  - 위치 선행 여부와 현재 제출 단계를 저장
- `evidence_submissions`
  - document 업로드 메타데이터와 artifact 상태를 저장
- `evidence_validation_signals`
  - EXIF, GPS, 촬영 시각, 거리 같은 기본 검증 신호를 저장
- `evidence_validation_state_logs`
  - append-only validation 상태 전이를 기록

원본 파일 업로드와 validation 결과는 같은 개념이 아니다.

업로드 row는 파일 수신 사실을 기록하고, validation log는 그 파일이 어떤 판단을 받았는지 따로 기록한다.

## 6. 기본 signal 기준

현재 단계에서 최소한 아래 signal을 저장할 수 있어야 한다.

- `exif_present`
- `gps_present`
- `capture_time_present`
- `capture_time`
- `gps_latitude`
- `gps_longitude`
- `location_distance_meters`
- `upload_delay_seconds`

이 signal 이름은 사용자 노출 문구가 아니라 내부 저장 vocabulary다.

## 7. 자동 판정 규칙

자동 완료는 아래 조건을 모두 만족할 때만 허용한다.

- 위치 수락이 끝났을 것
- document 업로드 메타데이터가 존재할 것
- EXIF, GPS, 촬영 시각 signal이 모두 존재할 것
- 필수 signal에 명백한 충돌이 없을 것

하나라도 만족하지 못하면 `재제출 안내` 또는 `운영 검토`로 내려간다.

## 8. 운영 검토 기준

아래 상황은 운영 검토 대상으로 본다.

- EXIF 없음
- GPS 없음
- 촬영 시각 없음
- 위치와 사진 좌표가 허용 범위를 벗어남
- 반복 재제출 후에도 같은 실패가 누적됨

운영 검토는 기존 챗봇 대화창과 별개 실시간 상담방을 만드는 기능이 아니다.

필요하면 운영자 후속 답변 또는 관리자 처리로 이어진다.

## 9. 완료 기준

- 증빙 요청 event와 제출 session이 SQLite에 남는다.
- 위치 수락 전에는 업로드 완료 상태가 되지 않는다.
- document 업로드 메타데이터와 validation signal이 분리 저장된다.
- validation state log가 append-only로 남는다.
- 자동 확정 불가 상황이 재제출 또는 운영 검토로 이어진다.
