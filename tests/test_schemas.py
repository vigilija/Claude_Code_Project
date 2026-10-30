"""Unit tests for the Pydantic schemas in :mod:`app.schemas`."""

import pytest
from pydantic import ValidationError

from app.schemas import Task, TaskCreate, TaskUpdate


class TestTaskCreate:
    """The create payload."""

    def test_title_is_required(self) -> None:
        with pytest.raises(ValidationError):
            TaskCreate()  # type: ignore[call-arg]

    def test_optional_fields_have_defaults(self) -> None:
        task = TaskCreate(title="Only a title")

        assert task.description == ""
        assert task.completed is False

    def test_rejects_unknown_fields(self) -> None:
        with pytest.raises(ValidationError):
            TaskCreate(title="ok", unexpected="value")  # type: ignore[call-arg]

    def test_rejects_an_id(self) -> None:
        """``id`` belongs to the response schema only."""
        with pytest.raises(ValidationError):
            TaskCreate(title="ok", id=1)  # type: ignore[call-arg]

    @pytest.mark.parametrize("title", ["", "a" * 201], ids=["too short", "too long"])
    def test_enforces_title_length(self, title: str) -> None:
        with pytest.raises(ValidationError):
            TaskCreate(title=title)

    def test_enforces_description_length(self) -> None:
        with pytest.raises(ValidationError):
            TaskCreate(title="ok", description="d" * 2001)


class TestTaskUpdate:
    """The replace payload mirrors the create payload."""

    def test_has_the_same_fields_as_create(self) -> None:
        assert set(TaskUpdate.model_fields) == set(TaskCreate.model_fields)

    def test_title_is_required(self) -> None:
        """Required even on update, because PUT replaces the whole resource."""
        with pytest.raises(ValidationError):
            TaskUpdate()  # type: ignore[call-arg]


class TestTask:
    """The response schema."""

    def test_requires_an_id(self) -> None:
        with pytest.raises(ValidationError):
            Task(title="ok")  # type: ignore[call-arg]

    def test_rejects_a_non_positive_id(self) -> None:
        with pytest.raises(ValidationError):
            Task(id=0, title="ok")

    def test_serialises_all_four_fields(self) -> None:
        task = Task(id=1, title="ok", description="d", completed=True)

        assert task.model_dump() == {
            "id": 1,
            "title": "ok",
            "description": "d",
            "completed": True,
        }
