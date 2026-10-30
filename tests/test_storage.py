"""Unit tests for :class:`app.storage.TaskStore`.

The HTTP tests cover the store indirectly. These exercise it directly, where
its contract can be checked without a request in the way -- in particular the
thread safety the API layer depends on.
"""

from concurrent.futures import ThreadPoolExecutor

from app.schemas import TaskCreate, TaskUpdate
from app.storage import TaskStore


class TestTaskStoreBasics:
    """The store's five operations."""

    def test_starts_empty(self, store: TaskStore) -> None:
        assert store.list_tasks() == []

    def test_add_returns_a_task_with_an_id(self, store: TaskStore) -> None:
        task = store.add_task(TaskCreate(title="First"))

        assert task.id == 1
        assert task.title == "First"

    def test_get_returns_none_for_a_missing_id(self, store: TaskStore) -> None:
        assert store.get_task(1) is None

    def test_replace_returns_none_for_a_missing_id(self, store: TaskStore) -> None:
        assert store.replace_task(1, TaskUpdate(title="Nope")) is None

    def test_delete_returns_false_for_a_missing_id(self, store: TaskStore) -> None:
        assert store.delete_task(1) is False

    def test_delete_returns_true_when_it_removes_something(
        self, store: TaskStore
    ) -> None:
        task = store.add_task(TaskCreate(title="Doomed"))

        assert store.delete_task(task.id) is True
        assert store.list_tasks() == []


class TestTaskStoreEncapsulation:
    """Callers cannot reach inside the store."""

    def test_list_returns_a_copy(self, store: TaskStore) -> None:
        store.add_task(TaskCreate(title="Safe"))

        store.list_tasks().clear()

        assert len(store.list_tasks()) == 1


class TestTaskStoreConcurrency:
    """The lock protects the id counter and the list."""

    def test_concurrent_adds_produce_unique_sequential_ids(
        self, store: TaskStore
    ) -> None:
        count = 200

        with ThreadPoolExecutor(max_workers=16) as pool:
            tasks = list(
                pool.map(
                    lambda n: store.add_task(TaskCreate(title=f"Task {n}")),
                    range(count),
                )
            )

        ids = sorted(task.id for task in tasks)
        assert ids == list(range(1, count + 1))
        assert len(store.list_tasks()) == count

    def test_concurrent_deletes_remove_each_task_once(self, store: TaskStore) -> None:
        ids = [store.add_task(TaskCreate(title=f"Task {n}")).id for n in range(50)]

        with ThreadPoolExecutor(max_workers=16) as pool:
            results = list(pool.map(store.delete_task, ids * 2))

        assert sum(results) == len(ids)
        assert store.list_tasks() == []
