from PROJECT.conversations.evidence_submission import service as evidence_service
from PROJECT.conversations.field_binding import service as field_binding_service
from PROJECT.conversations.evidence_submission.states import (
    STATE_EVIDENCE_WAITING_DOCUMENT,
    STATE_EVIDENCE_WAITING_LOCATION,
)
from PROJECT.conversations.fertilizer_intake import service as fertilizer_service
from PROJECT.conversations.input_resolve import service as input_resolve_service
from PROJECT.conversations.input_resolve.states import (
    STATE_INPUT_RESOLVE_DECISION,
    STATE_INPUT_RESOLVE_RAW_INPUT,
)
from PROJECT.conversations.fertilizer_intake.states import (
    STATE_FERTILIZER_CONFIRM,
    STATE_FERTILIZER_KIND,
)
from PROJECT.conversations.yield_intake import service as yield_service
from PROJECT.conversations.yield_intake.states import STATE_YIELD_AMOUNT
from PROJECT.i18n.translator import get_catalog
from PROJECT.storage.fields import FIELD_BINDING_SOURCE_LOCATION


def test_fertilizer_prompt_includes_progress_input_mode_and_draft_summary():
    catalog = get_catalog("ko")
    draft = fertilizer_service.update_draft(
        fertilizer_service.new_draft(),
        used=True,
    )

    text = fertilizer_service.prompt_for_state(STATE_FERTILIZER_KIND, catalog, draft)

    assert "비료 입력 2/5 · 버튼 선택" in text
    assert "현재 입력: 비료 사용 여부=사용함" in text
    assert catalog.FERTILIZER_KIND_PROMPT in text


def test_fertilizer_confirmation_includes_review_header():
    catalog = get_catalog("ko")
    draft = fertilizer_service.update_draft(
        fertilizer_service.new_draft(),
        used=True,
        kind="liquid",
        product_name="테스트 액비",
        amount_value=20.0,
        amount_unit="kg",
        applied_date="2026-05-06",
    )

    text = fertilizer_service.confirmation_text(draft, catalog)

    assert "비료 입력 검토 단계 · 버튼 선택" in text
    assert "비료 입력 내용을 확인하세요." in text


def test_yield_prompt_includes_progress_input_mode_and_draft_summary():
    catalog = get_catalog("ko")
    draft = yield_service.update_draft(
        yield_service.new_draft(),
        ready=True,
        field_name="A-1",
    )

    text = yield_service.prompt_for_state(STATE_YIELD_AMOUNT, catalog, draft)

    assert "수확량 입력 3/4 · 텍스트 입력" in text
    assert "현재 입력: 수확 준비 여부=예, 농지=A-1" in text
    assert catalog.YIELD_AMOUNT_PROMPT in text


def test_evidence_prompt_includes_attachment_modes_and_draft_summary():
    catalog = get_catalog("ko")
    draft = evidence_service.new_draft(
        request_event_id="request-1",
        session_id="session-1",
        request_type_code="field_photo",
        field_label="FIELD-001",
    )

    start_text = evidence_service.prompt_for_state(STATE_EVIDENCE_WAITING_LOCATION, catalog, draft)
    assert "증빙 제출 1/2 · 위치 첨부" in start_text
    assert "현재 입력: 농지=FIELD-001" in start_text

    updated = evidence_service.update_draft(
        draft,
        accepted_location=True,
        file_name="evidence.jpg",
    )
    document_text = evidence_service.prompt_for_state(STATE_EVIDENCE_WAITING_DOCUMENT, catalog, updated)
    assert "증빙 제출 2/2 · document 업로드" in document_text
    assert "위치 확인 완료" in document_text


def test_myfields_prompts_include_progress_and_draft_summary():
    catalog = get_catalog("ko")

    summary_text = field_binding_service.summary_text(
        participant_name="홍길동",
        bindings=(),
        catalog=catalog,
    )
    assert "자기 조회 요약 단계 · 버튼 선택" in summary_text

    method_text = field_binding_service.method_text(catalog, has_bindings=True)
    assert "자기 조회 1/4 · 버튼 선택" in method_text
    assert "현재 입력: 등록 농지 수=1" in method_text

    confirm_text = field_binding_service.confirm_text(
        field_name="논 1",
        field_code="FIELD-001",
        lookup_method=FIELD_BINDING_SOURCE_LOCATION,
        catalog=catalog,
    )
    assert "자기 조회 검토 단계 · 버튼 선택" in confirm_text
    assert "현재 입력: 등록 방법=위치 공유, 농지=논 1 (FIELD-001)" in confirm_text


def test_input_resolve_prompts_include_progress_and_draft_summary():
    catalog = get_catalog("ko")
    draft = input_resolve_service.update_draft(
        input_resolve_service.new_draft("session-1"),
        target_type_code=input_resolve_service.TARGET_FIELD_CODE,
        method_code=input_resolve_service.METHOD_TYPED_TEXT,
        raw_input_text="field-001",
        latest_candidates=(
            {
                "candidate_id": "candidate-1",
                "rank": 1,
                "label": "논 1 (FIELD-001)",
                "normalized_value": {"field_code": "FIELD-001"},
            },
        ),
        selected_candidate_label="논 1 (FIELD-001)",
    )

    raw_input_text = input_resolve_service.prompt_for_state(STATE_INPUT_RESOLVE_RAW_INPUT, catalog, draft)
    assert "입력 해석 3/4 · 텍스트 입력" in raw_input_text
    assert "현재 입력: 대상=농지 고유 번호, 입력 방식=글로 입력, 원문=field-001, 후보 수=1, 후보 확정=논 1 (FIELD-001)" in raw_input_text

    decision_text = input_resolve_service.prompt_for_state(STATE_INPUT_RESOLVE_DECISION, catalog, draft)
    assert "입력 해석 검토 단계 · 버튼 선택" in decision_text
    assert "현재 입력: 대상=농지 고유 번호, 입력 방식=글로 입력, 원문=field-001, 후보 수=1, 후보 확정=논 1 (FIELD-001)" in decision_text
