from __future__ import annotations

from threading import Thread

import uvicorn

from PROJECT.admin.follow_up import InMemoryAdminRuntime, admin_runtime
from PROJECT.admin.sqlite_follow_up import SqliteAdminRuntime
from PROJECT.admin_api.app import create_admin_api_app
from PROJECT.settings import Settings
from PROJECT.storage.admin_audit import SqliteAdminAuditRepository
from PROJECT.storage.invitations import SqliteInvitationRepository
from PROJECT.storage.onboarding_admin import SqliteOnboardingAdminRepository
from PROJECT.storage.sqlite import SqliteRuntime


def admin_runtime_for_storage(
    runtime: InMemoryAdminRuntime,
    sqlite_runtime: SqliteRuntime | None,
):
    if sqlite_runtime is None:
        return runtime
    return SqliteAdminRuntime(sqlite_runtime.connection)


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
    admin_audit_repository = (
        SqliteAdminAuditRepository(sqlite_runtime.connection)
        if sqlite_runtime is not None
        else None
    )
    api_runtime = admin_runtime_for_storage(runtime, sqlite_runtime)
    config = uvicorn.Config(
        create_admin_api_app(
            api_runtime,
            invitation_repository=invitation_repository,
            onboarding_admin_repository=onboarding_admin_repository,
            admin_audit_repository=admin_audit_repository,
            admin_access_token=settings.admin_api.access_token,
            admin_access_role=settings.admin_api.access_role,
        ),
        host=settings.admin_api.host,
        port=settings.admin_api.port,
        log_level="warning",
    )
    server = uvicorn.Server(config)
    thread = Thread(target=server.run, daemon=True, name="admin-api-server")
    thread.start()
    return server, thread
