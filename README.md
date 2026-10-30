# Task Management API

A small REST API for managing tasks, built with Python 3.13 and FastAPI.
Tasks are stored in an in-memory list, so all data is discarded when the
server stops.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux
pip install -r requirements.txt
```

## Running

```bash
uvicorn app.main:app --reload
```

* API root: <http://127.0.0.1:8000>
* Interactive docs (Swagger UI): <http://127.0.0.1:8000/docs>
* OpenAPI schema: <http://127.0.0.1:8000/openapi.json>

## Endpoints

| Method | Path          | Success | Description                      |
| ------ | ------------- | ------- | -------------------------------- |
| GET    | `/tasks`      | 200     | List all tasks                   |
| GET    | `/tasks/{id}` | 200     | Retrieve one task                |
| POST   | `/tasks`      | 201     | Create a task                    |
| PUT    | `/tasks/{id}` | 200     | Replace a task in full           |
| DELETE | `/tasks/{id}` | 204     | Delete a task                    |
| GET    | `/health`     | 200     | Health check                     |

A request for an unknown `id` returns `404`. An invalid body or a
non-positive `id` returns `422` with Pydantic's validation details.

## Task resource

```json
{
  "id": 1,
  "title": "Write project documentation",
  "description": "Cover installation and the HTTP API.",
  "completed": false
}
```

`id` is assigned by the server and cannot be set by the client. `title` is
required (1-200 characters); `description` defaults to `""` and `completed`
defaults to `false`.

## Example requests

```bash
curl -X POST http://127.0.0.1:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"title": "Buy milk", "description": "Two litres"}'

curl http://127.0.0.1:8000/tasks
curl http://127.0.0.1:8000/tasks/1

curl -X PUT http://127.0.0.1:8000/tasks/1 \
  -H "Content-Type: application/json" \
  -d '{"title": "Buy milk", "description": "Two litres", "completed": true}'

curl -X DELETE http://127.0.0.1:8000/tasks/1
```

## Project layout

```
app/
  main.py          FastAPI application, router registration, /health
  schemas.py       Pydantic models for requests and responses
  storage.py       Thread-safe in-memory TaskStore
  dependencies.py  Dependency provider for the store
  routers/
    tasks.py       The /tasks endpoints
```

The HTTP layer talks to storage only through `TaskStore`, so replacing the
in-memory list with a database means reimplementing that one class.
