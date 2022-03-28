import os
import time
from typing import Any, Callable

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from rungalileo.exceptions import RungalileoException
from starlette.responses import JSONResponse
from starlette_exporter import PrometheusMiddleware, handle_metrics

from api import __version__ as api_version
from api import apisecrets, objectstore
from api.routers import auth, edit, health, project, run, slice, user
from api.routers.content import embeddings, export, insights, jobs, meta

#
# initial operations
#
os.environ["TZ"] = "UTC"
objectstore.create_root_buckets()


#
# initialize the api
#
api = FastAPI(title="Galileo API Server", version=api_version)


#
# middleware
#
api.add_middleware(
    PrometheusMiddleware,
    app_name="galileo_api",
    prefix="galileo_api",
    filter_unhandled_paths=True,
    skip_paths=["/healthcheck", "/docs", "/metrics"],
)

api.add_middleware(
    CORSMiddleware,
    allow_origins=apisecrets.galileo_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@api.exception_handler(RungalileoException)
def rungalileo_exception_handler(
    request: Request, exc: RungalileoException
) -> JSONResponse:
    # When the user requests insights on a dataframe, and either (1) there's no data
    # for the run, or (2) the filter provided results in no rows
    if str(exc).startswith("No data"):
        status_code = 200
    # A multi-label run is being investigated but no task was provided
    elif str(exc) == "A task must be provided for this multi-label run":
        status_code = 422
    # Here, the multi-label task provided wasn't a correct task name for this run
    elif str(exc).startswith("Invalid task name"):
        status_code = 422
    # Requesting the tasks for a run type that does not have tasks
    elif str(exc).startswith("No tasks for run of type"):
        status_code = 422
    else:
        status_code = 400
    return JSONResponse(status_code=status_code, content={"detail": str(exc)})


@api.middleware("http")
async def add_process_time_header(request: Request, call_next: Callable) -> Any:
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


#
# routers
#
api.include_router(health.router)
api.include_router(auth.router)
api.include_router(user.router)
api.include_router(project.router)
api.include_router(run.router)
api.include_router(embeddings.router)
api.include_router(export.router)
api.include_router(insights.router)
api.include_router(meta.router)
api.include_router(slice.router)
api.include_router(edit.router)
api.include_router(jobs.router)

#
# route
#
api.add_route("/metrics", handle_metrics)
