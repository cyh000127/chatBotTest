from PROJECT.adapters.outbound.reply_sender import send_text
from PROJECT.conversations.onboarding import service as onboarding_service
from PROJECT.conversations.onboarding.states import (
    STATE_ONBOARDING_CONFIRM,
    STATE_ONBOARDING_NAME,
    STATE_ONBOARDING_PENDING_APPROVAL,
    STATE_ONBOARDING_PHONE,
)
from PROJECT.dispatch.session_dispatcher import (
    current_onboarding_session_id,
    current_locale,
    current_state,
    onboarding_draft,
    set_locale,
    set_onboarding_progress,
    set_state,
)
from PROJECT.i18n.translator import get_catalog
from PROJECT.telemetry.event_logger import log_event
from PROJECT.telemetry.events import ONBOARDING_SUBMITTED


def onboarding_repository(context):
    return getattr(context, "bot_data", {}).get("onboarding_repository")


def sync_onboarding_session(context, onboarding_session) -> dict:
    draft = onboarding_service.draft_from_json(onboarding_session.draft_payload_json).to_dict()
    set_onboarding_progress(
        context.user_data,
        status=onboarding_session.session_status_code,
        step=onboarding_session.current_step_code,
        draft=draft,
    )
    set_state(context.user_data, onboarding_session.current_step_code)
    return draft


def current_onboarding_draft(context) -> onboarding_service.OnboardingDraft:
    return onboarding_service.draft_from_dict(onboarding_draft(context.user_data))


async def send_onboarding_prompt(update, context, *, text: str | None = None) -> None:
    catalog = get_catalog(current_locale(context.user_data))
    state = current_state(context.user_data)
    draft = onboarding_service.draft_from_dict(onboarding_draft(context.user_data))
    await send_text(
        update,
        text or onboarding_service.prompt_for_state(state, catalog, draft),
        keyboard_layout=onboarding_service.keyboard_for_state(state, catalog),
    )


async def handle_onboarding_language_selection(update, context, locale: str) -> bool:
    repository = onboarding_repository(context)
    onboarding_session_id = current_onboarding_session_id(context.user_data)
    if repository is None or onboarding_session_id is None:
        return False

    set_locale(context.user_data, locale)
    updated = repository.update_locale(onboarding_session_id, locale)
    sync_onboarding_session(context, updated)
    await send_onboarding_prompt(update, context)
    return True


async def handle_onboarding_text(update, context, *, state: str, text: str, intent: str) -> bool:
    repository = onboarding_repository(context)
    onboarding_session_id = current_onboarding_session_id(context.user_data)
    if repository is None or onboarding_session_id is None:
        return False

    catalog = get_catalog(current_locale(context.user_data))
    if state == STATE_ONBOARDING_NAME:
        name = onboarding_service.parse_name(text)
        if name is None:
            await send_onboarding_prompt(update, context, text=catalog.ONBOARDING_NAME_FALLBACK)
            return True
        updated = repository.update_name(onboarding_session_id, name)
        sync_onboarding_session(context, updated)
        await send_onboarding_prompt(update, context)
        return True

    if state == STATE_ONBOARDING_PHONE:
        phone = onboarding_service.normalize_phone(text)
        if phone is None:
            await send_onboarding_prompt(update, context, text=catalog.ONBOARDING_PHONE_FALLBACK)
            return True
        updated = repository.update_phone(
            onboarding_session_id,
            phone_raw=text.strip(),
            phone_normalized=phone,
        )
        sync_onboarding_session(context, updated)
        await send_onboarding_prompt(update, context)
        return True

    if state == STATE_ONBOARDING_CONFIRM:
        if intent == "confirm":
            await submit_onboarding_for_approval(update, context)
            return True
        await send_onboarding_prompt(update, context, text=catalog.ONBOARDING_CONFIRM_FALLBACK)
        return True

    if state == STATE_ONBOARDING_PENDING_APPROVAL:
        await send_onboarding_prompt(update, context)
        return True

    return False


async def handle_onboarding_callback(update, context, *, action: str, payload: dict) -> bool:
    repository = onboarding_repository(context)
    onboarding_session_id = current_onboarding_session_id(context.user_data)
    if repository is None or onboarding_session_id is None:
        return False

    if action == "onboarding_confirm":
        if current_state(context.user_data) != STATE_ONBOARDING_CONFIRM:
            await send_onboarding_prompt(update, context)
            return True
        await submit_onboarding_for_approval(update, context)
        return True

    if action == "onboarding_edit":
        target = payload.get("target")
        target_step = STATE_ONBOARDING_NAME if target == "name" else STATE_ONBOARDING_PHONE
        updated = repository.move_to_step(onboarding_session_id, target_step)
        sync_onboarding_session(context, updated)
        await send_onboarding_prompt(update, context)
        return True

    return False


async def submit_onboarding_for_approval(update, context) -> None:
    repository = onboarding_repository(context)
    onboarding_session_id = current_onboarding_session_id(context.user_data)
    if repository is None or onboarding_session_id is None:
        return

    draft = current_onboarding_draft(context)
    if not onboarding_service.draft_ready_for_submission(draft):
        target_step = STATE_ONBOARDING_PHONE if draft.name else STATE_ONBOARDING_NAME
        updated = repository.move_to_step(onboarding_session_id, target_step)
        sync_onboarding_session(context, updated)
        await send_onboarding_prompt(update, context)
        return

    updated = repository.submit_pending_approval(onboarding_session_id)
    sync_onboarding_session(context, updated)
    log_event(ONBOARDING_SUBMITTED, onboarding_session_id=updated.id)
    await send_onboarding_prompt(update, context)
