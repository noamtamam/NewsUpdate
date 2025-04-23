import asyncio
from contextlib import asynccontextmanager
from typing import Any

import langgraph_api.config as config
import structlog
from langchain_core.runnables.config import var_child_runnable_config
from langgraph.constants import CONF, CONFIG_KEY_STORE
from langgraph_api.asyncio import SimpleTaskGroup, set_event_loop
from langgraph_api.graph import collect_graphs_from_env, stop_remote_graphs
from langgraph_api.http import start_http_client, stop_http_client
from langgraph_api.js.ui import start_ui_bundler, stop_ui_bundler
from langgraph_api.metadata import metadata_loop
from starlette.applications import Starlette

from langgraph_runtime_inmem.database import start_pool, stop_pool
from langgraph_runtime_inmem.queue import queue
from langgraph_runtime_inmem.store import Store

logger = structlog.stdlib.get_logger(__name__)


@asynccontextmanager
async def lifespan(
    app: Starlette | None = None,
    taskset: set[asyncio.Task] | None = None,
    **kwargs: Any,
):
    from langgraph_api import __version__

    await logger.ainfo(
        f"Starting In-Memory runtime with langgraph-api={__version__}",
        version=__version__,
    )
    try:
        current_loop = asyncio.get_running_loop()
        set_event_loop(current_loop)
    except RuntimeError:
        await logger.aerror("Failed to set loop")

    await start_http_client()
    await start_pool()
    await collect_graphs_from_env(True)
    await start_ui_bundler()
    try:
        async with SimpleTaskGroup(
            cancel=True, taskset=taskset, taskgroup_name="Lifespan"
        ) as tg:
            tg.create_task(metadata_loop())
            if config.N_JOBS_PER_WORKER > 0:
                tg.create_task(queue())
            store = Store()
            var_child_runnable_config.set({CONF: {CONFIG_KEY_STORE: store}})

            yield
    finally:
        await stop_ui_bundler()
        await stop_remote_graphs()
        await stop_http_client()
        await stop_pool()
