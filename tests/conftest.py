"""Shared pytest fixtures for the Task Management API test suite.

The application keeps its tasks in a single process-wide
:class:`~app.storage.TaskStore`. Tests must not share that instance, or the
order they run in would change their results. Every test therefore gets a
brand-new store injected through FastAPI's dependency override mechanism.
"""

from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.dependencies import get_task_store
from app.main import app
from app.schemas import Task, TaskCreate
from app.storage import TaskStore


@pytest.fixture
def store() -> TaskStore:
    """Return an empty, isolated task store."""
    return TaskStore()


@pytest.fixture
def client(store: TaskStore) -> Iterator[TestClient]:
    """Return a ``TestClient`` wired to an isolated store.

    The override is removed afterwards so no state leaks into the next test.
    """
    app.dependency_overrides[get_task_store] = lambda: store
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_task(store: TaskStore) -> Task:
    """Seed the store with one task and return it."""
    return store.add_task(
        TaskCreate(
            title="Write project documentation",
            description="Cover installation and the HTTP API.",
            completed=False,
        )
    )


@pytest.fixture
def many_tasks(store: TaskStore) -> list[Task]:
    """Seed the store with three tasks and return them in insertion order."""
    return [
        store.add_task(TaskCreate(title=f"Task {index}", completed=index % 2 == 0))
        for index in range(1, 4)
    ]


def valid_payload(**overrides: Any) -> dict[str, Any]:
    """Build a valid task payload, with ``overrides`` applied on top.

    Keeps individual tests focused on the one field they are exercising.
    """
    payload: dict[str, Any] = {
        "title": "Buy milk",
        "description": "Two litres, semi-skimmed.",
        "completed": False,
    }
    payload.update(overrides)
    return payload
