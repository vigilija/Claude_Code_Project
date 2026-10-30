"""Tests for ``PUT /tasks/{task_id}``.

``PUT`` replaces the whole resource, which is the behaviour most of these
tests pin down: omitted optional fields revert to their defaults rather than
retaining their previous values.
"""

from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.schemas import Task
from tests.conftest import valid_payload


class TestReplaceTaskSuccess:
    """Replacing an existing task."""

    def test_returns_200_with_the_updated_task(
        self, client: TestClient, sample_task: Task
    ) -> None:
        payload = valid_payload(title="Rewritten", description="New body")

        response = client.put(f"/tasks/{sample_task.id}", json=payload)

        assert response.status_code == 200
        assert response.json() == {
            "id": sample_task.id,
            "title": "Rewritten",
            "description": "New body",
            "completed": False,
        }

    def test_can_mark_a_task_completed(
        self, client: TestClient, sample_task: Task
    ) -> None:
        response = client.put(
            f"/tasks/{sample_task.id}", json=valid_payload(completed=True)
        )

        assert response.json()["completed"] is True

    def test_can_mark_a_completed_task_incomplete_again(
        self, client: TestClient, sample_task: Task
    ) -> None:
        client.put(f"/tasks/{sample_task.id}", json=valid_payload(completed=True))

        response = client.put(
            f"/tasks/{sample_task.id}", json=valid_payload(completed=False)
        )

        assert response.json()["completed"] is False

    def test_change_is_visible_on_subsequent_reads(
        self, client: TestClient, sample_task: Task
    ) -> None:
        client.put(f"/tasks/{sample_task.id}", json=valid_payload(title="Rewritten"))

        assert client.get(f"/tasks/{sample_task.id}").json()["title"] == "Rewritten"

    def test_preserves_the_id(self, client: TestClient, sample_task: Task) -> None:
        response = client.put(f"/tasks/{sample_task.id}", json=valid_payload())

        assert response.json()["id"] == sample_task.id

    def test_does_not_change_the_task_count(
        self, client: TestClient, many_tasks: list[Task]
    ) -> None:
        client.put("/tasks/2", json=valid_payload())

        assert len(client.get("/tasks").json()) == len(many_tasks)

    def test_leaves_other_tasks_untouched(
        self, client: TestClient, many_tasks: list[Task]
    ) -> None:
        client.put("/tasks/2", json=valid_payload(title="Only this one"))

        titles = [task["title"] for task in client.get("/tasks").json()]
        assert titles == ["Task 1", "Only this one", "Task 3"]

    def test_preserves_collection_position(
        self, client: TestClient, many_tasks: list[Task]
    ) -> None:
        """A replacement updates in place rather than moving to the end."""
        client.put("/tasks/1", json=valid_payload())

        assert [task["id"] for task in client.get("/tasks").json()] == [1, 2, 3]

    def test_is_idempotent(self, client: TestClient, sample_task: Task) -> None:
        payload = valid_payload(title="Same every time", completed=True)

        first = client.put(f"/tasks/{sample_task.id}", json=payload).json()
        second = client.put(f"/tasks/{sample_task.id}", json=payload).json()

        assert first == second


class TestReplaceTaskFullReplacementSemantics:
    """Omitted optional fields reset, they are not merged."""

    def test_omitted_description_resets_to_empty(
        self, client: TestClient, sample_task: Task
    ) -> None:
        assert sample_task.description != ""

        response = client.put(f"/tasks/{sample_task.id}", json={"title": "Replaced"})

        assert response.status_code == 200
        assert response.json()["description"] == ""

    def test_omitted_completed_resets_to_false(self, client: TestClient) -> None:
        created = client.post("/tasks", json=valid_payload(completed=True)).json()

        response = client.put(f"/tasks/{created['id']}", json={"title": "Replaced"})

        assert response.json()["completed"] is False


class TestReplaceTaskNotFound:
    """Replacing something that is not there."""

    def test_unknown_id_returns_404(self, client: TestClient) -> None:
        response = client.put("/tasks/999", json=valid_payload())

        assert response.status_code == 404
        assert response.json() == {"detail": "Task with id 999 was not found."}

    def test_does_not_create_the_missing_task(self, client: TestClient) -> None:
        """This API does not support PUT-as-upsert."""
        client.put("/tasks/999", json=valid_payload())

        assert client.get("/tasks").json() == []

    def test_deleted_task_cannot_be_replaced(
        self, client: TestClient, sample_task: Task
    ) -> None:
        client.delete(f"/tasks/{sample_task.id}")

        assert (
            client.put(f"/tasks/{sample_task.id}", json=valid_payload()).status_code
            == 404
        )

    def test_validation_runs_before_the_existence_check(
        self, client: TestClient
    ) -> None:
        """A bad body on a missing id reports the body problem (422, not 404)."""
        response = client.put("/tasks/999", json={"title": ""})

        assert response.status_code == 422


class TestReplaceTaskValidation:
    """The body is validated exactly as on create."""

    @pytest.mark.parametrize(
        ("payload", "reason"),
        [
            ({}, "empty object"),
            ({"description": "no title"}, "missing title"),
            ({"title": ""}, "empty title"),
            ({"title": None}, "null title"),
            ({"title": 123}, "numeric title"),
            ({"title": "a" * 201}, "title too long"),
            ({"title": "ok", "description": "d" * 2001}, "description too long"),
            ({"title": "ok", "completed": "maybe"}, "unparsable completed"),
            ({"title": "ok", "surprise": 1}, "unknown field"),
        ],
        ids=lambda value: value if isinstance(value, str) else "",
    )
    def test_invalid_payload_returns_422(
        self,
        client: TestClient,
        sample_task: Task,
        payload: dict[str, Any],
        reason: str,
    ) -> None:
        response = client.put(f"/tasks/{sample_task.id}", json=payload)

        assert response.status_code == 422, f"expected 422 for {reason}"

    def test_rejects_an_id_in_the_body(
        self, client: TestClient, sample_task: Task
    ) -> None:
        response = client.put(f"/tasks/{sample_task.id}", json=valid_payload(id=99))

        assert response.status_code == 422

    def test_rejects_missing_body(self, client: TestClient, sample_task: Task) -> None:
        assert client.put(f"/tasks/{sample_task.id}").status_code == 422

    @pytest.mark.parametrize(
        "task_id", ["0", "-1", "abc"], ids=["zero", "negative", "letters"]
    )
    def test_invalid_path_id_returns_422(
        self, client: TestClient, task_id: str
    ) -> None:
        assert client.put(f"/tasks/{task_id}", json=valid_payload()).status_code == 422

    def test_rejected_replacement_leaves_the_task_unchanged(
        self, client: TestClient, sample_task: Task
    ) -> None:
        client.put(f"/tasks/{sample_task.id}", json={"title": ""})

        unchanged = client.get(f"/tasks/{sample_task.id}").json()
        assert unchanged["title"] == sample_task.title
        assert unchanged["description"] == sample_task.description
