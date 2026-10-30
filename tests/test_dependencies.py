"""Tests for :mod:`app.dependencies`.

Every other test overrides ``get_task_store`` with an isolated store, which
means the real provider -- the wiring the deployed app actually uses -- would
otherwise go unexercised.
"""

from app.dependencies import get_task_store
from app.main import app
from app.storage import TaskStore, task_store


class TestGetTaskStore:
    """The default provider hands out the process-wide store."""

    def test_returns_a_task_store(self) -> None:
        assert isinstance(get_task_store(), TaskStore)

    def test_returns_the_module_level_singleton(self) -> None:
        assert get_task_store() is task_store

    def test_is_stable_across_calls(self) -> None:
        """Requests must not each get their own empty store."""
        assert get_task_store() is get_task_store()


class TestDependencyOverridesAreClean:
    """The ``client`` fixture must undo its override when it tears down."""

    def test_app_has_no_leftover_overrides(self) -> None:
        assert app.dependency_overrides == {}
