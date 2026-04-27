from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from PROJECT.conversations.input_resolve import keyboards
from PROJECT.conversations.input_resolve.states import (
    STATE_INPUT_RESOLVE_CANDIDATES,
    STATE_INPUT_RESOLVE_DECISION,
    STATE_INPUT_RESOLVE_METHOD,
    STATE_INPUT_RESOLVE_RAW_INPUT,
    STATE_INPUT_RESOLVE_TARGET,
)
from PROJECT.storage.fields import ParticipantFieldBindingRecord, SqliteFieldRegistryRepository
from PROJECT.storage.input_resolution import InputResolutionCandidate, InputResolutionSession
from PROJECT.storage.reminders import ReminderDelivery

TARGET_FIELD_CODE = "field_code"
TARGET_FIELD_NAME = "field_name"
METHOD_TYPED_TEXT = "typed_text"

DECISION_RESOLVED = "resolved"
DECISION_RETRY = "retry"
DECISION_RETRY_LATER = "retry_later"
DECISION_MANUAL_REVIEW = "manual_review"

TARGET_ALIASES = {
    TARGET_FIELD_CODE: ("농지 코드", "고유 번호", "field code", "code"),
    TARGET_FIELD_NAME: ("농지 이름", "필지 이름", "field name", "name"),
}

METHOD_ALIASES = {
    METHOD_TYPED_TEXT: ("글로 입력", "텍스트", "직접 입력", "typed", "text"),
}

DECISION_ALIASES = {
    DECISION_RESOLVED: ("확정", "선택", "맞아요", "resolved", "confirm"),
    DECISION_RETRY: ("다시", "다시 입력", "retry"),
    DECISION_RETRY_LATER: ("나중", "나중에 다시", "later"),
    DECISION_MANUAL_REVIEW: ("운영 검토", "사람", "manual review", "review"),
}


@dataclass(frozen=True)
class InputResolveDraft:
    session_id: str
    target_type_code: str = ""
    method_code: str = ""
    raw_input_text: str = ""
    selected_candidate_id: str | None = None
    selected_candidate_label: str = ""
    latest_candidates: tuple[dict, ...] = ()

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["latest_candidates"] = [dict(item) for item in self.latest_candidates]
        return payload


def new_draft(session_id: str) -> InputResolveDraft:
    return InputResolveDraft(session_id=session_id)


def draft_from_dict(payload: dict | None) -> InputResolveDraft | None:
    if not payload:
        return None
    candidates = tuple(dict(item) for item in payload.get("latest_candidates", ()))
    return InputResolveDraft(
        session_id=str(payload["session_id"]),
        target_type_code=str(payload.get("target_type_code", "")),
        method_code=str(payload.get("method_code", "")),
        raw_input_text=str(payload.get("raw_input_text", "")),
        selected_candidate_id=payload.get("selected_candidate_id"),
        selected_candidate_label=str(payload.get("selected_candidate_label", "")),
        latest_candidates=candidates,
    )


def update_draft(draft: InputResolveDraft, **changes) -> InputResolveDraft:
    payload = draft.to_dict()
    payload.update(changes)
    if "latest_candidates" in payload:
        payload["latest_candidates"] = tuple(dict(item) for item in payload["latest_candidates"])
    return InputResolveDraft(
        session_id=str(payload["session_id"]),
        target_type_code=str(payload.get("target_type_code", "")),
        method_code=str(payload.get("method_code", "")),
        raw_input_text=str(payload.get("raw_input_text", "")),
        selected_candidate_id=payload.get("selected_candidate_id"),
        selected_candidate_label=str(payload.get("selected_candidate_label", "")),
        latest_candidates=tuple(dict(item) for item in payload.get("latest_candidates", ())),
    )


def keyboard_for_state(state: str, catalog, draft: InputResolveDraft | None = None) -> list[list[dict[str, str]]]:
    if state == STATE_INPUT_RESOLVE_TARGET:
        return keyboards.target_keyboard(catalog)
    if state == STATE_INPUT_RESOLVE_METHOD:
        return keyboards.method_keyboard(catalog)
    if state == STATE_INPUT_RESOLVE_RAW_INPUT:
        return keyboards.raw_input_keyboard(catalog)
    if state == STATE_INPUT_RESOLVE_CANDIDATES:
        if draft is None or not draft.latest_candidates:
            return keyboards.candidate_empty_keyboard(catalog)
        return keyboards.candidate_keyboard(catalog, draft.latest_candidates)
    if state == STATE_INPUT_RESOLVE_DECISION:
        return keyboards.decision_keyboard(catalog)
    return keyboards.target_keyboard(catalog)


def prompt_for_state(state: str, catalog, draft: InputResolveDraft | None = None) -> str:
    if state == STATE_INPUT_RESOLVE_TARGET:
        return catalog.INPUT_RESOLVE_TARGET_PROMPT
    if state == STATE_INPUT_RESOLVE_METHOD:
        return catalog.INPUT_RESOLVE_METHOD_PROMPT
    if state == STATE_INPUT_RESOLVE_RAW_INPUT:
        return catalog.INPUT_RESOLVE_RAW_INPUT_PROMPT
    if state == STATE_INPUT_RESOLVE_CANDIDATES:
        if draft is None or not draft.latest_candidates:
            return catalog.INPUT_RESOLVE_CANDIDATE_NONE_MESSAGE
        return catalog.format_input_resolve_candidate_list(
            target_label=target_label(draft.target_type_code, catalog),
            raw_input=draft.raw_input_text,
            candidates=tuple(candidate["label"] for candidate in draft.latest_candidates),
        )
    if state == STATE_INPUT_RESOLVE_DECISION:
        return catalog.format_input_resolve_selected_candidate(
            target_label=target_label(draft.target_type_code if draft else "", catalog),
            candidate_label=draft.selected_candidate_label if draft else "-",
        )
    return catalog.INPUT_RESOLVE_ENTRY_MESSAGE


def target_label(target_type_code: str, catalog) -> str:
    if target_type_code == TARGET_FIELD_CODE:
        return catalog.BUTTON_INPUT_RESOLVE_TARGET_FIELD_CODE
    if target_type_code == TARGET_FIELD_NAME:
        return catalog.BUTTON_INPUT_RESOLVE_TARGET_FIELD_NAME
    return catalog.BUTTON_INPUT_RESOLVE


def parse_target_choice(text: str, catalog) -> str | None:
    normalized = _normalize(text)
    for target_type_code, aliases in TARGET_ALIASES.items():
        button = _normalize(target_label(target_type_code, catalog))
        if normalized == button or normalized in {_normalize(alias) for alias in aliases}:
            return target_type_code
    return None


def parse_method_choice(text: str, catalog) -> str | None:
    normalized = _normalize(text)
    for method_code, aliases in METHOD_ALIASES.items():
        button = _normalize(catalog.BUTTON_INPUT_RESOLVE_METHOD_TYPED_TEXT)
        if method_code == METHOD_TYPED_TEXT and (normalized == button or normalized in {_normalize(alias) for alias in aliases}):
            return method_code
    return None


def parse_candidate_choice(text: str, draft: InputResolveDraft | None) -> str | None:
    if draft is None or not draft.latest_candidates:
        return None
    normalized = _normalize(text)
    if normalized.isdigit():
        rank = int(normalized)
        for candidate in draft.latest_candidates:
            if int(candidate["rank"]) == rank:
                return str(candidate["candidate_id"])
    for candidate in draft.latest_candidates:
        if normalized == _normalize(candidate["label"]):
            return str(candidate["candidate_id"])
    return None


def parse_decision_choice(text: str) -> str | None:
    normalized = _normalize(text)
    for decision_code, aliases in DECISION_ALIASES.items():
        if normalized in {_normalize(alias) for alias in aliases}:
            return decision_code
    return None


def candidate_payload(candidate: InputResolutionCandidate) -> dict:
    normalized_value = json.loads(candidate.normalized_value_json)
    label = candidate.raw_value
    if isinstance(normalized_value, dict):
        display_name = str(normalized_value.get("display_name") or "").strip()
        field_code = str(normalized_value.get("field_code") or "").strip()
        if display_name and field_code:
            label = f"{display_name} ({field_code})"
        elif display_name:
            label = display_name
        elif field_code:
            label = field_code
    return {
        "candidate_id": candidate.id,
        "rank": candidate.candidate_rank,
        "label": label,
        "normalized_value": normalized_value,
    }


def build_field_candidates(
    repository: SqliteFieldRegistryRepository,
    *,
    provider_user_id: str,
    target_type_code: str,
    raw_input_text: str,
) -> list[dict]:
    participant = repository.find_active_participant_context(provider_user_id=provider_user_id)
    if participant is None:
        return []

    active_bindings = repository.list_active_bindings_for_participant(
        participant_id=participant.participant_id,
        project_id=participant.project_id,
    )
    records: dict[str, tuple[ParticipantFieldBindingRecord | None, object]] = {}
    for binding in active_bindings:
        records[binding.field.id] = (binding, binding.field)

    version = repository.latest_published_version(project_id=participant.project_id)
    if version is not None:
        for record in repository.list_fields_for_version(version.id):
            records.setdefault(record.field.id, (None, record.field))

    query = _normalize(raw_input_text)
    candidates: list[tuple[int, str, str, str, bool]] = []
    for field_id, (binding, field) in records.items():
        code = str(field.field_code).strip()
        name = str(field.display_name).strip()
        score = _field_match_score(
            query=query,
            target_type_code=target_type_code,
            field_code=code,
            field_name=name,
        )
        if score <= 0:
            continue
        if binding is not None:
            score += 25
        candidates.append((score, field_id, code, name, binding is not None))

    candidates.sort(key=lambda item: (-item[0], item[2], item[3]))
    payloads: list[dict] = []
    for score, field_id, code, name, is_bound in candidates[:3]:
        payloads.append(
            {
                "candidate_type_code": target_type_code,
                "raw_value": f"{name} ({code})",
                "normalized_value": {
                    "field_id": field_id,
                    "field_code": code,
                    "display_name": name,
                    "binding_scope": "active_binding" if is_bound else "project_registry",
                },
                "confidence_score": round(min(score / 500, 0.99), 2),
            }
        )
    return payloads


def reminder_due_at(*, now: datetime | None = None) -> datetime:
    current = now or datetime.now(UTC)
    return current + timedelta(days=1)


def new_resume_token() -> str:
    return f"rt_{uuid4().hex}"


def reminder_message(catalog, *, token: str) -> str:
    return catalog.format_input_resolve_reminder(command_text=f"/start {token}")


def reminder_created_text(catalog, *, token: str) -> str:
    return catalog.format_input_resolve_reminder_created(command_text=f"/start {token}")


def resolved_text(catalog, *, target_type_code: str, candidate_label: str) -> str:
    return catalog.format_input_resolve_resolved(
        target_label=target_label(target_type_code, catalog),
        candidate_label=candidate_label,
    )


def manual_review_text(catalog) -> str:
    return catalog.INPUT_RESOLVE_MANUAL_REVIEW_MESSAGE


def resume_prompt_text(catalog, session: InputResolutionSession, draft: InputResolveDraft | None) -> str:
    return catalog.format_input_resolve_resumed(
        step_label=step_label(session.current_step_code, catalog),
        prompt_text=prompt_for_state(session.current_step_code, catalog, draft),
    )


def step_label(state: str, catalog) -> str:
    mapping = {
        STATE_INPUT_RESOLVE_TARGET: catalog.INPUT_RESOLVE_STEP_TARGET_LABEL,
        STATE_INPUT_RESOLVE_METHOD: catalog.INPUT_RESOLVE_STEP_METHOD_LABEL,
        STATE_INPUT_RESOLVE_RAW_INPUT: catalog.INPUT_RESOLVE_STEP_RAW_INPUT_LABEL,
        STATE_INPUT_RESOLVE_CANDIDATES: catalog.INPUT_RESOLVE_STEP_CANDIDATES_LABEL,
        STATE_INPUT_RESOLVE_DECISION: catalog.INPUT_RESOLVE_STEP_DECISION_LABEL,
    }
    return mapping.get(state, catalog.BUTTON_INPUT_RESOLVE)


def _field_match_score(*, query: str, target_type_code: str, field_code: str, field_name: str) -> int:
    code = _normalize(field_code)
    name = _normalize(field_name)
    if not query:
        return 0

    candidates: list[int] = []
    if target_type_code == TARGET_FIELD_CODE:
        candidates.extend(_match_scores(query, code))
    elif target_type_code == TARGET_FIELD_NAME:
        candidates.extend(_match_scores(query, name))
    else:
        candidates.extend(_match_scores(query, code))
        candidates.extend(_match_scores(query, name))

    cross_scores = _match_scores(query, name if target_type_code == TARGET_FIELD_CODE else code)
    if cross_scores:
        candidates.append(max(cross_scores) - 30)
    return max(candidates, default=0)


def _match_scores(query: str, target: str) -> list[int]:
    scores: list[int] = []
    if query == target:
        scores.append(420)
    if target.startswith(query):
        scores.append(320)
    if query in target:
        scores.append(240)
    query_tokens = tuple(token for token in re.split(r"[\s()_-]+", query) if token)
    target_tokens = tuple(token for token in re.split(r"[\s()_-]+", target) if token)
    overlap = len(set(query_tokens) & set(target_tokens))
    if overlap:
        scores.append(120 + overlap * 20)
    return scores


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())
