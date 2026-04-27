from __future__ import annotations

from PROJECT.adapters.outbound.reply_sender import send_text
from PROJECT.conversations.field_binding import keyboards, service as field_binding_view
from PROJECT.conversations.field_binding.states import (
    STATE_FIELD_BINDING_CANDIDATE_SELECT,
    STATE_FIELD_BINDING_CODE,
    STATE_FIELD_BINDING_CONFIRM,
    STATE_FIELD_BINDING_LOCATION,
    STATE_FIELD_BINDING_METHOD,
    STATE_MYFIELDS_SUMMARY,
)
from PROJECT.dispatch.session_dispatcher import (
    clear_field_binding_draft,
    current_locale,
    current_onboarding_session_id,
    current_state,
    field_binding_draft,
    set_field_binding_draft,
    set_state,
)
from PROJECT.fields.binding import FIELD_CODE_BINDING_SOURCE, LOCATION_BINDING_SOURCE, FieldBindingService
from PROJECT.i18n.translator import get_catalog


def _catalog(context):
    return get_catalog(current_locale(context.user_data))


def _binding_service(context) -> FieldBindingService | None:
    return getattr(context, "bot_data", {}).get("field_binding_service")


def _draft(context) -> dict:
    return dict(field_binding_draft(context.user_data) or {})


def _candidate_payloads(candidates) -> tuple[dict, ...]:
    return tuple(
        {
            "field_id": candidate.field_id,
            "field_code": candidate.field_code,
            "display_name": candidate.display_name,
            "field_registry_version_id": candidate.field_registry_version_id,
        }
        for candidate in candidates
    )


def _selected_candidate(draft: dict) -> dict | None:
    selected_field_id = draft.get("selected_field_id")
    if not selected_field_id:
        return None
    for candidate in draft.get("candidates") or ():
        if candidate.get("field_id") == selected_field_id:
            return candidate
    return None


async def show_myfields_summary(update, context, *, prefix: str | None = None) -> None:
    catalog = _catalog(context)
    binding_service = _binding_service(context)
    if binding_service is None or update.effective_user is None:
        set_state(context.user_data, STATE_MYFIELDS_SUMMARY)
        set_field_binding_draft(context.user_data, {"has_bindings": False})
        await send_text(
            update,
            prefix or getattr(catalog, "MYFIELDS_EMPTY_MESSAGE", "등록된 농지가 없습니다."),
            keyboard_layout=keyboards.keyboard_for_state(STATE_MYFIELDS_SUMMARY, catalog, has_bindings=False),
        )
        return

    participant, bindings = binding_service.list_myfields(provider_user_id=str(update.effective_user.id))
    set_state(context.user_data, STATE_MYFIELDS_SUMMARY)
    set_field_binding_draft(context.user_data, {"has_bindings": bool(bindings)})
    participant_name = participant.participant_name if participant is not None else ""
    summary = field_binding_view.summary_text(
        participant_name=participant_name,
        bindings=bindings,
        catalog=catalog,
    )
    text = f"{prefix}\n\n{summary}" if prefix else summary
    await send_text(
        update,
        text,
        keyboard_layout=keyboards.keyboard_for_state(STATE_MYFIELDS_SUMMARY, catalog, has_bindings=bool(bindings)),
    )


async def open_binding_method(update, context) -> None:
    catalog = _catalog(context)
    draft = _draft(context)
    draft["lookup_method"] = None
    draft["candidates"] = ()
    draft["selected_field_id"] = None
    set_field_binding_draft(context.user_data, draft)
    set_state(context.user_data, STATE_FIELD_BINDING_METHOD, push_history=True)
    await send_text(
        update,
        field_binding_view.method_text(catalog),
        keyboard_layout=keyboards.keyboard_for_state(STATE_FIELD_BINDING_METHOD, catalog),
    )


async def choose_binding_method(update, context, *, method: str) -> None:
    catalog = _catalog(context)
    draft = _draft(context)
    draft["lookup_method"] = method
    draft["candidates"] = ()
    draft["selected_field_id"] = None
    set_field_binding_draft(context.user_data, draft)
    if method == LOCATION_BINDING_SOURCE:
        set_state(context.user_data, STATE_FIELD_BINDING_LOCATION, push_history=True)
        await send_text(
            update,
            field_binding_view.location_prompt_text(catalog),
            keyboard_layout=keyboards.keyboard_for_state(STATE_FIELD_BINDING_LOCATION, catalog),
        )
        return
    set_state(context.user_data, STATE_FIELD_BINDING_CODE, push_history=True)
    await send_text(
        update,
        field_binding_view.code_prompt_text(catalog),
        keyboard_layout=keyboards.keyboard_for_state(STATE_FIELD_BINDING_CODE, catalog),
    )


async def handle_field_code_text(update, context, *, text: str) -> bool:
    if current_state(context.user_data) != STATE_FIELD_BINDING_CODE:
        return False
    binding_service = _binding_service(context)
    if binding_service is None or update.effective_user is None:
        return False
    normalized_code = text.strip().upper()
    result = binding_service.lookup_field_code(
        provider_user_id=str(update.effective_user.id),
        field_code=normalized_code,
        onboarding_session_id=current_onboarding_session_id(context.user_data),
        chat_id=update.effective_chat.id if update.effective_chat else None,
    )
    catalog = _catalog(context)
    draft = _draft(context)
    draft["lookup_method"] = FIELD_CODE_BINDING_SOURCE
    draft["requested_field_code"] = normalized_code
    if result.version_id is None:
        await show_myfields_summary(update, context, prefix=field_binding_view.no_registry_text(catalog))
        return True
    if not result.candidates:
        if result.exception is not None:
            draft["exception_id"] = result.exception.id
        set_field_binding_draft(context.user_data, draft)
        await send_text(
            update,
            field_binding_view.field_code_not_found_text(catalog),
            keyboard_layout=keyboards.keyboard_for_state(STATE_FIELD_BINDING_CODE, catalog),
        )
        return True
    candidate = _candidate_payloads(result.candidates)[0]
    draft["version_id"] = result.version_id
    draft["candidates"] = (candidate,)
    draft["selected_field_id"] = candidate["field_id"]
    set_field_binding_draft(context.user_data, draft)
    set_state(context.user_data, STATE_FIELD_BINDING_CONFIRM, push_history=True)
    await send_text(
        update,
        field_binding_view.confirm_text(
            field_name=candidate["display_name"],
            field_code=candidate["field_code"],
            lookup_method=FIELD_CODE_BINDING_SOURCE,
            catalog=catalog,
        ),
        keyboard_layout=keyboards.keyboard_for_state(STATE_FIELD_BINDING_CONFIRM, catalog),
    )
    return True


async def handle_field_location(update, context) -> bool:
    if current_state(context.user_data) != STATE_FIELD_BINDING_LOCATION:
        return False
    binding_service = _binding_service(context)
    location = getattr(update.effective_message, "location", None)
    if binding_service is None or update.effective_user is None or location is None:
        return False
    result = binding_service.lookup_location(
        provider_user_id=str(update.effective_user.id),
        latitude=float(location.latitude),
        longitude=float(location.longitude),
        accuracy_meters=float(location.horizontal_accuracy) if getattr(location, "horizontal_accuracy", None) is not None else None,
        onboarding_session_id=current_onboarding_session_id(context.user_data),
        chat_id=update.effective_chat.id if update.effective_chat else None,
    )
    catalog = _catalog(context)
    draft = _draft(context)
    draft["lookup_method"] = LOCATION_BINDING_SOURCE
    draft["location_latitude"] = float(location.latitude)
    draft["location_longitude"] = float(location.longitude)
    draft["location_accuracy_meters"] = (
        float(location.horizontal_accuracy) if getattr(location, "horizontal_accuracy", None) is not None else None
    )
    if result.version_id is None:
        await show_myfields_summary(update, context, prefix=field_binding_view.no_registry_text(catalog))
        return True
    draft["version_id"] = result.version_id
    if not result.candidates:
        if result.exception is not None:
            draft["exception_id"] = result.exception.id
        set_field_binding_draft(context.user_data, draft)
        set_state(context.user_data, STATE_FIELD_BINDING_CODE, push_history=True)
        await send_text(
            update,
            field_binding_view.location_no_candidate_text(catalog),
            keyboard_layout=keyboards.keyboard_for_state(STATE_FIELD_BINDING_CODE, catalog),
        )
        return True
    candidates = _candidate_payloads(result.candidates)
    draft["candidates"] = candidates
    if result.exception is not None:
        draft["exception_id"] = result.exception.id
    if len(candidates) == 1:
        draft["selected_field_id"] = candidates[0]["field_id"]
        set_field_binding_draft(context.user_data, draft)
        set_state(context.user_data, STATE_FIELD_BINDING_CONFIRM, push_history=True)
        await send_text(
            update,
            field_binding_view.confirm_text(
                field_name=candidates[0]["display_name"],
                field_code=candidates[0]["field_code"],
                lookup_method=LOCATION_BINDING_SOURCE,
                catalog=catalog,
            ),
            keyboard_layout=keyboards.keyboard_for_state(STATE_FIELD_BINDING_CONFIRM, catalog),
        )
        return True
    draft["selected_field_id"] = None
    set_field_binding_draft(context.user_data, draft)
    set_state(context.user_data, STATE_FIELD_BINDING_CANDIDATE_SELECT, push_history=True)
    await send_text(
        update,
        field_binding_view.candidate_text(candidates=candidates, catalog=catalog),
        keyboard_layout=keyboards.keyboard_for_state(STATE_FIELD_BINDING_CANDIDATE_SELECT, catalog, candidates=candidates),
    )
    return True


async def handle_field_binding_callback(update, context, *, action: str, payload: dict) -> bool:
    catalog = _catalog(context)
    if action == "fieldbind_refresh":
        await show_myfields_summary(update, context)
        return True
    if action == "fieldbind_start":
        await open_binding_method(update, context)
        return True
    if action == "fieldbind_method":
        selected_method = payload["method"]
        if selected_method == "location":
            selected_method = LOCATION_BINDING_SOURCE
        elif selected_method == "code":
            selected_method = FIELD_CODE_BINDING_SOURCE
        await choose_binding_method(update, context, method=selected_method)
        return True
    if action == "fieldbind_candidate":
        draft = _draft(context)
        for candidate in draft.get("candidates") or ():
            if candidate.get("field_id") == payload["field_id"]:
                draft["selected_field_id"] = payload["field_id"]
                set_field_binding_draft(context.user_data, draft)
                set_state(context.user_data, STATE_FIELD_BINDING_CONFIRM, push_history=True)
                await send_text(
                    update,
                    field_binding_view.confirm_text(
                        field_name=candidate["display_name"],
                        field_code=candidate["field_code"],
                        lookup_method=draft.get("lookup_method") or LOCATION_BINDING_SOURCE,
                        catalog=catalog,
                    ),
                    keyboard_layout=keyboards.keyboard_for_state(STATE_FIELD_BINDING_CONFIRM, catalog),
                )
                return True
        return False
    if action != "fieldbind_confirm":
        return False

    draft = _draft(context)
    candidate = _selected_candidate(draft)
    binding_service = _binding_service(context)
    if candidate is None or binding_service is None or update.effective_user is None:
        await show_myfields_summary(update, context)
        return True
    binding, exception = binding_service.confirm_binding(
        provider_user_id=str(update.effective_user.id),
        field_id=candidate["field_id"],
        field_registry_version_id=candidate["field_registry_version_id"],
        binding_source_code=draft.get("lookup_method") or LOCATION_BINDING_SOURCE,
        onboarding_session_id=current_onboarding_session_id(context.user_data),
        chat_id=update.effective_chat.id if update.effective_chat else None,
        location_latitude=draft.get("location_latitude"),
        location_longitude=draft.get("location_longitude"),
        location_accuracy_meters=draft.get("location_accuracy_meters"),
        requested_field_code=draft.get("requested_field_code"),
    )
    if binding is None or exception is not None:
        set_state(context.user_data, STATE_FIELD_BINDING_METHOD)
        await send_text(
            update,
            field_binding_view.conflict_text(catalog),
            keyboard_layout=keyboards.keyboard_for_state(STATE_FIELD_BINDING_METHOD, catalog),
        )
        return True
    exception_id = draft.get("exception_id")
    repository = getattr(context, "bot_data", {}).get("field_registry_repository")
    if repository is not None and exception_id:
        try:
            repository.resolve_binding_exception(exception_id)
        except ValueError:
            pass
    clear_field_binding_draft(context.user_data)
    await show_myfields_summary(
        update,
        context,
        prefix=field_binding_view.binding_confirmed_text(
            field_name=binding.field.display_name,
            field_code=binding.field.field_code,
            catalog=catalog,
        ),
    )
    return True
