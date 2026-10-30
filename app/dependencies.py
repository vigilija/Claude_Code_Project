"""Shared FastAPI dependencies.

Routing code depends on :func:`get_task_store` rather than importing the
module-level store directly. That indirection keeps endpoints decoupled from
the concrete storage backend and lets tests override the store with
``app.dependency_overrides``.
"""

from app.storage import TaskStore, task_store


def get_task_store() -> TaskStore:
    """Return the application's task store."""
    return task_store
