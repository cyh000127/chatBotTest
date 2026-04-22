from PROJECT.adapters.outbound.reply_sender import send_text
from PROJECT.conversations.fertilizer_intake import service as fertilizer_service
from PROJECT.conversations.fertilizer_intake import keyboards as fertilizer_keyboards
from PROJECT.conversations.fertilizer_intake.states import STATE_FERTILIZER_CONFIRM, STATE_FERTILIZER_USED
from PROJECT.conversations.profile_intake import service as profile_service
from PROJECT.conversations.profile_intake.states import STATE_PROFILE_EDIT_SELECT, STATE_PROFILE_NAME
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
    reset_session(context.user_data)
    set_state(context.user_data, STATE_MAIN_MENU)
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

    args = [arg.strip().lower() for arg in getattr(context, "args", []) if arg.strip()]
    if args and args[0] == "edit":
        await open_profile_edit_selector(update, context)
        return
    if args and args[0] == "new":
        await start_profile_input(update, context)
        return
    await show_current_profile(update, context)


async def fertilizer_command(update, context) -> None:
    await start_fertilizer_input(update, context)


async def language_command(update, context) -> None:
    catalog = catalog_for(context)
    set_state(context.user_data, STATE_LANGUAGE_SELECT)
    await send_text(
        update,
        service.language_menu_text(catalog),
        keyboard_layout=language_keyboard(),
    )
