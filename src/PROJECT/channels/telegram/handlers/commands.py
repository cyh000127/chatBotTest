from datetime import UTC, datetime

from PROJECT.adapters.outbound.reply_sender import send_text
from PROJECT.conversations.fertilizer_intake import service as fertilizer_service
from PROJECT.conversations.fertilizer_intake import keyboards as fertilizer_keyboards
from PROJECT.conversations.fertilizer_intake.states import STATE_FERTILIZER_CONFIRM, STATE_FERTILIZER_USED
from PROJECT.conversations.input_resolve.states import STATE_INPUT_RESOLVE_TARGET
from PROJECT.conversations.profile_intake import service as profile_service
from PROJECT.conversations.profile_intake.states import STATE_PROFILE_EDIT_SELECT, STATE_PROFILE_NAME
from PROJECT.conversations.yield_intake import service as yield_service
from PROJECT.conversations.yield_intake.states import STATE_YIELD_READY
from PROJECT.conversations.sample_menu import service
from PROJECT.conversations.sample_menu.keyboards import keyboard_layout_for_state
from PROJECT.conversations.sample_menu.states import STATE_LANGUAGE_SELECT, STATE_MAIN_MENU
from PROJECT.dispatch.session_dispatcher import (
    confirmed_fertilizer,
    confirmed_profile,
    cancel_session,
    has_confirmed_fertilizer,
    has_confirmed_profile,
    current_locale,
    current_onboarding_session_id,
    current_onboarding_status,
    current_state,
    has_started,
    mark_started,
    profile_draft,
    reset_session,
    set_fertilizer_draft,
    set_onboarding_session,
    set_onboarding_progress,
    set_pending_slot,
    set_profile_draft,
    set_state,
    set_yield_draft,
)
from PROJECT.dispatch.support_handoff_dispatcher import (
    admin_runtime_for_context,
    close_support_handoff,
    create_support_handoff_request,
    record_support_handoff_admin_reply,
)
from PROJECT.channels.telegram.handlers.onboarding import send_onboarding_prompt, sync_onboarding_session
from PROJECT.i18n.translator import get_catalog, language_keyboard
from PROJECT.storage.invitations import INVITATION_STATUS_ISSUED
from PROJECT.storage.onboarding import ONBOARDING_STATUS_APPROVED
from PROJECT.telemetry.event_logger import log_event
from PROJECT.telemetry.events import ONBOARDING_ACCESS_BLOCKED, ONBOARDING_INVITE_REJECTED, ONBOARDING_STARTED


def catalog_for(context):
    return get_catalog(current_locale(context.user_data))


def _invitation_repository(context):
    return getattr(context, "bot_data", {}).get("invitation_repository")


def _onboarding_repository(context):
    return getattr(context, "bot_data", {}).get("onboarding_repository")


def _sqlite_onboarding_enabled(context) -> bool:
    return _invitation_repository(context) is not None and _onboarding_repository(context) is not None


def _start_invite_code(context) -> str | None:
    args = [arg.strip() for arg in getattr(context, "args", []) if arg.strip()]
    if not args:
        return None
    return args[0]


def _invitation_can_start_onboarding(invitation) -> bool:
    if invitation is None:
        return False
    if invitation.invite_status_code != INVITATION_STATUS_ISSUED:
        return False
    if invitation.expires_at and _is_expired(invitation.expires_at):
        return False
    return True


def _is_expired(expires_at: str) -> bool:
    try:
        parsed = datetime.fromisoformat(expires_at)
    except ValueError:
        return True
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed <= datetime.now(UTC)


def _farmer_feature_access_allowed(update, context) -> bool:
    if not _sqlite_onboarding_enabled(context):
        return has_started(context.user_data)
    if current_onboarding_status(context.user_data) == ONBOARDING_STATUS_APPROVED:
        return True
    effective_user = update.effective_user
    if effective_user is None:
        return False
    approved_session = _onboarding_repository(context).find_active_approved_session_for_provider(str(effective_user.id))
    if approved_session is None:
        return False
    set_onboarding_session(
        context.user_data,
        onboarding_session_id=approved_session.id,
        invite_code="",
        project_id=approved_session.project_id,
        status=approved_session.session_status_code,
        step=approved_session.current_step_code,
    )
    set_onboarding_progress(
        context.user_data,
        status=approved_session.session_status_code,
        step=approved_session.current_step_code,
    )
    return True


def _started_access_allowed(update, context) -> bool:
    if has_started(context.user_data):
        return True
    if current_onboarding_session_id(context.user_data) is not None:
        return True
    if current_onboarding_status(context.user_data) is not None:
        return True
    if _sqlite_onboarding_enabled(context):
        return _farmer_feature_access_allowed(update, context)
    return False


async def _send_onboarding_access_required(update, context) -> None:
    catalog = catalog_for(context)
    status = current_onboarding_status(context.user_data)
    message = (
        catalog.ONBOARDING_PENDING_APPROVAL_MESSAGE
        if status
        else catalog.ONBOARDING_ACCESS_REQUIRED_MESSAGE
    )
    log_event(
        ONBOARDING_ACCESS_BLOCKED,
        state=current_state(context.user_data),
        onboarding_status=status,
    )
    await send_text(
        update,
        message,
        keyboard_layout=[
            [{"text": catalog.BUTTON_SUPPORT, "data": "intent:support.escalate"}],
            [{"text": catalog.BUTTON_RESTART, "data": "intent:restart"}],
            [{"text": catalog.BUTTON_HELP, "data": "intent:help"}],
        ],
    )


async def _send_start_required(update, context) -> None:
    catalog = catalog_for(context)
    await send_text(
        update,
        catalog.START_REQUIRED_MESSAGE,
        keyboard_layout=[
            [{"text": catalog.BUTTON_RESTART, "data": "intent:restart"}],
        ],
    )


async def _require_started_access(update, context) -> bool:
    if _started_access_allowed(update, context):
        return True
    await _send_start_required(update, context)
    return False


async def _require_farmer_feature_access(update, context) -> bool:
    if not _sqlite_onboarding_enabled(context):
        if has_started(context.user_data):
            return True
        await _send_start_required(update, context)
        return False
    if _farmer_feature_access_allowed(update, context):
        return True
    await _send_onboarding_access_required(update, context)
    return False


async def start_profile_input(update, context) -> None:
    catalog = catalog_for(context)
    reset_session(context.user_data)
    set_state(context.user_data, STATE_PROFILE_NAME)
    draft = profile_service.new_draft()
    set_profile_draft(context.user_data, draft.to_dict())
    set_pending_slot(context.user_data, None)
    await send_text(
        update,
        profile_service.prompt_for_state(STATE_PROFILE_NAME, catalog),
        keyboard_layout=profile_service.keyboard_for_state(STATE_PROFILE_NAME, draft, catalog),
    )


async def start_fertilizer_input(update, context) -> None:
    catalog = catalog_for(context)
    reset_session(context.user_data)
    set_state(context.user_data, STATE_FERTILIZER_USED)
    draft = fertilizer_service.new_draft()
    set_fertilizer_draft(context.user_data, draft.to_dict())
    await send_text(
        update,
        fertilizer_service.prompt_for_state(STATE_FERTILIZER_USED, catalog),
        keyboard_layout=fertilizer_service.keyboard_for_state(STATE_FERTILIZER_USED, catalog),
    )


async def start_yield_input(update, context) -> None:
    catalog = catalog_for(context)
    reset_session(context.user_data)
    set_state(context.user_data, STATE_YIELD_READY)
    draft = yield_service.new_draft()
    set_yield_draft(context.user_data, draft.to_dict())
    await send_text(
        update,
        yield_service.prompt_for_state(STATE_YIELD_READY, catalog),
        keyboard_layout=yield_service.keyboard_for_state(STATE_YIELD_READY, catalog),
    )


async def show_myfields_entry(update, context) -> None:
    catalog = catalog_for(context)
    reset_session(context.user_data)
    await send_text(
        update,
        service.myfields_entry_text(catalog),
        keyboard_layout=keyboard_layout_for_state(current_state(context.user_data), catalog, profile_draft(context.user_data)),
    )


async def start_input_resolve_entry(update, context) -> None:
    catalog = catalog_for(context)
    reset_session(context.user_data)
    set_state(context.user_data, STATE_INPUT_RESOLVE_TARGET)
    await send_text(
        update,
        service.input_resolve_entry_text(catalog),
        keyboard_layout=keyboard_layout_for_state(current_state(context.user_data), catalog, profile_draft(context.user_data)),
    )


async def show_support_guidance(
    update,
    context,
    *,
    reason: str = "explicit_support_request",
    route_hint: str = "support.escalate",
    user_message: str = "/support",
    failure_count: int = 0,
    recent_messages_summary: str = "",
    source: str = "support_command",
) -> None:
    catalog = catalog_for(context)
    create_support_handoff_request(
        context.user_data,
        route_hint=route_hint,
        reason=reason,
        current_step=current_state(context.user_data),
        chat_id=update.effective_chat.id if update.effective_chat else None,
        user_id=update.effective_user.id if update.effective_user else None,
        locale=current_locale(context.user_data),
        user_message=user_message,
        failure_count=failure_count,
        recent_messages_summary=recent_messages_summary,
        source=source,
        runtime=admin_runtime_for_context(context),
    )
    await send_text(
        update,
        service.support_escalation_text(catalog),
        keyboard_layout=keyboard_layout_for_state(current_state(context.user_data), catalog, profile_draft(context.user_data)),
    )


async def relay_support_admin_reply(update, context, *, admin_message: str) -> bool:
    catalog = catalog_for(context)
    handoff = record_support_handoff_admin_reply(
        context.user_data,
        admin_message=admin_message,
        source="admin_reply_relay",
    )
    if handoff is None:
        return False
    await send_text(
        update,
        service.support_admin_reply_text(catalog, admin_message),
        keyboard_layout=keyboard_layout_for_state(current_state(context.user_data), catalog, profile_draft(context.user_data)),
    )
    return True


async def close_support_handoff_from_admin(update, context, *, reason: str = "admin_resolved") -> bool:
    catalog = catalog_for(context)
    handoff = close_support_handoff(
        context.user_data,
        reason=reason,
        source="admin_close",
        runtime=admin_runtime_for_context(context),
    )
    if handoff is None:
        return False
    await send_text(
        update,
        catalog.SUPPORT_HANDOFF_CLOSED_MESSAGE,
        keyboard_layout=keyboard_layout_for_state(current_state(context.user_data), catalog, profile_draft(context.user_data)),
    )
    return True


async def show_current_profile(update, context) -> bool:
    catalog = catalog_for(context)
    if not has_confirmed_profile(context.user_data):
        await send_text(
            update,
            profile_service.no_profile_text(catalog),
            keyboard_layout=keyboard_layout_for_state(current_state(context.user_data), catalog, profile_draft(context.user_data)),
        )
        return False

    confirmed = profile_service.draft_from_dict(confirmed_profile(context.user_data))
    reset_session(context.user_data)
    set_profile_draft(context.user_data, confirmed.to_dict())
    await send_text(
        update,
        profile_service.summary_text(confirmed, catalog),
        keyboard_layout=keyboard_layout_for_state(current_state(context.user_data), catalog, profile_draft(context.user_data)),
    )
    return True


async def open_profile_edit_selector(update, context) -> bool:
    catalog = catalog_for(context)
    if not has_confirmed_profile(context.user_data):
        await send_text(
            update,
            profile_service.no_profile_text(catalog),
            keyboard_layout=keyboard_layout_for_state(current_state(context.user_data), catalog, profile_draft(context.user_data)),
        )
        return False

    confirmed = profile_service.draft_from_dict(confirmed_profile(context.user_data))
    reset_session(context.user_data)
    set_profile_draft(context.user_data, confirmed.to_dict())
    set_pending_slot(context.user_data, None)
    set_state(context.user_data, STATE_PROFILE_EDIT_SELECT)
    await send_text(
        update,
        profile_service.edit_selection_text(confirmed, catalog),
        keyboard_layout=profile_service.keyboard_for_state(STATE_PROFILE_EDIT_SELECT, confirmed, catalog),
    )
    return True


async def open_profile_target_edit(update, context, target_state: str) -> bool:
    catalog = catalog_for(context)
    if not has_confirmed_profile(context.user_data):
        await send_text(
            update,
            profile_service.no_profile_text(catalog),
            keyboard_layout=keyboard_layout_for_state(current_state(context.user_data), catalog, profile_draft(context.user_data)),
        )
        return False

    confirmed = profile_service.draft_from_dict(confirmed_profile(context.user_data))
    draft = profile_service.reset_draft_for_repair(confirmed, target_state)
    reset_session(context.user_data)
    set_profile_draft(context.user_data, draft.to_dict())
    set_pending_slot(context.user_data, target_state)
    set_state(context.user_data, target_state)
    await send_text(
        update,
        profile_service.repair_message(target_state, catalog),
        keyboard_layout=profile_service.keyboard_for_state(target_state, draft, catalog),
    )
    return True


async def open_fertilizer_target_edit(update, context, target_state: str) -> bool:
    catalog = catalog_for(context)
    if not has_confirmed_fertilizer(context.user_data):
        await send_text(
            update,
            fertilizer_service.no_fertilizer_text(catalog),
            keyboard_layout=keyboard_layout_for_state(current_state(context.user_data), catalog, profile_draft(context.user_data)),
        )
        return False

    confirmed = fertilizer_service.draft_from_dict(confirmed_fertilizer(context.user_data))
    draft = fertilizer_service.reset_draft_for_repair(confirmed, target_state)
    reset_session(context.user_data)
    set_fertilizer_draft(context.user_data, draft.to_dict())
    set_state(context.user_data, target_state)
    await send_text(
        update,
        fertilizer_service.repair_message(target_state, catalog),
        keyboard_layout=fertilizer_service.keyboard_for_state(target_state, catalog),
    )
    return True


async def open_fertilizer_edit_selector(update, context) -> bool:
    catalog = catalog_for(context)
    if not has_confirmed_fertilizer(context.user_data):
        await send_text(
            update,
            fertilizer_service.no_fertilizer_text(catalog),
            keyboard_layout=keyboard_layout_for_state(current_state(context.user_data), catalog, profile_draft(context.user_data)),
        )
        return False

    confirmed = fertilizer_service.draft_from_dict(confirmed_fertilizer(context.user_data))
    reset_session(context.user_data)
    set_fertilizer_draft(context.user_data, confirmed.to_dict())
    set_state(context.user_data, STATE_FERTILIZER_CONFIRM)
    await send_text(
        update,
        fertilizer_service.edit_selection_text(confirmed, catalog),
        keyboard_layout=fertilizer_keyboards.fertilizer_edit_select_keyboard(catalog),
    )
    return True


async def start_command(update, context) -> None:
    catalog = catalog_for(context)
    close_support_handoff(
        context.user_data,
        reason="user_restart",
        source="start_command",
        runtime=admin_runtime_for_context(context),
    )

    if _sqlite_onboarding_enabled(context):
        invite_code = _start_invite_code(context)
        if not invite_code:
            reset_session(context.user_data)
            set_state(context.user_data, STATE_MAIN_MENU)
            await send_text(
                update,
                catalog.ONBOARDING_INVITE_REQUIRED_MESSAGE,
                keyboard_layout=[
                    [{"text": catalog.BUTTON_SUPPORT, "data": "intent:support.escalate"}],
                    [{"text": catalog.BUTTON_HELP, "data": "intent:help"}],
                ],
            )
            return

        invitation = _invitation_repository(context).get_by_code(invite_code)
        if not _invitation_can_start_onboarding(invitation):
            reset_session(context.user_data)
            set_state(context.user_data, STATE_MAIN_MENU)
            log_event(ONBOARDING_INVITE_REJECTED, reason="invalid_or_inactive_invitation")
            await send_text(
                update,
                catalog.ONBOARDING_INVALID_INVITE_MESSAGE,
                keyboard_layout=[
                    [{"text": catalog.BUTTON_SUPPORT, "data": "intent:support.escalate"}],
                    [{"text": catalog.BUTTON_HELP, "data": "intent:help"}],
                ],
            )
            return

        effective_user = update.effective_user
        if effective_user is None:
            await send_text(update, catalog.ONBOARDING_IDENTITY_REQUIRED_MESSAGE)
            return

        onboarding_session = _onboarding_repository(context).create_or_resume_from_invitation(
            invitation=invitation,
            provider_user_id=str(effective_user.id),
            provider_handle=getattr(effective_user, "username", None),
            preferred_locale_code=current_locale(context.user_data),
            chat_id=update.effective_chat.id if update.effective_chat else None,
        )
        reset_session(context.user_data)
        set_onboarding_session(
            context.user_data,
            onboarding_session_id=onboarding_session.id,
            invite_code=invitation.invite_code,
            project_id=invitation.project_id,
            status=onboarding_session.session_status_code,
            step=onboarding_session.current_step_code,
            draft=sync_onboarding_session(context, onboarding_session),
        )
        mark_started(context.user_data)
        log_event(
            ONBOARDING_STARTED,
            onboarding_session_id=onboarding_session.id,
            invitation_id=invitation.id,
            state=current_state(context.user_data),
        )
        await send_onboarding_prompt(update, context)
        return

    reset_session(context.user_data)
    mark_started(context.user_data)
    set_state(context.user_data, STATE_MAIN_MENU)
    await send_text(
        update,
        service.main_menu_text(catalog),
        keyboard_layout=keyboard_layout_for_state(current_state(context.user_data), catalog, profile_draft(context.user_data)),
    )


async def help_command(update, context) -> None:
    if not await _require_started_access(update, context):
        return
    catalog = catalog_for(context)
    await send_text(
        update,
        service.help_text(catalog),
        keyboard_layout=keyboard_layout_for_state(current_state(context.user_data), catalog, profile_draft(context.user_data)),
    )


async def menu_command(update, context) -> None:
    if not await _require_started_access(update, context):
        return
    catalog = catalog_for(context)
    close_support_handoff(
        context.user_data,
        reason="user_menu_exit",
        source="menu_command",
        runtime=admin_runtime_for_context(context),
    )
    reset_session(context.user_data)
    await send_text(
        update,
        service.main_menu_text(catalog),
        keyboard_layout=keyboard_layout_for_state(current_state(context.user_data), catalog, profile_draft(context.user_data)),
    )


async def cancel_command(update, context) -> None:
    if not await _require_started_access(update, context):
        return
    catalog = catalog_for(context)
    close_support_handoff(
        context.user_data,
        reason="user_cancel",
        source="cancel_command",
        runtime=admin_runtime_for_context(context),
    )
    cancel_session(context.user_data)
    await send_text(
        update,
        service.cancel_text(catalog),
        keyboard_layout=keyboard_layout_for_state(current_state(context.user_data), catalog, profile_draft(context.user_data)),
    )


async def profile_command(update, context) -> None:
    if not await _require_started_access(update, context):
        return
    if not await _require_farmer_feature_access(update, context):
        return
    catalog = catalog_for(context)

    args = [arg.strip().lower() for arg in getattr(context, "args", []) if arg.strip()]
    if args and args[0] == "edit":
        await open_profile_edit_selector(update, context)
        return
    if args and args[0] == "new":
        await start_profile_input(update, context)
        return
    await show_current_profile(update, context)


async def fertilizer_command(update, context) -> None:
    if not await _require_started_access(update, context):
        return
    if not await _require_farmer_feature_access(update, context):
        return
    await start_fertilizer_input(update, context)


async def yield_command(update, context) -> None:
    if not await _require_started_access(update, context):
        return
    if not await _require_farmer_feature_access(update, context):
        return
    await start_yield_input(update, context)


async def myfields_command(update, context) -> None:
    if not await _require_started_access(update, context):
        return
    if not await _require_farmer_feature_access(update, context):
        return
    await show_myfields_entry(update, context)


async def input_resolve_command(update, context) -> None:
    if not await _require_started_access(update, context):
        return
    if not await _require_farmer_feature_access(update, context):
        return
    await start_input_resolve_entry(update, context)


async def support_command(update, context) -> None:
    if not await _require_started_access(update, context):
        return
    await show_support_guidance(update, context)


async def language_command(update, context) -> None:
    if not await _require_started_access(update, context):
        return
    catalog = catalog_for(context)
    set_state(context.user_data, STATE_LANGUAGE_SELECT)
    await send_text(
        update,
        service.language_menu_text(catalog),
        keyboard_layout=language_keyboard(),
    )
