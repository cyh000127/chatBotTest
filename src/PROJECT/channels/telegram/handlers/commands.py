from PROJECT.auth.service import authenticate_login_id
from PROJECT.adapters.outbound.reply_sender import send_text
from PROJECT.conversations.profile_intake import service as profile_service
from PROJECT.conversations.profile_intake.states import STATE_PROFILE_NAME
from PROJECT.conversations.sample_menu import service
from PROJECT.conversations.sample_menu.keyboards import keyboard_layout_for_state
from PROJECT.conversations.sample_menu.states import STATE_AUTH_ID_INPUT, STATE_LANGUAGE_SELECT, STATE_MAIN_MENU
from PROJECT.dispatch.session_dispatcher import (
    authenticate_session,
    current_user_name,
    cancel_session,
    increment_auth_failures,
    is_authenticated,
    current_locale,
    current_state,
    profile_draft,
    reset_session,
    set_pending_slot,
    set_profile_draft,
    set_state,
)
from PROJECT.i18n.translator import get_catalog, language_keyboard


def catalog_for(context):
    return get_catalog(current_locale(context.user_data))


async def attempt_auth(update, context, login_id: str) -> bool:
    catalog = catalog_for(context)
    auth_result = authenticate_login_id(login_id)
    if auth_result is None:
        failures = increment_auth_failures(context.user_data)
        if failures >= 2:
            reset_session(context.user_data)
            await send_text(update, service.auth_retry_limit_text(catalog), keyboard_layout=None)
            return False
        set_state(context.user_data, STATE_AUTH_ID_INPUT)
        await send_text(update, service.auth_invalid_text(catalog), keyboard_layout=None)
        return False

    authenticate_session(
        context.user_data,
        login_id=auth_result["login_id"],
        user_name=auth_result["user_name"],
    )
    set_state(context.user_data, STATE_MAIN_MENU)
    await send_text(
        update,
        service.auth_welcome_text(catalog, auth_result["user_name"]),
        keyboard_layout=keyboard_layout_for_state(current_state(context.user_data), catalog, profile_draft(context.user_data)),
    )
    return True


async def start_command(update, context) -> None:
    catalog = catalog_for(context)
    reset_session(context.user_data)
    if is_authenticated(context.user_data):
        set_state(context.user_data, STATE_MAIN_MENU)
        await send_text(
            update,
            service.auth_already_logged_in_text(catalog, current_user_name(context.user_data) or ""),
            keyboard_layout=keyboard_layout_for_state(current_state(context.user_data), catalog, profile_draft(context.user_data)),
        )
        return

    login_id = " ".join(getattr(context, "args", [])).strip()
    if login_id:
        set_state(context.user_data, STATE_AUTH_ID_INPUT)
        await attempt_auth(update, context, login_id)
        return

    set_state(context.user_data, STATE_AUTH_ID_INPUT)
    await send_text(
        update,
        service.auth_start_text(catalog),
        keyboard_layout=None,
    )


async def help_command(update, context) -> None:
    catalog = catalog_for(context)
    if not is_authenticated(context.user_data):
        await send_text(update, service.auth_required_text(catalog), keyboard_layout=None)
        return
    await send_text(
        update,
        service.help_text(catalog),
        keyboard_layout=keyboard_layout_for_state(current_state(context.user_data), catalog, profile_draft(context.user_data)),
    )


async def menu_command(update, context) -> None:
    catalog = catalog_for(context)
    if not is_authenticated(context.user_data):
        await send_text(update, service.auth_required_text(catalog), keyboard_layout=None)
        return
    reset_session(context.user_data)
    await send_text(
        update,
        service.main_menu_text(catalog),
        keyboard_layout=keyboard_layout_for_state(current_state(context.user_data), catalog, profile_draft(context.user_data)),
    )


async def cancel_command(update, context) -> None:
    catalog = catalog_for(context)
    if not is_authenticated(context.user_data):
        await send_text(update, service.auth_required_text(catalog), keyboard_layout=None)
        return
    cancel_session(context.user_data)
    await send_text(
        update,
        service.cancel_text(catalog),
        keyboard_layout=keyboard_layout_for_state(current_state(context.user_data), catalog, profile_draft(context.user_data)),
    )


async def profile_command(update, context) -> None:
    catalog = catalog_for(context)
    if not is_authenticated(context.user_data):
        await send_text(update, service.auth_required_text(catalog), keyboard_layout=None)
        return
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


async def language_command(update, context) -> None:
    catalog = catalog_for(context)
    if not is_authenticated(context.user_data):
        await send_text(update, service.auth_required_text(catalog), keyboard_layout=None)
        return
    set_state(context.user_data, STATE_LANGUAGE_SELECT)
    await send_text(
        update,
        service.language_menu_text(catalog),
        keyboard_layout=language_keyboard(),
    )
