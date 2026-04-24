import asyncio
from types import SimpleNamespace

from PROJECT.channels.telegram.handlers import commands, onboarding
from PROJECT.conversations.fertilizer_intake.states import STATE_FERTILIZER_USED
from PROJECT.conversations.sample_menu.states import STATE_LANGUAGE_SELECT, STATE_MAIN_MENU
from PROJECT.dispatch.session_dispatcher import current_state, get_session, reset_session
from PROJECT.settings import SqliteSettings
from PROJECT.storage.invitations import SqliteInvitationRepository
from PROJECT.storage.onboarding import SqliteOnboardingRepository
from PROJECT.storage.onboarding_admin import SqliteOnboardingAdminRepository
from PROJECT.storage.sqlite import bootstrap_sqlite_runtime


def _update(text: str = "/start") -> SimpleNamespace:
    return SimpleNamespace(
        effective_message=SimpleNamespace(text=text),
        effective_user=SimpleNamespace(id=12345, username="farmer_user"),
        effective_chat=SimpleNamespace(id=67890),
    )


def _context(*, args=None, bot_data=None) -> SimpleNamespace:
    user_data: dict = {}
    reset_session(user_data)
    return SimpleNamespace(
        args=args or [],
        user_data=user_data,
        bot_data=bot_data or {},
    )


def _sqlite_repositories(tmp_path):
    runtime = bootstrap_sqlite_runtime(
        SqliteSettings(
            database_path=str(tmp_path / "runtime.sqlite3"),
            migrations_enabled=True,
        )
    )
    assert runtime is not None
    invitation_repository = SqliteInvitationRepository(runtime.connection)
    onboarding_repository = SqliteOnboardingRepository(runtime.connection)
    return runtime, invitation_repository, onboarding_repository


def test_start_with_valid_invitation_creates_onboarding_session(monkeypatch, tmp_path):
    sent: list[tuple[str, list[list[dict[str, str]]] | None]] = []

    async def fake_send_text(update, text, keyboard_layout=None):
        sent.append((text, keyboard_layout))

    monkeypatch.setattr(commands, "send_text", fake_send_text)
    monkeypatch.setattr(onboarding, "send_text", fake_send_text)
    runtime, invitation_repository, onboarding_repository = _sqlite_repositories(tmp_path)

    try:
        invitation = invitation_repository.create_invitation()
        context = _context(
            args=[invitation.invite_code],
            bot_data={
                "invitation_repository": invitation_repository,
                "onboarding_repository": onboarding_repository,
            },
        )

        asyncio.run(commands.start_command(_update(f"/start {invitation.invite_code}"), context))

        session = get_session(context.user_data)
        assert current_state(context.user_data) == STATE_LANGUAGE_SELECT
        assert session["authenticated"] is False
        assert session["onboarding_session_id"].startswith("onboarding_")
        assert session["onboarding_invite_code"] == invitation.invite_code
        assert session["onboarding_project_id"] == invitation.project_id
        assert onboarding_repository.get_by_id(session["onboarding_session_id"]) is not None
        assert "초대 코드" in sent[0][0]
        assert sent[0][1] is not None
    finally:
        runtime.close()


def test_start_without_invitation_code_in_sqlite_mode_does_not_open_menu(monkeypatch, tmp_path):
    sent: list[str] = []

    async def fake_send_text(update, text, keyboard_layout=None):
        sent.append(text)

    monkeypatch.setattr(commands, "send_text", fake_send_text)
    runtime, invitation_repository, onboarding_repository = _sqlite_repositories(tmp_path)

    try:
        context = _context(
            bot_data={
                "invitation_repository": invitation_repository,
                "onboarding_repository": onboarding_repository,
            },
        )

        asyncio.run(commands.start_command(_update("/start"), context))

        assert current_state(context.user_data) == STATE_MAIN_MENU
        assert "초대 코드" in sent[0]
        assert get_session(context.user_data)["onboarding_session_id"] is None
    finally:
        runtime.close()


def test_start_with_invalid_invitation_does_not_create_onboarding_session(monkeypatch, tmp_path):
    sent: list[str] = []

    async def fake_send_text(update, text, keyboard_layout=None):
        sent.append(text)

    monkeypatch.setattr(commands, "send_text", fake_send_text)
    runtime, invitation_repository, onboarding_repository = _sqlite_repositories(tmp_path)

    try:
        context = _context(
            args=["INV-MISSING"],
            bot_data={
                "invitation_repository": invitation_repository,
                "onboarding_repository": onboarding_repository,
            },
        )

        asyncio.run(commands.start_command(_update("/start INV-MISSING"), context))

        assert current_state(context.user_data) == STATE_MAIN_MENU
        assert "확인하지 못했습니다" in sent[0]
        assert get_session(context.user_data)["onboarding_session_id"] is None
    finally:
        runtime.close()


def test_protected_farmer_command_requires_approved_onboarding(monkeypatch, tmp_path):
    sent: list[str] = []

    async def fake_send_text(update, text, keyboard_layout=None):
        sent.append(text)

    monkeypatch.setattr(commands, "send_text", fake_send_text)
    runtime, invitation_repository, onboarding_repository = _sqlite_repositories(tmp_path)

    try:
        context = _context(
            bot_data={
                "invitation_repository": invitation_repository,
                "onboarding_repository": onboarding_repository,
            },
        )

        asyncio.run(commands.fertilizer_command(_update("/fertilizer"), context))

        assert current_state(context.user_data) != STATE_FERTILIZER_USED
        assert "인증" in sent[0]
    finally:
        runtime.close()


def test_protected_farmer_command_restores_access_after_admin_approval(monkeypatch, tmp_path):
    sent: list[str] = []

    async def fake_send_text(update, text, keyboard_layout=None):
        sent.append(text)

    monkeypatch.setattr(commands, "send_text", fake_send_text)
    runtime, invitation_repository, onboarding_repository = _sqlite_repositories(tmp_path)

    try:
        invitation = invitation_repository.create_invitation()
        onboarding_session = onboarding_repository.create_or_resume_from_invitation(
            invitation=invitation,
            provider_user_id="12345",
            provider_handle="farmer_user",
            preferred_locale_code="ko",
            chat_id=67890,
        )
        onboarding_session = onboarding_repository.update_locale(onboarding_session.id, "ko")
        onboarding_session = onboarding_repository.update_name(onboarding_session.id, "홍길동")
        onboarding_session = onboarding_repository.update_phone(
            onboarding_session.id,
            phone_raw="+855 12 345 678",
            phone_normalized="+85512345678",
        )
        onboarding_session = onboarding_repository.submit_pending_approval(onboarding_session.id)
        SqliteOnboardingAdminRepository(runtime.connection).approve_submission(onboarding_session.id)
        context = _context(
            bot_data={
                "invitation_repository": invitation_repository,
                "onboarding_repository": onboarding_repository,
            },
        )

        asyncio.run(commands.fertilizer_command(_update("/fertilizer"), context))

        assert current_state(context.user_data) == STATE_FERTILIZER_USED
        assert sent
    finally:
        runtime.close()
