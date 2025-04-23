import os

from starlette.responses import JSONResponse, PlainTextResponse

from langgraph_api import config, metadata
from langgraph_api.route import ApiRequest
from langgraph_license.validation import plus_features_enabled
from langgraph_runtime.database import connect, pool_stats
from langgraph_runtime.metrics import get_metrics
from langgraph_runtime.ops import Runs

METRICS_FORMATS = {"prometheus", "json"}


async def meta_info(request: ApiRequest):
    plus = plus_features_enabled()
    return JSONResponse(
        {
            "flags": {
                "assistants": True,
                "crons": plus and config.FF_CRONS_ENABLED,
                "langsmith": bool(config.LANGSMITH_API_KEY) and bool(config.TRACING),
            },
            "host": {
                "kind": metadata.HOST,
                "project_id": metadata.PROJECT_ID,
                "revision_id": metadata.REVISION,
                "tenant_id": metadata.TENANT_ID,
            },
        }
    )


async def meta_metrics(request: ApiRequest):
    # determine output format
    format = request.query_params.get("format", "prometheus")
    if format not in METRICS_FORMATS:
        format = "prometheus"

    # collect stats
    metrics = get_metrics()
    worker_metrics = metrics["workers"]
    workers_max = worker_metrics["max"]
    workers_active = worker_metrics["active"]
    workers_available = worker_metrics["available"]

    if format == "json":
        async with connect() as conn:
            return JSONResponse(
                {
                    **pool_stats(),
                    "workers": worker_metrics,
                    "queue": await Runs.stats(conn),
                }
            )
    elif format == "prometheus":
        # LANGSMITH_HOST_PROJECT_ID and HOSTED_LANGSERVE_REVISION_ID are injected
        # into the deployed image by host-backend.
        project_id = os.getenv("LANGSMITH_HOST_PROJECT_ID")
        revision_id = os.getenv("HOSTED_LANGSERVE_REVISION_ID")

        metrics = [
            "# HELP lg_api_workers_max The maximum number of workers available.",
            "# TYPE lg_api_workers_max gauge",
            f'lg_api_workers_max{{project_id="{project_id}", revision_id="{revision_id}"}} {workers_max}',
            "# HELP lg_api_workers_active The number of currently active workers.",
            "# TYPE lg_api_workers_active gauge",
            f'lg_api_workers_active{{project_id="{project_id}", revision_id="{revision_id}"}} {workers_active}',
            "# HELP lg_api_workers_available The number of available (idle) workers.",
            "# TYPE lg_api_workers_available gauge",
            f'lg_api_workers_available{{project_id="{project_id}", revision_id="{revision_id}"}} {workers_available}',
            # In the future, we can add more metrics to be scraped by Prometheus.
        ]

        metrics_response = "\n".join(metrics)
        return PlainTextResponse(metrics_response)
