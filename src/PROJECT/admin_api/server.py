from __future__ import annotations

from threading import Thread

import uvicorn

from PROJECT.admin.follow_up import InMemoryAdminRuntime, admin_runtime
from PROJECT.admin_api.app import create_admin_api_app
from PROJECT.settings import Settings


def start_admin_api_server(
    settings: Settings,
    *,
    runtime: InMemoryAdminRuntime = admin_runtime,
) -> tuple[uvicorn.Server, Thread]:
    config = uvicorn.Config(
        create_admin_api_app(runtime),
        host=settings.admin_api.host,
        port=settings.admin_api.port,
        log_level="warning",
    )
    server = uvicorn.Server(config)
    thread = Thread(target=server.run, daemon=True, name="admin-api-server")
    thread.start()
    return server, thread
