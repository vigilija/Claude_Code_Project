"""Tests for ``GET /tasks/{task_id}``."""

import pytest
from fastapi.testclient import TestClient

from app.schemas import Task


class TestGetTaskSuccess:
    """Retrieving an existing task."""

    def test_returns_the_requested_task(
        self, client: TestClient, sample_task: Task
    ) -> None:
        response = client.get(f"/tasks/{sample_task.id}")

        assert response.status_code == 200
        assert response.json() == {
            "id": sample_task.id,
            "title": "Write project documentation",
            "description": "Cover installation and the HTTP API.",
            "completed": False,
        }

    def test_selects_the_right_task_among_many(
        self, client: TestClient, many_tasks: list[Task]
    ) -> None:
        response = client.get("/tasks/2")

        assert response.status_code == 200
        assert response.json()["title"] == "Task 2"

    def test_repeated_reads_are_identical(
        self, client: TestClient, sample_task: Task
    ) -> None:
        """GET is safe: it must not change the resource."""
        first = client.get(f"/tasks/{sample_task.id}").json()
        second = client.get(f"/tasks/{sample_task.id}").json()

        assert first == second


class TestGetTaskNotFound:
    """Requesting a task that is not stored."""

    def test_unknown_id_returns_404(self, client: TestClient) -> None:
        response = client.get("/tasks/999")

        assert response.status_code == 404
        assert response.json() == {"detail": "Task with id 999 was not found."}

    def test_deleted_task_returns_404(
        self, client: TestClient, sample_task: Task
    ) -> None:
        client.delete(f"/tasks/{sample_task.id}")

        assert client.get(f"/tasks/{sample_task.id}").status_code == 404

    def test_very_large_id_returns_404_not_an_error(self, client: TestClient) -> None:
        """A huge but syntactically valid id is simply absent, not invalid."""
        response = client.get(f"/tasks/{2**62}")

        assert response.status_code == 404


class TestGetTaskInvalidId:
    """The path parameter must be a positive integer."""

    @pytest.mark.parametrize(
        "task_id",
        ["0", "-1", "abc", "1.5", "1e3", "%20", "null"],
        ids=["zero", "negative", "letters", "float", "exponent", "space", "null-word"],
    )
    def test_non_positive_or_non_integer_id_returns_422(
        self, client: TestClient, task_id: str
    ) -> None:
        response = client.get(f"/tasks/{task_id}")

        assert response.status_code == 422

    def test_validation_error_names_the_offending_parameter(
        self, client: TestClient
    ) -> None:
        response = client.get("/tasks/0")

        detail = response.json()["detail"]
        assert detail[0]["loc"] == ["path", "task_id"]
