"""Tests for ``GET /tasks``."""

from fastapi.testclient import TestClient

from app.schemas import Task


class TestListTasks:
    """Listing returns every stored task."""

    def test_returns_empty_list_when_no_tasks_exist(self, client: TestClient) -> None:
        response = client.get("/tasks")

        assert response.status_code == 200
        assert response.json() == []

    def test_returns_the_single_stored_task(
        self, client: TestClient, sample_task: Task
    ) -> None:
        response = client.get("/tasks")

        assert response.status_code == 200
        assert response.json() == [
            {
                "id": sample_task.id,
                "title": "Write project documentation",
                "description": "Cover installation and the HTTP API.",
                "completed": False,
            }
        ]

    def test_returns_all_tasks_in_insertion_order(
        self, client: TestClient, many_tasks: list[Task]
    ) -> None:
        response = client.get("/tasks")

        assert response.status_code == 200
        assert [task["id"] for task in response.json()] == [1, 2, 3]
        assert [task["title"] for task in response.json()] == [
            "Task 1",
            "Task 2",
            "Task 3",
        ]

    def test_every_item_exposes_the_full_schema(
        self, client: TestClient, many_tasks: list[Task]
    ) -> None:
        for item in client.get("/tasks").json():
            assert set(item) == {"id", "title", "description", "completed"}

    def test_reflects_tasks_created_through_the_api(self, client: TestClient) -> None:
        client.post("/tasks", json={"title": "Added via API"})

        body = client.get("/tasks").json()

        assert len(body) == 1
        assert body[0]["title"] == "Added via API"

    def test_collection_rejects_unsupported_methods(self, client: TestClient) -> None:
        """``/tasks`` supports GET and POST only."""
        assert client.put("/tasks", json={"title": "x"}).status_code == 405
        assert client.delete("/tasks").status_code == 405
        assert client.patch("/tasks", json={"title": "x"}).status_code == 405
