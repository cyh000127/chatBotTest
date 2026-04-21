from PROJECT.auth.service import authenticate_login_id
from PROJECT.adapters.outbound.reply_sender import send_text
from PROJECT.conversations.fertilizer_intake import service as fertilizer_service
from PROJECT.conversations.fertilizer_intake.states import STATE_FERTILIZER_USED
from PROJECT.conversations.profile_intake import service as profile_service
from PROJECT.conversations.profile_intake.states import STATE_PROFILE_EDIT_SELECT, STATE_PROFILE_NAME
from PROJECT.conversations.sample_menu import service
from PROJECT.conversations.sample_menu.keyboards import keyboard_layout_for_state
from PROJECT.conversations.sample_menu.states import STATE_AUTH_ID_INPUT, STATE_LANGUAGE_SELECT, STATE_MAIN_MENU
from PROJECT.dispatch.session_dispatcher import (
    authenticate_session,
    confirmed_fertilizer,
    confirmed_profile,
    current_user_name,
    cancel_session,
    has_confirmed_fertilizer,
    has_confirmed_profile,
    increment_auth_failures,
    is_authenticated,
    current_locale,
    current_state,
    profile_draft,
    reset_session,
    set_fertilizer_draft,
    set_pending_slot,
    set_profile_draft,
    set_state,
)
from PROJECT.i18n.translator import get_catalog, language_keyboard


def catalog_for(context):
    return get_catalog(current_locale(context.user_data))


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

    args = [arg.strip().lower() for arg in getattr(context, "args", []) if arg.strip()]
    if args and args[0] == "edit":
        await open_profile_edit_selector(update, context)
        return
    if args and args[0] == "new":
        await start_profile_input(update, context)
        return
    await show_current_profile(update, context)


async def fertilizer_command(update, context) -> None:
    catalog = catalog_for(context)
    if not is_authenticated(context.user_data):
        await send_text(update, service.auth_required_text(catalog), keyboard_layout=None)
        return
    await start_fertilizer_input(update, context)


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
