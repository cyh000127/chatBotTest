from PROJECT.channels.telegram.app import create_application
from PROJECT.settings import Settings


def test_create_application_registers_settings():
    application = create_application(Settings(bot_token="test-token"))
    assert application.bot_data["settings"].bot_token == "test-token"
    assert application.bot_data["gemini_recovery_classifier"] is None
    assert application.bot_data["gemini_edit_intent_resolver"] is None
