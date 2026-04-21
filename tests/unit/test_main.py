from PROJECT.channels.telegram.app import create_application
from PROJECT.settings import GeminiSettings, Settings


def test_create_application_registers_settings():
    application = create_application(Settings(bot_token="test-token"))
    assert application.bot_data["settings"].bot_token == "test-token"
    assert application.bot_data["gemini_recovery_classifier"] is None
    assert application.bot_data["gemini_edit_intent_resolver"] is None


def test_create_application_keeps_edit_intent_resolver_disabled_without_policy_gate():
    application = create_application(
        Settings(
            bot_token="test-token",
            gemini=GeminiSettings(
                api_key="test-key",
                model="gemini-2.5-flash",
                api_base="https://generativelanguage.googleapis.com/v1beta",
                timeout_seconds=15.0,
            ),
            enable_llm_edit_intent=False,
        )
    )

    assert application.bot_data["gemini_recovery_classifier"] is not None
    assert application.bot_data["gemini_edit_intent_resolver"] is None


def test_create_application_registers_edit_intent_resolver_only_when_policy_gate_is_enabled():
    application = create_application(
        Settings(
            bot_token="test-token",
            gemini=GeminiSettings(
                api_key="test-key",
                model="gemini-2.5-flash",
                api_base="https://generativelanguage.googleapis.com/v1beta",
                timeout_seconds=15.0,
            ),
            enable_llm_edit_intent=True,
        )
    )

    assert application.bot_data["gemini_recovery_classifier"] is not None
    assert application.bot_data["gemini_edit_intent_resolver"] is not None
