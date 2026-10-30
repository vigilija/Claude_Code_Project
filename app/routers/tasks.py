"""HTTP endpoints for the ``/tasks`` resource.

Route handlers stay thin: they validate input (delegated to Pydantic),
call the store, and translate a missing record into a 404. All business
state lives in :mod:`app.storage`.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, status

from app.dependencies import get_task_store
from app.schemas import Task, TaskCreate, TaskUpdate
from app.storage import TaskStore

router = APIRouter(prefix="/tasks", tags=["tasks"])

# Reused across the routes that address a single task.
TaskId = Annotated[int, Path(ge=1, description="Unique identifier of the task.")]
Store = Annotated[TaskStore, Depends(get_task_store)]


def _not_found(task_id: int) -> HTTPException:
    """Build the 404 raised when ``task_id`` does not exist."""
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Task with id {task_id} was not found.",
    )


@router.get(
    "",
    response_model=list[Task],
    summary="List all tasks",
    response_description="An array of every stored task.",
)
def list_tasks(store: Store) -> list[Task]:
    """Return every task currently held in the store."""
    return store.list_tasks()


@router.get(
    "/{task_id}",
    response_model=Task,
    summary="Retrieve a single task",
    response_description="The requested task.",
    responses={status.HTTP_404_NOT_FOUND: {"description": "Task not found."}},
)
def get_task(task_id: TaskId, store: Store) -> Task:
    """Return a single task, or respond 404 if it does not exist."""
    task = store.get_task(task_id)
    if task is None:
        raise _not_found(task_id)

    return task


@router.post(
    "",
    response_model=Task,
    status_code=status.HTTP_201_CREATED,
    summary="Create a task",
    response_description="The newly created task, including its id.",
)
def create_task(payload: TaskCreate, store: Store) -> Task:
    """Create a task and return it with its server-generated ``id``.

    Responds 201 Created, as the request adds a new resource.
    """
    return store.add_task(payload)


@router.put(
    "/{task_id}",
    response_model=Task,
    summary="Replace a task",
    response_description="The updated task.",
    responses={status.HTTP_404_NOT_FOUND: {"description": "Task not found."}},
)
def replace_task(task_id: TaskId, payload: TaskUpdate, store: Store) -> Task:
    """Replace an existing task in full.

    Per REST semantics ``PUT`` overwrites the whole resource, so omitted
    optional fields revert to their defaults. The ``id`` in the path wins;
    it is never taken from the body.
    """
    task = store.replace_task(task_id, payload)
    if task is None:
        raise _not_found(task_id)

    return task


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a task",
    response_description="The task was deleted; no content is returned.",
    responses={status.HTTP_404_NOT_FOUND: {"description": "Task not found."}},
)
def delete_task(task_id: TaskId, store: Store) -> None:
    """Delete a task, or respond 404 if it does not exist.

    Responds 204 No Content on success, so the body is intentionally empty.
    """
    if not store.delete_task(task_id):
        raise _not_found(task_id)
