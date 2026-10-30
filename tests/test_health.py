"""Tests for the ``GET /health`` endpoint."""

from fastapi.testclient import TestClient


class TestHealthCheck:
    """The health endpoint reports liveness."""

    def test_returns_200_and_ok_status(self, client: TestClient) -> None:
        response = client.get("/health")

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_responds_with_json_content_type(self, client: TestClient) -> None:
        response = client.get("/health")

        assert response.headers["content-type"].startswith("application/json")

    def test_needs_no_seeded_data(self, client: TestClient) -> None:
        """Health is independent of the store's contents."""
        assert client.get("/health").status_code == 200
