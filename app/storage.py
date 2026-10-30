"""In-memory persistence layer for tasks.

All state lives in a plain Python list inside :class:`TaskStore`, so it is
lost when the process exits. The store is deliberately isolated behind a
small class with a narrow interface: swapping it for a database later means
reimplementing these five methods and nothing else.

Access is guarded by a :class:`threading.Lock` because FastAPI runs
synchronous endpoint functions in a worker thread pool, which means two
requests can touch the list concurrently.
"""

import threading

from app.schemas import Task, TaskCreate, TaskUpdate


class TaskStore:
    """A thread-safe, in-memory collection of tasks."""

    def __init__(self) -> None:
        self._tasks: list[Task] = []
        self._next_id: int = 1
        self._lock = threading.Lock()

    def list_tasks(self) -> list[Task]:
        """Return every stored task.

        A shallow copy is returned so callers cannot mutate the internal
        list.
        """
        with self._lock:
            return list(self._tasks)

    def get_task(self, task_id: int) -> Task | None:
        """Return the task with ``task_id``, or ``None`` if it is absent."""
        with self._lock:
            return self._find(task_id)

    def add_task(self, payload: TaskCreate) -> Task:
        """Create a task from ``payload`` and return the stored resource."""
        with self._lock:
            task = Task(id=self._next_id, **payload.model_dump())
            self._next_id += 1
            self._tasks.append(task)
            return task

    def replace_task(self, task_id: int, payload: TaskUpdate) -> Task | None:
        """Replace the task with ``task_id``.

        Returns the updated task, or ``None`` if no such task exists. The
        ``id`` is preserved; every other field comes from ``payload``.
        """
        with self._lock:
            existing = self._find(task_id)
            if existing is None:
                return None

            updated = Task(id=task_id, **payload.model_dump())
            self._tasks[self._tasks.index(existing)] = updated
            return updated

    def delete_task(self, task_id: int) -> bool:
        """Delete the task with ``task_id``.

        Returns ``True`` if a task was removed, ``False`` if it was not
        found.
        """
        with self._lock:
            task = self._find(task_id)
            if task is None:
                return False

            self._tasks.remove(task)
            return True

    def _find(self, task_id: int) -> Task | None:
        """Return the matching task without locking. Call under ``_lock``."""
        return next((task for task in self._tasks if task.id == task_id), None)


# Single process-wide instance, handed to endpoints via FastAPI's dependency
# injection (see app.dependencies.get_task_store).
task_store = TaskStore()
