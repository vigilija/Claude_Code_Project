"""Application entry point.

Creates the FastAPI application and mounts the task routes. Run it with::

    uvicorn app.main:app --reload

Interactive documentation is then served at http://127.0.0.1:8000/docs.
"""

from fastapi import FastAPI

from app import __version__
from app.routers import tasks

app = FastAPI(
    title="Task Management API",
    description=(
        "A small REST API for managing tasks. Tasks are held in memory, so "
        "all data is discarded when the server stops."
    ),
    version=__version__,
)

app.include_router(tasks.router)


@app.get("/health", tags=["health"], summary="Service health check")
def health_check() -> dict[str, str]:
    """Report that the service is up.

    Useful as a liveness probe and as a quick check that the server is
    reachable.
    """
    return {"status": "ok"}
