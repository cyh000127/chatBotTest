import asyncio
from types import SimpleNamespace

from PROJECT.channels.telegram.handlers import messages
from PROJECT.channels.telegram.handlers.messages import parse_callback_data
from PROJECT.conversations.fertilizer_intake.states import STATE_FERTILIZER_CONFIRM, STATE_FERTILIZER_PRODUCT
from PROJECT.dispatch.session_dispatcher import mark_started, set_fertilizer_draft, set_locale, set_state


def test_parse_yield_edit_callback_data():
    action, payload = parse_callback_data("yield:edit:amount")

    assert action == "yield_edit_select"
    assert payload == {"target": "amount"}


class FakeMessage:
    def __init__(self):
        self.replies: list[tuple[str, object | None]] = []
        self.cleared = False

    async def reply_text(self, text: str, reply_markup=None):
        self.replies.append((text, reply_markup))

    async def edit_reply_markup(self, reply_markup=None):
        self.cleared = True


class FakeCallbackQuery:
    def __init__(self, data: str, message: FakeMessage):
        self.data = data
        self.message = message

    async def answer(self):
        return None


def _callback_update(data: str, message: FakeMessage) -> SimpleNamespace:
    return SimpleNamespace(
        effective_message=message,
        effective_user=SimpleNamespace(id=12345),
        effective_chat=SimpleNamespace(id=67890),
        callback_query=FakeCallbackQuery(data, message),
    )


def test_fertilizer_edit_callback_keeps_selected_current_value_summary():
    message = FakeMessage()
    context = SimpleNamespace(user_data={}, bot_data={})
    mark_started(context.user_data)
    set_locale(context.user_data, "ko")
    set_state(context.user_data, STATE_FERTILIZER_CONFIRM)
    set_fertilizer_draft(
        context.user_data,
        {
            "used": True,
            "kind": "compound",
            "product_name": "한아름 복합비료",
            "amount_value": 20.0,
            "amount_unit": "kg",
            "applied_date": "2026-04-21",
        },
    )

    asyncio.run(messages.button_callback(_callback_update("fertilizer:edit:product", message), context))

    assert message.replies
    reply_text = message.replies[-1][0]
    assert messages.current_state(context.user_data) == STATE_FERTILIZER_PRODUCT
    assert "현재 입력: 제품명=한아름 복합비료" in reply_text
    assert "사용량=20 kg" not in reply_text
