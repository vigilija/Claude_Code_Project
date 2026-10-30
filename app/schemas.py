"""Pydantic schemas for request validation and response serialisation.

The schemas are split by direction of travel so the API contract stays
explicit:

* ``TaskCreate``  -- client-supplied payload for ``POST /tasks``.
* ``TaskUpdate``  -- client-supplied payload for ``PUT /tasks/{id}``.
* ``Task``        -- the full resource returned to clients (includes ``id``).

Keeping the input schemas separate from ``Task`` prevents clients from
setting or overwriting the server-generated ``id``.
"""

from pydantic import BaseModel, ConfigDict, Field


class TaskBase(BaseModel):
    """Fields shared by every task representation."""

    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Short, human-readable name of the task.",
        examples=["Write project documentation"],
    )
    description: str = Field(
        default="",
        max_length=2000,
        description="Optional longer explanation of the task.",
        examples=["Cover installation, configuration and the HTTP API."],
    )
    completed: bool = Field(
        default=False,
        description="Whether the task has been finished.",
    )

    # Reject unknown keys instead of silently ignoring them, so typos in a
    # client payload surface as a 422 rather than as a lost field.
    model_config = ConfigDict(extra="forbid")


class TaskCreate(TaskBase):
    """Payload accepted by ``POST /tasks``."""


class TaskUpdate(TaskBase):
    """Payload accepted by ``PUT /tasks/{id}``.

    ``PUT`` is a full replacement of the resource, so any field the client
    omits falls back to its schema default (``description=""``,
    ``completed=False``) rather than keeping the previous value.
    """


class Task(TaskBase):
    """A task as returned by the API."""

    id: int = Field(
        ...,
        ge=1,
        description="Server-generated unique identifier.",
        examples=[1],
    )
