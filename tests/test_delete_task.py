"""Tests for ``DELETE /tasks/{task_id}``."""

import pytest
from fastapi.testclient import TestClient

from app.schemas import Task
from tests.conftest import valid_payload


class TestDeleteTaskSuccess:
    """Deleting an existing task."""

    def test_returns_204_with_an_empty_body(
        self, client: TestClient, sample_task: Task
    ) -> None:
        response = client.delete(f"/tasks/{sample_task.id}")

        assert response.status_code == 204
        assert response.content == b""

    def test_task_is_gone_afterwards(
        self, client: TestClient, sample_task: Task
    ) -> None:
        client.delete(f"/tasks/{sample_task.id}")

        assert client.get(f"/tasks/{sample_task.id}").status_code == 404

    def test_task_is_removed_from_the_collection(
        self, client: TestClient, sample_task: Task
    ) -> None:
        client.delete(f"/tasks/{sample_task.id}")

        assert client.get("/tasks").json() == []

    def test_deletes_only_the_requested_task(
        self, client: TestClient, many_tasks: list[Task]
    ) -> None:
        client.delete("/tasks/2")

        assert [task["id"] for task in client.get("/tasks").json()] == [1, 3]

    def test_remaining_ids_are_not_renumbered(
        self, client: TestClient, many_tasks: list[Task]
    ) -> None:
        """Deleting the first task must not shift the others' identities."""
        client.delete("/tasks/1")

        remaining = client.get("/tasks").json()
        assert [task["title"] for task in remaining] == ["Task 2", "Task 3"]
        assert client.get("/tasks/3").json()["title"] == "Task 3"

    def test_can_empty_the_collection(
        self, client: TestClient, many_tasks: list[Task]
    ) -> None:
        for task in many_tasks:
            assert client.delete(f"/tasks/{task.id}").status_code == 204

        assert client.get("/tasks").json() == []

    def test_store_still_accepts_new_tasks_after_emptying(
        self, client: TestClient, sample_task: Task
    ) -> None:
        client.delete(f"/tasks/{sample_task.id}")

        assert client.post("/tasks", json=valid_payload()).status_code == 201


class TestDeleteTaskNotFound:
    """Deleting something that is not there."""

    def test_unknown_id_returns_404(self, client: TestClient) -> None:
        response = client.delete("/tasks/999")

        assert response.status_code == 404
        assert response.json() == {"detail": "Task with id 999 was not found."}

    def test_second_delete_returns_404(
        self, client: TestClient, sample_task: Task
    ) -> None:
        """The effect is idempotent, though the status code is not."""
        assert client.delete(f"/tasks/{sample_task.id}").status_code == 204
        assert client.delete(f"/tasks/{sample_task.id}").status_code == 404

    def test_delete_on_empty_collection_returns_404(self, client: TestClient) -> None:
        assert client.delete("/tasks/1").status_code == 404


class TestDeleteTaskInvalidId:
    """The path parameter is validated before any lookup."""

    @pytest.mark.parametrize(
        "task_id",
        ["0", "-1", "abc", "1.5"],
        ids=["zero", "negative", "letters", "float"],
    )
    def test_invalid_id_returns_422(self, client: TestClient, task_id: str) -> None:
        assert client.delete(f"/tasks/{task_id}").status_code == 422

    def test_invalid_id_deletes_nothing(
        self, client: TestClient, sample_task: Task
    ) -> None:
        client.delete("/tasks/0")

        assert len(client.get("/tasks").json()) == 1
