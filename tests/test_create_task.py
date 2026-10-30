"""Tests for ``POST /tasks``."""

from typing import Any

import pytest
from fastapi.testclient import TestClient

from tests.conftest import valid_payload


class TestCreateTaskSuccess:
    """Creating a task with a well-formed payload."""

    def test_returns_201_with_the_created_task(self, client: TestClient) -> None:
        response = client.post("/tasks", json=valid_payload())

        assert response.status_code == 201
        assert response.json() == {
            "id": 1,
            "title": "Buy milk",
            "description": "Two litres, semi-skimmed.",
            "completed": False,
        }

    def test_optional_fields_fall_back_to_defaults(self, client: TestClient) -> None:
        """Only ``title`` is required."""
        response = client.post("/tasks", json={"title": "Minimal"})

        assert response.status_code == 201
        assert response.json() == {
            "id": 1,
            "title": "Minimal",
            "description": "",
            "completed": False,
        }

    def test_accepts_a_task_that_is_already_completed(self, client: TestClient) -> None:
        response = client.post("/tasks", json=valid_payload(completed=True))

        assert response.status_code == 201
        assert response.json()["completed"] is True

    def test_assigns_sequential_ids(self, client: TestClient) -> None:
        ids = [
            client.post("/tasks", json=valid_payload(title=f"Task {n}")).json()["id"]
            for n in range(1, 4)
        ]

        assert ids == [1, 2, 3]

    def test_does_not_reuse_the_id_of_a_deleted_task(self, client: TestClient) -> None:
        """Ids are monotonic, so a stale client cannot address a new task."""
        first = client.post("/tasks", json=valid_payload()).json()["id"]
        client.delete(f"/tasks/{first}")

        second = client.post("/tasks", json=valid_payload()).json()["id"]

        assert second != first

    def test_created_task_is_retrievable(self, client: TestClient) -> None:
        created = client.post("/tasks", json=valid_payload()).json()

        fetched = client.get(f"/tasks/{created['id']}")

        assert fetched.status_code == 200
        assert fetched.json() == created

    def test_allows_duplicate_titles(self, client: TestClient) -> None:
        """Titles are not a unique key."""
        first = client.post("/tasks", json=valid_payload())
        second = client.post("/tasks", json=valid_payload())

        assert first.status_code == second.status_code == 201
        assert first.json()["id"] != second.json()["id"]


class TestCreateTaskBoundaries:
    """Field limits at their exact edges."""

    def test_accepts_single_character_title(self, client: TestClient) -> None:
        assert client.post("/tasks", json={"title": "x"}).status_code == 201

    def test_accepts_title_of_maximum_length(self, client: TestClient) -> None:
        assert client.post("/tasks", json={"title": "a" * 200}).status_code == 201

    def test_rejects_title_one_character_too_long(self, client: TestClient) -> None:
        assert client.post("/tasks", json={"title": "a" * 201}).status_code == 422

    def test_accepts_description_of_maximum_length(self, client: TestClient) -> None:
        payload = valid_payload(description="d" * 2000)

        assert client.post("/tasks", json=payload).status_code == 201

    def test_rejects_description_one_character_too_long(
        self, client: TestClient
    ) -> None:
        payload = valid_payload(description="d" * 2001)

        assert client.post("/tasks", json=payload).status_code == 422

    def test_accepts_empty_description_explicitly(self, client: TestClient) -> None:
        response = client.post("/tasks", json=valid_payload(description=""))

        assert response.status_code == 201
        assert response.json()["description"] == ""

    def test_accepts_unicode_and_emoji(self, client: TestClient) -> None:
        payload = valid_payload(title="Ačiū 🙏 проверка", description="日本語の説明")

        response = client.post("/tasks", json=payload)

        assert response.status_code == 201
        assert response.json()["title"] == "Ačiū 🙏 проверка"
        assert response.json()["description"] == "日本語の説明"

    def test_preserves_newlines_in_description(self, client: TestClient) -> None:
        response = client.post("/tasks", json=valid_payload(description="a\nb\tc"))

        assert response.json()["description"] == "a\nb\tc"

    def test_does_not_interpret_html_in_the_title(self, client: TestClient) -> None:
        """Input is stored verbatim; escaping is the client's concern."""
        response = client.post("/tasks", json=valid_payload(title="<b>bold</b>"))

        assert response.json()["title"] == "<b>bold</b>"


class TestCreateTaskValidation:
    """Malformed payloads are rejected with 422."""

    @pytest.mark.parametrize(
        ("payload", "reason"),
        [
            ({}, "empty object"),
            ({"description": "no title"}, "missing title"),
            ({"title": ""}, "empty title"),
            ({"title": None}, "null title"),
            ({"title": 123}, "numeric title"),
            ({"title": ["a"]}, "list title"),
            ({"title": {"a": 1}}, "object title"),
            ({"title": "ok", "description": None}, "null description"),
            ({"title": "ok", "description": 5}, "numeric description"),
            ({"title": "ok", "completed": None}, "null completed"),
            ({"title": "ok", "completed": "maybe"}, "unparsable completed"),
            ({"title": "ok", "completed": []}, "list completed"),
        ],
        ids=lambda value: value if isinstance(value, str) else "",
    )
    def test_invalid_payload_returns_422(
        self, client: TestClient, payload: dict[str, Any], reason: str
    ) -> None:
        response = client.post("/tasks", json=payload)

        assert response.status_code == 422, f"expected 422 for {reason}"

    def test_rejects_client_supplied_id(self, client: TestClient) -> None:
        """``id`` is server-owned, so sending one is an error, not a hint."""
        response = client.post("/tasks", json=valid_payload(id=42))

        assert response.status_code == 422

    def test_rejects_unknown_field(self, client: TestClient) -> None:
        """``extra="forbid"`` turns a typo into a loud failure."""
        response = client.post("/tasks", json=valid_payload(titel="typo"))

        assert response.status_code == 422

    def test_rejects_malformed_json(self, client: TestClient) -> None:
        response = client.post(
            "/tasks",
            content='{"title": "unterminated',
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 422

    def test_rejects_missing_body(self, client: TestClient) -> None:
        assert client.post("/tasks").status_code == 422

    def test_rejects_json_array_as_body(self, client: TestClient) -> None:
        assert client.post("/tasks", json=[valid_payload()]).status_code == 422

    def test_validation_error_identifies_the_field(self, client: TestClient) -> None:
        response = client.post("/tasks", json={"title": ""})

        detail = response.json()["detail"]
        assert detail[0]["loc"] == ["body", "title"]

    def test_rejected_payload_is_not_stored(self, client: TestClient) -> None:
        client.post("/tasks", json={"title": ""})

        assert client.get("/tasks").json() == []


class TestCreateTaskCurrentlyPermitted:
    """Inputs the API accepts today, pinned so a change cannot pass unnoticed.

    These document current behaviour rather than endorse it -- see the
    whitespace case, which is arguably a validation gap: ``min_length=1``
    counts characters, so a blank-looking title satisfies it.
    """

    def test_whitespace_only_title_is_accepted(self, client: TestClient) -> None:
        response = client.post("/tasks", json={"title": "   "})

        assert response.status_code == 201
        assert response.json()["title"] == "   "

    def test_surrounding_whitespace_is_not_trimmed(self, client: TestClient) -> None:
        response = client.post("/tasks", json={"title": "  padded  "})

        assert response.json()["title"] == "  padded  "

    @pytest.mark.parametrize(
        ("value", "expected"),
        [("true", True), ("false", False), (1, True), (0, False)],
        ids=["string-true", "string-false", "int-1", "int-0"],
    )
    def test_completed_coerces_json_booleans(
        self, client: TestClient, value: object, expected: bool
    ) -> None:
        """Pydantic's lax mode converts these to real booleans."""
        response = client.post("/tasks", json=valid_payload(completed=value))

        assert response.status_code == 201
        assert response.json()["completed"] is expected
