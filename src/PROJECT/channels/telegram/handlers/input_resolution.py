from __future__ import annotations

from datetime import UTC

from PROJECT.adapters.outbound.reply_sender import send_text
from PROJECT.conversations.input_resolve import service as input_resolve_service
from PROJECT.conversations.input_resolve.states import (
    STATE_INPUT_RESOLVE_CANDIDATES,
    STATE_INPUT_RESOLVE_DECISION,
    STATE_INPUT_RESOLVE_METHOD,
    STATE_INPUT_RESOLVE_RAW_INPUT,
    STATE_INPUT_RESOLVE_TARGET,
)
from PROJECT.conversations.sample_menu.keyboards import keyboard_layout_for_state
from PROJECT.conversations.sample_menu.states import STATE_MAIN_MENU
from PROJECT.dispatch.session_dispatcher import (
    clear_input_resolution_draft,
    current_locale,
    current_state,
    input_resolution_draft,
    mark_started,
    reset_recovery_attempts,
    reset_session,
    set_input_resolution_draft,
    set_state,
)
from PROJECT.dispatch.support_handoff_dispatcher import admin_runtime_for_context, create_support_handoff_request
from PROJECT.i18n.translator import get_catalog
from PROJECT.storage.fields import SqliteFieldRegistryRepository
from PROJECT.storage.input_resolution import (
    InputResolutionSession,
    SqliteInputResolutionRepository,
)
from PROJECT.storage.reminders import SqliteReminderRepository
from PROJECT.telemetry.event_logger import log_event
from PROJECT.telemetry.events import (
    INPUT_RESOLUTION_CANDIDATES_CREATED,
    INPUT_RESOLUTION_MANUAL_REVIEW_REQUESTED,
    INPUT_RESOLUTION_RESOLVED,
    INPUT_RESOLUTION_RESUMED,
    INPUT_RESOLUTION_SESSION_STARTED,
    REMINDER_RESUMED,
    REMINDER_SCHEDULED,
)


def _catalog(context):
    return get_catalog(current_locale(context.user_data))


def _resolution_repository(context) -> SqliteInputResolutionRepository | None:
    return getattr(context, "bot_data", {}).get("input_resolution_repository")


def _field_repository(context) -> SqliteFieldRegistryRepository | None:
    return getattr(context, "bot_data", {}).get("field_registry_repository")


def _reminder_repository(context) -> SqliteReminderRepository | None:
    return getattr(context, "bot_data", {}).get("reminder_repository")


def _current_draft(context) -> input_resolve_service.InputResolveDraft | None:
    return input_resolve_service.draft_from_dict(input_resolution_draft(context.user_data))


def _sync_draft(
    context,
    session: InputResolutionSession,
) -> input_resolve_service.InputResolveDraft:
    repository = _resolution_repository(context)
    if repository is None:
        raise RuntimeError("input resolution repository가 없습니다.")
    candidates = tuple(
        input_resolve_service.candidate_payload(candidate)
        for candidate in repository.latest_candidates(session.id)
    )
    selected_label = ""
    if session.selected_candidate_id:
        selected_candidate = repository.candidate_by_id(session.selected_candidate_id)
        if selected_candidate is not None:
            selected_label = input_resolve_service.candidate_payload(selected_candidate)["label"]
    draft = input_resolve_service.InputResolveDraft(
        session_id=session.id,
        target_type_code=session.target_type_code or "",
        method_code=session.method_code or "",
        raw_input_text=session.raw_input_text or "",
        selected_candidate_id=session.selected_candidate_id,
        selected_candidate_label=selected_label,
        latest_candidates=candidates,
    )
    set_input_resolution_draft(context.user_data, draft.to_dict())
    return draft


def _participant_context(context, *, provider_user_id: str):
    field_repository = _field_repository(context)
    if field_repository is None:
        return None
    return field_repository.find_active_participant_context(provider_user_id=provider_user_id)


async def start_input_resolution_session(update, context) -> bool:
    repository = _resolution_repository(context)
    effective_user = update.effective_user
    effective_chat = update.effective_chat
    if repository is None or effective_user is None or effective_chat is None:
        return False

    participant = _participant_context(context, provider_user_id=str(effective_user.id))
    if participant is None:
        await send_text(update, _catalog(context).ONBOARDING_ACCESS_REQUIRED_MESSAGE)
        return True

    session = repository.create_session(
        project_id=participant.project_id,
        participant_id=participant.participant_id,
        provider_user_id=str(effective_user.id),
        chat_id=effective_chat.id,
    )
    reset_session(context.user_data)
    draft = input_resolve_service.new_draft(session.id)
    set_input_resolution_draft(context.user_data, draft.to_dict())
    set_state(context.user_data, STATE_INPUT_RESOLVE_TARGET)
    reset_recovery_attempts(context.user_data)
    log_event(
        INPUT_RESOLUTION_SESSION_STARTED,
        session_id=session.id,
        participant_id=participant.participant_id,
        project_id=participant.project_id,
    )
    catalog = _catalog(context)
    await send_text(
        update,
        f"{catalog.INPUT_RESOLVE_ENTRY_MESSAGE}\n\n"
        f"{input_resolve_service.prompt_for_state(STATE_INPUT_RESOLVE_TARGET, catalog, draft)}",
        keyboard_layout=input_resolve_service.keyboard_for_state(STATE_INPUT_RESOLVE_TARGET, catalog, draft),
    )
    return True


async def resume_input_resolution_session(update, context, *, resume_token: str) -> bool:
    reminder_repository = _reminder_repository(context)
    repository = _resolution_repository(context)
    effective_user = update.effective_user
    if reminder_repository is None or repository is None or effective_user is None:
        return False

    reminder = reminder_repository.get_by_resume_token(resume_token, provider_user_id=str(effective_user.id))
    if reminder is None or reminder.resume_target_code != "input_resolve" or not reminder.input_resolution_session_id:
        await send_text(update, _catalog(context).INPUT_RESOLVE_INVALID_RESUME_MESSAGE)
        return True

    session = repository.get_session(reminder.input_resolution_session_id)
    if session is None or session.session_status_code in {"resolved", "manual_review_required"}:
        await send_text(update, _catalog(context).INPUT_RESOLVE_INVALID_RESUME_MESSAGE)
        return True

    reminder_repository.mark_completed(reminder.id)
    reset_session(context.user_data)
    draft = _sync_draft(context, session)
    mark_started(context.user_data)
    set_state(context.user_data, session.current_step_code)
    reset_recovery_attempts(context.user_data)
    log_event(
        REMINDER_RESUMED,
        reminder_id=reminder.id,
        session_id=session.id,
        resume_target_code=reminder.resume_target_code,
    )
    log_event(
        INPUT_RESOLUTION_RESUMED,
        session_id=session.id,
        current_step=session.current_step_code,
        reminder_id=reminder.id,
    )
    catalog = _catalog(context)
    await send_text(
        update,
        input_resolve_service.resume_prompt_text(catalog, session, draft),
        keyboard_layout=input_resolve_service.keyboard_for_state(session.current_step_code, catalog, draft),
    )
    return True


async def handle_input_resolution_text(update, context, *, state: str, text: str) -> bool:
    repository = _resolution_repository(context)
    field_repository = _field_repository(context)
    effective_user = update.effective_user
    draft = _current_draft(context)
    catalog = _catalog(context)
    if repository is None or field_repository is None or effective_user is None or draft is None:
        return False

    if state == STATE_INPUT_RESOLVE_TARGET:
        target_type_code = input_resolve_service.parse_target_choice(text, catalog)
        if target_type_code is None:
            await send_text(
                update,
                catalog.INPUT_RESOLVE_TARGET_FALLBACK,
                keyboard_layout=input_resolve_service.keyboard_for_state(state, catalog, draft),
            )
            return True
        session = repository.update_target(draft.session_id, target_type_code)
        draft = input_resolve_service.update_draft(draft, target_type_code=target_type_code)
        set_input_resolution_draft(context.user_data, draft.to_dict())
        set_state(context.user_data, STATE_INPUT_RESOLVE_METHOD, push_history=True)
        await send_text(
            update,
            input_resolve_service.prompt_for_state(STATE_INPUT_RESOLVE_METHOD, catalog, draft),
            keyboard_layout=input_resolve_service.keyboard_for_state(STATE_INPUT_RESOLVE_METHOD, catalog, draft),
        )
        return True

    if state == STATE_INPUT_RESOLVE_METHOD:
        method_code = input_resolve_service.parse_method_choice(text, catalog)
        if method_code is None:
            await send_text(
                update,
                catalog.INPUT_RESOLVE_METHOD_FALLBACK,
                keyboard_layout=input_resolve_service.keyboard_for_state(state, catalog, draft),
            )
            return True
        repository.update_method(draft.session_id, method_code)
        draft = input_resolve_service.update_draft(draft, method_code=method_code)
        set_input_resolution_draft(context.user_data, draft.to_dict())
        set_state(context.user_data, STATE_INPUT_RESOLVE_RAW_INPUT, push_history=True)
        await send_text(
            update,
            input_resolve_service.prompt_for_state(STATE_INPUT_RESOLVE_RAW_INPUT, catalog, draft),
            keyboard_layout=input_resolve_service.keyboard_for_state(STATE_INPUT_RESOLVE_RAW_INPUT, catalog, draft),
        )
        return True

    if state == STATE_INPUT_RESOLVE_RAW_INPUT:
        raw_input_text = text.strip()
        if not raw_input_text:
            await send_text(
                update,
                catalog.INPUT_RESOLVE_RAW_INPUT_FALLBACK,
                keyboard_layout=input_resolve_service.keyboard_for_state(state, catalog, draft),
            )
            return True
        attempt = repository.create_attempt(
            session_id=draft.session_id,
            method_code=draft.method_code or input_resolve_service.METHOD_TYPED_TEXT,
            raw_input_text=raw_input_text,
        )
        candidate_rows = input_resolve_service.build_field_candidates(
            field_repository,
            provider_user_id=str(effective_user.id),
            target_type_code=draft.target_type_code,
            raw_input_text=raw_input_text,
        )
        created_candidates = repository.create_candidates(
            session_id=draft.session_id,
            attempt_id=attempt.id,
            candidates=candidate_rows,
        )
        draft = _sync_draft(context, repository.get_session(draft.session_id) or repository.get_session(attempt.input_resolution_session_id))
        draft = input_resolve_service.update_draft(draft, raw_input_text=raw_input_text)
        set_input_resolution_draft(context.user_data, draft.to_dict())
        set_state(context.user_data, STATE_INPUT_RESOLVE_CANDIDATES, push_history=True)
        log_event(
            INPUT_RESOLUTION_CANDIDATES_CREATED,
            session_id=draft.session_id,
            candidate_count=len(created_candidates),
            target_type_code=draft.target_type_code,
        )
        prompt = input_resolve_service.prompt_for_state(STATE_INPUT_RESOLVE_CANDIDATES, catalog, draft)
        keyboard = input_resolve_service.keyboard_for_state(STATE_INPUT_RESOLVE_CANDIDATES, catalog, draft)
        await send_text(update, prompt, keyboard_layout=keyboard)
        return True

    if state == STATE_INPUT_RESOLVE_CANDIDATES:
        candidate_id = input_resolve_service.parse_candidate_choice(text, draft)
        if candidate_id is not None:
            return await _select_candidate(update, context, draft.session_id, candidate_id)
        decision_code = input_resolve_service.parse_decision_choice(text)
        if decision_code == input_resolve_service.DECISION_RETRY:
            return await _retry_input(update, context, draft.session_id)
        if decision_code == input_resolve_service.DECISION_RETRY_LATER:
            return await _schedule_retry_later(update, context, draft.session_id)
        if decision_code == input_resolve_service.DECISION_MANUAL_REVIEW:
            return await _request_manual_review(update, context, draft.session_id)
        await send_text(
            update,
            input_resolve_service.prompt_for_state(STATE_INPUT_RESOLVE_CANDIDATES, catalog, draft),
            keyboard_layout=input_resolve_service.keyboard_for_state(STATE_INPUT_RESOLVE_CANDIDATES, catalog, draft),
        )
        return True

    if state == STATE_INPUT_RESOLVE_DECISION:
        decision_code = input_resolve_service.parse_decision_choice(text)
        if decision_code == input_resolve_service.DECISION_RESOLVED:
            return await _confirm_resolution(update, context, draft.session_id)
        if decision_code == input_resolve_service.DECISION_RETRY:
            return await _retry_input(update, context, draft.session_id)
        if decision_code == input_resolve_service.DECISION_RETRY_LATER:
            return await _schedule_retry_later(update, context, draft.session_id)
        if decision_code == input_resolve_service.DECISION_MANUAL_REVIEW:
            return await _request_manual_review(update, context, draft.session_id)
        await send_text(
            update,
            input_resolve_service.prompt_for_state(STATE_INPUT_RESOLVE_DECISION, catalog, draft),
            keyboard_layout=input_resolve_service.keyboard_for_state(STATE_INPUT_RESOLVE_DECISION, catalog, draft),
        )
        return True

    return False


async def handle_input_resolution_callback(update, context, *, action: str, payload: dict) -> bool:
    draft = _current_draft(context)
    if draft is None:
        return False
    repository = _resolution_repository(context)
    catalog = _catalog(context)

    if action == "inputresolve_target":
        if repository is None:
            return False
        repository.update_target(draft.session_id, payload["target"])
        draft = input_resolve_service.update_draft(draft, target_type_code=payload["target"])
        set_input_resolution_draft(context.user_data, draft.to_dict())
        set_state(context.user_data, STATE_INPUT_RESOLVE_METHOD, push_history=True)
        await send_text(
            update,
            input_resolve_service.prompt_for_state(STATE_INPUT_RESOLVE_METHOD, catalog, draft),
            keyboard_layout=input_resolve_service.keyboard_for_state(STATE_INPUT_RESOLVE_METHOD, catalog, draft),
        )
        return True

    if action == "inputresolve_method":
        if repository is None:
            return False
        repository.update_method(draft.session_id, payload["method"])
        draft = input_resolve_service.update_draft(draft, method_code=payload["method"])
        set_input_resolution_draft(context.user_data, draft.to_dict())
        set_state(context.user_data, STATE_INPUT_RESOLVE_RAW_INPUT, push_history=True)
        await send_text(
            update,
            input_resolve_service.prompt_for_state(STATE_INPUT_RESOLVE_RAW_INPUT, catalog, draft),
            keyboard_layout=input_resolve_service.keyboard_for_state(STATE_INPUT_RESOLVE_RAW_INPUT, catalog, draft),
        )
        return True

    if action == "inputresolve_candidate":
        return await _select_candidate(update, context, draft.session_id, payload["candidate_id"])

    if action == "inputresolve_retry":
        return await _retry_input(update, context, draft.session_id)

    if action == "inputresolve_retry_later":
        return await _schedule_retry_later(update, context, draft.session_id)

    if action == "inputresolve_manual_review":
        return await _request_manual_review(update, context, draft.session_id)

    if action == "inputresolve_decision":
        decision_code = payload["decision"]
        if decision_code == input_resolve_service.DECISION_RESOLVED:
            return await _confirm_resolution(update, context, draft.session_id)
        if decision_code == input_resolve_service.DECISION_RETRY:
            return await _retry_input(update, context, draft.session_id)
        if decision_code == input_resolve_service.DECISION_RETRY_LATER:
            return await _schedule_retry_later(update, context, draft.session_id)
        if decision_code == input_resolve_service.DECISION_MANUAL_REVIEW:
            return await _request_manual_review(update, context, draft.session_id)

    return False


async def _select_candidate(update, context, session_id: str, candidate_id: str) -> bool:
    repository = _resolution_repository(context)
    if repository is None:
        return False
    session = repository.mark_candidate_selected(session_id, candidate_id)
    draft = _sync_draft(context, session)
    set_state(context.user_data, STATE_INPUT_RESOLVE_DECISION, push_history=True)
    catalog = _catalog(context)
    await send_text(
        update,
        input_resolve_service.prompt_for_state(STATE_INPUT_RESOLVE_DECISION, catalog, draft),
        keyboard_layout=input_resolve_service.keyboard_for_state(STATE_INPUT_RESOLVE_DECISION, catalog, draft),
    )
    return True


async def _confirm_resolution(update, context, session_id: str) -> bool:
    repository = _resolution_repository(context)
    draft = _current_draft(context)
    if repository is None or draft is None or not draft.selected_candidate_id:
        return False
    selected_candidate = repository.candidate_by_id(draft.selected_candidate_id)
    if selected_candidate is None:
        return False
    repository.mark_resolved(
        session_id,
        selected_candidate_id=selected_candidate.id,
        resolved_value=selected_candidate.normalized_value,
    )
    log_event(
        INPUT_RESOLUTION_RESOLVED,
        session_id=session_id,
        candidate_id=selected_candidate.id,
        target_type_code=draft.target_type_code,
    )
    clear_input_resolution_draft(context.user_data)
    set_state(context.user_data, STATE_MAIN_MENU)
    catalog = _catalog(context)
    await send_text(
        update,
        input_resolve_service.resolved_text(
            catalog,
            target_type_code=draft.target_type_code,
            candidate_label=input_resolve_service.candidate_payload(selected_candidate)["label"],
        ),
        keyboard_layout=keyboard_layout_for_state(current_state(context.user_data), catalog, None),
    )
    return True


async def _retry_input(update, context, session_id: str) -> bool:
    repository = _resolution_repository(context)
    if repository is None:
        return False
    session = repository.mark_retry(session_id, note="user_requested_retry")
    draft = _sync_draft(context, session)
    draft = input_resolve_service.update_draft(
        draft,
        selected_candidate_id=None,
        selected_candidate_label="",
        latest_candidates=(),
    )
    set_input_resolution_draft(context.user_data, draft.to_dict())
    set_state(context.user_data, STATE_INPUT_RESOLVE_RAW_INPUT)
    catalog = _catalog(context)
    await send_text(
        update,
        input_resolve_service.prompt_for_state(STATE_INPUT_RESOLVE_RAW_INPUT, catalog, draft),
        keyboard_layout=input_resolve_service.keyboard_for_state(STATE_INPUT_RESOLVE_RAW_INPUT, catalog, draft),
    )
    return True


async def _schedule_retry_later(update, context, session_id: str) -> bool:
    repository = _resolution_repository(context)
    reminder_repository = _reminder_repository(context)
    effective_user = update.effective_user
    effective_chat = update.effective_chat
    if repository is None or reminder_repository is None or effective_user is None or effective_chat is None:
        return False
    session = repository.mark_retry_later(session_id, note="user_requested_retry_later")
    token = input_resolve_service.new_resume_token()
    reminder = reminder_repository.create_reminder(
        project_id=session.project_id,
        participant_id=session.participant_id,
        provider_user_id=str(effective_user.id),
        chat_id=effective_chat.id,
        resume_target_code="input_resolve",
        reminder_type_code="input_resolution_retry_later",
        due_at=input_resolve_service.reminder_due_at().isoformat(),
        message_text=input_resolve_service.reminder_message(_catalog(context), token=token),
        input_resolution_session_id=session.id,
        resume_token=token,
    )
    log_event(
        REMINDER_SCHEDULED,
        reminder_id=reminder.id,
        session_id=session.id,
        resume_token=token,
        resume_target_code=reminder.resume_target_code,
    )
    clear_input_resolution_draft(context.user_data)
    set_state(context.user_data, STATE_MAIN_MENU)
    catalog = _catalog(context)
    await send_text(
        update,
        input_resolve_service.reminder_created_text(catalog, token=token),
        keyboard_layout=keyboard_layout_for_state(current_state(context.user_data), catalog, None),
    )
    return True


async def _request_manual_review(update, context, session_id: str) -> bool:
    repository = _resolution_repository(context)
    effective_user = update.effective_user
    effective_chat = update.effective_chat
    draft = _current_draft(context)
    if repository is None or effective_user is None or effective_chat is None or draft is None:
        return False
    session = repository.mark_manual_review(session_id, note="user_requested_manual_review")
    summary = (
        f"input_resolve target={draft.target_type_code or '-'} "
        f"raw={draft.raw_input_text or '-'} "
        f"candidates={len(draft.latest_candidates)}"
    )
    create_support_handoff_request(
        context.user_data,
        route_hint="admin_follow_up_queue",
        reason="input_resolution_manual_review",
        current_step=session.current_step_code,
        chat_id=effective_chat.id,
        user_id=effective_user.id,
        locale=current_locale(context.user_data),
        user_message=summary,
        failure_count=repository.count_attempts(session.id),
        recent_messages_summary=summary,
        source="input_resolution_manual_review",
        runtime=admin_runtime_for_context(context),
    )
    log_event(
        INPUT_RESOLUTION_MANUAL_REVIEW_REQUESTED,
        session_id=session.id,
        target_type_code=draft.target_type_code,
        candidate_count=len(draft.latest_candidates),
    )
    clear_input_resolution_draft(context.user_data)
    set_state(context.user_data, STATE_MAIN_MENU)
    catalog = _catalog(context)
    await send_text(
        update,
        input_resolve_service.manual_review_text(catalog),
        keyboard_layout=keyboard_layout_for_state(current_state(context.user_data), catalog, None),
    )
    return True
