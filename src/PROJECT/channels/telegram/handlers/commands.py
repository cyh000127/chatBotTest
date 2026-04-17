from PROJECT.adapters.outbound.reply_sender import send_text
from PROJECT.conversations.profile_intake import service as profile_service
from PROJECT.conversations.profile_intake.states import STATE_PROFILE_NAME
from PROJECT.conversations.sample_menu import service
from PROJECT.conversations.sample_menu.keyboards import keyboard_layout_for_state
from PROJECT.conversations.sample_menu.states import STATE_LANGUAGE_SELECT
from PROJECT.dispatch.session_dispatcher import (
    cancel_session,
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


async def start_command(update, context) -> None:
    catalog = catalog_for(context)
    reset_session(context.user_data)
    await send_text(
        update,
        service.start_text(catalog),
        keyboard_layout=keyboard_layout_for_state(current_state(context.user_data), catalog, profile_draft(context.user_data)),
    )


async def help_command(update, context) -> None:
    catalog = catalog_for(context)
    await send_text(
        update,
        service.help_text(catalog),
        keyboard_layout=keyboard_layout_for_state(current_state(context.user_data), catalog, profile_draft(context.user_data)),
    )


async def menu_command(update, context) -> None:
    catalog = catalog_for(context)
    reset_session(context.user_data)
    await send_text(
        update,
        service.main_menu_text(catalog),
        keyboard_layout=keyboard_layout_for_state(current_state(context.user_data), catalog, profile_draft(context.user_data)),
    )


async def cancel_command(update, context) -> None:
    catalog = catalog_for(context)
    cancel_session(context.user_data)
    await send_text(
        update,
        service.cancel_text(catalog),
        keyboard_layout=keyboard_layout_for_state(current_state(context.user_data), catalog, profile_draft(context.user_data)),
    )


async def profile_command(update, context) -> None:
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


async def language_command(update, context) -> None:
    catalog = catalog_for(context)
    set_state(context.user_data, STATE_LANGUAGE_SELECT)
    await send_text(
        update,
        service.language_menu_text(catalog),
        keyboard_layout=language_keyboard(),
    )
