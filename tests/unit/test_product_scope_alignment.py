import asyncio
from types import SimpleNamespace

from PROJECT.canonical_intents import registry
from PROJECT.canonical_intents.mapping import command_to_intent, text_to_intent
from PROJECT.channels.telegram.handlers import commands
from PROJECT.conversations.sample_menu.keyboards import fallback_keyboard_layout_for_state, main_menu_keyboard
from PROJECT.conversations.sample_menu.states import STATE_MAIN_MENU
from PROJECT.dispatch.command_router import ROUTE_UNKNOWN_INPUT, route_message
from PROJECT.dispatch.input_fallback import FALLBACK_DEFAULT, fallback_key_for_state
from PROJECT.dispatch.session_dispatcher import current_state, has_started, is_authenticated, reset_session
from PROJECT.i18n.translator import get_catalog

LEGACY_REMOVED_STATE = "profile_name"
LEGACY_REMOVED_CONFIRM_STATE = "profile_confirm"


def _update(text: str) -> SimpleNamespace:
    return SimpleNamespace(
        effective_message=SimpleNamespace(text=text),
        effective_user=SimpleNamespace(id=10, username="local_user"),
        effective_chat=SimpleNamespace(id=20),
    )


def _context(*, args=None) -> SimpleNamespace:
    user_data: dict = {}
    reset_session(user_data)
    return SimpleNamespace(args=args or [], user_data=user_data, bot_data={})


def test_product_main_menu_and_button_mapping_do_not_expose_removed_profile_entry():
    catalog = get_catalog("ko")
    layout = main_menu_keyboard(catalog)
    button_texts = {button["text"] for row in layout for button in row}

    assert hasattr(catalog, "BUTTON_PROFILE") is False
    assert button_texts == {
        catalog.BUTTON_FERTILIZER,
        catalog.BUTTON_YIELD,
        catalog.BUTTON_MYFIELDS,
        catalog.BUTTON_INPUT_RESOLVE,
        catalog.BUTTON_SUPPORT,
        catalog.BUTTON_HELP,
        catalog.BUTTON_RESTART,
    }


def test_removed_profile_commands_and_texts_do_not_resolve_in_product_scope():
    assert command_to_intent("/profile") == registry.INTENT_UNKNOWN_COMMAND
    assert text_to_intent("내 프로필 보여줘") == (registry.INTENT_UNKNOWN_TEXT, {})
    assert text_to_intent("생일 수정할래") == (registry.INTENT_UNKNOWN_TEXT, {})


def test_removed_profile_intent_no_longer_routes_from_main_menu():
    decision = route_message(STATE_MAIN_MENU, "profile")

    assert decision.route == ROUTE_UNKNOWN_INPUT


def test_non_sqlite_start_argument_only_starts_runtime_without_auth(monkeypatch):
    sent: list[str] = []

    async def fake_send_text(update, text, keyboard_layout=None):
        sent.append(text)

    monkeypatch.setattr(commands, "send_text", fake_send_text)
    context = _context(args=["sample-user"])

    asyncio.run(commands.start_command(_update("/start sample-user"), context))

    assert current_state(context.user_data) == STATE_MAIN_MENU
    assert has_started(context.user_data) is True
    assert is_authenticated(context.user_data) is False
    assert sent
    assert "인증" not in sent[0]


def test_removed_profile_states_fall_back_to_default_product_navigation():
    catalog = get_catalog("ko")

    assert fallback_key_for_state(LEGACY_REMOVED_STATE) == FALLBACK_DEFAULT
    assert fallback_key_for_state(LEGACY_REMOVED_CONFIRM_STATE) == FALLBACK_DEFAULT

    layout = fallback_keyboard_layout_for_state(LEGACY_REMOVED_CONFIRM_STATE, catalog)
    button_texts = [button["text"] for row in layout for button in row]

    assert layout[0][0]["text"] == catalog.BUTTON_FERTILIZER
    assert layout[0][1]["text"] == catalog.BUTTON_YIELD
    assert "프로필 입력" not in button_texts
