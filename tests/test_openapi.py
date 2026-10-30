"""Tests for the generated OpenAPI schema and docs endpoints.

The schema is the API's published contract, so a change here is a change
clients can see.
"""

from fastapi.testclient import TestClient


class TestOpenApiSchema:
    """The documented surface matches the implementation."""

    def test_schema_is_served(self, client: TestClient) -> None:
        assert client.get("/openapi.json").status_code == 200

    def test_documents_exactly_the_expected_paths(self, client: TestClient) -> None:
        paths = client.get("/openapi.json").json()["paths"]

        assert sorted(paths) == ["/health", "/tasks", "/tasks/{task_id}"]

    def test_documents_the_expected_methods(self, client: TestClient) -> None:
        paths = client.get("/openapi.json").json()["paths"]

        assert sorted(paths["/tasks"]) == ["get", "post"]
        assert sorted(paths["/tasks/{task_id}"]) == ["delete", "get", "put"]

    def test_documents_the_success_status_codes(self, client: TestClient) -> None:
        paths = client.get("/openapi.json").json()["paths"]

        assert "200" in paths["/tasks"]["get"]["responses"]
        assert "201" in paths["/tasks"]["post"]["responses"]
        assert "200" in paths["/tasks/{task_id}"]["put"]["responses"]
        assert "204" in paths["/tasks/{task_id}"]["delete"]["responses"]

    def test_documents_404_on_single_task_routes(self, client: TestClient) -> None:
        route = client.get("/openapi.json").json()["paths"]["/tasks/{task_id}"]

        for method in ("get", "put", "delete"):
            assert "404" in route[method]["responses"], method

    def test_declares_the_task_schema(self, client: TestClient) -> None:
        schemas = client.get("/openapi.json").json()["components"]["schemas"]

        assert set(schemas["Task"]["properties"]) == {
            "id",
            "title",
            "description",
            "completed",
        }

    def test_create_schema_does_not_expose_id(self, client: TestClient) -> None:
        schemas = client.get("/openapi.json").json()["components"]["schemas"]

        assert "id" not in schemas["TaskCreate"]["properties"]


class TestDocsEndpoints:
    """Interactive documentation is reachable."""

    def test_swagger_ui_is_served(self, client: TestClient) -> None:
        assert client.get("/docs").status_code == 200

    def test_redoc_is_served(self, client: TestClient) -> None:
        assert client.get("/redoc").status_code == 200


class TestUnknownRoutes:
    """Anything outside the documented surface is a 404."""

    def test_unknown_path_returns_404(self, client: TestClient) -> None:
        assert client.get("/not-a-route").status_code == 404

    def test_unknown_nested_path_returns_404(self, client: TestClient) -> None:
        assert client.get("/tasks/1/subtasks").status_code == 404
