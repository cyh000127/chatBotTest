from __future__ import annotations

from dataclasses import asdict, dataclass

from PROJECT.conversations.evidence_submission import keyboards
from PROJECT.conversations.evidence_submission.states import (
    STATE_EVIDENCE_VALIDATING,
    STATE_EVIDENCE_WAITING_DOCUMENT,
    STATE_EVIDENCE_WAITING_LOCATION,
)
from PROJECT.evidence import (
    EVIDENCE_REASON_LOCATION_DISTANCE_TOO_FAR,
    EVIDENCE_REASON_MISSING_CAPTURE_TIME,
    EVIDENCE_REASON_MISSING_EXIF,
    EVIDENCE_REASON_MISSING_GPS,
)


@dataclass(frozen=True)
class EvidenceSubmissionDraft:
    request_event_id: str = ""
    session_id: str = ""
    request_type_code: str = ""
    field_label: str = ""
    accepted_location: bool = False
    accepted_latitude: float | None = None
    accepted_longitude: float | None = None
    accepted_accuracy_meters: float | None = None
    document_uploaded: bool = False
    provider_file_id: str = ""
    provider_file_unique_id: str = ""
    file_name: str = ""
    mime_type: str = ""
    file_size_bytes: int | None = None
    evidence_submission_id: str = ""
    artifact_status_code: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def new_draft(
    *,
    request_event_id: str,
    session_id: str,
    request_type_code: str,
    field_label: str = "",
) -> EvidenceSubmissionDraft:
    return EvidenceSubmissionDraft(
        request_event_id=request_event_id,
        session_id=session_id,
        request_type_code=request_type_code,
        field_label=field_label,
    )


def draft_from_dict(payload: dict | None) -> EvidenceSubmissionDraft | None:
    if not payload:
        return None
    return EvidenceSubmissionDraft(
        request_event_id=str(payload.get("request_event_id", "")),
        session_id=str(payload.get("session_id", "")),
        request_type_code=str(payload.get("request_type_code", "")),
        field_label=str(payload.get("field_label", "")),
        accepted_location=bool(payload.get("accepted_location", False)),
        accepted_latitude=payload.get("accepted_latitude"),
        accepted_longitude=payload.get("accepted_longitude"),
        accepted_accuracy_meters=payload.get("accepted_accuracy_meters"),
        document_uploaded=bool(payload.get("document_uploaded", False)),
        provider_file_id=str(payload.get("provider_file_id", "")),
        provider_file_unique_id=str(payload.get("provider_file_unique_id", "")),
        file_name=str(payload.get("file_name", "")),
        mime_type=str(payload.get("mime_type", "")),
        file_size_bytes=payload.get("file_size_bytes"),
        evidence_submission_id=str(payload.get("evidence_submission_id", "")),
        artifact_status_code=str(payload.get("artifact_status_code", "")),
    )


def update_draft(draft: EvidenceSubmissionDraft, **changes) -> EvidenceSubmissionDraft:
    payload = draft.to_dict()
    payload.update(changes)
    return EvidenceSubmissionDraft(
        request_event_id=str(payload.get("request_event_id", "")),
        session_id=str(payload.get("session_id", "")),
        request_type_code=str(payload.get("request_type_code", "")),
        field_label=str(payload.get("field_label", "")),
        accepted_location=bool(payload.get("accepted_location", False)),
        accepted_latitude=payload.get("accepted_latitude"),
        accepted_longitude=payload.get("accepted_longitude"),
        accepted_accuracy_meters=payload.get("accepted_accuracy_meters"),
        document_uploaded=bool(payload.get("document_uploaded", False)),
        provider_file_id=str(payload.get("provider_file_id", "")),
        provider_file_unique_id=str(payload.get("provider_file_unique_id", "")),
        file_name=str(payload.get("file_name", "")),
        mime_type=str(payload.get("mime_type", "")),
        file_size_bytes=payload.get("file_size_bytes"),
        evidence_submission_id=str(payload.get("evidence_submission_id", "")),
        artifact_status_code=str(payload.get("artifact_status_code", "")),
    )


def keyboard_for_state(
    state: str,
    catalog,
    draft: EvidenceSubmissionDraft | None = None,
) -> list[list[dict[str, str]]]:
    return keyboards.keyboard_for_state(state, catalog)


def start_text(catalog, draft: EvidenceSubmissionDraft) -> str:
    return catalog.format_evidence_entry(field_label=draft.field_label or "-")


def prompt_for_state(
    state: str,
    catalog,
    draft: EvidenceSubmissionDraft | None = None,
) -> str:
    if state == STATE_EVIDENCE_WAITING_LOCATION:
        return start_text(catalog, draft or EvidenceSubmissionDraft())
    if state == STATE_EVIDENCE_WAITING_DOCUMENT:
        return catalog.EVIDENCE_DOCUMENT_PROMPT
    if state == STATE_EVIDENCE_VALIDATING:
        return catalog.format_evidence_uploaded(file_name=(draft.file_name if draft else "") or "-")
    return start_text(catalog, draft or EvidenceSubmissionDraft())


def fallback_text_for_state(state: str, catalog) -> str:
    if state == STATE_EVIDENCE_WAITING_LOCATION:
        return catalog.EVIDENCE_LOCATION_FALLBACK
    if state == STATE_EVIDENCE_WAITING_DOCUMENT:
        return catalog.EVIDENCE_DOCUMENT_FALLBACK
    if state == STATE_EVIDENCE_VALIDATING:
        return catalog.EVIDENCE_VALIDATING_MESSAGE
    return catalog.EVIDENCE_RUNTIME_UNAVAILABLE_MESSAGE


def accepted_text(catalog, draft: EvidenceSubmissionDraft) -> str:
    return catalog.format_evidence_accepted(file_name=draft.file_name or "-")


def retry_text(catalog, draft: EvidenceSubmissionDraft, *, reason_codes: tuple[str, ...]) -> str:
    reason_lines = tuple(reason_text(catalog, reason_code) for reason_code in reason_codes)
    return catalog.format_evidence_retry_required(
        file_name=draft.file_name or "-",
        reason_lines=reason_lines,
    )


def manual_review_text(catalog, draft: EvidenceSubmissionDraft, *, reason_codes: tuple[str, ...]) -> str:
    reason_lines = tuple(reason_text(catalog, reason_code) for reason_code in reason_codes)
    return catalog.format_evidence_manual_review(
        file_name=draft.file_name or "-",
        reason_lines=reason_lines,
    )


def reason_text(catalog, reason_code: str) -> str:
    mapping = {
        EVIDENCE_REASON_MISSING_EXIF: catalog.EVIDENCE_REASON_MISSING_EXIF,
        EVIDENCE_REASON_MISSING_GPS: catalog.EVIDENCE_REASON_MISSING_GPS,
        EVIDENCE_REASON_MISSING_CAPTURE_TIME: catalog.EVIDENCE_REASON_MISSING_CAPTURE_TIME,
        EVIDENCE_REASON_LOCATION_DISTANCE_TOO_FAR: catalog.EVIDENCE_REASON_LOCATION_DISTANCE_TOO_FAR,
    }
    return mapping.get(reason_code, reason_code)
