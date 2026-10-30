"""End-to-end flows that span several endpoints.

These guard the interactions the per-endpoint tests cannot see on their own.
"""

from fastapi.testclient import TestClient

from tests.conftest import valid_payload


class TestFullCrudLifecycle:
    """One task through create, read, list, replace and delete."""

    def test_task_lifecycle(self, client: TestClient) -> None:
        created = client.post("/tasks", json=valid_payload(title="Draft report"))
        assert created.status_code == 201
        task_id = created.json()["id"]

        assert client.get(f"/tasks/{task_id}").status_code == 200
        assert len(client.get("/tasks").json()) == 1

        replaced = client.put(
            f"/tasks/{task_id}",
            json=valid_payload(title="Draft report", completed=True),
        )
        assert replaced.status_code == 200
        assert replaced.json()["completed"] is True

        assert client.delete(f"/tasks/{task_id}").status_code == 204
        assert client.get(f"/tasks/{task_id}").status_code == 404
        assert client.get("/tasks").json() == []


class TestMixedOperations:
    """Interleaved writes keep the collection consistent."""

    def test_create_delete_create_keeps_ids_unique(self, client: TestClient) -> None:
        first = client.post("/tasks", json=valid_payload(title="A")).json()["id"]
        second = client.post("/tasks", json=valid_payload(title="B")).json()["id"]
        client.delete(f"/tasks/{first}")
        third = client.post("/tasks", json=valid_payload(title="C")).json()["id"]

        assert len({first, second, third}) == 3
        assert [task["title"] for task in client.get("/tasks").json()] == ["B", "C"]

    def test_replacing_then_deleting_works(self, client: TestClient) -> None:
        task_id = client.post("/tasks", json=valid_payload()).json()["id"]
        client.put(f"/tasks/{task_id}", json=valid_payload(title="Changed"))

        assert client.delete(f"/tasks/{task_id}").status_code == 204
        assert client.get("/tasks").json() == []

    def test_failed_requests_do_not_corrupt_state(self, client: TestClient) -> None:
        """A run of rejected requests leaves the collection as it was."""
        task_id = client.post("/tasks", json=valid_payload(title="Keep me")).json()[
            "id"
        ]

        client.post("/tasks", json={"title": ""})
        client.put(f"/tasks/{task_id}", json={})
        client.put("/tasks/999", json=valid_payload())
        client.delete("/tasks/999")
        client.get("/tasks/0")

        remaining = client.get("/tasks").json()
        assert len(remaining) == 1
        assert remaining[0]["title"] == "Keep me"


class TestStoreIsolationBetweenTests:
    """The ``client`` fixture must hand out a fresh store every time.

    These two tests would interfere with each other if it did not, so a
    failure here means the whole suite's results are order-dependent.
    """

    def test_first_test_creates_a_task(self, client: TestClient) -> None:
        client.post("/tasks", json=valid_payload())

        assert len(client.get("/tasks").json()) == 1

    def test_second_test_starts_empty(self, client: TestClient) -> None:
        assert client.get("/tasks").json() == []
