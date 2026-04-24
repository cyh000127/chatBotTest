from __future__ import annotations

from threading import Thread

import uvicorn

from PROJECT.admin.follow_up import InMemoryAdminRuntime, admin_runtime
from PROJECT.admin_api.app import create_admin_api_app
from PROJECT.settings import Settings
from PROJECT.storage.invitations import SqliteInvitationRepository
from PROJECT.storage.onboarding_admin import SqliteOnboardingAdminRepository
from PROJECT.storage.sqlite import SqliteRuntime


def start_admin_api_server(
    settings: Settings,
    *,
    runtime: InMemoryAdminRuntime = admin_runtime,
    sqlite_runtime: SqliteRuntime | None = None,
) -> tuple[uvicorn.Server, Thread]:
    invitation_repository = (
        SqliteInvitationRepository(sqlite_runtime.connection)
        if sqlite_runtime is not None
        else None
    )
    onboarding_admin_repository = (
        SqliteOnboardingAdminRepository(sqlite_runtime.connection)
        if sqlite_runtime is not None
        else None
    )
    config = uvicorn.Config(
        create_admin_api_app(
            runtime,
            invitation_repository=invitation_repository,
            onboarding_admin_repository=onboarding_admin_repository,
        ),
        host=settings.admin_api.host,
        port=settings.admin_api.port,
        log_level="warning",
    )
    server = uvicorn.Server(config)
    thread = Thread(target=server.run, daemon=True, name="admin-api-server")
    thread.start()
    return server, thread
