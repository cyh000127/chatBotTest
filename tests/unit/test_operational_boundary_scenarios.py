import asyncio
from types import SimpleNamespace

import httpx

from PROJECT.channels.telegram.handlers import messages
from PROJECT.conversations.fertilizer_intake.states import STATE_FERTILIZER_CONFIRM
from PROJECT.policy import LocalAiGate
from PROJECT.settings import GeminiSettings, Settings
from PROJECT.dispatch.session_dispatcher import authenticate_session, reset_session, set_state


class _RaisingResolver:
    async def classify(self, **kwargs):
        raise httpx.ReadTimeout("timeout")


def _settings(local_ai_gate: LocalAiGate) -> Settings:
    return Settings(
        bot_token="test-token",
        gemini=GeminiSettings(
            api_key="test-key",
            model="gemini-2.5-flash",
            api_base="https://generativelanguage.googleapis.com/v1beta",
            timeout_seconds=15.0,
        ),
        local_ai_gate=local_ai_gate,
    )


def _context(local_ai_gate: LocalAiGate, resolver) -> SimpleNamespace:
    user_data = {}
    reset_session(user_data)
    authenticate_session(user_data, login_id="sample-user", user_name="테스터")
    set_state(user_data, STATE_FERTILIZER_CONFIRM)
    return SimpleNamespace(
        user_data=user_data,
        bot_data={
            "settings": _settings(local_ai_gate),
            "gemini_edit_intent_resolver": resolver,
        },
    )


def test_manual_review_fallback_logs_policy_skip_for_unknown_repair(monkeypatch):
    captured_events: list[tuple[str, dict]] = []

    def fake_log_event(event: str, **fields):
        captured_events.append((event, fields))

    monkeypatch.setattr(messages, "log_event", fake_log_event)

    handled = asyncio.run(
        messages.attempt_llm_repair_after_rules(
            SimpleNamespace(),
            _context(LocalAiGate.MANUAL_REVIEW_FALLBACK, resolver=None),
            text="제품명 수정할래",
            domain="fertilizer",
            use_confirmed=False,
        )
    )

    assert handled is False
    assert ("llm_skipped_by_policy", {
        "invocation_type": "repair",
        "state": STATE_FERTILIZER_CONFIRM,
        "domain": "fertilizer",
        "policy_scope": "unknown_input",
        "reason": "manual_review_fallback_active",
    }) in captured_events


def test_llm_runtime_failure_downgrades_to_rules_only_fallback(monkeypatch):
    captured_events: list[tuple[str, dict]] = []
    sent_messages: list[dict] = []

    async def fake_send_text(update, text, keyboard_layout=None):
        sent_messages.append({"text": text, "keyboard_layout": keyboard_layout})

    def fake_log_event(event: str, **fields):
        captured_events.append((event, fields))

    monkeypatch.setattr(messages, "send_text", fake_send_text)
    monkeypatch.setattr(messages, "log_event", fake_log_event)

    handled = asyncio.run(
        messages.maybe_send_llm_repair_confirmation(
            SimpleNamespace(),
            _context(LocalAiGate.REPAIR_ASSIST_ONLY, resolver=_RaisingResolver()),
            text="제품명 수정할래",
            allowed_actions=messages.FERTILIZER_REPAIR_ALLOWED_ACTIONS,
            use_confirmed=False,
            policy_scope="unknown_input",
            unknown_policy_reason="fertilizer_confirm_context_allowed",
        )
    )

    assert handled is True
    assert any(event == "llm_failed" and fields["failure_reason"] == "timeout" for event, fields in captured_events)
    assert any(event == "fallback_shown" and fields["source"] == "llm_runtime_failure" for event, fields in captured_events)
    assert any("직접 선택" in message["text"] for message in sent_messages)
